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


def check_registry(registry):
    if registry.get('format') != 'managed-method-registry-v1' or not isinstance(registry.get('records'), list):
        raise ValueError('配置迁移需要准确方法定义包')
    if any(row.get('payload', {}).get('format') not in CONFIG_FORMATS for row in registry['records']):
        raise ValueError('配置迁移只能含方法、共用资料和绑定，不能混入工作产物或冻结范围')


def export_configuration(database):
    from review_desk import methods
    from review_desk.store import Store
    store = Store.open_existing(Path(database))
    try:
        archive = methods.export_registry(store)
    finally:
        store.close()
    archive['records'] = [row for row in archive['records'] if row['payload']['format'] in CONFIG_FORMATS]
    archive.pop('sha256')
    archive['sha256'] = methods.checksum(archive)
    check_registry(archive)
    return archive


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
        result = methods.restore_registry(store, registry)
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
                if name == 'revisions': where = ' WHERE object_id NOT IN (SELECT id FROM allowed)'
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
    registry = json.loads(args.registry.read_text())
    result = apply(args.database, registry, activate_media=args.activate_media) if args.action == 'apply' else compare(args.before, args.after, registry)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
