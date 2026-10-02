#!/usr/bin/env python3
"""Verify the story's relationship-only increment without opening a writable DB.

Both database paths are read-only snapshots. The authored batch names the exact
objects allowed to change; all previous revisions, comments and material rounds
must remain intact. Complete bundle recovery is verified separately.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3


def read_tables(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {name: [tuple(r) for r in db.execute('SELECT * FROM ' + name)] for name in names}
    finally:
        db.close()


def verify(before, after, batch):
    document = batch['document']
    records = {r['object_id']: r for r in document['records']}
    if len(records) != len(document['records']) or any(r['kind'] != 'RELATION' or r['payload'].get('relation_type') != 'entity' for r in records.values()):
        raise ValueError('only distinct authored entity relationships are allowed')
    old, new = read_tables(before), read_tables(after)
    if old.keys() != new.keys():
        raise ValueError('unexpected table migration')
    unchanged = {}
    for name in sorted(old.keys() - {'objects', 'revisions', 'dependencies'}):
        if Counter(old[name]) != Counter(new[name]):
            raise ValueError('protected table changed: ' + name)
        unchanged[name] = len(new[name])
    previous, current = {r[0]: r for r in old['objects']}, {r[0]: r for r in new['objects']}
    if previous.keys() != current.keys():
        raise ValueError('object identities changed')
    changed = {oid for oid in previous if previous[oid] != current[oid]}
    if changed != records.keys():
        raise ValueError('changed heads differ from authored batch')
    old_revisions, new_revisions = Counter(old['revisions']), Counter(new['revisions'])
    if old_revisions - new_revisions:
        raise ValueError('old revision changed or disappeared')
    added = list((new_revisions - old_revisions).elements())
    if len(added) != len(records) or {r[1] for r in added} != records.keys():
        raise ValueError('unexpected new revision')
    for row in added:
        oid, version, payload = row[1], row[2], json.loads(row[3])
        spec, head = records[oid], current[oid]
        if (previous[oid][3] != spec['expected_version'] or
                version != spec['expected_version'] + 1 or payload != spec['payload'] or
                head[1] != 'RELATION' or head[2] != row[0] or head[3] != version or
                head[4] != previous[oid][4]):
            raise ValueError('new relation differs from reviewed increment: ' + oid)
    previous_dependencies, current_dependencies = Counter(old['dependencies']), Counter(new['dependencies'])
    if previous_dependencies - current_dependencies:
        raise ValueError('old dependency changed or disappeared')
    added_dependencies = list((current_dependencies - previous_dependencies).elements())
    if any(r[0] not in {v[0] for v in added} for r in added_dependencies):
        raise ValueError('dependency appended to an old revision')
    return {'format': 'production-review-delta-verification-v1', 'relationships_revised': len(records),
            'changed_objects': sorted(changed), 'old_revisions_preserved': len(old['revisions']),
            'new_revisions': len(added), 'old_dependencies_preserved': len(old['dependencies']),
            'new_dependencies': len(added_dependencies), 'protected_tables_unchanged': unchanged,
            'object_identities_preserved': len(current)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'batch', 'report'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.before, args.after, json.loads(args.batch.read_text()))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'changed_objects'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
