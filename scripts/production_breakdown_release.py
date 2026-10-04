#!/usr/bin/env python3
"""Prepare and apply the reviewed breakdown release in guarded serial phases.

No confirmation is inferred by this script. Apply requires the user's explicit
approval of both candidates and the internal task API exception described in the
delivery notes. It never invokes _complete, pushes, or restores a live snapshot.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import material_review_release as service
import publish_generation as publication
from generation_workspace import verify_media

base=service.base
TASK='task-20261004-0007'
ROOT=Path(__file__).resolve().parents[1]
HELPERS=('production_breakdown_release.py','material_review_release.py','autonomous_optimization_release.py',
         'integrate_generation_review_system.py','publish_generation.py','generation_publication.py','generation_workspace.py')


def prepare(a):
    root=a.bundle.resolve()
    base.require((ROOT/'.runtime').resolve() in root.parents and not root.exists(),'new task runtime bundle required')
    service.prepare(argparse.Namespace(**{**vars(a),'bundle':root/'service','task':TASK,'story_worktree':ROOT}))
    m=base.read(root/'service/manifest.json')
    hashes={}
    for name in HELPERS:
        raw=base.git_file(ROOT,a.story_candidate,'scripts/'+name)
        base.require(raw==(ROOT/'scripts'/name).read_bytes(),'release helper differs from committed candidate')
        hashes[name]=base.sha(raw)
    raw=base.git_file(ROOT,a.story_candidate,'production/breakdown/publication.json')
    base.require(raw==(ROOT/'production/breakdown/publication.json').read_bytes(),'publication differs from committed candidate')
    base.write_once(root/'publication.json',raw)
    manifest=json.loads(base.git_file(ROOT,a.story_candidate,'export/manifest.json'))
    originals=[{'file':n[len('assets/'):],'sha256':v,'bytes':(ROOT/'export'/n).stat().st_size}
               for n,v in manifest['files'].items() if n.startswith('assets/')]
    verify_media(ROOT,originals)
    api=a.task_api.resolve()
    base.require((api/'codex_project.py').is_file() and (api/'task_worktree.py').is_file(),'task API not found')
    outer={'format':'production-breakdown-release-v1','task':TASK,'service_manifest_sha256':base.sha((root/'service/manifest.json').read_bytes()),
           'publication_sha256':base.sha(raw),'helpers':hashes,'originals':originals,'task_api':str(api),
           'task_api_hashes':{p.name:base.sha(p.read_bytes()) for p in sorted(api.glob('*.py'))},
           'requires_explicit_internal_api_exception':True,'complete_invoked':False,'push':False,
           'prepared_at':datetime.now(timezone.utc).isoformat()}
    base.save(root/'manifest.json',outer)
    print(json.dumps({'bundle':str(root),'manifest_sha256':base.sha((root/'manifest.json').read_bytes()),
                      'candidates':{'story':m['story_candidate'],'system':m['system_candidate']},'formal_writes':False}))


def load(path):
    root=path.resolve();m=base.read(root/'manifest.json')
    base.require(m['format']=='production-breakdown-release-v1' and m['task']==TASK,'wrong breakdown bundle')
    base.require(base.sha((root/'service/manifest.json').read_bytes())==m['service_manifest_sha256'],'service manifest changed')
    base.require(base.sha((root/'publication.json').read_bytes())==m['publication_sha256'],'publication package changed')
    base.require(base.sha((ROOT/'production/breakdown/publication.json').read_bytes())==m['publication_sha256'],'worktree publication changed')
    for name,digest in m['helpers'].items():
        base.require(base.sha((ROOT/'scripts'/name).read_bytes())==digest,'release helper changed')
    for name,digest in m['task_api_hashes'].items():
        base.require(base.sha((Path(m['task_api'])/name).read_bytes())==digest,'task runtime changed; reprepare the phase exception')
    _,s=service.load_bundle(root/'service')
    sys.path.insert(0,s['system_worktree'])
    return root,m,s


def originals(m,s):
    verify_media(ROOT,m['originals'])
    verify_media(Path(s['story_main']),m['originals'])
    return len(m['originals'])


def rehearse(root,s,apply=False):
    return publication.run_publication(ROOT,Path(s['story_main']),ROOT/'production/breakdown/publication.json',
        'breakdown-'+('apply-' if apply else 'preflight-')+str(time.time_ns()),apply=apply,source_commit=s['story_candidate'])


def preflight(a):
    root,m,s=load(a.bundle)
    service.preflight(argparse.Namespace(bundle=root/'service'))
    count=originals(m,s);result=rehearse(root,s)
    base.save(root/('preflight-'+str(time.time_ns())+'.json'),result)
    print(json.dumps({'preflight_only':True,'formal_database_written':False,'originals_verified':count,
                      'publication_id':result['publication_id'],'scope':result['scope']}))


def integrate_story(root,m,s,note):
    # This is the existing task runner's authenticated, locked integration path.
    # Calling it outside its CLI requires the separately reviewed user exception.
    sys.path.insert(0,m['task_api'])
    import codex_project as runner
    import task_worktree
    record,session=runner.authenticate_task_session(Path(s['story_main']),TASK)
    stage=record.get('integration') or {}
    base.require(stage.get('candidate_commit')==s['story_candidate'] and stage.get('target_commit')==s['story_target'],'task candidate or target changed')
    if stage.get('phase') in ('approved','applied'):
        task_worktree.recover_integration(Path(s['story_main']),record,complete=False)
    else:
        task_worktree.integrate(Path(s['story_main']),record,session,note,complete=False)
    base.require(base.git(s['story_main'],'rev-parse','HEAD')==s['story_candidate'],'story integration differs')
    base.save(root/'story-integration.json',{'candidate':s['story_candidate'],'task':TASK,'complete':False,'push':False})


def runtime_preflight(root,s,image):
    """Reject a foreign deployment before any code or business-data mutation."""
    current=service.inspect(base.APP)
    if base.safe_container(current)==s['previous_app']:
        service.checks(root/'service',s,live=True)
        return
    release=Path(s['story_main'])/'.runtime/service-releases'/s['release_name']
    expected=base.compose_definition(s,image,release)['services']['app']
    mounts={v['target']:(v['source'],not v['read_only']) for v in expected['volumes']}
    base.require(current['Image']==image['image'] and
        {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']}==mounts,
        'another formal runtime is active; stop before integration')
    proxy=base.safe_container(service.inspect(base.NGINX))
    base.require(proxy=={**s['previous_nginx'],'config_files':str(release/'compose.release.json')},
        'formal proxy drifted; stop before integration')
    for name in base.INSTANCE_FILES:
        base.require((release/'instance'/name).read_bytes()==(root/'service/instance'/name).read_bytes(),
                     'candidate overlay drifted; stop before integration')


def apply(a):
    base.require(a.apply and a.allow_internal_task_api,'apply requires actual user confirmation including the internal task API exception')
    root,m,s=load(a.bundle)
    base.require(base.sha((root/'manifest.json').read_bytes())==a.manifest_sha256,'confirmed breakdown digest changed')
    base.require(base.sha((root/'service/image.json').read_bytes())==a.image_receipt_sha256,'confirmed image digest changed')
    image=service.checks(root/'service',s,live=False)
    runtime_preflight(root,s,image)
    originals(m,s)
    # Validate the latest live rows before changing either main checkout. The
    # write phase repeats the same optimistic guards inside its transaction.
    rehearse(root,s)
    integrate_story(root,m,s,a.note)
    base.run([sys.executable,ROOT/'scripts/integrate_generation_review_system.py','--plan',root/'service/system-delivery.json',
              '--apply','--receipt',root/'system-integration.json'])
    delta=rehearse(root,s,apply=True)
    base.save(root/('publication-'+str(time.time_ns())+'.json'),delta)
    service.apply(argparse.Namespace(bundle=root/'service',apply=True,
        manifest_sha256=m['service_manifest_sha256'],image_receipt_sha256=a.image_receipt_sha256))
    print(json.dumps({'status':'formal_browser_pending','publication_id':delta['publication_id'],
        'story_candidate':s['story_candidate'],'system_candidate':s['system_candidate'],
        'next':'Perform the one formal browser acceptance, then invoke codex.project task _complete.','push':False,'complete_invoked':False}))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare');q.add_argument('--bundle',type=Path,required=True);q.add_argument('--system-worktree',type=Path,required=True)
    for name in ('story-candidate','system-candidate','story-target','system-target'):q.add_argument('--'+name,required=True)
    q.add_argument('--task-api',type=Path,default=Path.home()/'bin/codex.project.d/scripts')
    q=sub.add_parser('preflight');q.add_argument('--bundle',type=Path,required=True)
    q=sub.add_parser('apply');q.add_argument('--bundle',type=Path,required=True);q.add_argument('--apply',action='store_true')
    q.add_argument('--allow-internal-task-api',action='store_true');q.add_argument('--manifest-sha256',required=True)
    q.add_argument('--image-receipt-sha256',required=True);q.add_argument('--note',required=True)
    a=p.parse_args();globals()[a.command](a)


if __name__=='__main__':main()
