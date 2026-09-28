"""Append the reviewed screenplay to a current instance, never restore over it.

Default: read-only dry run. --apply requires the task's explicit integration
confirmation. Exact candidate timestamps are preserved so an unchanged formal
baseline exports the same reviewed bundle. New formal comments are preserved.
"""
import argparse
import json
import sqlite3
from pathlib import Path

from review_desk.screenplay import import_screenplay
from review_desk.store import Store


def prepare(candidate, target):
    document = json.loads((candidate / 'imports/screenplay-01.json').read_text())
    bundle = json.loads((candidate / 'export/objects.json').read_text())
    ids = {document['id'], *(e['id'] for e in document['episodes'])}
    records = {table: [row for row in bundle[table] if row['id' if table == 'objects' else 'object_id'] in ids]
               for table in ('objects', 'revisions')}
    revision_ids = {row['id'] for row in records['revisions']}
    records['dependencies'] = [d for d in bundle['dependencies'] if d['from_revision'] in revision_ids]
    sandbox = Store(':memory:')
    with sqlite3.connect(f"file:{target / '.runtime/review.sqlite3'}?mode=ro", uri=True) as live:
        live.backup(sandbox.db)
    try:
        # Do not silently adapt or publish against newer upstream work.
        assert_current_basis(sandbox, document)
        before = {o['id'] for o in sandbox.objects()}
        receipt = import_screenplay(sandbox, document)
        for table in ('objects', 'revisions', 'dependencies'):
            actual = getattr(sandbox, table)()
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


def assert_current_basis(store, document):
    for ref in document['basis'].values():
        row = store.db.execute('SELECT current_revision FROM objects WHERE id=?', (ref['object_id'],)).fetchone()
        if not row or row[0] != ref['revision_id']:
            raise ValueError('upstream revision changed; review before publication')
    novels = [s for s in store.sources() if s.get('group') == 'story-refinements']
    if novels and max(novels, key=lambda s: (s.get('order', 0), s['id']))['id'] != document['basis']['story']['object_id']:
        raise ValueError('a newer published story exists; review before publication')


def publish(candidate, target, apply=False):
    document, records, receipt, exists = prepare(candidate, target)
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
    args = parser.parse_args()
    print(json.dumps(publish(args.candidate.resolve(), args.target.resolve(), args.apply), ensure_ascii=False, indent=2))
