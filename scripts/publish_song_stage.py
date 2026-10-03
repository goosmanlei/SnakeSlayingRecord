#!/usr/bin/env python3
"""Publish the reviewed song increment without replacing the active database.

Defaults to rehearsal on a fresh backup. Explicit --apply requires the shared
writer lock, exact song heads and references, and the validated media bytes.
Does not export, deploy a service, generate audio, accept audio or complete a task.
"""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
KEYS = {'objects': ('id',), 'revisions': ('id',), 'dependencies': ('from_revision', 'to_revision', 'role'), 'comments': ('id',), 'material_rounds': ('material_id', 'number'), 'material_members': ('material_id', 'number', 'revision_id'), 'material_feedback': ('comment_id',), 'material_comment_scopes': ('comment_id', 'material_id')}
ENTITIES = {'entity-boat-song', 'entity-blue-awning-song', 'entity-snake-welcome-song', 'entity-blessing-stage-song'}
STEMS = ('boat', 'blue-awning', 'snake-welcome', 'blessing-stage', 'welcome', 'blessing')

def allowed(oid):
    return oid in ENTITIES or oid.startswith(('call-songs-', 'asset-songs-', 'review-songs-')) or any((oid.startswith(prefix + stem + '-song-') for prefix in ('form-', 'need-form-') for stem in STEMS))

def connect(path, readonly=True):
    db = sqlite3.connect(path.resolve().as_uri() + ('?mode=ro' if readonly else '?mode=rw'), uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def rows(db, table):
    return [dict(r) for r in db.execute('SELECT * FROM ' + table)]

def save(path, value):
    if path.exists():
        raise ValueError('preserve earlier evidence: ' + str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def copy_media(plan, source_dir, destination_dir):
    for entry in plan['media']:
        if not re.fullmatch(r'[a-f0-9]{64}\.[a-z0-9]+', entry['file']):
            raise ValueError('media must use a content-addressed basename')
        source = source_dir / entry['file']
        if not (source.is_file() and source.stat().st_size == entry['bytes'] and (sha(source) == entry['sha256'])):
            raise ValueError('invalid song publication data')
        target = destination_dir / entry['file']
        if target.exists():
            if not (target.is_file() and sha(target) == entry['sha256']):
                raise ValueError('existing file conflict')
    destination_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    for entry in plan['media']:
        target = destination_dir / entry['file']
        if not target.exists():
            with target.open('xb') as stream, (source_dir / entry['file']).open('rb') as source:
                shutil.copyfileobj(source, stream)
            if not sha(target) == entry['sha256']:
                raise ValueError('invalid song publication data')
            added += 1
    return added

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
    with db:
        db.execute('BEGIN IMMEDIATE')
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

def verify_preservation(before_path, after_path, plan):
    (before, after) = (connect(before_path), connect(after_path))
    try:
        names = [r[0] for r in before.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        report = {}
        for table in names:
            old = [tuple(r) for r in before.execute('SELECT * FROM ' + table)]
            new = [tuple(r) for r in after.execute('SELECT * FROM ' + table)]
            removed = list((Counter(old) - Counter(new)).elements())
            if table == 'objects':
                if not {r[0] for r in removed} == {k for (k, v) in plan['expected_heads'].items() if v is not None}:
                    raise ValueError('invalid song publication data')
            elif removed:
                raise ValueError('protected row changed: ' + table)
            report[table] = {'before': len(old), 'after': len(new), 'removed_or_updated': len(removed)}
        return report
    finally:
        before.close()
        after.close()


def backup(source, destination):
    if destination.exists():
        raise ValueError('preserve previous attempt: ' + str(destination))
    src, dst = connect(source), sqlite3.connect(destination)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.run_name):
        parser.error('run-name must be a safe, unique runtime directory name')
    target = args.instance.resolve()
    db_path = target / '.runtime/review.sqlite3'
    if target == ROOT or not db_path.is_file():
        parser.error('explicit existing instance required; never restore over a task checkout')
    plan_path = ROOT / 'production/song-stage/publication-plan.json'
    plan = json.loads(plan_path.read_text())
    run = ROOT / '.runtime/songs/current-state-closeout/publication' / args.run_name
    run.mkdir(parents=True, exist_ok=False)
    with (target / '.runtime/publication.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = run / 'before.sqlite3'
        backup(db_path, before)
        rehearsal = run / 'rehearsal.sqlite3'
        shutil.copyfile(before, rehearsal)
        db = connect(rehearsal, readonly=False)
        try:
            simulated = apply(db, plan)
        finally:
            db.close()
        preserved = verify_preservation(before, rehearsal, plan)
        # Verify source bytes even in dry-run mode. Stage them only in this run.
        copied = copy_media(plan, ROOT / 'export/assets', run / 'assets')
        result = {'plan_sha256': sha(plan_path), 'scope': simulated,
                  'preserved_tables': preserved, 'verified_media_files': copied,
                  'applied': False, 'audio_quality_accepted': False,
                  'exported': False, 'deployed': False}
        save(run / 'preflight.json', result)
        if args.apply:
            # A concurrent non-cooperating song writer is rejected again inside
            # the transaction. Unreferenced copied files are safe to retain.
            copy_media(plan, ROOT / 'export/assets', target / 'export/assets')
            db = connect(db_path, readonly=False)
            try:
                result['scope'] = apply(db, plan)
            finally:
                db.close()
            # Write the transaction receipt before post-commit verification so a
            # failed later check cannot be mistaken for a safe-to-repeat call.
            save(run / 'transaction.json', result['scope'])
            after = run / 'after.sqlite3'
            backup(db_path, after)
            result.update(applied=True,
                          preserved_tables=verify_preservation(before, after, plan))
            save(run / 'applied.json', result)
        print(json.dumps({'applied': result['applied'], 'objects': len(plan['scope']),
                          'media_files': len(plan['media']),
                          'receipt': str(run.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
