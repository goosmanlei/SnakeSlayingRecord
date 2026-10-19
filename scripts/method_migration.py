"""Append exact method configuration; compare unaffected data without replacing it.

The caller owns the formal publication and HTTP write window. This module does
not stop services, authorize model calls or restore an old database snapshot.
"""
import argparse
import json
from pathlib import Path
import sqlite3
import socket
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler

CONFIG_FORMATS = {'managed-method-' + name + '-v1' for name in ('skill', 'resource', 'binding')}
BASELINES = 'configuration_history_baselines'


def check_registry(registry):
    if registry.get('format') != 'managed-method-registry-v1' or not isinstance(registry.get('records'), list):
        raise ValueError('配置迁移需要准确方法定义包')
    if any(row.get('payload', {}).get('format') not in CONFIG_FORMATS for row in registry['records']):
        raise ValueError('配置迁移只能含方法、共用资料和绑定，不能混入工作产物或冻结范围')
    if BASELINES not in registry:
        return  # Ordinary archives retain the native validation contract.
    baselines = registry.get(BASELINES, {})
    if not isinstance(baselines, dict):
        raise ValueError('方法配置历史起点必须是准确对象映射')
    owners = {}
    for row in registry['records']:
        owners.setdefault(row['object_id'], []).append(row)
    for oid, start in baselines.items():
        rows = sorted(owners.get(oid, []), key=lambda row: row['version'])
        if (not rows or start != {'version': rows[0]['version'], 'revision_id': rows[0]['revision_id']}
                or type(start['version']) is not int or start['version'] < 2):
            raise ValueError('方法历史起点与保留的第一份准确版本不一致：' + oid)
    for oid, rows in owners.items():
        versions = sorted(row['version'] for row in rows)
        first = baselines.get(oid, {}).get('version', 1)
        if versions[0] != first or any(right != left + 1 for left, right in zip(versions, versions[1:])):
            raise ValueError('方法包缺少已声明起点之后的连续历史：' + oid)


def restore_configuration(store, registry, *, transaction=True):
    """Restore an explicit retained-history baseline without renumbering it.

    This never removes target rows. Only the separately reviewed cleanup can
    prune history. Baselines let an empty instance retain the latest revision's
    exact identity after that cleanup; future versions remain consecutive.
    The native validator still checks every payload, dependency and file map.
    """
    from contextlib import nullcontext
    from review_desk import methods
    from review_desk.store import canonical
    check_registry(registry)
    if not registry.get(BASELINES):
        return methods.restore_registry(store, registry, transaction=transaction)
    body = {key: value for key, value in registry.items() if key != 'sha256'}
    if methods.checksum(body) != registry.get('sha256'):
        raise ValueError('方法包摘要不匹配')
    rows = registry['records']
    ids = {row['revision_id'] for row in rows}
    if len(ids) != len(rows):
        raise ValueError('方法包有重复准确版本')
    for row in rows:
        expected = methods.checksum({key: row[key] for key in ('object_id', 'version', 'payload')})
        if row['revision_id'] != expected or row['kind'] != 'GUIDANCE':
            raise ValueError('方法版本身份损坏')
        if any(dep['revision_id'] not in ids for dep in row['dependencies']):
            raise ValueError('方法包缺少准确依赖')
    with store.db if transaction else nullcontext():
        if transaction:
            store.db.execute('BEGIN IMMEDIATE')
        elif not store.db.in_transaction:
            raise ValueError('方法恢复需要所属事务')
        # Validate all heads before inserting any baseline. A normal import
        # cannot overwrite a newer target or silently repair a different row.
        for oid in {row['object_id'] for row in rows}:
            head = store.db.execute('SELECT version FROM objects WHERE id=?', (oid,)).fetchone()
            if head and head[0] > max(row['version'] for row in rows if row['object_id'] == oid):
                raise ValueError('目标已更新；不能用旧方法包覆盖当前版本')
        inserted = 0
        missing = []
        for row in sorted(rows, key=lambda item: (item['object_id'], item['version'])):
            old = store.db.execute('SELECT * FROM revisions WHERE id=?', (row['revision_id'],)).fetchone()
            if old:
                continue  # Native verification below compares exact old rows.
            head = store.db.execute('SELECT * FROM objects WHERE id=?', (row['object_id'],)).fetchone()
            version = head['version'] if head else 0
            start = registry.get(BASELINES, {}).get(row['object_id'], {}).get('version', 1)
            if row['version'] != (version + 1 if head else start):
                raise ValueError('目标历史不同或版本不连续：' + row['object_id'])
            if not head:
                store.db.execute('INSERT INTO objects VALUES (?,?,?,?,?,?)',
                                 (row['object_id'], row['kind'], row['revision_id'], row['version'],
                                  row['created_at'], row['created_at']))
            else:
                if head['kind'] != row['kind']:
                    raise ValueError('目标方法对象类型不同')
                store.db.execute('UPDATE objects SET current_revision=?,version=?,updated_at=? WHERE id=?',
                                 (row['revision_id'], row['version'], row['created_at'], row['object_id']))
            store.db.execute('INSERT INTO revisions VALUES (?,?,?,?,?)',
                             (row['revision_id'], row['object_id'], row['version'],
                              canonical(row['payload']), row['created_at']))
            missing.append(row)
            inserted += 1
        for row in missing:
            for dep in row['dependencies']:
                store.db.execute('INSERT INTO dependencies VALUES (?,?,?)',
                                 (row['revision_id'], dep['revision_id'], dep['role']))
        result = methods.restore_registry(store, registry, transaction=False)
        result['inserted'] += inserted
        result[BASELINES] = registry[BASELINES]
    return result


