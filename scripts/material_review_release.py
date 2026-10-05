#!/usr/bin/env python3
"""Prepare an immutable code-only release; apply only the user-confirmed bundle.

No business-data import, generation, acceptance, task completion or push. The
system fast-forward, live row-preservation checks and service switch run serially.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
import autonomous_optimization_release as base

TASK='task-20261004-0004'
RELEASE_PREFIXES={TASK:'materials-20261004-0004', 'task-20261004-0005':'asset-cleanup-20261004-0005',
                  'task-20261004-0007':'breakdown-20261004-0007',
                  'task-20261004-0008':'ui-unification-20261004-0008',
                  'task-20261004-0009':'ui-material-model-20261004-0009',
                  'task-20261005-0001':'autonomous-20261005-0001',
                  'entity-acceptance-20261004':'entity-acceptance-20261004'}
require,sha,read,save,run,git,inspect=base.require,base.sha,base.read,base.save,base.run,base.git,base.inspect


def release_name(task, story_candidate, system_candidate):
    require(task in RELEASE_PREFIXES, 'unsupported release task')
    return RELEASE_PREFIXES[task]+'-'+story_candidate[:12]+'-'+system_candidate[:12]


def prepare(a):
    task=getattr(a,'task',TASK)
    release_id=release_name(task,a.story_candidate,a.system_candidate)
    story,system=a.story_worktree.resolve(),a.system_worktree.resolve()
    sm,gm=base.primary(story),base.primary(system)
    base.repo_check(story,sm,a.story_candidate,a.story_target)
    base.repo_check(system,gm,a.system_candidate,a.system_target,system=True)
    root=a.bundle.resolve();require((story/'.runtime').resolve() in root.parents and not root.exists(),'new task runtime bundle required')
    app,nginx=inspect(base.APP),inspect(base.NGINX)
    old,proxy=base.safe_container(app),base.safe_container(nginx)
    require(old['working_dir']==str(sm) and proxy['working_dir']==str(sm),'another formal instance')
    require(proxy['ports']==base.PORTS and not nginx['Mounts'],'formal proxy layout changed')
    require(app['State']['Running'] and app['State'].get('Health',{}).get('Status')=='healthy','formal app unhealthy')
    mounts={m['Destination']:m for m in old['mounts']}
    require(set(mounts)=={'/instance','/instance/config/instance.json','/instance/content/production-approach.json','/run/local-ca/cacert.pem'},'review unknown formal mounts')
    require(mounts['/instance']['Source']==str(sm) and mounts['/instance']['RW'],'normal live instance mount differs')
    require(all(not mounts[n]['RW'] for n in mounts if n!='/instance'),'overlay and CA must be read-only')
    # Preserve exact service process/environment semantics of the verified images.
    for current in (app,nginx):
        image=inspect(current['Image'],image=True)
        for key in ('Cmd','Entrypoint','WorkingDir','User'):
            require((current['Config'].get(key) or '')==(image['Config'].get(key) or ''),'nondefault process configuration')
        require(current['HostConfig']['RestartPolicy']=={'Name':'unless-stopped','MaximumRetryCount':0},'restart policy changed')
    require(base.env_values(nginx)==base.env_values(inspect(nginx['Image'],image=True)),'custom proxy environment')
    hashes={}
    def put(rel,raw):base.write_once(root/rel,raw);hashes[rel]=sha(raw)
    for name in base.INSTANCE_FILES:put('instance/'+name,base.git_file(story,a.story_candidate,name))
    cfg=read(root/'instance/config/instance.json');require(cfg['review_desk_commit']==a.system_candidate,'candidate instance pin differs')
    current_files={name:sha(Path(mounts['/instance/'+name]['Source']).read_bytes()) for name in base.INSTANCE_FILES}
    require(current_files['content/production-approach.json']==hashes['instance/content/production-approach.json'],'approach content change is outside this release')
    source={}
    for line in git(system,'ls-tree','-r',a.system_candidate,'--','review_desk').splitlines():
        header,name=line.split('\t',1);require(header.split()[0] in ('100644','100755'),'special source file')
        raw=base.git_file(system,a.system_candidate,name);put('build/'+name,raw);source[name]=sha(raw)
    tag=base.base_image_tag(app['Image'])
    put('build/Dockerfile',('FROM '+tag+'\nRUN rm -rf /app/review_desk\nCOPY review_desk /app/review_desk\n').encode())
    for helper in ('material_review_release.py','autonomous_optimization_release.py','integrate_generation_review_system.py'):
        raw=base.git_file(story,a.story_candidate,'scripts/'+helper);require(raw==(story/'scripts'/helper).read_bytes(),'helper differs from committed candidate');put('helpers/'+helper,raw)
    files=old['config_files'].split(',');require(files==proxy['config_files'].split(','),'compose sets differ')
    plan={'format':'generation-system-delivery-v1','task':task,'push':False,'system_main_from_story_main':os.path.relpath(gm,sm),'system_worktree':os.path.relpath(system,story),'expected_target':a.system_target,'candidate':a.system_candidate}
    put('system-delivery.json',json.dumps(plan,ensure_ascii=False,indent=2).encode()+b'\n')
    m={'format':'material-review-release-v1','task':task,'push':False,'story_worktree':str(story),'system_worktree':str(system),'story_main':str(sm),'system_main':str(gm),'story_candidate':a.story_candidate,'story_target':a.story_target,'system_candidate':a.system_candidate,'system_target':a.system_target,'release_name':release_id,'hashes':hashes,'source_hashes':source,'base_image_tag':tag,'previous_app':old,'previous_nginx':proxy,'previous_compose_hashes':{f:sha(Path(f).read_bytes()) for f in files},'previous_instance_hashes':current_files,'ca_sha256':sha(Path(mounts['/run/local-ca/cacert.pem']['Source']).read_bytes()),'prepared_at':datetime.now(timezone.utc).isoformat()}
    save(root/'manifest.json',m);print(json.dumps({'bundle':str(root),'manifest_sha256':sha((root/'manifest.json').read_bytes()),'formal_writes':False,'business_delta':0}))


def load_bundle(path):
    root=path.resolve();m=read(root/'manifest.json');require(m.get('format')=='material-review-release-v1' and m.get('task') in RELEASE_PREFIXES and m.get('push') is False,'wrong bundle')
    require(m.get('release_name')==release_name(m['task'],m['story_candidate'],m['system_candidate']),'release task or name differs')
    for rel,value in m['hashes'].items():
        require(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'invalid package path');require(sha((root/rel).read_bytes())==value,'bundle changed: '+rel)
    require(sha(Path(__file__).read_bytes())==m['hashes']['helpers/material_review_release.py'],'wrapper changed')
    require(sha(Path(base.__file__).read_bytes())==m['hashes']['helpers/autonomous_optimization_release.py'],'runtime helper changed')
    return root,m


def build(a):
    root,m=load_bundle(a.bundle);require(not (root/'image.json').exists(),'immutable image already prepared')
    base.pin_base_image(m['previous_app']['image'],m['base_image_tag'])
    tag='story-review-desk:materials-'+m['system_candidate'][:12]+'-'+m['story_candidate'][:12]
    run([base.DOCKER,'build','--pull=false','--network=none','-t',tag,root/'build'])
    image=inspect(tag,image=True)['Id'];base.source_check(image,m['source_hashes'])
    save(root/'image.json',{'image':image,'tag':tag,'source_verified':True,'manifest_sha256':sha((root/'manifest.json').read_bytes())})
    print(json.dumps({'image':image,'image_receipt_sha256':sha((root/'image.json').read_bytes()),'formal_writes':False}))


def checks(root,m,live=True):
    # The breakdown release has an explicitly approved two-stage integration:
    # code first, data/service next, task completion after formal page acceptance.
    base.repo_check(m['story_worktree'],m['story_main'],m['story_candidate'],m['story_target'],system=m['task']=='task-20261004-0007')
    base.repo_check(m['system_worktree'],m['system_main'],m['system_candidate'],m['system_target'],system=True)
    for path,value in m['previous_compose_hashes'].items():require(sha(Path(path).read_bytes())==value,'compose input drifted')
    ca=next(x['Source'] for x in m['previous_app']['mounts'] if x['Destination']=='/run/local-ca/cacert.pem');require(sha(Path(ca).read_bytes())==m['ca_sha256'],'CA drifted')
    image=read(root/'image.json');require(image['manifest_sha256']==sha((root/'manifest.json').read_bytes()),'image manifest differs');base.source_check(image['image'],m['source_hashes'])
    if live:
        require(base.safe_container(inspect(base.APP))==m['previous_app'] and base.safe_container(inspect(base.NGINX))==m['previous_nginx'],'formal service drifted')
        for name,value in m['previous_instance_hashes'].items():
            path=next(x['Source'] for x in m['previous_app']['mounts'] if x['Destination']=='/instance/'+name);require(sha(Path(path).read_bytes())==value,'formal overlay drifted')
    return image


def preflight(a):
    root,m=load_bundle(a.bundle);image=checks(root,m)
    result=json.loads(run([sys.executable,root/'helpers/integrate_generation_review_system.py','--plan',root/'system-delivery.json','--system-main',m['system_main'],'--system-worktree',m['system_worktree']]))
    require(result['preflight_only'],'unexpected integrator action')
    print(json.dumps({'preflight_only':True,'manifest_sha256':sha((root/'manifest.json').read_bytes()),'image_receipt_sha256':sha((root/'image.json').read_bytes()),'image':image['image']}))


def preserved(before,after):
    old,new=base.rows(before),base.rows(after);require(old.keys()==new.keys(),'database table set changed')
    evidence={}
    mutable={'objects','comments','configurations','material_rounds','material_members','sources'}
    for table,value in old.items():
        require(value['schema']==new[table]['schema'],'business table schema changed')
        if table not in mutable:
            a=Counter(sha(base.canonical(v)) for v in value['rows']);b=Counter(sha(base.canonical(v)) for v in new[table]['rows']);require(not a-b,'immutable history lost: '+table)
        else:
            # Concurrent user edits may advance current heads/status. Keep every
            # original identity and every immutable history/event; never restore.
            keys={'objects':('id','kind','created_at'),'comments':('id','target_object_id','target_revision_id','anchor','created_at'),'sources':('id',),'configurations':('scope',),'material_rounds':('material_id','number','created_at'),'material_members':('material_id','number','revision_id')}[table]
            keys=tuple(k for k in keys if not value['rows'] or k in value['rows'][0])
            require({tuple(r[k] for k in keys) for r in value['rows']}<={tuple(r[k] for k in keys) for r in new[table]['rows']},'current identities lost: '+table)
        evidence[table]={'before':len(value['rows']),'after':len(new[table]['rows']),'preserved':True}
    return evidence


def install(root,m,image):
    release=Path(m['story_main'])/'.runtime/service-releases'/m['release_name']
    require(not release.is_symlink(),'release must not be symlink')
    for name in base.INSTANCE_FILES:base.write_once(release/'instance'/name,(root/'instance'/name).read_bytes())
    for name in ('manifest.json','image.json'):base.write_once(release/name,(root/name).read_bytes())
    for name in ('material_review_release.py','autonomous_optimization_release.py'):base.write_once(release/name,(root/'helpers'/name).read_bytes())
    save(release/'compose.release.json',base.compose_definition(m,image,release))
    save(release/'README.json',{'purpose':'Permanent immutable config and approach mounts; live DB/assets stay on /instance. Never restore the before database.','restart':['python3','material_review_release.py','restart','--release','.','--apply']})
    return release


def authorized(a):
    require(a.apply,'--apply is required and does not replace user confirmation');root,m=load_bundle(a.bundle)
    require(sha((root/'manifest.json').read_bytes())==a.manifest_sha256 and sha((root/'image.json').read_bytes())==a.image_receipt_sha256,'confirmed bundle digest differs')
    return root,m


def apply(a):
    root,m=authorized(a)
    with base.publication_locks(m):
        image=checks(root,m,live=False);receipt=root/'run';receipt.mkdir(exist_ok=True)
        release=Path(m['story_main'])/'.runtime/service-releases'/m['release_name']
        current=inspect(base.APP);candidate_mounts={v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}
        exact_candidate=current['Image']==image['image'] and {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']}==candidate_mounts
        proxy=base.safe_container(inspect(base.NGINX));expected_proxy={**m['previous_nginx'],'config_files':str(release/'compose.release.json')}
        require(proxy in (m['previous_nginx'],expected_proxy),'another proxy runtime is active')
        before=receipt/'before.sqlite3'
        if not before.exists():
            checks(root,m);base.snapshot(Path(m['story_main'])/'.runtime/review.sqlite3',before);save(receipt/'before.json',{'sha256':sha(before.read_bytes())})
        else:
            require(sha(before.read_bytes())==read(receipt/'before.json')['sha256'],'before snapshot changed')
            require(exact_candidate or base.safe_container(current)==m['previous_app'],'another runtime is active; recover or prepare again')
        # Integrator receipt root is task runtime, irrespective of copied helper.
        integration=json.loads(run([sys.executable,Path(m['story_worktree'])/'scripts/integrate_generation_review_system.py','--plan',root/'system-delivery.json','--apply','--receipt',receipt/'system-integration.json']))
        require(integration['target_after']==m['system_candidate'],'system integration mismatch')
        release=install(root,m,image);environment=base.env_values(inspect(base.APP))
        if not exact_candidate:base.compose_up(m,[release/'compose.release.json'],environment,release=True)
        service=base.verify_service(m,image,release)
        after=receipt/('after-'+str(time.time_ns())+'.sqlite3');base.snapshot(Path(m['story_main'])/'.runtime/review.sqlite3',after)
        evidence=preserved(before,after)
        result={'status':'formal_browser_pending','service':service,'release':str(release),'rows':evidence,'business_delta':0,'system_candidate':m['system_candidate'],'push':False,'complete_invoked':False}
        save(receipt/('service-'+str(time.time_ns())+'.json'),result);print(json.dumps(result,ensure_ascii=False))


def recover(a):
    root,m=authorized(a);image=read(root/'image.json');release=Path(m['story_main'])/'.runtime/service-releases'/m['release_name']
    with base.publication_locks(m):
        current=inspect(base.APP);known_mounts=[{v['Destination']:(v['Source'],v['RW']) for v in m['previous_app']['mounts']},{v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}];require(current['Image'] in (image['image'],m['previous_app']['image']) and {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']} in known_mounts,'another release is active')
        proxy=base.safe_container(inspect(base.NGINX));expected_proxy={**m['previous_nginx'],'config_files':str(release/'compose.release.json')};recovered_proxy={**m['previous_nginx'],'config_files':str(root/'compose.previous.json')}
        require(proxy in (m['previous_nginx'],expected_proxy,recovered_proxy),'another proxy runtime is active')
        previous=base.compose_definition(m,{'image':m['previous_app']['image']},release)
        previous['services']['app']['volumes']=[{'type':'bind','source':v['Source'],'target':v['Destination'],'read_only':not v['RW']} for v in m['previous_app']['mounts']]
        path=root/'compose.previous.json';save(path,previous);base.compose_up(m,[path],base.env_values(current),release=True);base.wait_healthy()
        require(inspect(base.APP)['Image']==m['previous_app']['image'],'recovery image differs')
        print(json.dumps({'runtime_recovered':True,'database_restored':False,'git_reset':False}))


def restart(a):
    require(a.apply,'restart requires --apply');root=a.release.resolve();m=read(root/'manifest.json');image=read(root/'image.json')
    require(m['format']=='material-review-release-v1','not this release');expected=base.compose_definition(m,image,root)
    for name in (base.APP,base.NGINX):
        current=inspect(name);require(current['Image']==expected['services']['app' if name==base.APP else 'nginx']['image'],'another image is active')
    require({v['Destination']:(v['Source'],v['RW']) for v in inspect(base.APP)['Mounts']}=={v['target']:(v['source'],not v['read_only']) for v in expected['services']['app']['volumes']},'another mount is active')
    run([base.DOCKER,'restart',base.APP,base.NGINX]);base.verify_service(m,image,root);print(json.dumps({'restarted':True,'recreated':False}))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare');q.add_argument('--story-worktree',type=Path,default=Path(__file__).resolve().parents[1]);q.add_argument('--system-worktree',type=Path,required=True);q.add_argument('--bundle',type=Path,required=True)
    q.add_argument('--task',choices=sorted(RELEASE_PREFIXES),default=TASK)
    for name in ('story-candidate','system-candidate','story-target','system-target'):q.add_argument('--'+name,required=True)
    for cmd in ('build','preflight','apply','recover'):
        q=sub.add_parser(cmd);q.add_argument('--bundle',type=Path,required=True)
        if cmd in ('apply','recover'):
            q.add_argument('--apply',action='store_true');q.add_argument('--manifest-sha256',required=True);q.add_argument('--image-receipt-sha256',required=True)
    q=sub.add_parser('restart');q.add_argument('--release',type=Path,required=True);q.add_argument('--apply',action='store_true')
    a=p.parse_args();globals()[a.command](a)

if __name__=='__main__':main()
