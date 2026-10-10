#!/usr/bin/env python3
"""Inspect, validate and apply authored exact reading arrangements.

This tool never decides which prose is redundant and never changes stored work.
The author supplies every disposition and exact range after reading the work.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from generation_workspace import generation_root


def row_for(store, reference):
    from review_desk.production import snapshot
    return snapshot(store, object_id=reference['object_id'], revision_id=reference['revision_id'])['record']


def compile_entry(store, plan):
    from review_desk.review_text import production_text_blocks
    from review_desk.review_composition import composition
    row = row_for(store, plan['reference'])
    blocks = {b['id']: b for b in production_text_blocks(row['payload'])}
    if set(plan['sources']) != set(blocks):
        raise ValueError('author must account for every exact source block')
    entry = dict(object_id=row['object_id'], sources={
        key: dict(value, sha256=hashlib.sha256(blocks[key]['text'].encode()).hexdigest())
        for key, value in plan['sources'].items()}, sections=plan['sections'],
        requires=[row_for(store, ref)['id'] for ref in plan.get('requires', [])])
    composition(row, dict(format='exact-review-composition-v1', entries={row['id']: entry}))
    return row['id'], entry


def validate(store, config):
    from review_desk.review_composition import composition
    from review_desk.production import record
    spec = config['production_reading']
    for revision, entry in spec['entries'].items():
        row = row_for(store, dict(object_id=entry['object_id'], revision_id=revision))
        composition(row, spec)
        for companion in entry.get('requires', []):
            record(store, revision_id=companion)
    return len(spec['entries'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('config/instance.json'))
    sub = parser.add_subparsers(dest='command', required=True)
    inspect = sub.add_parser('inspect')
    inspect.add_argument('--object-id', required=True)
    inspect.add_argument('--revision-id')
    sub.add_parser('validate')
    apply = sub.add_parser('apply')
    apply.add_argument('--plan', type=Path, required=True)
    apply.add_argument('--expected-config-sha256', required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk.production import snapshot
    from review_desk.review_text import production_text_blocks
    store = Store(args.instance / '.runtime/review.sqlite3')
    try:
        if args.command == 'inspect':
            row = snapshot(store, object_id=args.object_id, revision_id=args.revision_id)['record']
            print(json.dumps(dict(reference=dict(object_id=row['object_id'], revision_id=row['id']),
                                  blocks=production_text_blocks(row['payload'])), ensure_ascii=False, indent=2))
            return
        raw = args.config.read_bytes()
        config = json.loads(raw)
        if args.command == 'apply':
            root = generation_root(Path(__file__).resolve().parents[1])
            target = args.config.resolve(strict=True)
            target.relative_to(root)
            if args.config.is_symlink() or hashlib.sha256(raw).hexdigest() != args.expected_config_sha256:
                raise ValueError('configuration changed; read and reconcile it before applying')
            plan = json.loads(args.plan.read_text())
            if plan.get('format') != 'authored-production-reading-v1':
                raise ValueError('unsupported author plan')
            entries = [compile_entry(store, item) for item in plan['entries']]
            if len({revision for revision, _ in entries}) != len(entries):
                raise ValueError('duplicate authored revision')
            config['production_reading']['entries'].update(dict(entries))
        count = validate(store, config)
        if args.command == 'apply':
            # Validation finishes before the sole configuration mutation.
            if target.read_bytes() != raw:
                raise ValueError('configuration changed during validation; no write applied')
            staged = target.with_suffix('.reading-tmp')
            staged.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
            staged.replace(target)
        print(json.dumps(dict(validated=count, applied=args.command == 'apply')))
    finally:
        store.close()


if __name__ == '__main__':
    main()
