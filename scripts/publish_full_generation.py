#!/usr/bin/env python3
"""Validate generation batches in isolation; publish their delta after Git merge."""
import argparse
import json
from pathlib import Path
import shutil
import sys

try:
    from .generation_workspace import generation_root, contained, publication_target
    from .generation_publication import backup, build_plan, apply_plan, publication_id, connect
    from .publish_generation import run_publication, copy_media
except ImportError:
    from generation_workspace import generation_root, contained, publication_target
    from generation_publication import backup, build_plan, apply_plan, publication_id, connect
    from publish_generation import run_publication, copy_media

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--registration', type=Path, default=Path('production/full-generation/registration.json'))
    parser.add_argument('--run-name', default='publication')
    parser.add_argument('--source-commit')
    args = parser.parse_args()
    root = generation_root(args.workspace)
    target, _ = publication_target(root, args.instance)
    source = contained(root, args.registration)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    document = material_read_json(source)
    entries = [c for b in document['batches'] for r in b['records']
               for c in r['payload'].get('components', [])]
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk import production
    from review_desk.store import Store
    try:
        from .verify_full_generation import verify
    except ImportError:
        from verify_full_generation import verify

    def prepare(before, run, package):
        instance = run / 'validated-instance'
        (instance / '.runtime').mkdir(parents=True)
        path = instance / '.runtime/review.sqlite3'
        backup(before, path)
        shutil.copytree(target / 'export/assets', instance / 'export/assets')
        copy_media(root, instance, entries)
        store = Store(path)
        try:
            for batch in package['batches']:
                production.import_records(store, batch)
        finally:
            store.close()
        verify(before, path, package)
        delta = build_plan(before, path)
        # Retain exact inputs from all batches when they existed at the baseline.
        # Later batches may intentionally consume heads created by earlier ones.
        db = connect(before)
        try:
            heads = dict(db.execute('SELECT id,current_revision FROM objects'))
        finally:
            db.close()
        for batch in package['batches']:
            for oid, rid in batch.get('expected_heads', {}).items():
                if heads.get(oid) == rid:
                    delta['guard_heads'][oid] = rid
        return delta

    result = run_publication(root, args.instance, source, args.run_name,
        apply=args.apply, source_commit=args.source_commit, entries=entries,
        prepare_fn=prepare,
        apply_fn=lambda db, delta: apply_plan(db, delta, identity=publication_id(document)))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
