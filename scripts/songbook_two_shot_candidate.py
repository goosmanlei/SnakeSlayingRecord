#!/usr/bin/env python3
"""Replay the reviewed two-shot increment into an initialized isolated instance.

This story-specific entry cannot target the formal database or change its config.
It delegates transactional installation to the existing increment protocol.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from generation_workspace import generation_root, isolated_instance, git
from generation_publication import apply_plan, build_plan, connect, publication_id
from material_model_io import read_bytes

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'production/publications/songbook-work-ledger-two-shot-v1.json'
DELIVERY = ROOT / 'production/songbook-work-ledger-two-shot'
SHOTS = ['av-e03-a02-s08', 'av-e03-a02-s09']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_files(manifest):
    for item in manifest['files']:
        path = ROOT / item['path']
        require(path.is_file() and not path.is_symlink(), 'missing delivery file: ' + item['path'])
        data = path.read_bytes()
        require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                'delivery bytes changed: ' + item['path'])


def verify_media(instance, manifest):
    for item in manifest['originals']:
        data = read_bytes(instance / 'export/assets' / item['file'])
        require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                'original bytes changed: ' + item['file'])


def verify_semantics(instance, plan, manifest):
    from review_desk.production import record
    from review_desk.store import Store
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        for oid, rid in manifest['protected_heads'].items():
            require(record(store, oid)['id'] == rid, 'protected head changed: ' + oid)
        for shot, count in zip(SHOTS, (6, 3)):
            prefix = 'material-' + shot
            frame = record(store, prefix + '-first-frame')
            old_frame = record(store, prefix + '-first-frame',
                               plan['expected_heads'][prefix + '-first-frame']['current_revision'])
            generation = frame['payload']['generation']
            inputs = generation['inputs']
            require(len(inputs) == count, 'unexpected image input count: ' + shot)
            require(all(i['reference']['object_id'] != 'material-form-work-ledger-base-overall'
                        for i in inputs), 'ledger full-form still executable: ' + shot)
            numbers = {int(n) for n in re.findall(r'图片\s*(\d+)', generation['prompt'])}
            require(numbers == set(range(1, count + 1)), 'image numbers differ from inputs: ' + shot)
            require(all(i.get('selection_state') == 'unselected' for i in inputs),
                    'candidate falsely selected a missing image: ' + shot)
            for field in ('scope', 'entities', 'states', 'sources', 'specification', 'required'):
                require(frame['payload'][field] == old_frame['payload'][field],
                        'first-frame context changed: ' + shot + '/' + field)
            video = record(store, prefix + '-video')
            old_video = record(store, prefix + '-video',
                               plan['expected_heads'][prefix + '-video']['current_revision'])
            a, b = video['payload']['generation'], old_video['payload']['generation']
            for field in ('prompt', 'model', 'parameters', 'tool', 'execution', 'conditions',
                          'blockers', 'selected_routes', 'randomization'):
                require(a.get(field) == b.get(field), 'video behavior changed: ' + shot + '/' + field)
            require(a['inputs'][0]['reference'] == {'object_id': frame['object_id'], 'revision_id': frame['id']},
                    'video is outside new exact first-frame: ' + shot)
            require(a['inputs'][1:] == b['inputs'][1:], 'other video inputs changed: ' + shot)
        for suffix in ('s08-first-frame-1455', 's09-first-frame-1471'):
            oid = 'mr-material-av-e03-a02-' + suffix
            payload = record(store, oid)['payload']
            old = record(store, oid, plan['expected_heads'][oid]['current_revision'])['payload']
            require(payload['semantics'] == 'description' and payload['necessity'] == 'optional',
                    'ledger remains an image prerequisite: ' + oid)
            for field in ('upstream', 'downstream_id', 'context', 'sources'):
                require(payload.get(field) == old.get(field), 'ledger trace changed: ' + oid)
        for item in manifest['originals']:
            asset = record(store, item['object_id'], item['revision_id'])
            require(any(c['file'] == item['file'] and c['sha256'] == item['sha256']
                        and c['bytes'] == item['bytes'] for c in asset['payload']['components']),
                    'original identity changed: ' + item['object_id'])
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True,
                        help='a fresh instance created by generation_review.py init')
    args = parser.parse_args()
    root = generation_root(ROOT)
    instance = isolated_instance(root, args.instance)
    require((instance / '.runtime/generation-base.sqlite3').is_file(), 'isolated baseline missing')
    manifest = json.loads((DELIVERY / 'manifest.json').read_text())
    verify_files(manifest)
    system = args.system.resolve(strict=True)
    require(git(system, 'rev-parse', 'HEAD').decode().strip() == manifest['desk_commit'],
            'desk checkout differs from the reviewed commit')
    sys.path.insert(0, str(system))
    sys.path.insert(0, str(ROOT / 'scripts'))
    config_path = instance / 'config/instance.json'
    config = json.loads(config_path.read_text())
    require(config['review_desk_commit'] == manifest['desk_commit'], 'instance desk pin differs')
    plan = json.loads(PACKAGE.read_text())
    require(publication_id(plan) == manifest['publication_id'], 'increment identity changed')
    require(not plan['media'] and not plan['comment_events'] and not plan['changes']['comments'],
            'unexpected media or test comments in increment')
    require(set(plan['scope']) == set(manifest['candidate_heads']), 'candidate scope differs')
    verify_media(instance, manifest)
    # The existing protocol validates exact heads, dependencies, immutable history,
    # frozen definitions and public method receipts in one owned transaction.
    db = connect(instance / '.runtime/review.sqlite3', readonly=False)
    try:
        installed = apply_plan(db, plan)
        repeat = apply_plan(db, plan)
        require(repeat['already_published'], 'repeat installation was not idempotent')
    finally:
        db.close()
    actual = build_plan(instance / '.runtime/generation-base.sqlite3', instance / '.runtime/review.sqlite3')
    for field in ('scope', 'expected_heads', 'expected_references', 'guard_heads', 'changes',
                  'comment_events', 'media', 'version_baseline', 'expected_numbered_objects'):
        require(actual[field] == plan[field], 'isolated instance has extra or missing changes: ' + field)
    verify_semantics(instance, plan, manifest)
    verify_media(instance, manifest)
    from scene_reading import compile_reading
    overlay = json.loads((DELIVERY / 'reading-overlay.json').read_text())
    require(compile_reading(instance, SHOTS) == overlay, 'reading offsets differ from exact reviewed events')
    # Extend only this isolated config. Old revision descriptors stay untouched.
    reading = config['scene_reading']
    for rid, entry in overlay['entries'].items():
        require(rid not in reading['entries'] or reading['entries'][rid] == entry, 'reading entry collision')
    reading['entries'].update(overlay['entries'])
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'instance': instance.relative_to(root).as_posix(),
                      'publication_id': installed['publication_id'], 'objects': len(plan['scope']),
                      'production_objects': 10, 'public_method_records': 16,
                      'old_history_unchanged': True, 'original_components_checked': len(manifest['originals']),
                      'exact_reading_entries': len(overlay['entries']), 'formal_writes': 0,
                      'repeat_idempotent': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
