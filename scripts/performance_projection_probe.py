#!/usr/bin/env python3
"""Count SQL statements and record expansion on an isolated frozen instance.

Run separately from browser timing. PYTHONPATH selects the exact system commit;
the probe can initialize its disposable cache but never changes business rows.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import resource
import platform
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', action='store_true')
    args = parser.parse_args()
    from review_desk import production, ui_projection, business_codes
    from review_desk.store import Store
    root = args.instance.resolve()
    task_runtime = Path(__file__).resolve().parents[1]/'.runtime/system-performance'
    if task_runtime.resolve() not in root.parents or root.name == 'frozen-instance':
        raise ValueError('use a disposable performance instance under task runtime')
    store = Store(root/'.runtime/review.sqlite3')
    try:
        if args.cache:
            from review_desk import read_cache
            read_cache.attach(store)
            read_cache.manage(store, 'clear')
        queries = []
        counts = {'record_expansions': 0}
        original = production.record_view
        def viewed(row):
            counts['record_expansions'] += 1
            return original(row)
        production.record_view = viewed
        store.db.set_trace_callback(lambda sql: queries.append(sql.partition(' ')[0]))
        compact = 'compact' in inspect.signature(ui_projection.material_list).parameters
        cases = [
            ('materials-full', lambda: ui_projection.material_list(store, grouped=True)),
            ('materials-combination', lambda: ui_projection.material_list(store, grouped=True, **({'compact':True} if compact else {}),
                episode='screenplay-04-lantern-home-e01', scene='s001', media='image', status='generated', search='李寄')),
            ('card-large', lambda: ui_projection.card(store, 'entity-li-ji')),
            ('scene-full', lambda: ui_projection.scene(store, 'preparation-s001')),
        ]
        if compact:cases.insert(1, ('materials-compact', lambda: ui_projection.material_list(store, grouped=True, compact=True)))
        result = []
        for name, reader in cases:
            for condition in ('first', 'repeat'):
                queries.clear(); counts['record_expansions'] = 0
                start = time.perf_counter(); cpu = time.process_time()
                with production.read_scope(store):
                    value = business_codes.annotate(store, reader())
                    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
                result.append({'case': name, 'condition': condition,
                    'wall_ms': (time.perf_counter()-start)*1000, 'cpu_ms': (time.process_time()-cpu)*1000,
                    'sql_statements': len(queries), 'sql_selects': queries.count('SELECT'),
                    **counts, 'json_bytes': len(body), 'json_sha256': hashlib.sha256(body).hexdigest(),
                    'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024)})
        args.output.write_text(json.dumps({'system_source': str(Path(production.__file__).resolve()),
            'cache': args.cache, 'counter': 'all traced business SQL; record_expansions counts production.record_view calls',
            'not_browser_latency': True, 'serialization':'sorted-key full JSON, not the negotiated HTTP graph representation',
            'rows': result}, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps(result, ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    main()
