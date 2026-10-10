"""Apply an exact latest-state package only inside the publisher's stopped window."""
import json
import sqlite3
from pathlib import Path
import sys
import autonomous_optimization_release as base
import material_review_release as release
import method_migration
import audiovisual_publication


def migrate(database, system, package, registry):
    sys.path.insert(0, str(system))
    from review_desk.store import Store
    store = Store(database)  # Current runtime's additive schema initialization.
    try:
        result = audiovisual_publication.apply_package(store, package)
        from review_desk import read_cache
        read_cache.initialize(store)
    finally:
        store.close()
    result['methods'] = method_migration.apply(database, registry)
    return result


def compare(before, after, package, registry):
    """Compare all unaffected physical rows; validate each permitted changed payload."""
    from review_desk.store import Store
    from review_desk import audiovisual_cleanup as cleanup
    ids = {r['object_id'] for r in registry['records']} | {r['object_id'] for r in package['records']} | {r['object_id'] for r in package['cleanup']['decisions']}
    rids = {r['revision_id'] for r in package['cleanup']['revisions']}
    with sqlite3.connect(Path(before).resolve().as_uri()+'?mode=ro', uri=True) as db:
        db.execute('PRAGMA temp_store=FILE'); db.execute('PRAGMA cache_size=-4096')
        db.execute('ATTACH DATABASE ? AS candidate', (Path(after).resolve().as_uri()+'?mode=ro',))
        db.execute('CREATE TEMP TABLE allowed_objects(id TEXT PRIMARY KEY)')
        db.executemany('INSERT INTO allowed_objects VALUES (?)', [(i,) for i in ids])
        db.execute('CREATE TEMP TABLE allowed_revisions(id TEXT PRIMARY KEY)')
        db.executemany('INSERT INTO allowed_revisions VALUES (?)', [(i,) for i in rids])
        old=dict(db.execute("SELECT name,sql FROM main.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        new=dict(db.execute("SELECT name,sql FROM candidate.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        expected={'audiovisual_notes','audiovisual_cleanup_receipts','audiovisual_cleanup_runs'}
        base.require(set(new)-set(old)<=expected and set(old)<=set(new), 'unexpected schema migration')
        evidence={}
        for table, schema in old.items():
            base.require(schema==new[table], 'old schema changed: '+table)
            if table in expected or table=='read_generations':continue
            quoted='"'+table.replace('"','""')+'"'
            queries=[]
            for prefix in ('main','candidate'):
                where=''
                if table=='objects':where=' WHERE id NOT IN (SELECT id FROM allowed_objects)'
                if table=='revisions':where=' WHERE object_id NOT IN (SELECT id FROM allowed_objects) AND id NOT IN (SELECT id FROM allowed_revisions)'
                if table=='dependencies':where=' WHERE from_revision NOT IN (SELECT id FROM '+prefix+'.revisions WHERE object_id IN (SELECT id FROM allowed_objects))'
                queries.append('SELECT * FROM '+prefix+'.'+quoted+where)
            for a,b in (queries,queries[::-1]):
                base.require(db.execute('SELECT 1 FROM ('+a+' EXCEPT '+b+') LIMIT 1').fetchone() is None,'unrelated history changed: '+table)
            evidence[table]=db.execute('SELECT COUNT(*) FROM ('+queries[0]+')').fetchone()[0]
    store=Store.open_existing(after)
    try:
        for item in package['cleanup']['revisions']:
            cleanup.verify_row(store.db.execute('SELECT * FROM revisions WHERE id=?',(item['revision_id'],)).fetchone(),store.db.execute('SELECT * FROM audiovisual_cleanup_receipts WHERE revision_id=?',(item['revision_id'],)).fetchone())
        base.require(not store.db.execute('PRAGMA foreign_key_check').fetchone(),'foreign key mismatch')
        retry=audiovisual_publication.apply_package(store, package,validate_only=True)
        base.require(retry['already_applied'],'migration receipt missing')
    finally:store.close()
    return {'unaffected_tables':evidence,'exact_cleanup_receipts':len(rids),'retry':retry}


def apply(root, manifest):
    change=manifest['latest_state_migration']; receipt=root/'run'; receipt.mkdir(exist_ok=True)
    database=Path(manifest['story_main'])/'.runtime/review.sqlite3'
    cutoff=receipt/'latest-cutoff.sqlite3'
    if not cutoff.exists():base.snapshot(database,cutoff)
    package=base.read(root/change['package']); registry=base.read(root/change['registry'])
    assets=Path(manifest['story_main'])/'export/assets'
    originals={str(p.relative_to(assets)):release.file_sha256(p) for p in assets.rglob('*') if p.is_file()}
    result=migrate(database,Path(manifest['system_worktree']),package,registry)
    result['preservation']=compare(cutoff,database,package,registry)
    base.require(originals=={str(p.relative_to(assets)):release.file_sha256(p) for p in assets.rglob('*') if p.is_file()}, 'original files changed')
    result['originals_preserved']={'files':len(originals),'hashes':originals}
    base.save(receipt/'latest-migration.json',result)
    return result
