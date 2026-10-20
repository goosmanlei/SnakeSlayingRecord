"""One uncached read profile on a marked private performance instance."""
import cProfile
import json
from pathlib import Path
import pstats
import sys
import time
from collections import defaultdict

instance, workload, output = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
assert (instance / 'performance-copy.json').is_file()
from review_desk.store import Store
from review_desk import production, production_breakdown, editing_api, ui_projection
from review_desk.resources import lease_scope
store = Store.open_readonly(instance / '.runtime/review.sqlite3')
spec = json.loads((instance / 'performance-copy.json').read_text())
operation = {
    'global_entities':lambda: production_breakdown.index(store, 'settings'),
    'shot_entities':lambda: production_breakdown.index(store, 'settings', scope='shot', scope_episode='new26-e01', scope_scene='new26-s001', scope_shot='new26-s001-q02'),
    'shot_card':lambda: ui_projection.card(store, 'new26-s001-q02'),
    'scene_actual':lambda: ui_projection.scene(store, 'new26-s028', 'ed81bda32cb297a0f518707981d0960da7f4032bea13acc809433978dd4c303b', shot_revision='0c7a20f2874f7b81096896155a88153d6efe129d9070ca16c1ce4294fed6fb60', view='reader', episode='new26-e12', episode_revision='ae04e993ba5a10c097677ed12bdff89658672b2efdca8ccb5e6d0e064b0eb379'),
    'film_review':lambda: editing_api.dispatch(store, instance, 'review', spec['workloads'][1]['body']),
}[workload]
profile = cProfile.Profile()
file_reads = defaultdict(lambda: {'calls': 0, 'logical_bytes': 0})
original_read_text = Path.read_text
def counted_read_text(path, *args, **kwargs):
    value = original_read_text(path, *args, **kwargs)
    try:
        relative = path.resolve().relative_to(instance.resolve()).as_posix()
    except ValueError:
        relative = '<outside-instance>'
    if relative.startswith('config/') or relative.startswith('.runtime/resource-cache/'):
        row = file_reads[relative]
        row['calls'] += 1
        row['logical_bytes'] += len(value.encode(kwargs.get('encoding') or 'utf-8'))
    return value
Path.read_text = counted_read_text
start, cpu = time.perf_counter(), time.process_time()
try:
    # Preserve the old production POST behavior for its exact baseline.
    if workload == 'film_review':
        value = profile.runcall(operation)
    else:
        with production.read_scope(store), lease_scope():
            value = profile.runcall(operation)
finally:
    wall, cpu = time.perf_counter()-start, time.process_time()-cpu
    Path.read_text = original_read_text
    store.close()
stats = pstats.Stats(profile)
rows = [{'file':Path(k[0]).name,'line':k[1],'function':k[2], 'calls':v[1], 'self_seconds':v[2],'cumulative_seconds':v[3]}
        for k,v in stats.stats.items()]
report = {'workload':workload,'wall_seconds':wall,'cpu_seconds':cpu,'calls':stats.total_calls,
          'top_self':sorted(rows,key=lambda r:-r['self_seconds'])[:30],
          'top_cumulative':sorted(rows,key=lambda r:-r['cumulative_seconds'])[:40],
          'selected':[r for r in rows if r['function'] in ('settings','submission','text_layer_document','_text_project','hash_file','record','parents','graph','checksum','materialize','erased_files')],
          'text_file_reads': dict(file_reads),
          'boundary':'One instrumented uncached projection; excludes HTTP encoding and transport. Cumulative times overlap.'}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'wall_seconds':wall,'cpu_seconds':cpu,'top_self':report['top_self'][:12],'top_cumulative':report['top_cumulative'][:18]}),flush=True)