def configuration_registry(store):
    from review_desk import methods
    archive = methods.export_registry(store)
    archive['records'] = [row for row in archive['records'] if row['payload']['format'] in CONFIG_FORMATS]
    archive.pop('sha256')
    first = {}
    for row in archive['records']:
        first.setdefault(row['object_id'], row)
    starts = {oid: {'version': row['version'], 'revision_id': row['revision_id']}
              for oid, row in first.items() if row['version'] > 1}
    if starts:
        archive[BASELINES] = starts
    archive['sha256'] = methods.checksum(archive)
    check_registry(archive)
    return archive


def export_configuration(database):
    from review_desk.store import Store
    store = Store.open_readonly(Path(database))
    try:
        return configuration_registry(store)
    finally:
        store.close()


def check_cutover(story_main, audit):
    if audit.get('format') != 'managed-method-cutover-v1' or not audit.get('reviewed_work'):
        raise ValueError('缺少工作类型与准确在途范围的切换核对')
    ledger = json.loads((Path(story_main) / '.codex-task/tasks.json').read_text())
    rows = ledger['tasks']; rows = rows.values() if isinstance(rows, dict) else rows
    tasks = {row['id']: row for row in rows}
    for task_id in audit.get('wait_for_delivery', []):
        if tasks.get(task_id, {}).get('status') != 'completed':
            raise ValueError('先完成已核对的旧交付，再启用方法约束：' + task_id)


def stopped_api(*, application_stopped=False):
    """Probe ingress only after the caller verifies the exact app is stopped.

    Docker/HTTP proxies may keep accepting sockets while the upstream is gone.
    A timeout is recorded as such, not treated as independent proof of a lock.
    The stopped application is the write barrier; invalid probes cannot create
    queued business writes if the proxy reconnects after service restoration.
    """
    if application_stopped is not True:
        raise ValueError('先核验准确应用已经停止，不能仅凭请求超时认定写入已阻断')
    result = []
    opener = build_opener(ProxyHandler({}))
    surfaces = [('POST', '/api/comments'), ('POST', '/api/production/acceptance'),
                ('PATCH', '/api/configurations/PROJECT'), ('POST', '/api/production/import')]
    for port in (3000, 64401):
        for method, path in surfaces:
            request = Request('http://127.0.0.1:' + str(port) + path, data=b'{}', method=method,
                              headers={'Content-Type': 'application/json'})
            try:
                with opener.open(request, timeout=5) as response: status = response.status
            except HTTPError as error:
                status = error.code; error.close()
            except URLError:
                status = 'connection-unavailable'
            except (socket.timeout, TimeoutError, ConnectionError):
                status = 'response-unavailable-after-verified-stop'
            if status not in (502, 503, 504, 'connection-unavailable', 'response-unavailable-after-verified-stop'):
                raise ValueError('写入口尚未停止：' + path + ' ' + str(status))
            result.append({'port': port, 'method': method, 'path': path, 'status': status})
    return result


