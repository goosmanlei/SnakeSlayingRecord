#!/usr/bin/env python3
"""Install the reviewed two-night candidate into a fresh isolated instance."""
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
DELIVERY = ROOT / 'production/songbook-two-nights'
PACKAGE = ROOT / 'production/publications/songbook-two-nights-v1.json'
SHOTS = ('av-e04-a01-s03', 'av-e04-a01-s05')


def require(value, message):
    if not value:
        raise ValueError(message)


def verify_files(manifest, instance):
    for entry in manifest['files']:
        path = ROOT / entry['path']
        require(path.is_file() and not path.is_symlink(), 'delivery file missing: ' + entry['path'])
        data = path.read_bytes()
        require(len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'],
                'delivery bytes changed: ' + entry['path'])
    for entry in manifest['originals']:
        data = read_bytes(instance / 'export/assets' / entry['file'])
        require(len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'],
                'original bytes changed: ' + entry['file'])


def verify_heads(instance, manifest, *, installed):
    db = connect(instance / '.runtime/review.sqlite3')
    try:
        for oid, rid in manifest['protected_heads'].items():
            row = db.execute('SELECT current_revision FROM objects WHERE id=?', (oid,)).fetchone()
            require(row and row[0] == rid, 'protected head changed: ' + oid)
        if installed:
            for oid, rid in manifest['candidate_heads'].items():
                row = db.execute('SELECT current_revision FROM objects WHERE id=?', (oid,)).fetchone()
                require(row and row[0] == rid, 'candidate head differs: ' + oid)
        by_upstream = {}
        for edge in manifest['consumer_edges']:
            by_upstream.setdefault(edge['upstream'], set()).add(edge['relation'])
        for oid, expected in by_upstream.items():
            rows = db.execute("SELECT DISTINCT o.id FROM objects o JOIN dependencies d ON d.from_revision=o.current_revision "
                              "JOIN revisions r ON r.id=d.to_revision WHERE r.object_id=? AND o.kind='MATERIAL_RELATION' "
                              "AND d.role='payload.upstream'", (oid,)).fetchall()
            require({row[0] for row in rows} == expected, 'consumer membership changed: ' + oid)
    finally:
        db.close()


