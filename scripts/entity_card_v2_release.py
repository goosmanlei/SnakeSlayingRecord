#!/usr/bin/env python3
"""Freeze, rehearse and publish the exact state retirement and matching reader.

No database snapshot rollback: recovery resumes the approved sanitized reader.
Git delivery belongs to the task launcher and the existing system integrator.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
import material_review_release as service
from entity_material_release import fingerprint as full_fingerprint
from entity_material_cleanup import compact

base=service.base
TASK='task-20261006-0001'
PREFIX='production/entity-card-v2/'

def fingerprint(path):
    return {k:v for k,v in full_fingerprint(path).items()
            if not (k.startswith('state_cleanup_') and v['count']==0)}

def api(m):
    sys.path.insert(0,m['system_worktree'])
    from review_desk.store import Store
    from review_desk import state_cleanup,material_model,bundle
    return Store,state_cleanup,material_model,bundle

def prepare(a):
    a.task=TASK;service.prepare(a)
    root,m=service.load_bundle(a.bundle);story=Path(m['story_worktree'])
    names=[PREFIX+'cleanup-plan.json',PREFIX+'archive-plan.json','scripts/entity_card_v2_release.py',
           'export/objects.json','export/material-content.json','export/manifest.json','export/comments.json']
    delta=base.read(story/(PREFIX+'archive-plan.json'))
    names += [r['path'] for r in delta['files']]
    hashes={n:base.sha(base.git_file(story,m['story_candidate'],n)) for n in names}
    for n,h in hashes.items():base.require(base.sha((story/n).read_bytes())==h,'candidate file differs: '+n)
    before=fingerprint(story/'.runtime/entity-card-v2/review/.runtime/generation-base.sqlite3')
    after=fingerprint(story/'.runtime/entity-card-v2/review/.runtime/review.sqlite3')
    base.require(fingerprint(Path(m['story_main'])/'.runtime/review.sqlite3')==before,'formal data drifted')
    c={'format':'entity-card-v2-release-v1','hashes':hashes,'before':before,'after':after,
       'service_manifest_sha256':base.sha((root/'manifest.json').read_bytes()),
       'recovery':'Forward only: sanitized Schema 7 export plus approved reader. Never restore old state bodies.'}
    base.save(root/'cleanup-manifest.json',c)
    print(json.dumps({'cleanup_manifest_sha256':base.sha((root/'cleanup-manifest.json').read_bytes()),'formal_writes':False}))

def load(a):
    root,m=service.load_bundle(a.bundle);c=base.read(root/'cleanup-manifest.json');story=Path(m['story_worktree'])
    base.require(m['task']==TASK and c['format']=='entity-card-v2-release-v1','wrong cleanup release')
    base.require(c['service_manifest_sha256']==base.sha((root/'manifest.json').read_bytes()),'service manifest changed')
    for n,h in c['hashes'].items():base.require(base.sha((story/n).read_bytes())==h,'cleanup input changed: '+n)
    return root,m,c,base.read(story/(PREFIX+'cleanup-plan.json')),base.read(story/(PREFIX+'archive-plan.json'))

def rehearsal(root,m,c,plan,delta):
    live=Path(m['story_main'])/'.runtime/review.sqlite3'
    base.require(fingerprint(live)==c['before'],'formal data changed; no cleanup applied')
    path=root/'run'/('shadow-'+str(time.time_ns())+'.sqlite3');base.snapshot(live,path)
    Store,cleanup,model,_=api(m);s=Store(path)
    try:
        result=cleanup.apply(s,plan,archive_delta=delta);compact(s);model.verify(s)
        base.require(fingerprint(path)==c['after'],'rehearsal differs from approved database')
        base.require(cleanup.apply(s,plan,archive_delta=delta)['removed_state_objects']==0,'cleanup is not idempotent')
        return result
    finally:
        s.close()
        for suffix in ('','-wal','-shm'):Path(str(path)+suffix).unlink(missing_ok=True)

def preflight(a):
    root,m,c,plan,delta=load(a);service.preflight(a)
    result=rehearsal(root,m,c,plan,delta)
    for r in delta['files']:
        actual=base.sha((Path(m['story_main'])/r['path']).read_bytes())
        base.require(actual in (r['before_sha256'],r['after_sha256']),'managed archive drifted')
    base.save(root/'run/cleanup-preflight.json',{'passed':True,'cleanup':result,'formal_writes':False})
    print(json.dumps({'passed':True,'cleanup':result,'formal_writes':False}))

def authorized(a):
    root,m,c,plan,delta=load(a);base.require(a.apply,'explicit apply required')
    for n,h in (('manifest.json',a.manifest_sha256),('image.json',a.image_receipt_sha256),('cleanup-manifest.json',a.cleanup_manifest_sha256)):
        base.require(base.sha((root/n).read_bytes())==h,'approved bundle changed')
    return root,m,c,plan,delta

def apply(a):
    root,m,c,plan,delta=authorized(a)
    with base.publication_locks(m):
        image=service.checks(root,m,live=False);live=Path(m['story_main'])/'.runtime/review.sqlite3'
        release=Path(m['story_main'])/'.runtime/service-releases'/m['release_name'];current=base.inspect(base.APP)
        expected={r['target']:(r['source'],not r['read_only']) for r in base.compose_definition(m,image,release)['services']['app']['volumes']}
        candidate=current['Image']==image['image'] and {r['Destination']:(r['Source'],r['RW']) for r in current['Mounts']}==expected
        base.require(candidate or base.safe_container(current)==m['previous_app'],'formal runtime changed')
        proxy=base.safe_container(base.inspect(base.NGINX))
        base.require(proxy in (m['previous_nginx'],{**m['previous_nginx'],'config_files':str(release/'compose.release.json')}),'formal proxy changed')
        if fingerprint(live)!=c['after']:service.checks(root,m);rehearsal(root,m,c,plan,delta)
        integration=json.loads(base.run([sys.executable,Path(m['story_worktree'])/'scripts/integrate_generation_review_system.py','--plan',root/'system-delivery.json','--apply','--receipt',root/'run/system-integration.json']))
        base.require(integration['target_after']==m['system_candidate'],'system integration differs')
        env=base.env_values(current);base.run([base.DOCKER,'stop','--time','20',base.APP])
        Store,cleanup,model,bundle=api(m);s=None
        try:
            base.require(fingerprint(live) in (c['before'],c['after']),'formal data drifted before transaction')
            s=Store(live);result=cleanup.apply(s,plan,archive_delta=delta);compact(s);verification=model.verify(s)
            base.require(fingerprint(live)==c['after'],'formal cleanup differs')
            recovery=root/'run/sanitized-recovery'
            if not recovery.exists():
                for n in ('config','content'):shutil.copytree(Path(m['story_main'])/n,recovery/n)
                (recovery/'config/instance.json').write_bytes((root/'instance/config/instance.json').read_bytes())
                shutil.copytree(Path(m['story_main'])/'export/assets',recovery/'export/assets',copy_function=os.link)
            bundle.export(s,recovery/'export')
            base.require(fingerprint(live)==c['after'],'export changed business rows')
            service.install(root,m,image);base.compose_up(m,[release/'compose.release.json'],env,release=True)
            running=base.verify_service(m,image,release)
            output={'status':'formal_browser_pending','cleanup':result,'verification':verification,'service':running,
                    'recovery':'run/sanitized-recovery','state_snapshot_restored':False,'git_delivery_is_separate':True}
            base.save(root/'run/applied.json',output);print(json.dumps(output,ensure_ascii=False))
        except BaseException as error:
            base.save(root/'run'/('forward-recovery-'+str(time.time_ns())+'.json'),{'resume_approved_candidate':True,'error':type(error).__name__,'old_state_bodies_restored':False})
            raise
        finally:
            if s:s.close()

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare');q.add_argument('--story-worktree',type=Path,default=Path(__file__).resolve().parents[1]);q.add_argument('--system-worktree',type=Path,required=True);q.add_argument('--bundle',type=Path,required=True);q.add_argument('--push-system',action='store_true')
    for n in ('story-candidate','story-target','system-candidate','system-target'):q.add_argument('--'+n,required=True)
    for cmd in ('preflight','apply'):
        q=sub.add_parser(cmd);q.add_argument('--bundle',type=Path,required=True)
        if cmd=='apply':
            q.add_argument('--apply',action='store_true')
            for n in ('manifest-sha256','image-receipt-sha256','cleanup-manifest-sha256'):q.add_argument('--'+n,required=True)
    a=p.parse_args();globals()[a.command](a)

if __name__=='__main__':main()
