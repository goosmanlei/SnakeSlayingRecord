#!/usr/bin/env python3
"""Verify the reviewed shot package, additive migration and full empty restore.

All writes stay in a fresh task-local run directory. No formal database is opened.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

try:
    from .material_model_io import read_json as material_read_json
except ImportError:
    from material_model_io import read_json as material_read_json

ROOT=Path(__file__).resolve().parents[1]


def verify(system,instance,run):
    from generation_workspace import generation_root,isolated_instance,contained
    from generation_publication import backup,build_plan,apply_plan,connect,tables,canonical
    generation_root(ROOT);instance=isolated_instance(ROOT,instance)
    run=contained(ROOT,run)
    if (ROOT/'.runtime').resolve() not in run.resolve().parents or run.exists():
        raise ValueError('a fresh task runtime verification directory is required')
    run.mkdir(parents=True)
    sys.path.insert(0,str(system.resolve()))
    from review_desk.store import Store
    from review_desk.bundle import restore
    from review_desk import material_plans as mp,production as p
    from production_breakdown import compile_design
    from production_data import refresh_drafts
    started=time.monotonic()
    def equal(left,right):
        return left.keys()==right.keys() and all(Counter(map(canonical,left[k]))==Counter(map(canonical,right[k])) for k in left)
    baseline=instance/'.runtime/generation-base.sqlite3';candidate=instance/'.runtime/review.sqlite3'
    before,after=tables(baseline),tables(candidate)
    protected={}
    for table,rows in before.items():
        if table=='objects':continue
        a,b=Counter(map(canonical,rows)),Counter(map(canonical,after[table]))
        if a-b:raise ValueError('original row lost or rewritten: '+table)
        protected[table]={'before':len(rows),'after':len(after[table]),'all_original_rows_preserved':True}
    delta=material_read_json(ROOT/'production/breakdown/publication.json')
    if delta!=build_plan(baseline,candidate):raise ValueError('publication differs from isolated candidate')
    replay=run/'replay.sqlite3';backup(baseline,replay)
    db=connect(replay,readonly=False)
    try:
        result=apply_plan(db,delta)
        first=tables(replay)
        if not equal(first,after):raise ValueError('publication replay differs from candidate')
        if not apply_plan(db,delta)['already_published'] or not equal(tables(replay),first):
            raise ValueError('publication retry was not idempotent')
    finally:db.close()
    # Latest unrelated business edits survive. A conflicting head rejects even
    # the additive DDL, leaving neither partial rows nor migration tables.
    concurrent=run/'concurrent.sqlite3';backup(baseline,concurrent)
    db=connect(concurrent,readonly=False)
    try:
        comment=db.execute('SELECT id,body FROM comments LIMIT 1').fetchone()
        if not comment:raise ValueError('expected historical comment for concurrency proof')
        body=comment['body']+'\n[isolated concurrent-edit fixture]'
        with db:
            db.execute('UPDATE comments SET body=?,version=version+1 WHERE id=?',(body,comment['id']))
            db.execute('INSERT INTO comment_events(comment_id,action,body,at) VALUES (?,?,?,?)',(comment['id'],'EDIT',body,'isolated-proof'))
        apply_plan(db,delta)
        if db.execute('SELECT body FROM comments WHERE id=?',(comment['id'],)).fetchone()[0]!=body:
            raise ValueError('concurrent comment overwritten')
    finally:db.close()
    conflict=run/'conflict.sqlite3';backup(baseline,conflict)
    db=connect(conflict,readonly=False)
    try:
        oid=next(k for k,v in delta['expected_heads'].items() if v is not None)
        with db:db.execute('UPDATE objects SET updated_at=? WHERE id=?',('isolated-conflict',oid))
        snapshot='\n'.join(db.iterdump())
        try:apply_plan(db,delta)
        except ValueError as error:
            if 'changed' not in str(error):raise
        else:raise ValueError('conflicting publication accepted')
        if '\n'.join(db.iterdump())!=snapshot:raise ValueError('failed publication left schema/data changes')
    finally:db.close()
    recovered=run/'recovered'
    # Hardlinks are confined to isolated, immutable originals. Metadata is copied.
    shutil.copytree(instance/'export',recovered/'export',ignore=shutil.ignore_patterns('assets'))
    shutil.copytree(instance/'export/assets',recovered/'export/assets',copy_function=os.link)
    store=Store(recovered/'.runtime/review.sqlite3')
    try:
        restore(store,recovered/'export')
        restored=tables(store.db_path)
        if not equal(restored,after):raise ValueError('full empty restore differs from candidate rows')
        mp.validate(store)
        map_again=mp.migration_plan(store)
        if not mp.migrate(store,map_again)['already_applied']:raise ValueError('repeat migration changed data')
        document,shots,coverage,options=compile_design(store,p)
        if refresh_drafts(store,p,document,apply=False)['records']:raise ValueError('shot compiler is not idempotent')
        needs=[r for r in document['records'] if r['kind']=='REQUIREMENT']
        if any(not r['payload']['generation']['blockers'] for r in needs):raise ValueError('unbound plan claimed executable')
        if any(r['kind'] in ('CALL','ASSET','JUDGMENT') for r in document['records']):raise ValueError('design compiler generated or accepted media')
    finally:store.close()
    manifest=json.loads((instance/'export/manifest.json').read_text())
    media={k:v for k,v in manifest['files'].items() if k.startswith('assets/')}
    for name,expected in media.items():
        for root in (instance,recovered,ROOT):
            path=root/'export'/name
            actual=hashlib.file_digest(path.open('rb'),'sha256').hexdigest() if hasattr(hashlib,'file_digest') else hashlib.sha256(path.read_bytes()).hexdigest()
            if actual!=expected:raise ValueError('original hash mismatch: '+str(path))
    report={'format':'production-breakdown-verification-v1','shots':len(shots),'scenes':len(coverage['scenes']),
        'source_blocks':sum(s['blocks'] for s in coverage['scenes']),'episodes':coverage['episodes'],
        'schema':manifest['schema_version'],'original_files':len(media),'original_sha256':media,
        'preserved_tables':protected,'restored_tables':{k:len(v) for k,v in after.items()},
        'delta_replay_equal':True,'publication_retry_noop':True,'concurrent_comment_preserved':True,
        'conflict_rolls_back_schema_and_data':True,'empty_restore_equal':True,'migration_retry_noop':True,
        'compiler_retry_noop':True,'new_media_calls':0,'new_media_candidates':0,'executable_new_plans':0,
        'elapsed_seconds':round(time.monotonic()-started,3)}
    (run/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--run',type=Path,required=True)
    a=parser.parse_args();result=verify(a.system,a.instance,a.run)
    print(json.dumps({k:v for k,v in result.items() if k not in ('original_sha256','preserved_tables','restored_tables','episodes')},ensure_ascii=False))
