"""Exact additive relationship release inside the publisher's stopped window."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def file_of(root, item):
    path = Path(item['file'])
    require(not path.is_absolute() and '..' not in path.parts, '迁移文件路径越界')
    target = Path(root) / path
    require(not target.is_symlink() and sha(target) == item['sha256'], '准确迁移文件已变化：' + str(path))
    return target


def apply_package(store, root, package, *, validate_only=False):
    from review_desk import business_relations as br, production as p, methods
    from review_desk.store import Conflict, canonical, digest
    require(package.get('format') == 'unified-relation-release-v1', '统一关系发布格式无效')
    files = {name: file_of(root, item) for name, item in package['files'].items()}
    require(set(files) == {'relations', 'bindings', 'methods', 'authored', 'audiovisual', 'scopes'}, '迁移步骤不完整')
    checksum = digest(canonical(package).encode())
    store.db.execute('BEGIN IMMEDIATE')
    try:
        previous = store.db.execute('SELECT receipt FROM business_relation_runs WHERE id=?', (checksum,)).fetchone()
        if previous:
            result = {**json.loads(previous[0]), 'already_applied': True}
        else:
            for oid, revision in package['expected_heads'].items():
                row = store.db.execute('SELECT current_revision FROM objects WHERE id=?', (oid,)).fetchone()
                if not row or row[0] != revision:
                    raise Conflict('正式基线已变化，不能覆盖较新内容：' + oid)
            relation_result = br.apply_migration(store, read(files['relations']), transaction=False)
            counts = {}
            for key in ('bindings', 'methods', 'authored', 'audiovisual', 'scopes'):
                document = read(files[key])
                if key == 'methods':
                    counts[key] = methods.restore_registry(store, document, transaction=False)['inserted']
                elif document['records']:
                    counts[key] = len(p._import_records(store, document, transaction=False)['records'])
                else:
                    counts[key] = 0
            for oid, revision in package['final_heads'].items():
                row = store.db.execute('SELECT current_revision FROM objects WHERE id=?', (oid,)).fetchone()
                require(row and row[0] == revision, '增量结果与隔离候选不同：' + oid)
            require(not store.db.execute('PRAGMA foreign_key_check').fetchone(), '迁移引用损坏')
            result = {'id': checksum, 'contract': 'unified-relation-release-v1', 'relations': relation_result,
                      'appended_revisions': counts, 'old_history_rewritten': False}
            store.db.execute('INSERT INTO business_relation_runs VALUES (?,?)', (checksum, canonical(result)))
        if validate_only:
            store.db.rollback()
        else:
            store.db.commit()
        return {**result, 'validated_only': validate_only}
    except BaseException:
        store.db.rollback()
        raise


def compare(before, after, package):
    """Every old immutable row survives; all unrelated current rows are exact."""
    allowed = set(package['final_heads'])
    with sqlite3.connect(Path(before).resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.execute('PRAGMA cache_size=-4096'); db.execute('PRAGMA temp_store=FILE')
        db.execute('ATTACH DATABASE ? AS candidate', (Path(after).resolve().as_uri() + '?mode=ro',))
        db.execute('CREATE TEMP TABLE changed(id TEXT PRIMARY KEY)')
        db.executemany('INSERT INTO changed VALUES (?)', [(oid,) for oid in allowed])
        old = dict(db.execute("SELECT name,sql FROM main.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        new = dict(db.execute("SELECT name,sql FROM candidate.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        require(set(old) <= set(new) and set(new)-set(old) <= {
            'business_relations', 'business_relation_aliases', 'business_relation_runs'}, '迁移改变了范围外表结构')
        evidence = {}
        for table, schema in old.items():
            require(schema == new[table], '旧表结构改变：' + table)
            quoted = '"' + table.replace('"', '""') + '"'
            a = 'SELECT * FROM main.' + quoted
            b = 'SELECT * FROM candidate.' + quoted
            if table == 'read_generations':
                continue  # Disposable invalidation tokens, not business data.
            if table == 'objects':
                # Existing identity/kind/creation time is immutable even for
                # objects whose current revision this release advances.
                columns = 'id,kind,created_at'
                require(db.execute('SELECT 1 FROM (SELECT '+columns+' FROM main.objects EXCEPT SELECT '+columns+' FROM candidate.objects) LIMIT 1').fetchone() is None, '原对象身份丢失')
                a += ' WHERE id NOT IN (SELECT id FROM changed)'
                b += ' WHERE id NOT IN (SELECT id FROM changed)'
            elif table in ('material_plan_versions', 'material_definition_versions'):
                # These are current indexes; original definitions and members
                # remain in their immutable tables and are checked below.
                if table == 'material_plan_versions':
                    columns = 'material_id,number,frozen,evidence'
                    require(db.execute('SELECT 1 FROM (SELECT '+columns+' FROM main.'+quoted+' EXCEPT SELECT '+columns+' FROM candidate.'+quoted+') LIMIT 1').fetchone() is None, '素材版本身份或冻结状态改变')
                    require(db.execute('SELECT 1 FROM (SELECT * FROM main.'+quoted+' WHERE frozen!=0 EXCEPT SELECT * FROM candidate.'+quoted+') LIMIT 1').fetchone() is None, '冻结方案改变')
                a += ' WHERE material_id NOT IN (SELECT id FROM changed)'
                b += ' WHERE material_id NOT IN (SELECT id FROM changed)'
            require(db.execute('SELECT 1 FROM ('+a+' EXCEPT '+b+') LIMIT 1').fetchone() is None, '旧记录丢失或被改写：' + table)
            if table in ('objects', 'material_plan_versions', 'material_definition_versions', 'comments', 'comment_events', 'sources', 'configurations'):
                require(db.execute('SELECT 1 FROM ('+b+' EXCEPT '+a+') LIMIT 1').fetchone() is None, '范围外数据改变：' + table)
            evidence[table] = {'before': db.execute('SELECT COUNT(*) FROM main.'+quoted).fetchone()[0],
                               'after': db.execute('SELECT COUNT(*) FROM candidate.'+quoted).fetchone()[0]}
        for table in ('revisions', 'dependencies'):
            query = ('SELECT * FROM {side}.revisions WHERE object_id NOT IN (SELECT id FROM changed)' if table == 'revisions' else
                     'SELECT * FROM {side}.dependencies WHERE from_revision NOT IN (SELECT id FROM {side}.revisions WHERE object_id IN (SELECT id FROM changed))')
            require(db.execute('SELECT 1 FROM ('+query.format(side='candidate')+' EXCEPT '+query.format(side='main')+') LIMIT 1').fetchone() is None, '范围外历史增加：' + table)
        require(not db.execute('PRAGMA candidate.foreign_key_check').fetchone(), '引用完整性不通过')
    return {'all_old_immutable_rows_preserved': True, 'unrelated_current_rows_exact': True, 'tables': evidence}


def apply(root, manifest):
    import autonomous_optimization_release as base
    change = manifest['unified_relation_migration']
    database = Path(manifest['story_main']) / '.runtime/review.sqlite3'
    receipt = root / 'run'; receipt.mkdir(exist_ok=True)
    cutoff = receipt / 'relations-cutoff.sqlite3'
    if not cutoff.exists():
        base.snapshot(database, cutoff)
    package = read(root / change['package'])
    assets = Path(manifest['story_main']) / 'export/assets'
    originals = {str(p.relative_to(assets)): sha(p) for p in assets.rglob('*') if p.is_file()}
    sys.path.insert(0, str(manifest['system_worktree']))
    from review_desk.store import Store
    from review_desk import read_cache
    store = Store(database)
    try:
        result = apply_package(store, root / change['root'], package)
        read_cache.initialize(store)
    finally:
        store.close()
    result['preservation'] = compare(cutoff, database, package)
    require(originals == {str(p.relative_to(assets)): sha(p) for p in assets.rglob('*') if p.is_file()}, '原件哈希变化')
    result['originals_preserved'] = {'files': len(originals), 'hashes': originals}
    base.save(receipt / 'relations-migration.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(); sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    store = Store(args.database)
    try:
        print(json.dumps(apply_package(store, args.root, read(args.package), validate_only=args.validate_only), ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    main()
