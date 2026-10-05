#!/usr/bin/env python3
"""Restore a Schema 6 song export, validating two legacy PCM rounding cases."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
from types import SimpleNamespace
import wave

from generation_workspace import generation_root, isolated_instance, write_json
from generation_publication import tables, canonical
from material_model_io import read_json


def recover(root, destination, package, output, candidate=None):
    from review_desk.store import Store
    from review_desk import bundle, production, material_archives
    root = generation_root(root)
    destination = isolated_instance(root, destination)
    if destination.exists():
        raise ValueError('recovery requires a new isolated destination')
    plan = read_json(root / package)
    legacy = read_json(root / 'production/song-stage/publication-plan.json')
    checks = plan['origin']['historical_pcm_precision_checks']
    if len(checks) != 2 or {c['revision_id'] for c in checks} != {
            '6f6ac04c7e2749e57158e98c814d67a44ea642e77515b52c4997ddccad86263f',
            '527f86af6ab9ba0ab0ce6f4ca86685326f82d6a7e0978676a3dd47dc4a7e59ec'}:
        raise ValueError('unexpected historical precision scope')
    originals = {r['id']: r for r in legacy['insert']['revisions']}
    for check in checks:
        path = root / 'export/assets' / check['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != path.stem:
            raise ValueError('historical PCM original changed')
        with wave.open(str(path)) as audio:
            duration = audio.getnframes() / audio.getframerate()
        if (duration != check['pcm_duration'] or check['range_end'] != duration or
                not 0 < duration - check['recorded_duration'] < 0.0000005):
            raise ValueError('PCM precision evidence differs')
    destination.mkdir(parents=True)
    for folder in ('config', 'content', 'export'):
        shutil.copytree(root / folder, destination / folder)
    store = Store(destination / '.runtime/review.sqlite3')
    # Prevalidation reads immutable archive nodes on a separate connection. This
    # avoids repeatedly parsing the 100 MB graph while the destination is empty.
    reader_path = destination / '.runtime/archive-reader.sqlite3'
    reader = sqlite3.connect(reader_path)
    reader.execute('CREATE TABLE material_content (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
    graph = json.loads((destination / 'export/material-content.json').read_text())
    reader.executemany('INSERT INTO material_content VALUES (?,?)',
                       ((r['id'], r['body']) for r in graph['material_content']))
    reader.commit()
    del graph
    archive_reader = SimpleNamespace(db_path=store.db_path, db=reader)
    validate = production.validate_payload
    validated = set()

    def precise_validation(db_store, object_id, kind, payload, inspect=True, check_current=True):
        view = payload
        for check in checks:
            original = originals[check['revision_id']]
            if (object_id == original['object_id'] and kind == 'CALL' and
                    payload == json.loads(original['payload'])):
                view = copy.deepcopy(payload)
                matched = False
                for ref in view.get('inputs', []):
                    if ref.get('component_id') and ref.get('range', {}).get('end_seconds') == check['range_end']:
                        _, component = production.component_for(db_store, ref, ref['component_id'])
                        if (component['file'] == check['file'] and
                                component['duration_seconds'] == check['recorded_duration']):
                            ref['range']['end_seconds'] = check['recorded_duration']
                            matched = True
                if not matched:
                    raise ValueError('historical precision reference differs')
                validated.add(check['revision_id'])
                break
        return validate(db_store, object_id, kind, view, inspect=inspect, check_current=check_current)

    production.validate_payload = precise_validation
    try:
        with material_archives.read_scope(archive_reader):
            bundle.restore(store, destination / 'export')
        assert validated == {c['revision_id'] for c in checks}
    finally:
        production.validate_payload = validate
        reader.close()
        store.close()
        reader_path.unlink()
    restored = tables(destination / '.runtime/review.sqlite3')
    if candidate is not None:
        expected = tables(candidate)
        assert restored.keys() == expected.keys()
        for table in expected:
            assert sorted(map(canonical, restored[table])) == sorted(map(canonical, expected[table])), table
    result = {'schema_version': 6, 'restored': True,
              'historical_precision_revisions': sorted(validated),
              'historical_payloads_changed': False,
              'all_business_tables_equal': candidate is not None,
              'tables': len(restored), 'counts': {t: len(restored[t]) for t in
                  ('objects', 'revisions', 'comments', 'comment_events')},
              'system_modified': False}
    write_json(root, output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--package', type=Path, default=Path('production/publications/songs-current-model-v2.json'))
    parser.add_argument('--output', type=Path, default=Path('production/song-publication/recovery-verification.json'))
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    print(json.dumps(recover(Path(__file__).resolve().parents[1], args.destination,
                             args.package, args.output, args.candidate), ensure_ascii=False))


if __name__ == '__main__':
    main()
