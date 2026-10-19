#!/usr/bin/env python3
"""Inventory current Git resources and exact live references without loading big bundles."""
import argparse
from collections import defaultdict
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

MEDIA = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico', '.wav', '.mp3',
         '.m4a', '.flac', '.ogg', '.mp4', '.mov', '.webm', '.zip', '.pdf', '.srt', '.ass'}
HASH_NAME = re.compile(r'^[0-9a-f]{64}\.[a-z0-9]{1,12}$')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def references(value, pointer='$'):
    if isinstance(value, dict):
        for key, child in value.items():
            location = pointer + '/' + key
            if isinstance(child, str) and key in ('file', 'path', 'filename', 'input_file', 'source_file', 'site_favicon'):
                if child.startswith(('export/assets/', 'content/production-approach-assets/', 'production/', 'design/')):
                    yield child, location
                elif HASH_NAME.fullmatch(child) or key == 'site_favicon' and child:
                    yield 'export/assets/' + child, location
                elif key == 'file' and '/visuals/' in pointer:
                    yield 'export/assets/' + child, location
            # Historical prose/content_json is not parsed into new active inputs.
            yield from references(child, location)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from references(child, pointer + '/' + str(i))


def database_references(database):
    db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
    db.execute('BEGIN')
    roots = defaultdict(set)
    erased = set()
    counts = {}
    fingerprints = {}
    embedded = defaultdict(list)
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if 'material_content' in tables and db.execute('SELECT COUNT(*) FROM material_content').fetchone()[0]:
            raise ValueError('inventory requires a hydrated per-row reader for this legacy content graph')
        if 'production_current_operations' in tables:
            for (raw,) in db.execute("SELECT result FROM production_current_operations WHERE json_extract(result,'$.format') IN ('generated-candidates-reset-v1','full-production-reset-v1')"):
                erased.update(json.loads(raw).get('erased_files', {}))
        for table in sorted(tables):
            if table == 'read_generations':
                continue
            digest = hashlib.sha256()
            columns = [x[1] for x in db.execute('PRAGMA table_info("' + table + '")')]
            count = 0
            for row in db.execute('SELECT * FROM "' + table + '" ORDER BY 1'):
                if table=='method_file_versions':
                    record=dict(zip(columns,row))
                    if record['kind']=='text':
                        body=record['content'].encode()
                        if hashlib.sha256(body).hexdigest()!=record['sha256']:
                            raise ValueError('embedded method history checksum differs')
                        embedded[record['path']].append({'revision_id':record['id'],'sha256':record['sha256'],'bytes':len(body)})
                digest.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode())
                digest.update(b'\n')
                count += 1
                # Every persistent JSON column includes history, comments, submissions,
                # method files and associations, not just the current asset table.
                for column, raw in zip(columns, row):
                    if not isinstance(raw, str) or not raw.lstrip().startswith(('{', '[')):
                        continue
                    try:
                        value = json.loads(raw)
                    except ValueError:
                        continue
                    for name, pointer in references(value):
                        if Path(name).name not in erased:
                            roots[name].add(f'{table}/{row[0]}/{column}{pointer}')
            counts[table] = count
            fingerprints[table] = digest.hexdigest()
        return roots, erased, {'counts': counts, 'sha256_by_table': fingerprints}, embedded
    finally:
        db.rollback()
        db.close()


