"""Append the reviewed screenplay to a current instance, never restore over it.

Default: read-only dry run. --apply requires the task's explicit integration
confirmation. Exact candidate timestamps are preserved so an unchanged formal
baseline exports the same reviewed bundle. New formal comments are preserved.
"""
import argparse
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from review_desk.screenplay import import_screenplay
from review_desk.store import Store


def prepare(candidate, target, document_path='imports/screenplay-01.json', records_path=None):
    document = json.loads((candidate / document_path).read_text())
    from material_model_io import framework_members
    ids = {document['id'], *(e['id'] for e in document['episodes'])}
    supplied = None
    if records_path:
        from material_model_io import read_json
        from generation_workspace import contained
        supplied = read_json(contained(candidate, records_path))
        if supplied.get('format') != 'screenplay-publication-records-v1':
            raise ValueError('invalid exact screenplay records package')
    def members(table):
        return supplied[table] if supplied is not None else framework_members(candidate/'export/objects.json',table)
    records = {table: [row for row in members(table) if row['id' if table == 'objects' else 'object_id'] in ids]
               for table in ('objects', 'revisions')}
    revision_ids = {row['id'] for row in records['revisions']}
    records['dependencies'] = [d for d in members('dependencies') if d['from_revision'] in revision_ids]
    temporary = TemporaryDirectory(prefix='screenplay-preflight-')
    sandbox = Store(Path(temporary.name) / 'review.sqlite3')
    try:
        with sqlite3.connect(f"file:{target / '.runtime/review.sqlite3'}?mode=ro", uri=True) as live:
            live.backup(sandbox.db)
        # Do not silently adapt or publish against newer upstream work.
        assert_current_basis(sandbox, document)
        placeholders = ','.join('?' for _ in ids)
        before = {r['id'] for r in sandbox.db.execute(
            'SELECT id FROM objects WHERE id IN (' + placeholders + ')', tuple(ids))}
        receipt = import_screenplay(sandbox, document)
        for table in ('objects', 'revisions', 'dependencies'):
            field = {'objects': 'id', 'revisions': 'object_id', 'dependencies': 'from_revision'}[table]
            selected = revision_ids if table == 'dependencies' else ids
            actual = [dict(r) for r in sandbox.db.execute(
                'SELECT * FROM ' + table + ' WHERE ' + field + ' IN (' +
                ','.join('?' for _ in selected) + ')', tuple(selected))]
            if table == 'objects':
                expected = [{k: v for k, v in r.items() if k not in ('created_at', 'updated_at')} for r in records[table]]
                actual = [{k: v for k, v in r.items() if k not in ('created_at', 'updated_at')} for r in actual if r['id'] in ids]
            elif table == 'revisions':
                expected = [{k: v for k, v in r.items() if k != 'created_at'} for r in records[table]]
                actual = [{k: v for k, v in r.items() if k != 'created_at'} for r in actual if r['object_id'] in ids]
            else:
                expected = records[table]
                actual = [r for r in actual if r['from_revision'] in revision_ids]
            if sorted(json.dumps(x, sort_keys=True) for x in actual) != sorted(json.dumps(x, sort_keys=True) for x in expected):
                raise ValueError(table + ' does not match reviewed edition')
        return document, records, receipt, bool(ids & before)
    finally:
        sandbox.close()
        temporary.cleanup()


def assert_current_basis(store, document):
    for ref in document['basis'].values():
        row = store.db.execute('SELECT current_revision FROM objects WHERE id=?', (ref['object_id'],)).fetchone()
        if not row or row[0] != ref['revision_id']:
            raise ValueError('upstream revision changed; review before publication')
    novels = [s for s in store.sources() if s.get('group') == 'story-refinements']
    if novels and max(novels, key=lambda s: (s.get('order', 0), s['id']))['id'] != document['basis']['story']['object_id']:
        raise ValueError('a newer published story exists; review before publication')


def publish(candidate, target, apply=False, document_path='imports/screenplay-01.json', records_path=None):
    document, records, receipt, exists = prepare(candidate, target, document_path, records_path)
    result = {'dry_run': not apply, 'screenplay_id': document['id'], 'revision': receipt['revision'],
              'already_present': exists, 'objects': len(records['objects']),
              'revisions': len(records['revisions']), 'dependencies': len(records['dependencies'])}
    if not apply or exists:
        return result
    store = Store(target / '.runtime/review.sqlite3')
    try:
        with store.db:
            store.db.execute('BEGIN IMMEDIATE')
            assert_current_basis(store, document)
            # Check collisions again under the write lock; never replace a row.
            ids = [r['id'] for r in records['objects']]
            if any(store.db.execute('SELECT 1 FROM objects WHERE id=?', (id,)).fetchone() for id in ids):
                raise ValueError('publication target changed; rerun dry run')
            for row in records['objects']:
                store.db.execute('INSERT INTO objects VALUES (?,?,?,?,?,?)', tuple(row[k] for k in ('id', 'kind', 'current_revision', 'version', 'created_at', 'updated_at')))
            for row in records['revisions']:
                store.db.execute('INSERT INTO revisions VALUES (?,?,?,?,?)', tuple(row[k] for k in ('id', 'object_id', 'version', 'payload', 'created_at')))
            for row in records['dependencies']:
                store.db.execute('INSERT INTO dependencies VALUES (?,?,?)', tuple(row[k] for k in ('from_revision', 'to_revision', 'role')))
    finally:
        store.close()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, default=Path('.'))
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--document', default='imports/screenplay-01.json', help='Path relative to candidate root')
    parser.add_argument('--records', type=Path, help='Exact immutable screenplay rows when the full production export is not yet publishable')
    args = parser.parse_args()
    print(json.dumps(publish(args.candidate.resolve(), args.target.resolve(), args.apply, args.document, args.records), ensure_ascii=False, indent=2))
