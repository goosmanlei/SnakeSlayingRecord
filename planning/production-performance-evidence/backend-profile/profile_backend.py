"""One isolated editing-review profile; no business mutations or network.

Prepare on the host: python3 profile_backend.py prepare STORY_ROOT
Profile in the verified app runtime: python profile_backend.py profile
Cleanup after saving evidence: python3 profile_backend.py cleanup
"""
import collections
import cProfile
import hashlib
import json
import os
from pathlib import Path
import pstats
import shutil
import sqlite3
import sys
import time

HERE = Path(__file__).resolve().parent
INSTANCE = HERE / 'instance'


def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def readonly(path):
    return sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)


def prepare(source):
    source = Path(source).resolve()
    if INSTANCE.exists():
        raise RuntimeError('Refusing to overwrite an existing diagnostic instance')
    original = source / '.runtime/review.sqlite3'
    if shutil.disk_usage(HERE).free < original.stat().st_size + 1024 ** 3:
        raise RuntimeError('Insufficient space for isolated backup and reserve')
    (INSTANCE / '.runtime').mkdir(parents=True)
    (INSTANCE / 'config').mkdir()
    (INSTANCE / 'resource-bundle').mkdir()
    for relative in ('config/instance.json', 'config/resource-storage.json', 'config/resource-catalog.json'):
        shutil.copyfile(source / relative, INSTANCE / relative)
    if (source / '.runtime/resources/catalog.json').is_file():
        (INSTANCE / '.runtime/resources').mkdir()
        shutil.copyfile(source / '.runtime/resources/catalog.json', INSTANCE / '.runtime/resources/catalog.json')
    started = time.perf_counter()
    with readonly(original) as src:
        with sqlite3.connect(INSTANCE / '.runtime/review.sqlite3') as dst:
            src.backup(dst, pages=256, sleep=.01)
    backup_seconds = time.perf_counter() - started
    with readonly(INSTANCE / '.runtime/review.sqlite3') as db:
        raw = db.execute("SELECT o.id,r.id,r.payload FROM objects o JOIN revisions r ON r.id=o.current_revision WHERE o.kind='EPISODE_FILM' ORDER BY o.created_at DESC,o.id DESC LIMIT 1").fetchone()
        oid, rid, body = raw
        film = json.loads(body)
        associations = [json.loads(r[0]) for r in db.execute("SELECT r.payload FROM objects o JOIN revisions r ON r.id=o.current_revision WHERE o.kind='EDIT_ASSOCIATION'")]
    matching = [a for a in associations if a['output'] == {'object_id': oid, 'revision_id': rid}]
    selected = max(matching, key=lambda a: a['version'])
    components = {e['binding']['component']['file']: e['binding']['component']
                  for e in selected['elements'] if e['element_type'] != 'clip'}
    copied = []
    for relative, component in components.items():
        if component['bytes'] > 8 * 1024 * 1024:
            raise RuntimeError('Text component exceeds the reviewed small-file limit')
        sha = component['sha256']
        candidates = [source / '.runtime/resource-cache' / (sha + Path(relative).suffix), source / 'resource-bundle' / sha]
        original_file = next((p for p in candidates if p.is_file() and not p.is_symlink()), None)
        if original_file is None:
            raise RuntimeError('Required local text original absent; no network fallback: ' + relative)
        data = original_file.read_bytes()
        if len(data) != component['bytes'] or hashlib.sha256(data).hexdigest() != sha:
            raise RuntimeError('Local text original differs: ' + relative)
        (INSTANCE / 'resource-bundle' / sha).write_bytes(data)
        copied.append({'logical_file': relative, 'sha256': sha, 'bytes': len(data)})
    save('preparation.json', {'source_database_bytes': original.stat().st_size,
         'backup_seconds': backup_seconds, 'output_id': oid, 'output_revision': rid,
         'association_digest': selected['digest'], 'elements': len(selected['elements']),
         'text_elements': sum(e['element_type'] != 'clip' for e in selected['elements']),
         'sources': len(film['project']['sources']), 'copied_text_originals': copied,
         'copied_text_bytes': sum(x['bytes'] for x in copied), 'backup_count': 1})
    print(json.dumps({'prepared': True, 'backup_seconds': backup_seconds, 'text_originals': len(copied), 'text_bytes': sum(x['bytes'] for x in copied)}))