def inventory(root, database, output, system, filesystem=False):
    if system:
        sys.path.insert(0, str(system))
    paths = ([str(p.relative_to(root)) for folder in ('export/assets', 'content')
              for p in (root / folder).rglob('*') if p.is_file()] if filesystem else
             subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0'))
    tracked = set(filter(None, paths))
    roots, erased, snapshot, embedded = database_references(database)
    selected = set(roots)
    # Include non-hash names and resources outside the export directory. Metadata
    # archives have their own role; they are never promoted to production inputs.
    for name in tracked:
        path = root / name
        if not path.is_file():
            raise ValueError('tracked input missing: ' + name)
        if (name.startswith('export/assets/') or path.suffix.lower() in MEDIA or
                path.suffix.lower() in ('.json', '.jsonl') and path.stat().st_size > 1024 * 1024):
            selected.add(name)
            roots[name].add('git:' + name)
    missing = []
    embedded_references=[];source_references=[]
    rows = []
    for name in sorted(selected):
        path = root / name
        if path.is_symlink() or '..' in Path(name).parts or Path(name).is_absolute():
            raise ValueError('unsafe resource path: ' + name)
        if not path.is_file():
            if name in embedded:
                embedded_references.append({'path':name,'versions':embedded[name],'roots':sorted(roots[name])})
                continue
            source_fields=('/provenance/file','/lyrics_source/path','/directions_source/path','/budget_evidence/path')
            if path.suffix.lower() in ('.md','.txt','.json') and all(r.endswith(source_fields) for r in roots[name]):
                source_references.append({'path':name,'roots':sorted(roots[name]),'role':'historical-text-provenance-retained-in-story-git'})
                continue
            missing.append({'path': name, 'roots': sorted(roots[name])})
            continue
        with path.open('rb') as stream:
            if stream.read(44).startswith(b'version https://git-lfs'):
                raise ValueError('unhydrated resource: ' + name)
        physical = {'sha256': sha(path), 'bytes': path.stat().st_size}
        archive = None
        if path.suffix == '.json':
            with path.open('rb') as stream:
                archive_header = b'material-archive-reference-v1' in stream.read(160)
            if archive_header:
                from review_desk.material_archives import reference, read_bytes
                archive = reference(path)
        logical = dict(physical)
        if archive:
            data = read_bytes(path)
            logical = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
            del data
            if logical != {key: archive[key] for key in ('sha256', 'bytes')}:
                raise ValueError('archive does not match logical original: ' + name)
        category = ('asset' if name.startswith('export/assets/') else
                    'method-media' if name.startswith('content/') else
                    'recovery-metadata' if name.startswith('export/') else
                    'historical-publication' if name.startswith('production/publications/') else
                    'evidence')
        storage = 'oss' if (name.startswith('export/assets/') or path.suffix.lower() in MEDIA or
                            path.suffix.lower() in ('.json', '.jsonl') and path.stat().st_size > 1024 * 1024) else 'git-text'
        rows.append({'path': name, 'category': category, 'tracked': name in tracked and not filesystem,
                     'origin': 'filesystem' if filesystem else 'git+database', 'storage': storage,
                     'disposition': 'historical-only' if Path(name).name in erased else 'retained',
                     'logical': logical, 'physical': physical,
                     'mime': {'.wav': 'audio/wav', '.srt': 'application/x-subrip', '.ico': 'image/x-icon',
                              '.blend': 'application/x-blender'}.get(Path(name).suffix.lower())
                             or mimetypes.guess_type(name)[0] or 'application/octet-stream',
                     'archive': archive, 'reference_roots': sorted(roots[name])})
    unique = {x['logical']['sha256']: x['logical']['bytes'] for x in rows}
    report = {'format': 'oss-migration-inventory-v1',
              'story_commit': None if filesystem else subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
              'database': snapshot, 'erased_file_count': len(erased), 'files': rows, 'missing': missing,
              'embedded_references':embedded_references,'source_only_references':source_references,
              'summary': {'paths': len(rows), 'tracked_paths': sum(x['tracked'] for x in rows),
                          'oss_paths':sum(x['storage']=='oss' for x in rows),
                          'oss_physical_bytes':sum(x['physical']['bytes'] for x in rows if x['storage']=='oss'),
                          'physical_bytes': sum(x['physical']['bytes'] for x in rows),
                          'logical_objects': len(unique), 'logical_unique_bytes': sum(unique.values()),
                          'archive_references': sum(bool(x['archive']) for x in rows)}}
    if str(output) == '-':
        print(json.dumps(report, ensure_ascii=False))
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'summary': report['summary'], 'missing_count': len(missing), 'output': str(output)}, ensure_ascii=False))
    if missing:
        raise ValueError('unresolved references; inspect inventory before migrating')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--system', type=Path)
    parser.add_argument('--filesystem', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inventory(args.root.resolve(), args.database, args.output, args.system.resolve() if args.system else None, args.filesystem)
