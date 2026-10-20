"""Reproducible, sequential performance measurements on an owned private copy.

Run inside the verified application image. Never pass a live instance to bench.
Snapshot copies no credentials and only locally available small JSON originals.
No signed URL or business response body is written to the measurement report.
"""
import argparse
import collections
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import statistics
import sys
import threading
import time
from urllib.parse import urlencode


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def snapshot(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if target.exists() or source == target or target.is_symlink():
        raise ValueError('snapshot must be a new owned directory')
    database = source / '.runtime/review.sqlite3'
    target.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(target.parent).free < database.stat().st_size * 3 + 1024**3:
        raise ValueError('insufficient snapshot and working-copy reserve')
    target.mkdir()
    for folder in ('config', 'content'):
        shutil.copytree(source / folder, target / folder)
    (target / '.runtime').mkdir()
    runtime_catalog = source / '.runtime/resources/catalog.json'
    if runtime_catalog.is_file():
        (target / '.runtime/resources').mkdir()
        shutil.copyfile(runtime_catalog, target / '.runtime/resources/catalog.json')
    started = time.perf_counter()
    with readonly(database) as original, sqlite3.connect(target / '.runtime/review.sqlite3') as copy:
        original.backup(copy, pages=256, sleep=.01)
    copied = []
    cache = target / '.runtime/resource-cache'
    cache.mkdir()
    for file in sorted((source / '.runtime/resource-cache').glob('*.json')):
        if file.is_file() and not file.is_symlink() and file.stat().st_size <= 8 * 1024**2:
            shutil.copyfile(file, cache / file.name)
            copied.append({'name': file.name, 'bytes': file.stat().st_size})
    describe(target, database.stat().st_size, time.perf_counter()-started, copied)


def describe(target, database_bytes=None, snapshot_seconds=None, copied=None):
    target = Path(target)
    with readonly(target / '.runtime/review.sqlite3') as db:
        counts = {name: db.execute('SELECT count(*) FROM "' + name + '"').fetchone()[0]
                  for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        outputs = db.execute("SELECT o.id,r.id,r.payload FROM objects o JOIN revisions r ON r.id=o.current_revision WHERE o.kind='EPISODE_FILM' ORDER BY o.created_at DESC,o.id DESC").fetchall()
        films = [{'object_id': oid, 'revision_id': rid, 'project': json.loads(payload)['project']} for oid, rid, payload in outputs]
        shot = db.execute("SELECT current_revision FROM objects WHERE id='new26-s001-q02'").fetchone()[0]
        episode = db.execute("SELECT current_revision FROM objects WHERE id='new26-e01'").fetchone()[0]
        source_id, source_revision = db.execute("SELECT id,current_revision FROM objects WHERE kind='SOURCE' ORDER BY id LIMIT 1").fetchone()
    catalog = json.loads((target / 'config/resource-catalog.json').read_text())['entries']
    small = next(name for name, spec in catalog.items() if 'small' in spec.get('variants', {}) and name.startswith('export/assets/'))
    workloads = [
        {'name': 'small_image', 'method': 'HEAD', 'path': '/api/production/files/' + Path(small).name + '?variant=small'},
        {'name': 'film_review', 'method': 'POST', 'path': '/api/editing/review', 'body': {k: films[0][k] for k in ('object_id', 'revision_id')}},
        {'name': 'shot_entities', 'path': '/api/production/index?' + urlencode(dict(view='settings', scope='shot', scope_episode='new26-e01', scope_revision=episode, scope_scene='new26-s001', scope_shot='new26-s001-q02'))},
        {'name': 'shot_card', 'path': '/api/production/card?' + urlencode(dict(object_id='new26-s001-q02', revision_id=shot))},
        {'name': 'scene', 'path': '/api/production/scene?' + urlencode(dict(object_id='new26-s001', view='reader', episode='new26-e01', episode_revision=episode))},
        {'name': 'materials', 'path': '/api/production/materials?grouped=1&compact=1&cards=1&scope=av'},
        {'name': 'editing_catalog', 'path': '/api/editing/catalog'},
        {'name': 'global_entities', 'path': '/api/production/index?view=settings'},
    ]
    evidence = {'format': 'private-performance-copy-v1', 'created_at': time.time(), 'source_database_bytes': database_bytes,
                'snapshot_seconds': snapshot_seconds, 'counts': counts, 'copied_json': copied,
                'workloads': workloads, 'source_comment_target': [source_id, source_revision],
                'films': [{**{k:f[k] for k in ('object_id','revision_id')}, 'clips':len(f['project']['clips']),
                           'subtitles':len(f['project']['subtitles']), 'titles':len(f['project']['titles'])} for f in films]}
    save(target / 'performance-copy.json', evidence)
    print(json.dumps({k: evidence[k] for k in ('source_database_bytes','snapshot_seconds','counts','films')}, ensure_ascii=False), flush=True)


def bench(instance, output, only=None, warm=20):
    instance = Path(instance).resolve()
    if not (instance / 'performance-copy.json').is_file():
        raise ValueError('bench requires the owned snapshot marker')
    from review_desk.server import ReviewServer, ReviewHandler
    from review_desk.store import Store
    evidence = json.loads((instance / 'performance-copy.json').read_text())
    metrics = {}
    class TimedHandler(ReviewHandler):
        def run_timed(self, function):
            start, cpu = time.perf_counter(), time.thread_time()
            try:
                return function(self)
            finally:
                metrics[self.headers.get('X-Performance-Sample')] = {'server_ms': (time.perf_counter()-start)*1000,
                    'server_thread_cpu_ms': (time.thread_time()-cpu)*1000}
        def do_GET(self):
            return self.run_timed(ReviewHandler.do_GET)
        def do_POST(self):
            return self.run_timed(ReviewHandler.do_POST)
        def log_message(self, *args):
            pass
    config = json.loads((instance / 'config/instance.json').read_text())
    server = ReviewServer(('127.0.0.1', 0), instance, config)
    server.RequestHandlerClass = TimedHandler
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    writer = Store.open_existing(instance / '.runtime/review.sqlite3')
    results = {'python':sys.version, 'platform':platform.platform(), 'pid':os.getpid(), 'samples':[],
               'percentile': 'sorted values[ceil(.95*n)-1]; P95 reported only for n>=20', 'workloads': evidence['workloads'],
               'boundary':'Sequential loopback HTTP including real JSON/graph encoding. CPU is server request thread, not process or browser. Private database and cache only.'}
    def request(workload, condition, index):
        key = workload['name'] + '-' + condition + '-' + str(index)
        connection = http.client.HTTPConnection(*server.server_address, timeout=90)
        start = time.perf_counter()
        value = {'workload':workload['name'], 'condition':condition, 'index':index}
        try:
            body = json.dumps(workload['body']).encode() if 'body' in workload else None
            connection.request(workload.get('method','GET'), workload['path'], body, {'X-Performance-Sample':key,
                'Content-Type':'application/json', 'Accept':'application/vnd.review-desk.graph+json','Accept-Encoding':'gzip'})
            response = connection.getresponse()
            value.update(status=response.status, ttfb_ms=(time.perf_counter()-start)*1000, cache=response.getheader('X-Review-Cache'))
            data = response.read()
            value.update(bytes=len(data), total_ms=(time.perf_counter()-start)*1000, response_sha256=hashlib.sha256(data).hexdigest())
            if response.status not in (200,307):
                value['error'] = data[:500].decode(errors='replace')
        except Exception as error:
            value['error'] = str(error)
        finally:
            connection.close()
        # Handler finishes just after sending the final response byte.
        for _ in range(200):
            if key in metrics:
                break
            time.sleep(.005)
        value.update(metrics.pop(key, {}))
        results['samples'].append(value)
        save(output, results)
        print(json.dumps(value), flush=True)
    try:
        for workload in evidence['workloads']:
            if only and workload['name'] not in only.split(','):
                continue
            for i in range(3):
                with writer.db:
                    writer.db.execute('UPDATE read_generations SET token=lower(hex(randomblob(16)))')
                request(workload, 'first_build', i)
            for i in range(warm):
                request(workload, 'warm', i)
            for i in range(3):
                # A normal existing comment state transition; only this private
                # copy is changed. Each build starts from a newly committed token.
                row = writer.db.execute('SELECT id,status,version FROM comments ORDER BY id LIMIT 1').fetchone()
                writer.change_comment(row['id'], 'CLOSE' if row['status']=='OPEN' else 'REOPEN', row['version'])
                request(workload, 'after_comment', i)
    finally:
        writer.close()
        server.shutdown()
        thread.join()
        server.server_close()
    grouped = collections.defaultdict(list)
    for sample in results['samples']:
        grouped[(sample['workload'],sample['condition'])].append(sample)
    results['summary'] = []
    for (name, condition), samples in grouped.items():
        row = {'workload':name,'condition':condition,'n':len(samples),'failed':sum('error' in s for s in samples)}
        for field in ('ttfb_ms','total_ms','server_ms','server_thread_cpu_ms'):
            values = sorted(s[field] for s in samples if field in s)
            if values:
                row[field]={'median':statistics.median(values), 'values':values}
                if len(values)>=20:
                    row[field]['p95']=values[math.ceil(.95*len(values))-1]
        results['summary'].append(row)
    save(output, results)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    prepare=commands.add_parser('snapshot');prepare.add_argument('source');prepare.add_argument('target')
    describe_cmd=commands.add_parser('describe');describe_cmd.add_argument('target')
    measure=commands.add_parser('bench');measure.add_argument('instance');measure.add_argument('output');measure.add_argument('--only');measure.add_argument('--warm',type=int,default=20)
    args=parser.parse_args()
    if args.action=='snapshot':snapshot(args.source,args.target)
    elif args.action=='describe':describe(args.target)
    else:bench(args.instance,args.output,args.only,args.warm)
