"""One-scene author checkpoints. No model calls or formal-instance writes.

Earlier adopted scenes remain in the author conversation. `context --full`
reloads their exact text after a context reset; the default prints the index
and continuity notes. Read/accept records establish order, not literary merit.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


class Run:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS checkpoints(seq INTEGER PRIMARY KEY, hash TEXT UNIQUE, payload TEXT);
          CREATE TABLE IF NOT EXISTS pending(singleton INTEGER PRIMARY KEY CHECK(singleton=1), base TEXT, payload TEXT, read_hash TEXT);
          CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, at TEXT, action TEXT, payload TEXT);
        ''')
        if not self.db.execute('SELECT 1 FROM checkpoints').fetchone():
            with self.db:
                self.checkpoint({'scenes': [], 'notes': '', 'reviewed': False}, 'INIT')

    def close(self):
        self.db.close()

    def current(self):
        row = self.db.execute('SELECT hash,payload FROM checkpoints ORDER BY seq DESC LIMIT 1').fetchone()
        return row[0], json.loads(row[1])

    def event(self, action, value):
        self.db.execute('INSERT INTO events(at,action,payload) VALUES (?,?,?)',
                        (datetime.now(timezone.utc).isoformat(), action, encoded(value)))

    def checkpoint(self, value, reason):
        previous = self.db.execute('SELECT hash FROM checkpoints ORDER BY seq DESC LIMIT 1').fetchone()
        sha = digest({'previous': previous[0] if previous else None, 'value': value, 'reason': reason})
        self.db.execute('INSERT INTO checkpoints(hash,payload) VALUES (?,?)', (sha, encoded(value)))
        self.event(reason, {'revision': sha})
        return sha

    def context(self, full=False):
        head, state = self.current()
        result = {'revision': head, 'notes': state['notes'], 'scenes': state['scenes'] if full else
                  [{k: s[k] for k in ('id','episode','episode_title','heading','seconds')} for s in state['scenes']],
                  'pending': bool(self.db.execute('SELECT 1 FROM pending').fetchone())}
        with self.db:
            self.event('CONTEXT_FULL' if full else 'CONTEXT_INDEX', {'revision': head})
        return result

    def save(self, scene):
        required = ('id','episode','episode_title','heading','location','time','seconds','chapters','design','text')
        if not isinstance(scene, dict) or any(not scene.get(k) for k in required):
            raise ValueError('one complete scene and its design required')
        if type(scene['episode']) is not int or scene['episode'] < 1 or type(scene['seconds']) is not int or scene['seconds'] < 1:
            raise ValueError('positive episode and duration required')
        if not isinstance(scene['text'], str) or not isinstance(scene['chapters'], list):
            raise ValueError('scene text and source chapters required')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute('SELECT 1 FROM pending').fetchone():
                raise ValueError('read and accept or reject current scene first')
            head, _ = self.current()
            self.db.execute('INSERT INTO pending VALUES (1,?,?,NULL)', (head, encoded(scene)))
            self.event('SAVE', {'base': head, 'scene_id': scene['id'], 'sha256': digest(scene)})
        return {'saved': scene['id'], 'base': head, 'sha256': digest(scene)}

    def read(self):
        with self.db:
            row = self.db.execute('SELECT base,payload FROM pending').fetchone()
            if not row:
                raise ValueError('no candidate')
            scene = json.loads(row[1])
            self.db.execute('UPDATE pending SET read_hash=?', (digest(scene),))
            self.event('READ', {'base': row[0], 'scene_id': scene['id'], 'sha256': digest(scene)})
        return scene

    def accept(self, review):
        if not review.get('assessment') or not review.get('continuity'):
            raise ValueError('actual assessment and continuity notes required')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self.db.execute('SELECT base,payload,read_hash FROM pending').fetchone()
            if not row:
                raise ValueError('no candidate')
            head, state = self.current()
            scene = json.loads(row[1])
            if head != row[0] or row[2] != digest(scene):
                raise ValueError('candidate must be reread on current base')
            index = next((i for i,s in enumerate(state['scenes']) if s['id']==scene['id']), None)
            if index is None:
                state['scenes'].append(scene)
            else:
                state['scenes'][index] = scene
            state['notes'] = review['continuity']
            state['reviewed'] = False
            self.event('ACCEPT', {'scene_id': scene['id'], 'review': review, 'base': head})
            new = self.checkpoint(state, 'ADOPT')
            self.db.execute('DELETE FROM pending')
        return {'accepted': scene['id'], 'revision': new, 'scenes': len(state['scenes'])}

    def reject(self, reason):
        if not reason:
            raise ValueError('reason required')
        with self.db:
            self.event('REJECT', {'reason': reason})
            self.db.execute('DELETE FROM pending')

    def arrange(self, change):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute('SELECT 1 FROM pending').fetchone():
                raise ValueError('finish candidate first')
            _, state = self.current()
            by_id = {s['id']: s for s in state['scenes']}
            order, retired = change['order'], change.get('retired', [])
            if not change.get('reason') or len(order) != len(set(order)) or set(order)&set(retired) or set(order)|set(retired) != set(by_id):
                raise ValueError('explicit complete order and retired IDs required')
            state['scenes'] = [by_id[id] for id in order]
            for s in state['scenes']:
                if s['id'] in change.get('episodes', {}):
                    s['episode'], s['episode_title'] = change['episodes'][s['id']]
            state['reviewed'] = False
            self.event('ARRANGE', change)
            return self.checkpoint(state, 'ARRANGED')

    def finalize(self, review):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            head, state = self.current()
            if self.db.execute('SELECT 1 FROM pending').fetchone() or not state['scenes']:
                raise ValueError('unfinished manuscript')
            if review.get('revision') != head or not review.get('assessment'):
                raise ValueError('review exact current manuscript')
            if set(review.get('scene_ids', [])) != {s['id'] for s in state['scenes']}:
                raise ValueError('review every active scene')
            state['reviewed'] = review
            return self.checkpoint(state, 'FULL_REVIEW')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', default='.runtime/screenplay-02')
    parser.add_argument('action', choices=['context','save','read','accept','reject','arrange','finalize'])
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    run = Run(Path(args.run)/'work.sqlite3')
    try:
        if args.action == 'context': result = run.context(args.full)
        elif args.action == 'read': result = run.read()
        else: result = getattr(run, args.action)(json.load(sys.stdin))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        run.close()


if __name__ == '__main__':
    main()
