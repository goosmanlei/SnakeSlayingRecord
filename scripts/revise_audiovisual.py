#!/usr/bin/env python3
"""Prepare/apply an append-only audiovisual revision in an isolated review DB.

Formal publication uses generation_review prepare and publish_generation. This
entry point cannot write the main instance or adopt any candidate.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from audiovisual_design import (ROOT, read_score, coverage, bind_sources, bind_states,
                                score_records, canonical)
from audiovisual_events import ReviewedEvents
from audiovisual_materials import Builder, casting
from generation_workspace import generation_root, isolated_instance, contained


def authored_hashes(root):
    paths = [root / 'imports/screenplay-04.json', *sorted((root / 'production/audiovisual').glob('*')),
             *[root / 'scripts' / name for name in ('audiovisual_design.py', 'audiovisual_events.py',
                                                   'audiovisual_materials.py', 'revise_audiovisual.py')]]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def reconcile(store, p, records):
    """Resolve immutable revisions topologically; omit equal payloads entirely."""
    from review_desk.version_consolidation import new_identity
    current = {r['object_id']: r for r in p.current_records(store)}
    resolved, changed = {}, []
    for row in records:
        oid = row['object_id']
        if oid in resolved:
            raise ValueError('duplicate compiled identity: ' + oid)
        payload = deepcopy(row['payload'])
        for _, ref in p.references(payload):
            if ref['revision_id'].startswith('@'):
                if ref['revision_id'] != '@' + ref['object_id'] or ref['object_id'] not in resolved:
                    raise ValueError('non-topological compiled reference: ' + oid)
                ref['revision_id'] = resolved[ref['object_id']]
        previous = current.get(oid)
        if previous and previous['kind'] != row['kind']:
            raise ValueError('compiled identity changed kind: ' + oid)
        if previous and canonical(payload) == canonical(previous['payload']):
            resolved[oid] = previous['id']
            continue
        version = previous['version'] if previous else 0
        resolved[oid] = new_identity(store, oid, version + 1, payload)
        changed.append(dict(object_id=oid, kind=row['kind'], expected_version=version, payload=payload))
    return {'format': 'production-import-v1',
            'expected_heads': {oid: r['id'] for oid, r in current.items()}, 'records': changed}, resolved


def prepare(store, p):
    score = read_score()
    screenplay = json.loads((ROOT / 'imports/screenplay-04.json').read_text())
    report = coverage(score, screenplay)
    reviewed = ReviewedEvents(ROOT, score, casting())
    lock, episodes = bind_sources(store, screenplay, p)
    bindings, issues = bind_states(store, score, episodes, p)
    if issues:
        raise ValueError('state binding needs review: ' + json.dumps(issues, ensure_ascii=False))
    records = score_records(score, lock, episodes, bindings, reviewed)
    materials = Builder(store, p, records, reviewed).build()
    records.extend(materials['records'])
    batch, resolved = reconcile(store, p, records)
    changed = batch['records']
    return {'format': 'audiovisual-revision-v1', 'authored_sha256': authored_hashes(ROOT),
            'coverage': report, 'changed_kinds': dict(Counter(r['kind'] for r in changed)),
            'unchanged_objects': len(records) - len(changed),
            'preserved_songs': materials['preserve_exact_requirements'],
            'expected_results': {r['object_id']: resolved[r['object_id']] for r in changed}, 'import': batch}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'apply'))
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    root = generation_root(ROOT)
    instance = isolated_instance(root, args.instance)
    database = instance / '.runtime/review.sqlite3'
    if not database.is_file():
        raise ValueError('initialize isolated review first')
    path = contained(root, args.plan)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk import production as p
    if args.command == 'prepare':
        store = Store.open_readonly(database)
        try:
            plan = prepare(store, p)
        finally:
            store.close()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'changed_kinds': plan['changed_kinds'], 'unchanged_objects': plan['unchanged_objects']}, ensure_ascii=False))
    else:
        plan = json.loads(path.read_text())
        if plan.get('format') != 'audiovisual-revision-v1' or plan['authored_sha256'] != authored_hashes(ROOT):
            raise ValueError('authoring changed; prepare and review a fresh plan')
        # Recompute read-only before opening a writer: a modified/stale plan is
        # never permission to import unrelated kinds or rewrite historical data.
        store = Store.open_readonly(database)
        try:
            if canonical(plan) != canonical(prepare(store, p)):
                raise ValueError('review database or plan changed; prepare again')
        finally:
            store.close()
        if not plan['import']['records']:
            print('{"applied": 0}')
            return
        store = Store(database)
        try:
            result = p.import_records(store, plan['import'])
            actual = {r['id']: r['revision'] for r in result['records']}
            if actual != plan['expected_results']:
                raise ValueError('applied identity differs from prepared result; inspect before retrying')
            print(json.dumps({'applied': len(actual), 'changed_kinds': plan['changed_kinds']}))
        finally:
            store.close()


if __name__ == '__main__':
    main()
