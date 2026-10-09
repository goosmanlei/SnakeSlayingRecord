"""One-scene author checkpoints. No model calls or formal-instance writes.

Earlier adopted scenes remain in the author conversation. `context --full`
reloads their exact text after a context reset; the default prints the index
and continuity notes. Read/accept records establish order, not literary merit.
"""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from .method_runtime import MethodClient
except ImportError:
    from method_runtime import MethodClient


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


class Run:
    def __init__(self, path, method_client=None):
        self.method_client = method_client
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS checkpoints(seq INTEGER PRIMARY KEY, hash TEXT UNIQUE, payload TEXT);
          CREATE TABLE IF NOT EXISTS pending(singleton INTEGER PRIMARY KEY CHECK(singleton=1), base TEXT, payload TEXT, read_hash TEXT);
          CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, at TEXT, action TEXT, payload TEXT);
          CREATE TABLE IF NOT EXISTS method_steps(id TEXT PRIMARY KEY, base TEXT, spec TEXT, delivery TEXT, status TEXT);
          CREATE TABLE IF NOT EXISTS method_meta(key TEXT PRIMARY KEY, value TEXT);
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
        active = self.db.execute("SELECT delivery FROM method_steps WHERE status='ACTIVE'").fetchone()
        result['method_execution'] = json.loads(active[0])['execution'] if active else None
        with self.db:
            self.event('CONTEXT_FULL' if full else 'CONTEXT_INDEX', {'revision': head})
        return result

    def begin(self, spec):
        if (not isinstance(spec, dict) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', spec.get('step_id', ''))
                or not spec.get('scene_id') or not spec.get('context')):
            raise ValueError('begin requires step_id, scene_id and accurate context')
        if self.method_client is None:
            raise ValueError('新剧本步骤须指定 --method-url，取得准确方法后再写作')
        # Retain the run identity even if the remote prepare succeeds but its
        # response is lost. Retrying must retrieve the original execution.
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO method_meta VALUES ('run_id',?)", (str(uuid.uuid4()),))
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.db.execute('SELECT spec,delivery FROM method_steps WHERE id=?', (spec['step_id'],)).fetchone()
            if old:
                if json.loads(old[0]) != spec:
                    raise ValueError('step identity reused with different inputs')
                delivery = json.loads(old[1])
                self._verify_method(delivery)
                return delivery['execution']
            if self.db.execute("SELECT 1 FROM pending UNION ALL SELECT 1 FROM method_steps WHERE status='ACTIVE'").fetchone():
                raise ValueError('finish or reject the active scene first')
            head, state = self.current()
            if spec.get('base_revision') != head:
                raise ValueError('read the current checkpoint before begin')
            row = self.db.execute("SELECT value FROM method_meta WHERE key='run_id'").fetchone()
            run_id = row[0]
            request = {'work_type': 'screenplay-writing', 'run_id': run_id, 'step_id': spec['step_id'],
                       'target': spec['scene_id'], 'private': True, 'conditions': spec.get('conditions', {}),
                       'inputs': {'context': {'source': spec['context'], 'checkpoint': state, 'spec': spec}}}
            execution = self.method_client.prepare(request)
            if execution['payload']['package']['steps'] != ['draft', 'review', 'result']:
                raise ValueError('剧本方法须支持 draft、review、result')
            delivery = {'request': request, 'execution': execution}
            self.db.execute("INSERT INTO method_steps VALUES (?,?,?,?,'ACTIVE')",
                            (spec['step_id'], head, encoded(spec), encoded(delivery)))
            self.event('METHOD_BEGIN', {'step_id': spec['step_id'], 'base': head})
        return execution

    def _verify_method(self, delivery):
        if self.method_client is None or self.method_client.prepare(delivery['request']) != delivery['execution']:
            raise ValueError('准确方法服务或原步骤快照不一致；不能借用其他步骤')

    def _method(self, scene_id, stage, output):
        row = self.db.execute("SELECT base,delivery FROM method_steps WHERE status='ACTIVE'").fetchone()
        if not row:
            raise ValueError('本候选缺少方法历史；先 begin 新步骤，不能补造旧记录')
        delivery = json.loads(row[1])
        if row[0] != self.current()[0] or delivery['request']['target'] != scene_id:
            raise ValueError('方法步骤与当前场次或检查点不一致')
        self._verify_method(delivery)
        return self.method_client.artifact(delivery['execution'], delivery['request'], stage, output)

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
            self._method(scene['id'], 'draft', scene)
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
            self._method(scene['id'], 'review', review)
            self._method(scene['id'], 'result', scene)
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
            self.db.execute("UPDATE method_steps SET status='ACCEPTED' WHERE status='ACTIVE'")
        return {'accepted': scene['id'], 'revision': new, 'scenes': len(state['scenes'])}

    def reject(self, reason):
        if not reason:
            raise ValueError('reason required')
        with self.db:
            self.event('REJECT', {'reason': reason})
            self.db.execute('DELETE FROM pending')
            self.db.execute("UPDATE method_steps SET status='REJECTED' WHERE status='ACTIVE'")

    def arrange(self, change):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute("SELECT 1 FROM pending UNION ALL SELECT 1 FROM method_steps WHERE status='ACTIVE'").fetchone():
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
            if self.db.execute("SELECT 1 FROM pending UNION ALL SELECT 1 FROM method_steps WHERE status='ACTIVE'").fetchone() or not state['scenes']:
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
    parser.add_argument('--method-url', help='新场次必需的本机方法服务')
    parser.add_argument('action', choices=['begin','context','save','read','accept','reject','arrange','finalize'])
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    run = Run(Path(args.run)/'work.sqlite3', MethodClient(args.method_url) if args.method_url else None)
    try:
        if args.action == 'context': result = run.context(args.full)
        elif args.action == 'read': result = run.read()
        else: result = getattr(run, args.action)(json.load(sys.stdin))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        run.close()


if __name__ == '__main__':
    main()
