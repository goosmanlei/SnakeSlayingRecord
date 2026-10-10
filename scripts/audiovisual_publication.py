#!/usr/bin/env python3
"""Prepare and rehearse the exact audiovisual retirement on an isolated instance.

This is a data-specific transaction, not a relaxation of append-only publication.
An authorized publisher may call apply_package inside its exclusive write window;
the CLI deliberately accepts only a task generation instance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from generation_workspace import generation_root, isolated_instance, contained

ROOT = Path(__file__).resolve().parents[1]


def checksum(value):
    from review_desk.store import canonical, digest
    return digest(canonical(value).encode())


def prepare(before, after, sources):
    from review_desk import audiovisual_cleanup as cleanup, audiovisual_notes as notes, production as p
    from review_desk.audiovisual import KINDS, READING_CONTRACT
    heads = {r['object_id']: r['id'] for r in p.current_records(before, KINDS)}
    final = {r['object_id']: r for r in p.current_records(after, KINDS)}
    if set(heads) != set(final) or any(r['payload'].get('reading_contract') != READING_CONTRACT for r in final.values()):
        raise ValueError('candidate must cover every unchanged audiovisual object')
    records = []
    for kind in ('AV_SHOT', 'AV_SCENE', 'AV_EPISODE'):
        for row in after.db.execute('SELECT r.* FROM revisions r JOIN objects o ON o.id=r.object_id WHERE o.kind=? ORDER BY r.version,r.object_id', (kind,)):
            if before.db.execute('SELECT 1 FROM revisions WHERE id=?', (row['id'],)).fetchone():
                continue
            payload = json.loads(row['payload'])
            if payload.get('reading_contract') != READING_CONTRACT:
                raise ValueError('candidate contains an obsolete audiovisual revision')
            records.append({'object_id': row['object_id'], 'kind': kind, 'expected_version': row['version']-1,
                            'revision_id': row['id'], 'payload': payload})
    removal = cleanup.plan(before, heads)
    removal['heads'] = {oid: row['id'] for oid, row in final.items()}
    package = {'format': 'audiovisual-retirement-package-v1', 'expected_heads': heads,
               'authored_sha256': {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
               'records': records, 'cleanup': removal,
               'working_notes': [{**row, 'expected_etag': notes.get(before, row['object_id'])['etag']} for row in notes.dump(after)]}
    package['sha256'] = checksum(package)
    return package


def apply_package(store, package, *, validate_only=False):
    from review_desk import audiovisual_cleanup as cleanup, audiovisual_notes as notes, production as p
    from review_desk.store import Conflict
    if package.get('format') != 'audiovisual-retirement-package-v1' or package.get('sha256') != checksum({k:v for k,v in package.items() if k != 'sha256'}):
        raise ValueError('invalid audiovisual retirement package')
    run_id = checksum(package['cleanup'])
    store.db.execute('BEGIN IMMEDIATE')
    try:
        applied = store.db.execute('SELECT 1 FROM audiovisual_cleanup_runs WHERE id=?', (run_id,)).fetchone() is not None
        expected = package['cleanup']['heads'] if applied else package['expected_heads']
        for oid, rid in expected.items():
            if p.record(store, oid)['id'] != rid:
                raise Conflict('audiovisual head changed: '+oid)
        for row in package['working_notes']:
            current = notes.get(store, row['object_id'])
            if (current['body'] != row['body']) if applied else (current['etag'] != row['expected_etag']):
                raise Conflict('audiovisual working note changed: '+row['object_id'])
        if applied:
            for item in package['records']:
                if p.record(store, item['object_id'], item['revision_id'])['payload'] != item['payload']:
                    raise Conflict('applied candidate changed')
            for item in package['cleanup']['revisions']:
                raw = store.db.execute('SELECT * FROM revisions WHERE id=?', (item['revision_id'],)).fetchone()
                receipt = store.db.execute('SELECT * FROM audiovisual_cleanup_receipts WHERE revision_id=?', (item['revision_id'],)).fetchone()
                if not receipt: raise Conflict('cleanup receipt missing')
                cleanup.verify_row(raw, receipt)
            store.db.rollback()
            return {'run_id': run_id, 'already_applied': True, 'validate_only': validate_only}
        # Several deliberately saved authoring revisions may belong to one object.
        # Exact children have already been ordered before their parents.
        for row in package['records']:
            result = p._import_records(store, {'format':'production-import-v1', 'records':[row]}, transaction=False)
            if result['records'][0]['revision'] != row['revision_id']:
                raise ValueError('candidate revision identity differs')
        result = cleanup.apply(store, package['cleanup'], transaction=False)
        for row in package['working_notes']:
            store.db.execute('INSERT INTO audiovisual_notes VALUES (?,?,?) ON CONFLICT(object_id) DO UPDATE SET body=excluded.body,updated_at=excluded.updated_at',
                             (row['object_id'], row['body'], row['updated_at']))
        if store.db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('candidate has invalid references')
        if validate_only: store.db.rollback()
        else: store.db.commit()
        return {**result, 'new_revisions': len(package['records']), 'working_notes':len(package['working_notes']), 'validate_only':validate_only}
    except BaseException:
        store.db.rollback()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare','validate','apply'))
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    root = generation_root(ROOT)
    instance = isolated_instance(root, args.instance)
    path = contained(root, args.package)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    store = Store(instance/'.runtime/review.sqlite3')
    try:
        if args.command == 'prepare':
            candidate = isolated_instance(root, args.candidate)
            after = Store.open_existing(candidate/'.runtime/review.sqlite3')
            try: package = prepare(store, after, sorted((ROOT/'production/audiovisual/readings').glob('e*.json')))
            finally: after.close()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(package, ensure_ascii=False, indent=2)+'\n')
            result = {'sha256':package['sha256'], 'records':len(package['records']), 'cleanup':len(package['cleanup']['revisions'])}
        else:
            package = json.loads(path.read_text())
            for filename, digest in package['authored_sha256'].items():
                if hashlib.sha256(contained(root, Path(filename)).read_bytes()).hexdigest() != digest:
                    raise ValueError('authored reading changed: '+filename)
            result = apply_package(store, package, validate_only=args.command == 'validate')
        print(json.dumps(result, ensure_ascii=False))
    finally: store.close()


if __name__ == '__main__': main()
