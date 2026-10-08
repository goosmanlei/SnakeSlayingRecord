#!/usr/bin/env python3
"""Publish the exact audiovisual cutover with the task-owned Git/service flow.

Stop the formal writer before delivery. A committed cutover is recovered only
forward; the clean Schema 9 export is the lasting recovery source.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import material_review_release as service
import task_repository_delivery as delivery
from publication_receipts import sha

base=service.base
TASK='task-20261008-0004'
PREFIX='production/audiovisual/'


def api(manifest):
    sys.path.insert(0,manifest['system_worktree'])
    from review_desk.store import Store
    from review_desk import production_cutover as cut,version_consolidation as vc
    return Store,cut,vc


def committed(root,commit,name):
    raw=base.git_file(root,commit,name);path=Path(root)/name
    pointer=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n',raw)
    if pointer:base.require(path.stat().st_size==int(pointer[2]) and sha(path)==pointer[1].decode(),'LFS input differs: '+name)
    else:base.require(base.sha(raw)==sha(path),'uncommitted input: '+name)


def check_files(root,plan):
    for item in plan['files']:
        path=Path(root)/'export/assets'/item['file']
        base.require(not path.is_symlink() and path.is_file() and sha(path)==item['physical_sha256'],'retained original changed: '+item['file'])


def prepare(args):
    args.task=TASK;service.prepare(args)
    root,m=service.load_bundle(args.bundle);story=Path(m['story_worktree'])
    names=[PREFIX+'cutover.json',PREFIX+'result-tables.json',PREFIX+'file-retirement.json',PREFIX+'index.json',PREFIX+'recovery.json',
           'scripts/audiovisual_release.py','scripts/audiovisual_cutover.py','scripts/publication_receipts.py',
           'export/objects.json','export/material-content.json','export/comments.json','export/manifest.json']
    hashes={n:sha(story/n) for n in names}
    for n in names:committed(story,m['story_candidate'],n)
    Store,cut,vc=api(m);plan=base.read(story/(PREFIX+'cutover.json'));design=base.read(args.design)
    base.require(cut.checksum(design['records'])==plan['record_sha256'],'authored package differs from reviewed plan')
    base.write_once(root/'design.json',args.design.read_bytes())
    store=Store.open_readonly(Path(m['story_main'])/'.runtime/review.sqlite3')
    try:base.require(vc.fingerprint(store)==plan['baseline'],'formal data drifted')
    finally:store.close()
    check_files(m['story_main'],plan)
    manifest={'format':'audiovisual-release-v1','plan_id':plan['id'],'hashes':hashes,'design_sha256':sha(root/'design.json'),
              'service_manifest_sha256':sha(root/'manifest.json'),'before':plan['baseline'],
              'after':base.read(story/(PREFIX+'result-tables.json')),
              'recovery':'Resume this exact release until applied; thereafter use only the clean Schema 9 export and minimal publication receipts.'}
    base.save(root/'audiovisual-manifest.json',manifest)
    print(json.dumps({'audiovisual_manifest_sha256':sha(root/'audiovisual-manifest.json'),'formal_writes':False}))


def load(args):
    root,m=service.load_bundle(args.bundle);c=base.read(root/'audiovisual-manifest.json')
    base.require(m['task']==TASK and c['format']=='audiovisual-release-v1','wrong release')
    base.require(sha(root/'manifest.json')==c['service_manifest_sha256'],'service manifest changed')
    for n,h in c['hashes'].items():base.require(sha(Path(m['story_worktree'])/n)==h,'cutover input changed: '+n)
    base.require(sha(root/'design.json')==c['design_sha256'],'frozen design changed')
    plan=base.read(Path(m['story_worktree'])/(PREFIX+'cutover.json'))
    base.require(plan['id']==c['plan_id'],'cutover plan differs')
    return root,m,c,plan


def preflight(args):
    root,m,c,plan=load(args);service.preflight(args)
    Store,cut,vc=api(m);store=Store.open_readonly(Path(m['story_main'])/'.runtime/review.sqlite3')
    try:base.require(vc.fingerprint(store)==c['before'],'formal data drifted')
    finally:store.close()
    check_files(m['story_main'],plan)
    base.save(root/'run/preflight.json',{'passed':True,'plan_id':plan['id'],'formal_writes':False})
    print(json.dumps({'passed':True,'formal_writes':False}))


def retire_files(main,document):
    removed=[];absent=[];pending=[]
    for item in document['files']:
        name=item['path'];relative=Path(name)
        base.require(relative.parts[:2]==('export','assets') and len(relative.parts)==3
                     and relative.name not in ('.','..'),'unsafe retirement path')
        path=main/relative
        base.require(not path.is_symlink(),'unexpected retired symlink: '+name)
        if not path.exists():absent.append(name);continue
        base.require(path.is_file() and sha(path)==item['sha256'],'retired file changed: '+name)
        pending.append((name,path))
    for name,path in pending:path.unlink();removed.append(name)
    return {'removed':removed,'already_absent':absent}


def apply(args):
    root,m,c,plan=load(args);base.require(args.apply,'explicit apply required')
    for name,value in [('manifest.json',args.manifest_sha256),('image.json',args.image_receipt_sha256),('audiovisual-manifest.json',args.audiovisual_manifest_sha256)]:
        base.require(sha(root/name)==value,'approved digest differs')
    with base.publication_locks(m):
        image=service.checks(root,m,live=False);Store,cut,vc=api(m)
        main=Path(m['story_main']);live=main/'.runtime/review.sqlite3';release=main/'.runtime/service-releases'/m['release_name']
        current=base.inspect(base.APP)
        expected={v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}
        candidate=current['Image']==image['image'] and {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']}==expected
        base.require(candidate or base.safe_container(current)==m['previous_app'],'formal runtime changed')
        if not candidate:
            base.require(base.safe_container(base.inspect(base.NGINX))==m['previous_nginx'],'formal proxy changed')
            for name,digest in m['previous_instance_hashes'].items():
                overlay=next(v['Source'] for v in current['Mounts'] if v['Destination']=='/instance/'+name)
                base.require(sha(overlay)==digest,'formal configuration changed')
        store=Store.open_readonly(live)
        try:
            applied=bool(store.db.execute('SELECT 1 FROM consolidation_runs WHERE id=?',(plan['id'],)).fetchone())
            base.require((cut.result_fingerprint(store,plan)==c['after']) if applied else (vc.fingerprint(store)==c['before']),'formal data drifted; no overwrite')
        finally:store.close()
        check_files(main,plan)
        if applied and candidate and (root/'run/applied.json').exists():
            base.verify_service(m,image,release)
            print(json.dumps({'already_applied':True,'plan_id':plan['id'],'formal_writes':False}));return
        environment=base.env_values(current)
        base.run([base.DOCKER,'stop','--time','20',base.APP]);store=None
        try:
            record=delivery.validate(m['task_delivery'])
            if all(record['repositories'][key].get('git_delivery',{}).get('phase')=='pushed' for key in m['task_delivery']['repositories']):
                delivery.validate(m['task_delivery'],delivered=True,require_push=True)
            else:delivery.apply(m['task_delivery'],root/'run/git-delivery.json')
            store=Store(live);result=cut.apply(store,plan,base.read(root/'design.json')['records'])
            files=retire_files(main,base.read(main/(PREFIX+'file-retirement.json')))
            store.db.execute('PRAGMA wal_checkpoint(TRUNCATE)');store.db.execute('VACUUM');store.db.commit()
            base.require(cut.result_fingerprint(store,plan)==c['after'],'formal result differs from isolated candidate')
            base.require(store.db.execute('PRAGMA freelist_count').fetchone()[0]==0,'free pages remain')
            base.require(not store.db.execute('PRAGMA foreign_key_check').fetchone(),'foreign key violation')
            check_files(main,plan);store.close();store=None
            cache=[]
            for name in ('read-cache.sqlite3','read-cache.sqlite3-wal','read-cache.sqlite3-shm'):
                path=main/'.runtime'/name
                if path.exists():
                    base.require(path.is_file() and not path.is_symlink(),'unexpected cache identity')
                    cache.append({'file':name,'bytes':path.stat().st_size});path.unlink()
            service.install(root,m,image);base.compose_up(m,[release/'compose.release.json'],environment,release=True)
            running=base.verify_service(m,image,release);base.update_image_aliases(m,image)
            output={'status':'formal_browser_pending','plan_id':plan['id'],'database':result,'files':files,
                    'result_tables_match':True,'retained_originals_verified':len(plan['files']),'removed_cache':cache,
                    'service':running,'effective_recovery':'export/manifest.json + '+PREFIX+'recovery.json',
                    'old_database_restored':False,'actual_generation_calls':0}
            base.save(root/'run/applied.json',output)
            print(json.dumps({k:v for k,v in output.items() if k!='database'},ensure_ascii=False))
        except BaseException as error:
            if not (root/'run/forward-recovery.json').exists():
                base.save(root/'run/forward-recovery.json',{'error':type(error).__name__,'resume_exact_release':True,'old_database_restored':False})
            raise
        finally:
            if store:store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    q=commands.add_parser('prepare');q.add_argument('--story-worktree',type=Path,default=Path(__file__).resolve().parents[1]);q.add_argument('--system-worktree',type=Path,required=True);q.add_argument('--bundle',type=Path,required=True);q.add_argument('--design',type=Path,required=True)
    for name in ('story-candidate','story-target','system-candidate','system-target'):q.add_argument('--'+name,required=True)
    for name in ('preflight','apply'):
        q=commands.add_parser(name);q.add_argument('--bundle',type=Path,required=True)
        if name=='apply':
            q.add_argument('--apply',action='store_true')
            for name in ('manifest-sha256','image-receipt-sha256','audiovisual-manifest-sha256'):q.add_argument('--'+name,required=True)
    args=parser.parse_args();globals()[args.command](args)

if __name__=='__main__':main()