def apply(database, registry, *, activate_media=False):
    from review_desk import methods, method_media
    from review_desk.store import Store
    check_registry(registry)
    store = Store.open_existing(Path(database))
    try:
        result = restore_configuration(store, registry)
        if activate_media:
            policy = method_media.activate(store)
            result['activation'] = methods.reference(policy)
            result['frozen_plans'] = len(policy['payload']['frozen'])
        return result
    finally:
        store.close()


def compare(before, after, registry):
    """Exact schemas and all unaffected rows, using SQLite's disk-backed set ops."""
    ids = {row['object_id'] for row in registry['records']} | {'method.activation.media-plan'}
    uri = Path(before).resolve().as_uri() + '?mode=ro'
    with sqlite3.connect(uri, uri=True) as db:
        db.execute('PRAGMA cache_size=-4096'); db.execute('PRAGMA temp_store=FILE')
        db.execute('ATTACH DATABASE ? AS after', (Path(after).resolve().as_uri() + '?mode=ro',))
        schemas = []
        for prefix in ('main', 'after'):
            schemas.append(db.execute('SELECT type,name,tbl_name,sql FROM ' + prefix + ".sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall())
        if schemas[0] != schemas[1]:
            raise ValueError('方法迁移改变了数据库结构')
        db.execute('CREATE TEMP TABLE allowed(id TEXT PRIMARY KEY)')
        db.executemany('INSERT INTO allowed VALUES (?)', [(oid,) for oid in ids])
        result = {}
        for kind, name, _, _ in schemas[0]:
            if kind != 'table' or name == 'read_generations':
                continue
            quoted = '"' + name.replace('"', '""') + '"'
            queries = []
            for prefix in ('main', 'after'):
                where = ''
                if name == 'objects': where = ' WHERE id NOT IN (SELECT id FROM allowed)'
                if name in ('revisions','method_file_versions','method_file_packages'): where = ' WHERE object_id NOT IN (SELECT id FROM allowed)'
                if name == 'method_file_members':
                    where = ' WHERE package_revision NOT IN (SELECT revision_id FROM '+prefix+'.method_file_packages WHERE object_id IN (SELECT id FROM allowed))'
                if name == 'dependencies':
                    where = ' WHERE from_revision NOT IN (SELECT id FROM ' + prefix + '.revisions WHERE object_id IN (SELECT id FROM allowed))'
                queries.append('SELECT * FROM ' + prefix + '.' + quoted + where)
            for left, right in (queries, queries[::-1]):
                if db.execute('SELECT 1 FROM (' + left + ' EXCEPT ' + right + ') LIMIT 1').fetchone():
                    raise ValueError('方法迁移改变了无关数据：' + name)
            result[name] = {'unchanged_rows': db.execute('SELECT COUNT(*) FROM (' + queries[0] + ')').fetchone()[0]}
        return {'schema_unchanged': True, 'unaffected': result, 'read_generations': 'disposable cache tokens only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    export = sub.add_parser('export')
    export.add_argument('--database', type=Path, required=True)
    export.add_argument('--output', type=Path, required=True)
    change = sub.add_parser('apply')
    change.add_argument('--database', type=Path, required=True)
    change.add_argument('--registry', type=Path, required=True)
    change.add_argument('--activate-media', action='store_true')
    check = sub.add_parser('compare')
    check.add_argument('--before', type=Path, required=True)
    check.add_argument('--after', type=Path, required=True)
    check.add_argument('--registry', type=Path, required=True)
    args = parser.parse_args(); sys.path.insert(0, str(args.system.resolve()))
    if args.action == 'export':
        result = export_configuration(args.database)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'sha256': result['sha256'], 'revisions': len(result['records']), 'output': str(args.output)}))
        return
    try:
        from .material_model_io import read_json
    except ImportError:
        from material_model_io import read_json
    registry = read_json(args.registry)
    result = apply(args.database, registry, activate_media=args.activate_media) if args.action == 'apply' else compare(args.before, args.after, registry)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
