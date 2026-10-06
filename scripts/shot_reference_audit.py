#!/usr/bin/env python3
"""Freeze the exact all-series review inputs; never write the production database."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def freeze(system, instance, output):
    from review_desk import production as p, material_plans as mp
    from review_desk.store import Store
    from generation_workspace import generation_root, contained
    root = generation_root(ROOT)
    output = contained(root, output)
    if output.exists():
        raise ValueError('Baseline already exists; do not replace a reviewed baseline')
    base = instance / '.runtime/generation-base.sqlite3'
    if not base.is_file():
        raise ValueError('Use an initialized isolated review instance')
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        rows = p.current_records(store)
        heads = {r['object_id']: r for r in rows}
        lock = json.loads((root / 'production/source-lock.json').read_text())
        source = root / lock['screenplay']['source_file']
        if sha(source) != lock['screenplay']['file_sha256']:
            raise ValueError('Locked screenplay bytes changed')
        episodes = [p.ref_record(store, ref) for ref in lock['episodes']]
        scenes = sorted((r for r in rows if r['kind'] == 'PREPARATION'), key=lambda r: r['object_id'])
        shots = sorted((r for r in rows if r['kind'] == 'SHOT_DESIGN'), key=lambda r: r['object_id'])
        needs = [r for r in rows if r['kind'] == 'REQUIREMENT' and r['payload'].get('status') != 'withdrawn']
        videos = [r for r in needs if r['payload']['media_type'] == 'video']
        plans = []
        for shot in shots:
            exact = {'object_id': shot['object_id'], 'revision_id': shot['id']}
            owned = [r for r in videos if r['payload']['scope'] == exact]
            if len(owned) != 1:
                raise ValueError('Expected one current video need: ' + shot['object_id'])
            video = owned[0]
            memberships = mp.memberships(store, video['id'])
            pair = next(v for v in memberships if v['material_id'] == video['object_id'])
            frozen = store.db.execute('SELECT frozen FROM material_plan_versions WHERE material_id=? AND number=?',
                                     (video['object_id'], pair['number'])).fetchone()[0]
            refs = []
            seen = set()
            def visit(row, path):
                if row['id'] in path:
                    raise ValueError('Cyclic production inputs: ' + row['object_id'])
                if row['id'] in seen:
                    return
                seen.add(row['id'])
                inputs = row['payload'].get('generation', {}).get('inputs', [])
                refs.append({'object_id': row['object_id'], 'revision_id': row['id'], 'kind': row['kind'],
                             'inputs': inputs})
                for value in inputs:
                    target = p.ref_record(store, value['reference'])
                    if target['kind'] == 'REQUIREMENT':
                        visit(target, [*path, row['id']])
            visit(video, [])
            plans.append({'shot': exact, 'source': shot['payload']['source'], 'parent': shot['payload']['parent'],
                          'video': {'object_id': video['object_id'], 'revision_id': video['id']},
                          'material_version': pair['number'], 'frozen': bool(frozen),
                          'prompt_sha256': hashlib.sha256(video['payload']['generation']['prompt'].encode()).hexdigest(),
                          'reference_chain': refs})
        result = {'format': 'shot-reference-baseline-v1', 'origin': json.loads((instance / '.runtime/generation-base.json').read_text()),
                  'system_commit': json.loads((root / 'config/instance.json').read_text())['review_desk_commit'],
                  'screenplay': lock['screenplay'], 'baseline_database_sha256': sha(base),
                  'counts': {'episodes': len(episodes), 'scenes': len(scenes), 'shots': len(shots), 'current_video_plans': len(plans)},
                  'plans': plans}
        if result['counts'] != {'episodes': 17, 'scenes': 42, 'shots': 297, 'current_video_plans': 297}:
            raise ValueError('Coverage changed; investigate before freezing')
        write(output, result)
        return result['counts']
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    print(json.dumps(freeze(args.system, args.instance, args.output)))


if __name__ == '__main__':
    main()
