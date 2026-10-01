#!/usr/bin/env python3
"""Prepare explicit whole-entity submissions; never infer media from candidates."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def build(store, production, entity_review):
    rows = production.current_records(store)
    existing = {r['payload']['entities'][0]['object_id']: r for r in rows if entity_review.submission(r)}
    records, heads = [], {}
    for entity in (r for r in rows if r['kind'] == 'ENTITY'):
        # Existing submissions, even if stale, require deliberate review of changes.
        if entity['object_id'] in existing:
            continue
        states = sorted(entity_review.full_states(rows, entity['object_id']), key=lambda r: ((r['payload'].get('sources') or [{}])[0].get('scene_id', ''), r['object_id']))
        if not states:
            raise ValueError('missing complete state: ' + entity['object_id'])
        ref = lambda r: {'object_id': r['object_id'], 'revision_id': r['id']}
        for row in [entity, *states]:
            heads[row['object_id']] = row['id']
        title = entity['payload']['title'] + ' · 整实体送审'
        records.append({'object_id': 'review-' + entity['object_id'], 'kind': 'REPRESENTATION', 'expected_version': 0,
                        'payload': {'format': 'production-representation-v1', 'review_model': 'entity-review-v1',
                                    'title': title, 'blocks': [{'id': 'scope', 'text': f"本次送审包括{entity['payload']['title']}的基础信息和全部 {len(states)} 个完整状态。当前未提交素材；旧候选尚未完成与完整状态的适配核对。"}],
                                    'entities': [ref(entity)], 'states': [ref(s) for s in states], 'media': [],
                                    'sources': [], 'choices': [], 'unknowns': []}})
    return {'format': 'production-import-v1', 'expected_heads': heads, 'records': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--import-records', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk import production, entity_review
    from review_desk.store import Store
    store = Store(args.instance.resolve() / '.runtime/review.sqlite3')
    try:
        batch = build(store, production, entity_review)
        if batch['records']:
            production.import_records(store, batch, validate_only=not args.import_records)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'submissions': len(batch['records']), 'media_submitted': 0, 'imported': args.import_records}, ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    main()
