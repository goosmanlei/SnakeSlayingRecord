#!/usr/bin/env python3
"""Read-only baseline and verification for production workspace unification."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def database(path):
    db = sqlite3.connect('file:' + str(path.resolve()) + '?mode=ro', uri=True)
    tables = {}
    db.execute('BEGIN')
    with db:
        for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            h = hashlib.sha256(); count = 0
            columns = list(db.execute('PRAGMA table_info("' + name + '")'))
            order = ','.join('"' + c[1] + '"' for c in columns)
            for row in db.execute('SELECT * FROM "' + name + '" ORDER BY ' + order):
                h.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode()); h.update(b'\n'); count += 1
            tables[name] = {'rows': count, 'sha256': h.hexdigest()}
        retired = db.execute("SELECT id,kind FROM objects WHERE kind IN ('ASSEMBLY','DELIVERABLE') ORDER BY id").fetchall()
        formats = db.execute("SELECT id FROM revisions WHERE json_extract(payload,'$.format') IN ('production-assembly-v1','production-deliverable-v1')").fetchall()
        codes = db.execute("SELECT object_id FROM business_codes WHERE prefix IN ('A','O')").fetchall()
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        foreign = list(db.execute('PRAGMA foreign_key_check'))
    db.close()
    return {'tables': tables, 'retired_objects': retired, 'retired_revisions': formats,
            'retired_codes': codes, 'integrity': integrity, 'foreign_key_violations': foreign}


def recovery_inputs(system, instance):
    """Inspect only effective inputs; historical task evidence is not a replay."""
    sys.path.insert(0, str(system.resolve()))
    from review_desk.material_content_stream import members
    export = instance / 'export'
    manifest_path = export / 'manifest.json'
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text())
    retired_objects = [r['id'] for r in members(export / 'objects.json', 'objects')
                       if r['kind'] in ('ASSEMBLY', 'DELIVERABLE')]
    retired_revisions = [r['id'] for r in members(export / 'objects.json', 'revisions')
                         if json.loads(r['payload']).get('format') in
                         ('production-assembly-v1', 'production-deliverable-v1')]
    inputs = {str(path.relative_to(instance)): {'bytes': path.stat().st_size, 'sha256': file_sha(path)}
              for path in (manifest_path, instance / 'production/replay.json',
                           instance / 'production/version-consolidation/recovery.json') if path.exists()}
    mismatches = [name for name, expected in manifest['files'].items()
                  if file_sha(export / name) != expected]
    assert not mismatches, 'effective export checksum mismatch'
    assert not retired_objects and not retired_revisions, 'retired data in effective export'
    return {'schema_version': manifest['schema_version'], 'manifest_files': len(manifest['files']),
            'verified_files': len(manifest['files']), 'retired_objects': retired_objects,
            'retired_revisions': retired_revisions, 'inputs': inputs}


def coverage(system, instance, baseline=False):
    sys.path.insert(0, str(system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p, production_breakdown as b, ui_projection as ui
    store = Store.open_existing(instance / '.runtime/review.sqlite3')
    with p.read_scope(store):
        catalog = b.catalog(store)
    scenes = {}; total_shots = 0
    for ep in catalog['episodes']:
        with p.read_scope(store):
            selected = b.catalog(store, ep['object_id'])
        for scene in selected['scenes']:
            with p.read_scope(store):
                design = ui.scene(store, scene['object_id'], scene['id'], view='breakdown')
            with p.read_scope(store):
                merged = ui.scene(store, scene['object_id'], scene['id'], view='shots') if baseline else design
            rows = []
            for d, m in zip(design['shots'], merged['shots']):
                assert d['record']['id'] == m['record']['id']
                dc, mc = d['context'], m['context']
                material_ids = sorted({i.get('canonical_material_id') or i['object_id'] for i in dc['materials']})
                videos = sorted({i.get('canonical_material_id') or i['object_id'] for i in mc['materials'] if i['media_type'] == 'video'})
                assert set(videos) <= set(material_ids)
                rows.append({'object_id': d['record']['object_id'], 'revision_id': d['record']['id'],
                    'design_sha256': sha(d['record']['payload']), 'materials': material_ids, 'videos': videos,
                    'video_details_sha256': sha(mc['video_details']), 'adoptions_sha256': sha(mc['adoptions'])})
            total_shots += len(rows)
            scenes[scene['object_id']] = {'revision_id': scene['id'], 'episode': ep['object_id'], 'shots': rows}
            print(scene['object_id'], len(rows), file=sys.stderr, flush=True)
    store.db.close()
    return {'episode_count': len(catalog['episodes']), 'scene_count': len(scenes), 'shot_count': total_shots, 'scenes': scenes}


def main():
    a = argparse.ArgumentParser(); a.add_argument('--system', type=Path, required=True)
    a.add_argument('--instance', type=Path, required=True); a.add_argument('--output', type=Path, required=True)
    a.add_argument('--baseline', action='store_true'); a.add_argument('--compare', type=Path); a.add_argument('--database-only', action='store_true')
    args = a.parse_args(); instance = args.instance.resolve()
    result = {'format': 'production-unification-audit-v1', 'database': database(instance / '.runtime/review.sqlite3')}
    manifest = json.loads((instance / 'export/manifest.json').read_text()) if (instance / 'export/manifest.json').exists() else None
    files = {}
    for path in sorted((instance / 'export/assets').iterdir()):
        if path.is_file(): files[path.name] = {'bytes': path.stat().st_size, 'sha256': file_sha(path)}
    result['assets'] = files
    result['effective_export_manifest_sha256'] = sha(manifest) if manifest else None
    result['recovery_inputs'] = recovery_inputs(args.system, instance)
    if not args.database_only: result['coverage'] = coverage(args.system, instance, args.baseline)
    if args.compare:
        old = json.loads(args.compare.read_text())
        assert old['database'] == result['database'], 'database changed'
        assert old['assets'] == result['assets'], 'asset bytes changed'
        if not args.database_only: assert old['coverage'] == result['coverage'], 'exact scene associations changed'
        result['compared_to'] = str(args.compare); result['preserved'] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result.get(k) for k in ('preserved', 'compared_to')}))


if __name__ == '__main__': main()