def profile():
    os.environ['REVIEW_RESOURCES_OFFLINE'] = '1'
    os.environ['REVIEW_READ_CACHE'] = '0'
    os.environ.pop('REVIEW_OSS_CREDENTIALS_FILE', None)
    os.environ.pop('REVIEW_OSS_ACCESS_KEY_ID', None)
    os.environ.pop('REVIEW_OSS_ACCESS_KEY_SECRET', None)
    def no_network(event, args):
        if event.startswith('socket.'):
            raise RuntimeError('Network prohibited by isolated diagnostic')
    sys.addaudithook(no_network)
    sys.path.insert(0, '/app')
    from review_desk.store import Store
    from review_desk.editing_review import review
    evidence = json.loads((HERE / 'preparation.json').read_text())
    store = Store.open_readonly(INSTANCE / '.runtime/review.sqlite3')
    store._production_root = INSTANCE
    trace_counts = collections.Counter()
    def trace(sql):
        # Retain statement classes only, never SQL payloads or user content.
        words = sql.strip().split(None, 1)
        if words:
            trace_counts[words[0].upper()] += 1
    store.db.set_trace_callback(trace)
    profiler = cProfile.Profile()
    wall = time.perf_counter()
    cpu = time.process_time()
    try:
        # Production UI uses POST without production.read_scope. Preserve that
        # behavior here instead of adding request reuse absent from production.
        profiler.enable()
        result = review(store, evidence['output_id'], evidence['output_revision'])
        profiler.disable()
    finally:
        profiler.disable()
        wall = time.perf_counter() - wall
        cpu = time.process_time() - cpu
        store.close()
    profiler.dump_stats(str(HERE / 'editing-review.pstats'))
    stats = pstats.Stats(profiler)
    def row(key, value):
        cc, nc, tt, ct, callers = value
        filename, line, name = key
        return {'file': filename, 'line': line, 'function': name,
                'primitive_calls': cc, 'total_calls': nc, 'self_seconds': tt,
                'cumulative_seconds': ct, 'cumulative_share': ct / wall,
                'self_share': tt / wall}
    functions = [row(k, v) for k, v in stats.stats.items()]
    chosen = {'review', 'verify_binding', 'text_layer_document', 'submission', 'checksum',
              'materialize', 'hash_file', 'physical_file_hash', 'record', 'annotate',
              'enabled', 'material_origin', 'elements', 'settings', 'descriptor',
              '_catalog', 'asset_path', 'validate_component'}
    summaries = sorted((f for f in functions if f['function'] in chosen and 'review_desk/' in f['file']), key=lambda f: -f['cumulative_seconds'])
    save('summary.json', {'python': sys.version, 'code_root': '/app/review_desk',
         'wall_seconds': wall, 'process_cpu_seconds': cpu,
         'profiling_runs': 1, 'read_only_database': True, 'network_prohibited': True,
         'cache_mode': 'independent cold resource cache; business cache disabled; production POST has no business response cache',
         'output_id': evidence['output_id'], 'output_revision': evidence['output_revision'],
         'result_elements': len(result['elements']),
         'unavailable_count': sum(bool(e.get('unavailable')) for e in result['elements']),
         'sql_statement_counts': dict(trace_counts),
         'total_calls': stats.total_calls, 'primitive_calls': stats.prim_calls,
         'instance_configuration_bytes': (INSTANCE / 'config/instance.json').stat().st_size,
         'selected_functions': summaries,
         'top_self': sorted(functions, key=lambda f: -f['self_seconds'])[:20],
         'top_cumulative': sorted(functions, key=lambda f: -f['cumulative_seconds'])[:25],
         'measurement_boundary': 'One cProfile-instrumented direct review call in production Python runtime; excludes HTTP/catalog/browser and includes diagnostic trace overhead. Cumulative function shares overlap and must not be summed.'})
    print(json.dumps({'profile': 'editing-review', 'wall_seconds': wall, 'cpu_seconds': cpu, 'elements': len(result['elements']), 'unavailable': sum(bool(e.get('unavailable')) for e in result['elements']), 'selected_functions': summaries}, ensure_ascii=False))
    from review_desk.candidate_reset import erased_files
    media_store = Store.open_readonly(INSTANCE / '.runtime/review.sqlite3')
    query = "SELECT result FROM production_current_operations WHERE json_extract(result,'$.format') IN (?,?)"
    args = ('generated-candidates-reset-v1', 'full-production-reset-v1')
    metadata = dict(zip(('rows', 'total_result_characters', 'max_result_characters'), media_store.db.execute('SELECT count(*),sum(length(result)),max(length(result)) FROM production_current_operations').fetchone()))
    metadata['matching'] = dict(zip(('rows', 'total_result_characters', 'max_result_characters'), media_store.db.execute("SELECT count(*),sum(length(result)),max(length(result)) FROM production_current_operations WHERE json_extract(result,'$.format') IN (?,?)", args).fetchone()))
    metadata['query_plan'] = [dict(r) for r in media_store.db.execute('EXPLAIN QUERY PLAN ' + query, args)]
    if metadata['matching']['total_result_characters'] > 64 * 1024 * 1024:
        raise RuntimeError('Receipt expansion exceeds diagnostic bound')
    media_profile = cProfile.Profile()
    media_wall, media_cpu = time.perf_counter(), time.process_time()
    try:
        media_profile.enable()
        erased = erased_files(media_store)
        media_profile.disable()
    finally:
        media_profile.disable()
        media_wall, media_cpu = time.perf_counter() - media_wall, time.process_time() - media_cpu
        media_store.close()
    media_profile.dump_stats(str(HERE / 'erased-files.pstats'))
    media_stats = pstats.Stats(media_profile)
    media_rows = []
    for key, value in media_stats.stats.items():
        cc, nc, tt, ct, callers = value
        media_rows.append({'file': key[0], 'line': key[1], 'function': key[2], 'primitive_calls': cc,
                           'total_calls': nc, 'self_seconds': tt, 'cumulative_seconds': ct,
                           'cumulative_share': ct / media_wall, 'self_share': tt / media_wall})
    save('erased-files-summary.json', {'python': sys.version, 'wall_seconds': media_wall,
         'process_cpu_seconds': media_cpu, 'profiling_runs': 1, 'metadata': metadata,
         'erased_file_count': len(erased),
         'top_self': sorted(media_rows, key=lambda f: -f['self_seconds'])[:15],
         'top_cumulative': sorted(media_rows, key=lambda f: -f['cumulative_seconds'])[:15],
         'boundary': 'Direct erased_files call in the same isolated backup; metadata queries preceded it; no HTTP, resource lookup, OSS or Store initialization included.'})
    print(json.dumps({'profile': 'erased-files', 'wall_seconds': media_wall, 'cpu_seconds': media_cpu, 'erased_file_count': len(erased), 'metadata': metadata}, ensure_ascii=False))


def cleanup():
    target = HERE / 'instance'
    if target != INSTANCE or target.is_symlink() or not (HERE / 'summary.json').is_file() or not (HERE / 'erased-files-summary.json').is_file():
        raise RuntimeError('Refusing cleanup without completed diagnostic evidence')
    count, size = 0, 0
    for path in target.rglob('*'):
        if path.is_symlink():
            raise RuntimeError('Unexpected symlink in private diagnostic instance')
        if path.is_file():
            count += 1
            size += path.stat().st_size
    shutil.rmtree(target)
    save('cleanup.json', {'removed_owned_instance': 'instance', 'files': count, 'bytes': size,
                         'instance_absent': not target.exists(),
                         'retained': ['profile_backend.py', 'preparation.json', 'editing-review.pstats', 'summary.json', 'erased-files.pstats', 'erased-files-summary.json', 'cleanup.json']})
    print(json.dumps({'removed_files': count, 'removed_bytes': size, 'instance_absent': not target.exists()}))


if __name__ == '__main__':
    {'prepare': lambda: prepare(sys.argv[2]), 'profile': profile, 'cleanup': cleanup}[sys.argv[1]]()
