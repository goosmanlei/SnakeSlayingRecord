"""Exact current-production migration within the existing stopped release window."""
import json
from pathlib import Path
import sqlite3
import sys
from unified_relation_migration import read, sha, require, file_of

FORMAT = 'production-current-release-v1'


def apply_package(store, root, package, validate_only=False):
    from review_desk import production_current_migration as migration, methods, production_current as current
    require(package.get('format') == FORMAT, '当前制作发布包格式无效')
    files = {name:file_of(root,item) for name,item in package['files'].items()}
    require(set(files) == {'migration','methods'}, '发布包必须包含准确迁移与方法')
    plan = read(files['migration'])
    store.db.execute('BEGIN IMMEDIATE')
    try:
        for table, identities in package['prerequisites'].items():
            require(table in ('consolidation_runs','audiovisual_cleanup_runs','business_relation_runs'), '前置迁移表无效')
            for identity in identities:
                require(store.db.execute('SELECT 1 FROM '+table+' WHERE id=?',(identity,)).fetchone(), '缺少前置迁移：'+identity)
        result = migration.apply(store, plan, transaction=False)
        method_result = methods.restore_registry(store, read(files['methods']), transaction=False)
        require(not store.db.execute('PRAGMA foreign_key_check').fetchone(), '迁移引用检查失败')
        if validate_only:store.db.rollback()
        else:store.db.commit()
        return {'contract':FORMAT,'migration':result,'methods':method_result,'validated_only':validate_only}
    except BaseException:
        store.db.rollback()
        raise


def compare(before, after, package, root):
    """Inspect every table and explicitly account for retired bodies and edges."""
    from review_desk.production_current import LEGACY_TABLES, TABLES, RECORD_KINDS
    with sqlite3.connect(Path(before).resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA cache_size=-4096')
        db.execute('ATTACH DATABASE ? AS candidate',(Path(after).resolve().as_uri()+'?mode=ro',))
        names={side:{r[0] for r in db.execute("SELECT name FROM "+side+".sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
               for side in ('main','candidate')}
        require(names['main']-names['candidate']==set(LEGACY_TABLES),'删除表范围不同')
        require(names['candidate']-names['main']==set(TABLES),'新增表范围不同')
        kinds=','.join("'"+v+"'" for v in sorted(RECORD_KINDS|{'MATERIAL_RELATION'}))
        production='SELECT id FROM main.objects WHERE kind IN ('+kinds+')'
        revisions='SELECT id FROM main.revisions WHERE object_id IN ('+production+')'
        changed_methods = package['method_changes']
        db.execute('CREATE TEMP TABLE method_changes(id TEXT PRIMARY KEY)')
        db.executemany('INSERT INTO method_changes VALUES (?)',[(v,) for v in changed_methods])
        filters={
            'objects':'id NOT IN ('+production+') AND id NOT IN (SELECT id FROM method_changes)',
            'revisions':'object_id NOT IN ('+production+')',
            'dependencies':'from_revision NOT IN ('+revisions+') AND to_revision NOT IN ('+revisions+')',
            'material_content':'1',
            'comments':'1',
            'state_cleanup_receipts':'revision_id NOT IN ('+revisions+')',
            'state_cleanup_preserved':'revision_id NOT IN ('+revisions+')',
            'relation_explanation_redactions':'revision_id NOT IN ('+revisions+')',
            'audiovisual_cleanup_receipts':'revision_id NOT IN ('+revisions+')',
        }
        evidence={}
        for table in sorted(names['main']&names['candidate']):
            if table=='read_generations':continue
            columns='id,source_id,anchor,body,status,version,created_at,updated_at' if table=='comments' else '*'
            a='SELECT '+columns+' FROM main.'+table+' WHERE '+filters.get(table,'1')
            b='SELECT '+columns+' FROM candidate.'+table
            if table not in ('material_content',):
                require(not db.execute('SELECT 1 FROM ('+a+' EXCEPT '+b+') LIMIT 1').fetchone(),'范围外旧记录丢失或改变：'+table)
            if table in ('objects','revisions','dependencies','material_content'):
                if table=='material_content':
                    require(not db.execute('SELECT 1 FROM ('+b+' EXCEPT '+a+') LIMIT 1').fetchone(),'迁移不应制造新内容节点')
            else:
                require(not db.execute('SELECT 1 FROM ('+b+' EXCEPT SELECT '+columns+' FROM main.'+table+') LIMIT 1').fetchone(),'范围外新增记录：'+table)
            evidence[table]={'before':db.execute('SELECT count(*) FROM main.'+table).fetchone()[0],
                             'after':db.execute('SELECT count(*) FROM candidate.'+table).fetchone()[0]}
        require(not db.execute('SELECT id,kind,created_at FROM candidate.objects WHERE kind IN ('+kinds+') EXCEPT SELECT id,kind,created_at FROM main.objects').fetchone(),'制作对象身份改变')
        require(not db.execute('SELECT r.object_id FROM candidate.revisions r JOIN candidate.objects o ON o.id=r.object_id WHERE o.kind IN ('+kinds+') GROUP BY r.object_id HAVING count(*)!=1').fetchone(),'制作全文链仍存在')
        require(not db.execute('PRAGMA candidate.foreign_key_check').fetchone(),'引用检查失败')
    return {'all_unrelated_rows_exact':True,'current_production_one_body':True,'tables':evidence}


def apply(root, manifest):
    import autonomous_optimization_release as base
    change=manifest['production_current'];receipt=root/'run';receipt.mkdir(exist_ok=True)
    database=Path(manifest['story_main'])/'.runtime/review.sqlite3'
    cutoff=receipt/'production-current-cutoff.sqlite3'
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
    base.save(receipt/'production-current.json',result)
    return result
