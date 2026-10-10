"""Apply the exact approval retirement and method delta in one stopped write window."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
from unified_relation_migration import read, sha, require, file_of

FORMAT = 'comment-review-release-v1'


def apply_package(store, root, package, *, validate_only=False):
    from review_desk import review_retirement as retirement, methods
    from review_desk.store import Conflict
    require(package.get('format') == FORMAT, '评论迁移发布格式无效')
    files = {name:file_of(root,item) for name,item in package['files'].items()}
    require(set(files) == {'retirement','methods'}, '迁移包必须包含退役与当前方法')
    plan = read(files['retirement'])
    store.db.execute('BEGIN IMMEDIATE')
    try:
        done = store.db.execute('SELECT 1 FROM consolidation_runs WHERE id=?',(plan['id'],)).fetchone()
        expected = package['final_heads'] if done else package['expected_heads']
        for oid,rid in expected.items():
            row = store.db.execute('SELECT current_revision FROM objects WHERE id=?',(oid,)).fetchone()
            if not row or row[0] != rid:
                raise Conflict('准确迁移基线已变化：'+oid)
        for table,ids in package['prerequisites'].items():
            require(table in ('consolidation_runs','audiovisual_cleanup_runs','business_relation_runs'), '前置迁移表无效')
            for identity in ids:
                require(store.db.execute('SELECT 1 FROM '+table+' WHERE id=?',(identity,)).fetchone(), '缺少前置迁移：'+identity)
        result = retirement.apply(store,plan,transaction=False)
        method_result = methods.restore_registry(store,read(files['methods']),transaction=False)
        for oid,rid in package['final_heads'].items():
            require(store.db.execute('SELECT current_revision FROM objects WHERE id=?',(oid,)).fetchone()[0] == rid, '当前头与准确候选不同：'+oid)
        require(not store.db.execute('PRAGMA foreign_key_check').fetchone(), '迁移产生无效引用')
        if validate_only:store.db.rollback()
        else:store.db.commit()
        return {'contract':FORMAT,'retirement':result,'methods':method_result,'validated_only':validate_only}
    except BaseException:
        store.db.rollback();raise


def compare(before, after, package, root):
    """Compare every business table; allow only explicitly classified removals/additions."""
    plan = read(file_of(root,package['files']['retirement']))
    added_comments = [v['comment_id'] for v in plan['dispositions'].values() if v['action']=='import']
    with sqlite3.connect(Path(before).resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA cache_size=-4096')
        db.execute('ATTACH DATABASE ? AS candidate',(Path(after).resolve().as_uri()+'?mode=ro',))
        for table,values in [('retired',[r['revision_id'] for r in plan['revisions']]),('retired_objects',list({r['object_id'] for r in plan['revisions']})),('changed',list(package['final_heads'])),('appended',package['appended_revisions']),('imported',added_comments)]:
            db.execute('CREATE TEMP TABLE '+table+'(id TEXT PRIMARY KEY)')
            db.executemany('INSERT INTO '+table+' VALUES (?)',[(v,) for v in values])
        schemas={side:dict(db.execute("SELECT name,sql FROM "+side+".sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")) for side in ['main','candidate']}
        require(schemas['main']==schemas['candidate'],'迁移改变表结构')
        evidence={}
        old_filters={
            'objects':'id NOT IN (SELECT id FROM retired_objects) AND id NOT IN (SELECT id FROM changed)',
            'revisions':'id NOT IN (SELECT id FROM retired)',
            'dependencies':'from_revision NOT IN (SELECT id FROM retired) AND to_revision NOT IN (SELECT id FROM retired)',
            'business_codes':"prefix NOT IN ('RV','DC')",
            'consolidation_revisions':'revision_id NOT IN (SELECT id FROM retired)',
            'state_cleanup_preserved':'revision_id NOT IN (SELECT id FROM retired)',
            'relation_explanation_redactions':'revision_id NOT IN (SELECT id FROM retired)',
        }
        new_filters={**old_filters,
            'revisions':old_filters['revisions']+' AND id NOT IN (SELECT id FROM appended)',
            'dependencies':old_filters['dependencies']+' AND from_revision NOT IN (SELECT id FROM appended)',
            'comments':'id NOT IN (SELECT id FROM imported)',
            'comment_events':"NOT (action='HISTORY_IMPORT' AND json_extract(body,'$.migration_id')='"+plan['id']+"')",
            'business_comments':'comment_id NOT IN (SELECT id FROM imported)',
            'material_comment_scopes':'comment_id NOT IN (SELECT id FROM imported)',
            'material_plan_comments':'comment_id NOT IN (SELECT id FROM imported)',
            'consolidation_revisions':old_filters['consolidation_revisions']+" AND revision_id NOT IN (SELECT revision_id FROM candidate.consolidation_revisions WHERE plan_id='"+plan['id']+"' AND revision_id NOT IN (SELECT revision_id FROM main.consolidation_revisions))",
            'consolidation_missing':'NOT (target_revision IN (SELECT id FROM retired) OR revision_id IN (SELECT id FROM appended))',
            'consolidation_objects':'object_id NOT IN (SELECT id FROM retired_objects)',
            'consolidation_runs':"id!='"+plan['id']+"'",
        }
        for table in schemas['main']:
            if table=='read_generations':continue
            q='"'+table+'"';a='SELECT * FROM main.'+q;b='SELECT * FROM candidate.'+q
            if table in old_filters:a+=' WHERE '+old_filters[table]
            if table in new_filters:b+=' WHERE '+new_filters[table]
            require(not db.execute('SELECT 1 FROM ('+a+' EXCEPT SELECT * FROM candidate.'+q+') LIMIT 1').fetchone(),'旧记录丢失或被改写：'+table)
            require(not db.execute('SELECT 1 FROM ('+b+' EXCEPT '+a+') LIMIT 1').fetchone(),'范围外记录增加或改变：'+table)
            evidence[table]={'before':db.execute('SELECT COUNT(*) FROM main.'+q).fetchone()[0],'after':db.execute('SELECT COUNT(*) FROM candidate.'+q).fetchone()[0]}
        require(not db.execute('SELECT id,kind,created_at FROM main.objects WHERE id IN (SELECT id FROM changed) EXCEPT SELECT id,kind,created_at FROM candidate.objects').fetchone(),'原对象身份改变')
        require(not db.execute("SELECT 1 FROM candidate.objects WHERE kind IN ('JUDGMENT','REPRESENTATION')").fetchone(),'退役对象仍有正文')
        require(not db.execute('PRAGMA candidate.foreign_key_check').fetchone(),'引用检查失败')
    return {'all_unrelated_rows_exact':True,'old_call_payloads_and_identities_exact':True,'tables':evidence}


def apply(root, manifest):
    import autonomous_optimization_release as base
    change=manifest['review_retirement'];receipt=root/'run';receipt.mkdir(exist_ok=True)
    database=Path(manifest['story_main'])/'.runtime/review.sqlite3'
    cutoff=receipt/'review-retirement-cutoff.sqlite3'
    if not cutoff.exists():base.snapshot(database,cutoff)
    package=read(root/change['package']);assets=Path(manifest['story_main'])/'export/assets'
    originals={str(p.relative_to(assets)):sha(p) for p in assets.rglob('*') if p.is_file()}
    sys.path.insert(0,str(manifest['system_worktree']))
    from review_desk.store import Store
    from review_desk import read_cache
    store=Store(database)
    try:
        result=apply_package(store,root/change['root'],package)
        read_cache.initialize(store)
    finally:store.close()
    result['preservation']=compare(cutoff,database,package,root/change['root'])
    require(originals=={str(p.relative_to(assets)):sha(p) for p in assets.rglob('*') if p.is_file()},'原件发生变化')
    result['originals_preserved']={'files':len(originals),'hashes':originals}
    base.save(receipt/'review-retirement.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--package',type=Path,required=True);parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    store=Store(args.database)
    try:print(json.dumps(apply_package(store,args.root,read(args.package),validate_only=args.validate_only),ensure_ascii=False))
    finally:store.close()

if __name__=='__main__':main()
