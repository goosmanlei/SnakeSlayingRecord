#!/usr/bin/env python3
"""Publish the reviewed song increment without replacing the active database.

Defaults to rehearsal on a fresh backup. Explicit --apply requires the shared
writer lock, exact song heads and references, and the validated media bytes.
Does not export, deploy a service, generate audio, accept audio or complete a task.
"""
import argparse
import json
from pathlib import Path

try:
    from .generation_publication import KEYS, journal, publication_id
    from .publish_generation import run_publication
except ImportError:
    from generation_publication import KEYS, journal, publication_id
    from publish_generation import run_publication

ROOT = Path(__file__).resolve().parents[1]
ENTITIES = {'entity-boat-song', 'entity-blue-awning-song', 'entity-snake-welcome-song', 'entity-blessing-stage-song'}
STEMS = ('boat', 'blue-awning', 'snake-welcome', 'blessing-stage', 'welcome', 'blessing')

def allowed(oid):
    return oid in ENTITIES or oid.startswith(('call-songs-', 'asset-songs-', 'review-songs-')) or any((oid.startswith(prefix + stem + '-song-') for prefix in ('form-', 'need-form-') for stem in STEMS))

def apply(db, plan):
    if not plan['format'] == 'songs-current-stage-publication-v1':
        raise ValueError('invalid song publication data')
    if not set(plan['scope']) == set(plan['expected_heads']) == {r['id'] for r in plan['objects']}:
        raise ValueError('invalid song publication data')
    if not all(map(allowed, plan['scope'])):
        raise ValueError('invalid song publication data')
    if not set(plan['insert']) == set(KEYS) - {'objects'}:
        raise ValueError('invalid song publication data')
    if not all((r['object_id'] in plan['scope'] for r in plan['insert']['revisions'])):
        raise ValueError('invalid song publication data')
    if not all((r['target_object_id'] in plan['scope'] for r in plan['insert']['comments'])):
        raise ValueError('invalid song publication data')
    if not all((r['material_id'] in plan['scope'] for t in ('material_rounds', 'material_members', 'material_feedback', 'material_comment_scopes') for r in plan['insert'][t])):
        raise ValueError('invalid song publication data')
    new_rids = {r['id'] for r in plan['insert']['revisions']}
    if not all((r['from_revision'] in new_rids for r in plan['insert']['dependencies'])):
        raise ValueError('invalid song publication data')
    new_cids = {r['id'] for r in plan['insert']['comments']}
    if not all((r['comment_id'] in new_cids for r in plan['comment_events'])):
        raise ValueError('invalid song publication data')
    event_map = []
    def mutate():
        for (oid, expected) in plan['expected_heads'].items():
            row = db.execute('SELECT * FROM objects WHERE id=?', (oid,)).fetchone()
            if (dict(row) if row else None) != expected:
                raise ValueError('formal song head changed: ' + oid)
        for (rid, expected) in plan['expected_references'].items():
            row = db.execute('SELECT * FROM revisions WHERE id=?', (rid,)).fetchone()
            if not row or dict(row) != expected:
                raise ValueError('exact reference changed: ' + rid)
        for row in plan['objects']:
            if plan['expected_heads'][row['id']] is None:
                db.execute('INSERT INTO objects VALUES (?,?,?,?,?,?)', tuple((row[k] for k in ('id', 'kind', 'current_revision', 'version', 'created_at', 'updated_at'))))
            else:
                db.execute('UPDATE objects SET current_revision=?,version=?,updated_at=? WHERE id=?', (row['current_revision'], row['version'], row['updated_at'], row['id']))
        for (table, records) in plan['insert'].items():
            for row in records:
                names = list(row)
                db.execute('INSERT INTO ' + table + ' (' + ','.join(names) + ') VALUES (' + ','.join(('?' for _ in names)) + ')', tuple((row[k] for k in names)))
        for row in plan['comment_events']:
            result = db.execute('INSERT INTO comment_events (comment_id,action,body,at) VALUES (?,?,?,?)', tuple((row[k] for k in ('comment_id', 'action', 'body', 'at'))))
            event_map.append({'source_id': row['id'], 'published_id': result.lastrowid, 'comment_id': row['comment_id']})
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('foreign key validation failed')
        return {'objects': len(plan['objects']), 'new_objects': sum((x is None for x in plan['expected_heads'].values())), 'inserted': {t: len(rs) for (t, rs) in plan['insert'].items()}, 'comment_events': event_map, 'audio_quality_accepted': False, 'screenplay_changed': False}
    return journal(db, publication_id(plan), mutate)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--source-commit')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = run_publication(args.workspace, args.instance,
        'production/song-stage/publication-plan.json', args.run_name,
        apply=args.apply, source_commit=args.source_commit, apply_fn=apply)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
