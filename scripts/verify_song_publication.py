#!/usr/bin/env python3
"""Verify song history, preservation, conflict refusal and idempotency on copies."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generation_publication import apply_plan, backup, canonical, connect, key, tables, KEYS
from generation_workspace import generation_root, contained, verify_media, write_json
from material_model_io import read_json, sqlite_compatibility


def verify(root, baseline, candidate, package, run, output):
    from review_desk.store import Store
    from review_desk import material_plans, material_model
    root = generation_root(root)
    run = contained(root, run)
    run.mkdir(parents=True, exist_ok=False)
    plan = read_json(root / package)
    legacy = read_json(root / 'production/song-stage/publication-plan.json')
    before, after = tables(baseline), tables(candidate)
    for table, rows in before.items():
        if table in KEYS:
            actual = {key(table, r): r for r in after[table]}
            touched = {key(table, c['before']) for c in plan['changes'][table] if c['before']}
            assert all(actual.get(key(table, row)) == row for row in rows if key(table, row) not in touched), table
        else:
            actual = {r['id']: r for r in after[table]} if table == 'comment_events' else None
            assert (all(actual.get(r['id']) == r for r in rows) if actual is not None else rows == after[table]), table
    db = connect(candidate)
    sqlite_compatibility(db, hydrate=True)
    for original in legacy['insert']['revisions']:
        actual = dict(db.execute('SELECT * FROM revisions WHERE id=?', (original['id'],)).fetchone())
        assert actual == original, 'historical revision bytes changed: ' + original['id']
    for original in legacy['insert']['comments']:
        actual = dict(db.execute('SELECT * FROM comments WHERE id=?', (original['id'],)).fetchone())
        assert actual == original, 'historical comment changed'
    db.close()
    verify_media(root, plan['media'])
    store = Store(candidate)
    songs = []
    try:
        material_model.verify(store)
        material_plans.validate(store)
        for stem, expected in [('boat', 3), ('blue-awning', 3), ('welcome', 2), ('blessing', 2)]:
            mid = 'need-form-' + stem + '-song-independent-overall'
            versions = material_plans.snapshot(store, mid)
            results = [r for v in versions for r in v['results']]
            originals = {c['sha256'] for r in results for c in r['payload']['components'] if c['role'] == 'original'}
            assert len(originals) == expected, 'missing independent recording: ' + stem
            songs.append({'song': stem, 'material_id': mid,
                          'versions': [{'number': v['number'], 'state': v['state'],
                                        'candidates': [{'revision_id': r['id'], 'candidate_id': r['candidate_id'],
                                                        'duration_seconds': next(c['duration_seconds'] for c in r['payload']['components'] if c['role'] == 'original')}
                                                       for r in v['results']]} for v in versions]})
    finally:
        store.close()
    conflict = run / 'conflict.sqlite3'
    backup(baseline, conflict)
    db = connect(conflict, readonly=False)
    oid = next(oid for oid, old in plan['expected_heads'].items() if old)
    db.execute('UPDATE objects SET updated_at=? WHERE id=?', ('isolated-concurrent-edit', oid))
    db.commit()
    unchanged = tables(conflict)
    try:
        apply_plan(db, plan)
        raise AssertionError('changed song head was accepted')
    except ValueError as exc:
        assert 'formal object changed' in str(exc), str(exc)
    db.close()
    assert tables(conflict) == unchanged, 'conflict left partial writes'
    rollback = run / 'rollback.sqlite3'
    backup(baseline, rollback)
    broken = copy.deepcopy(plan)
    broken['changes']['dependencies'][0]['after']['to_revision'] = 'isolated-missing-reference'
    db = connect(rollback, readonly=False)
    try:
        apply_plan(db, broken)
        raise AssertionError('broken dependency was accepted')
    except Exception as exc:
        assert 'FOREIGN KEY' in str(exc), str(exc)
    db.close()
    assert tables(rollback) == before, 'failed transaction left partial writes'
    concurrent = run / 'concurrent.sqlite3'
    backup(baseline, concurrent)
    db = connect(concurrent, readonly=False)
    fixture = dict(next(r for r in before['comments'] if r['target_object_id'] not in plan['scope']))
    fixture.update(id='isolated-song-publication-concurrent-comment', body='isolated concurrency fixture')
    db.execute('INSERT INTO comments (' + ','.join(fixture) + ') VALUES (' +
               ','.join('?' for _ in fixture) + ')', tuple(fixture.values()))
    db.execute('INSERT INTO comment_events(comment_id,action,body,at) VALUES (?,?,?,?)',
               (fixture['id'], 'created', fixture['body'], fixture['created_at']))
    db.commit()
    first = apply_plan(db, plan)
    actual = dict(db.execute('SELECT * FROM comments WHERE id=?', (fixture['id'],)).fetchone())
    assert actual == fixture, 'unrelated concurrent comment changed'
    once = tables(concurrent)
    repeated = apply_plan(db, plan)
    db.close()
    assert repeated['already_published'] and tables(concurrent) == once, 'repeat duplicated history'
    result = {'format': 'songs-current-model-verification-v1',
              'publication_sha256': hashlib.sha256((root / package).read_bytes()).hexdigest(),
              'historical_revisions_preserved': len(legacy['insert']['revisions']),
              'historical_comments_preserved': len(legacy['insert']['comments']),
              'managed_files_verified': len(plan['media']), 'independent_recordings': 10,
              'unrelated_rows_preserved': True, 'conflict_rollback': True,
              'broken_dependency_rollback': True, 'concurrent_comment_preserved': True,
              'repeat_is_idempotent': True, 'songs': songs,
              'audio_quality_accepted': False, 'screenplay_changed': False}
    write_json(root, output, result)
    return {k: v for k, v in result.items() if k != 'songs'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--package', type=Path, default=Path('production/publications/songs-current-model-v2.json'))
    parser.add_argument('--run', type=Path, default=Path('.runtime/song-publication/checks'))
    parser.add_argument('--output', type=Path, default=Path('production/song-publication/verification.json'))
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    print(json.dumps(verify(Path(__file__).resolve().parents[1], args.baseline, args.candidate,
                            args.package, args.run, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