def verify_semantics(instance, plan, manifest):
    from review_desk.production import record
    from review_desk.store import Store
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        for shot, suffixes in zip(SHOTS, (('1512', '1513'), ('1530', '1531'))):
            prefix = 'material-' + shot
            frame = record(store, prefix + '-first-frame')
            old = record(store, prefix + '-first-frame',
                         plan['expected_heads'][prefix + '-first-frame']['current_revision'])
            a, b = frame['payload']['generation'], old['payload']['generation']
            require(len(a['inputs']) == 3, 'three image references required: ' + shot)
            require(a['inputs'][:2] == b['inputs'][:2], 'camera or character reference changed: ' + shot)
            require(a['inputs'][2]['reference'] == b['inputs'][2]['reference'], 'physical songbook changed: ' + shot)
            require(all(i.get('selection_state') == 'unselected' for i in a['inputs']),
                    'missing images falsely selected: ' + shot)
            require({int(n) for n in re.findall(r'图片\s*(\d+)', a['prompt'])} == {1, 2, 3},
                    'image numbers differ from inputs: ' + shot)
            for field in ('scope', 'entities', 'states', 'sources', 'specification', 'required', 'usage'):
                require(frame['payload'].get(field) == old['payload'].get(field),
                        'first-frame context changed: ' + shot + '/' + field)
            for field in ('model', 'parameters', 'tool', 'conditions', 'blockers', 'randomization', 'selected_routes'):
                require(a.get(field) == b.get(field), 'image execution changed: ' + shot + '/' + field)
            for suffix, ledger in zip(suffixes, (False, True)):
                oid = 'mr-material-' + shot + '-first-frame-' + suffix
                row = record(store, oid)['payload']
                previous = record(store, oid, plan['expected_heads'][oid]['current_revision'])['payload']
                for field in ('upstream', 'downstream_id', 'context', 'sources', 'attributes'):
                    require(row.get(field) == previous.get(field), 'purpose identity changed: ' + oid)
                require(row['semantics'] == ('description' if ledger else 'reference') and
                        row['necessity'] == ('optional' if ledger else 'required'),
                        'incorrect image prerequisite: ' + oid)
                require(all(word in row['preserve'] for word in ('同一本', '纸材', '接触')) and
                        '内容一致' not in row['preserve'] and '阶段' in row['preserve'] + row['change'],
                        'physical identity and staged text disagree: ' + oid)
            video = record(store, prefix + '-video')
            old_video = record(store, prefix + '-video',
                               plan['expected_heads'][prefix + '-video']['current_revision'])
            v, w = video['payload']['generation'], old_video['payload']['generation']
            for field in ('prompt', 'model', 'parameters', 'tool', 'execution', 'conditions',
                          'blockers', 'selected_routes', 'randomization'):
                require(v.get(field) == w.get(field), 'video behavior changed: ' + shot + '/' + field)
            require(v['parameters']['duration'] == 8, 'night duration changed')
            require(v['inputs'][0]['reference'] == {'object_id': frame['object_id'], 'revision_id': frame['id']},
                    'video does not consume exact new first-frame: ' + shot)
            require(v['inputs'][1:] == w['inputs'][1:], 'other video inputs changed: ' + shot)
            rel = record(store, **{'object_id': v['inputs'][0]['relation']['object_id'],
                                  'revision_id': v['inputs'][0]['relation']['revision_id']})
            require(rel['payload']['upstream'] == v['inputs'][0]['reference'], 'handoff reference differs')
        for entry in manifest['originals']:
            asset = record(store, entry['object_id'], entry['revision_id'])
            require(any(c['file'] == entry['file'] and c['sha256'] == entry['sha256'] and c['bytes'] == entry['bytes']
                        for c in asset['payload']['components']), 'original identity changed')
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    args = parser.parse_args()
    root = generation_root(ROOT)
    instance = isolated_instance(root, args.instance)
    require((instance / '.runtime/generation-base.sqlite3').is_file(), 'isolated baseline missing')
    manifest = json.loads((DELIVERY / 'manifest.json').read_text())
    system = args.system.resolve(strict=True)
    require(git(system, 'rev-parse', 'HEAD').decode().strip() == manifest['desk_commit'], 'desk commit differs')
    sys.path.insert(0, str(system))
    config_path = instance / 'config/instance.json'
    config = json.loads(config_path.read_text())
    require(config['review_desk_commit'] == manifest['desk_commit'], 'instance desk pin differs')
    plan = json.loads(PACKAGE.read_text())
    require(publication_id(plan) == manifest['publication_id'], 'increment identity changed')
    require(set(plan['scope']) == set(manifest['candidate_heads']), 'scope differs')
    require(not plan['media'] and not plan['comment_events'] and not plan['changes']['comments'],
            'media or test comments included')
    verify_files(manifest, instance)
    verify_heads(instance, manifest, installed=False)
    db = connect(instance / '.runtime/review.sqlite3', readonly=False)
    try:
        result = apply_plan(db, plan)
        require(apply_plan(db, plan)['already_published'], 'repeat was not idempotent')
    finally:
        db.close()
    actual = build_plan(instance / '.runtime/generation-base.sqlite3', instance / '.runtime/review.sqlite3')
    actual['guard_heads'].update(manifest['protected_heads'])
    for field in ('scope', 'expected_heads', 'expected_references', 'guard_heads', 'changes', 'comment_events',
                  'media', 'version_baseline', 'expected_numbered_objects'):
        require(actual[field] == plan[field], 'extra or missing changes: ' + field)
    verify_heads(instance, manifest, installed=True)
    verify_semantics(instance, plan, manifest)
    verify_files(manifest, instance)
    from scene_reading import compile_reading
    overlay = json.loads((DELIVERY / 'reading-overlay.json').read_text())
    require(compile_reading(instance, SHOTS) == overlay, 'exact reading offsets differ')
    for rid, entry in overlay['entries'].items():
        require(rid not in config['scene_reading']['entries'] or config['scene_reading']['entries'][rid] == entry,
                'reading entry collision')
    config['scene_reading']['entries'].update(overlay['entries'])
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'instance': instance.relative_to(root).as_posix(), 'publication_id': result['publication_id'],
                      'objects': len(plan['scope']), 'production_objects': 10, 'public_method_records': 16,
                      'protected_heads': len(manifest['protected_heads']), 'consumer_edges': len(manifest['consumer_edges']),
                      'original_components_checked': len(manifest['originals']), 'formal_writes': 0,
                      'repeat_idempotent': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
