#!/usr/bin/env python3
"""Adapt the archived song increment to the current material model in isolation."""
import argparse
import copy
import json
from pathlib import Path
import sys
import wave

from generation_workspace import generation_root, isolated_instance, write_json
from generation_publication import build_plan
from material_model_io import read_json
from publish_song_stage import allowed


def insert(db, table, row):
    columns = list(row)
    db.execute('INSERT INTO ' + table + ' (' + ','.join(columns) + ') VALUES (' +
               ','.join('?' for _ in columns) + ')', tuple(row.values()))


def prepare(root, instance, output):
    from review_desk.store import Store
    from review_desk import production, material_plans, material_model, material_storage
    root = generation_root(root)
    instance = isolated_instance(root, instance)
    source = read_json(root / 'production/song-stage/publication-plan.json')
    legacy_tables = {'revisions', 'dependencies', 'comments', 'material_rounds',
                     'material_members', 'material_feedback', 'material_comment_scopes'}
    if source.get('format') != 'songs-current-stage-publication-v1':
        raise ValueError('unsupported song increment')
    scope = set(source['scope'])
    if (scope != set(source['expected_heads']) or
            scope != {r['id'] for r in source['objects']} or
            not all(map(allowed, scope)) or set(source['insert']) != legacy_tables):
        raise ValueError('invalid archived song scope')
    new_revisions = {r['id'] for r in source['insert']['revisions']}
    new_comments = {r['id'] for r in source['insert']['comments']}
    if (any(r['object_id'] not in scope for r in source['insert']['revisions']) or
            any(r['target_object_id'] not in scope for r in source['insert']['comments']) or
            any(r['from_revision'] not in new_revisions for r in source['insert']['dependencies']) or
            any(r['comment_id'] not in new_comments for r in source['comment_events']) or
            any(r['material_id'] not in scope for t in legacy_tables if t.startswith('material_')
                for r in source['insert'][t])):
        raise ValueError('archived history outside song scope')
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        db = store.db
        db.execute('BEGIN IMMEDIATE')
        for oid, expected in source['expected_heads'].items():
            actual = db.execute('SELECT * FROM objects WHERE id=?', (oid,)).fetchone()
            if (dict(actual) if actual else None) != expected:
                raise ValueError('song head changed: ' + oid)
        for rid, expected in source['expected_references'].items():
            actual = db.execute('SELECT * FROM revisions WHERE id=?', (rid,)).fetchone()
            if not actual or dict(actual) != expected:
                raise ValueError('exact song dependency changed: ' + rid)
        for row in source['objects']:
            if source['expected_heads'][row['id']] is None:
                insert(db, 'objects', row)
            else:
                db.execute('UPDATE objects SET current_revision=?,version=?,updated_at=? WHERE id=?',
                           tuple(row[k] for k in ('current_revision', 'version', 'updated_at', 'id')))
        for table in ('revisions', 'dependencies', 'comments', 'material_rounds',
                      'material_members', 'material_feedback', 'material_comment_scopes'):
            for original in source['insert'][table]:
                row = dict(original)
                if table == 'revisions':
                    row['payload'] = material_storage.encode(store, json.loads(row['payload']), row['payload'])
                insert(db, table, row)
        for event in source['comment_events']:
            insert(db, 'comment_events', {k: v for k, v in event.items() if k != 'id'})
        rows = [production.record(store, revision_id=r['id']) for r in
                sorted(source['insert']['revisions'], key=lambda r: (r['created_at'], r['object_id'], r['version']))]
        # Actual calls/results establish frozen definitions before historical drafts.
        for row in rows:
            if row['kind'] != 'REQUIREMENT':
                material_plans.register(store, row)
        for row in rows:
            if row['kind'] == 'CALL':
                material_plans.register(store, row)
        for row in rows:
            if row['kind'] == 'REQUIREMENT':
                material_model.refresh_identity(store, row)
                material_plans.register(store, row)
        for comment in source['insert']['comments']:
            legacy = {r['material_id'] for r in source['insert']['material_comment_scopes']
                      if r['comment_id'] == comment['id']}
            for membership in material_plans.memberships(store, comment['target_revision_id']):
                if membership['material_id'] in legacy:
                    material_plans.comment_scope(store, comment, {
                        'model': 'plan-v1', 'material_id': membership['material_id'],
                        'number': membership['number']})
        precision_checks = []
        for row in rows:
            validation_payload = copy.deepcopy(row['payload'])
            if row['kind'] == 'CALL':
                for ref in validation_payload.get('inputs', []):
                    interval = ref.get('range')
                    if not interval or not ref.get('component_id'):
                        continue
                    _, component = production.component_for(store, ref, ref['component_id'])
                    end = interval['end_seconds']
                    duration = component.get('duration_seconds', 0)
                    if end > duration and component['mime'] == 'audio/wav':
                        with wave.open(str(instance / 'export/assets' / component['file'])) as audio:
                            actual = audio.getnframes() / audio.getframerate()
                        # Historical metadata rounds to six decimals. Verify exact PCM
                        # frames, then adjust ONLY the validation view, never history.
                        if end <= actual and 0 < end - duration < 0.0000005:
                            precision_checks.append({'revision_id': row['id'], 'file': component['file'],
                                                     'recorded_duration': duration, 'pcm_duration': actual,
                                                     'range_end': end})
                            interval['end_seconds'] = duration
            try:
                production.validate_payload(store, row['object_id'], row['kind'], validation_payload,
                                            inspect=True, check_current=False)
            except ValueError as exc:
                raise ValueError(row['object_id'] + ' revision ' + str(row['version']) + ': ' + str(exc)) from exc
        material_plans.validate(store)
        material_model.verify(store)
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('song increment has broken references')
        db.commit()
    except BaseException:
        store.db.rollback()
        raise
    finally:
        store.close()
    return write_plan(root, instance, output, precision_checks)


def write_plan(root, instance, output, precision_checks):
    source = read_json(root / 'production/song-stage/publication-plan.json')
    scope = set(source['scope'])
    plan = build_plan(instance / '.runtime/generation-base.sqlite3', instance / '.runtime/review.sqlite3')
    if not set(plan['scope']) <= scope:
        raise ValueError('current model touched unrelated objects')
    plan['origin'] = {'kind': 'archived-song-stage', 'source': 'production/song-stage/publication-plan.json',
                      'audio_quality_accepted': False, 'screenplay_changed': False,
                      'historical_pcm_precision_checks': precision_checks}
    write_json(root, output, plan)
    return {'package': str(output), 'objects': len(plan['scope']), 'media': len(plan['media']),
            'changes': {t: len(rows) for t, rows in plan['changes'].items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('production/publications/songs-current-model-v2.json'))
    parser.add_argument('--refresh-after-export', action='store_true',
                        help='rebuild the delta after isolated export has registered metadata archives')
    parser.add_argument('--prior-package', type=Path,
                        help='original private package, when refreshing into a new output')
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    root = generation_root(Path(__file__).resolve().parents[1])
    if args.refresh_after_export:
        if not args.prior_package:
            parser.error('--refresh-after-export requires --prior-package and a new --output')
        instance = isolated_instance(root, args.instance)
        prior = read_json(root / args.prior_package)
        result = write_plan(root, instance, args.output, prior['origin']['historical_pcm_precision_checks'])
    else:
        result = prepare(root, args.instance, args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
