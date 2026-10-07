#!/usr/bin/env python3
"""Freeze and publish one exact version-consolidation candidate.

The formal writer is stopped before task-controlled Git delivery changes its
managed files. Recovery only moves forward through the approved transaction;
an old database or old export must never be restored after it commits.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import material_review_release as service
import content_version_consolidation as migration
import task_repository_delivery as delivery

base=service.base
TASK='task-20261006-0007'
PREFIX='production/version-consolidation/'


def api(m):
    sys.path.insert(0,m['system_worktree'])
    from review_desk.store import Store
    from review_desk import version_consolidation as vc
    return Store,vc


def prepare(a):
    a.task=TASK;service.prepare(a)
    root,m=service.load_bundle(a.bundle);story=Path(m['story_worktree'])
    plan=base.read(story/(PREFIX+'plan.json'))
    names=[PREFIX+'plan.json',PREFIX+'verification.json',PREFIX+'recovery.json',PREFIX+'tables.json',
           'scripts/content_version_release.py','scripts/content_version_consolidation.py',
           'export/objects.json','export/material-content.json','export/comments.json','export/manifest.json']
    hashes={n:migration.sha(story/n) for n in names}
    for n,h in hashes.items():base.require(base.sha(base.git_file(story,m['story_candidate'],n))==h,'uncommitted migration input: '+n)
    Store,vc=api(m);s=Store.open_readonly(Path(m['story_main'])/'.runtime/review.sqlite3')
    try:base.require(vc.fingerprint(s)==plan['baseline'],'formal database changed')
    finally:s.close()
    migration.check_files(Path(m['story_main']),plan)
    # Preserve only the precise originals needed to check the pre-delivery
    # transaction. Git may delete their formal paths before the DB commits.
    originals=root/'run/originals';originals.mkdir(parents=True)
    for item in plan['verified_files']:
        src=Path(m['story_main'])/'export/assets'/item['file'];dst=originals/item['file']
        base.require(migration.sha(src)==item['physical_sha256'],'original drifted')
        shutil.copy2(src,dst)
    c={'format':'content-version-release-v1','hashes':hashes,'plan_id':plan['id'],
       'service_manifest_sha256':migration.sha(root/'manifest.json'),
       'before':plan['baseline'],'after':base.read(story/(PREFIX+'tables.json')),
       'recovery':'Resume the exact candidate; after commit use only the schema 8 export and publication receipts.'}
    base.save(root/'consolidation-manifest.json',c)
    print(json.dumps({'consolidation_manifest_sha256':migration.sha(root/'consolidation-manifest.json'),'formal_writes':False}))


def load(a):
    root,m=service.load_bundle(a.bundle);c=base.read(root/'consolidation-manifest.json')
    base.require(m['task']==TASK and c['format']=='content-version-release-v1','wrong release')
    base.require(migration.sha(root/'manifest.json')==c['service_manifest_sha256'],'service manifest changed')
    for n,h in c['hashes'].items():base.require(migration.sha(Path(m['story_worktree'])/n)==h,'migration input changed: '+n)
    plan=base.read(Path(m['story_worktree'])/(PREFIX+'plan.json'))
    base.require(plan['id']==c['plan_id'],'plan differs')
    for item in plan['verified_files']:
        base.require(migration.sha(root/'run/originals'/item['file'])==item['physical_sha256'],'frozen original changed')
    return root,m,c,plan


def preflight(a):
    root,m,c,plan=load(a);service.preflight(a)
    Store,vc=api(m);s=Store.open_readonly(Path(m['story_main'])/'.runtime/review.sqlite3')
    try:base.require(vc.fingerprint(s)==c['before'],'formal data drifted')
    finally:s.close()
    migration.check_files(Path(m['story_main']),plan)
    base.save(root/'run/preflight.json',{'passed':True,'plan_id':plan['id'],'formal_writes':False})
    print(json.dumps({'passed':True,'formal_writes':False}))


def apply(a):
    root,m,c,plan=load(a);base.require(a.apply,'explicit apply required')
    for name,value in [('manifest.json',a.manifest_sha256),('image.json',a.image_receipt_sha256),('consolidation-manifest.json',a.consolidation_manifest_sha256)]:
        base.require(migration.sha(root/name)==value,'approved release digest differs')
    with base.publication_locks(m):
        image=service.checks(root,m,live=False);Store,vc=api(m)
        main=Path(m['story_main']);live=main/'.runtime/review.sqlite3';release=main/'.runtime/service-releases'/m['release_name']
        current=base.inspect(base.APP)
        expected={v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}
        candidate=current['Image']==image['image'] and {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']}==expected
        base.require(candidate or base.safe_container(current)==m['previous_app'],'formal runtime changed')
        if not candidate:
            base.require(base.safe_container(base.inspect(base.NGINX))==m['previous_nginx'],'formal proxy changed')
            for name,checksum in m['previous_instance_hashes'].items():
                overlay=next(v['Source'] for v in current['Mounts'] if v['Destination']=='/instance/'+name)
                base.require(migration.sha(overlay)==checksum,'formal configuration changed')
        s=Store.open_readonly(live)
        try:head=vc.fingerprint(s)
        finally:s.close()
        base.require(head in (c['before'],c['after']),'formal data drifted; no overwrite')
        migration.check_files(main,plan,allow_applied=True)
        env=base.env_values(current)
        base.run([base.DOCKER,'stop','--time','20',base.APP])
        s=None
        try:
            record=delivery.validate(m['task_delivery'])
            if all(record['repositories'][key].get('git_delivery',{}).get('phase')=='pushed' for key in m['task_delivery']['repositories']):
                delivery.validate(m['task_delivery'],delivered=True,require_push=True)
            else:
                delivery.apply(m['task_delivery'],root/'run/git-delivery.json')
            s=Store(live)
            result=vc.apply_database(s,plan,original_root=root/'run/originals')
            files=migration.apply_files(main,plan,root/'run/files.json')
            s.db.execute('PRAGMA wal_checkpoint(TRUNCATE)');s.db.execute('VACUUM');s.db.commit()
            verification=migration.verify(s,plan)
            base.require(vc.fingerprint(s)==c['after'],'formal result differs from verified candidate')
            base.require(s.db.execute('PRAGMA freelist_count').fetchone()[0]==0,'database free pages remain')
            s.close();s=None
            cache=[]
            for name in ('read-cache.sqlite3','read-cache.sqlite3-wal','read-cache.sqlite3-shm'):
                path=main/'.runtime'/name
                if path.exists():
                    base.require(path.is_file() and not path.is_symlink(),'unexpected cache identity')
                    cache.append({'file':name,'bytes':path.stat().st_size});path.unlink()
            service.install(root,m,image);base.compose_up(m,[release/'compose.release.json'],env,release=True)
            running=base.verify_service(m,image,release);base.update_image_aliases(m,image)
            output={'status':'formal_browser_pending','plan_id':plan['id'],'database':result,'files':files,
                    'verification':verification,'removed_cache':cache,'service':running,
                    'effective_recovery':'export/manifest.json + '+PREFIX+'recovery.json','old_database_restored':False}
            base.save(root/'run/applied.json',output);print(json.dumps(output,ensure_ascii=False))
        except BaseException as error:
            base.save(root/'run/forward-recovery.json',{'error':type(error).__name__,'resume_exact_release':True,'old_database_restored':False})
            raise
        finally:
            if s:s.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    q=commands.add_parser('prepare');q.add_argument('--story-worktree',type=Path,default=Path(__file__).resolve().parents[1]);q.add_argument('--system-worktree',type=Path,required=True);q.add_argument('--bundle',type=Path,required=True)
    for name in ('story-candidate','story-target','system-candidate','system-target'):q.add_argument('--'+name,required=True)
    for name in ('preflight','apply'):
        q=commands.add_parser(name);q.add_argument('--bundle',type=Path,required=True)
        if name=='apply':
            q.add_argument('--apply',action='store_true')
            for option in ('manifest-sha256','image-receipt-sha256','consolidation-manifest-sha256'):q.add_argument('--'+option,required=True)
    args=parser.parse_args();globals()[args.command](args)


if __name__=='__main__':main()
