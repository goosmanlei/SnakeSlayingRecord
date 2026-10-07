#!/usr/bin/env python3
"""Save exact production revisions or recover a fresh, isolated review instance.

The complete export preserves story and production records, comments and events.
Older story-only exports can add production records through the shared import API;
neither path replaces a live database or copies any credentials.
"""
import argparse
from contextlib import contextmanager, nullcontext
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import sys
import wave
from production_data import exact_replay

try:
    from .generation_workspace import generation_root, contained, isolated_instance
except ImportError:
    from generation_workspace import generation_root, contained, isolated_instance

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility

ROOT = Path(__file__).resolve().parents[1]


def complete_export_index(store, production):
    """Index exact identities without expanding historical material payloads.

    Schema 6+ bundles already contain every revision. A second import replay is
    redundant and can multiply memory use by retaining all hydrated histories.
    """
    formats = tuple(production.FORMATS)
    placeholders = ','.join('?' for _ in formats)
    rows = store.db.execute(
        'SELECT id,object_id,version FROM revisions WHERE '
        "json_extract(payload,'$.format') IN (" + placeholders + ') '
        'ORDER BY object_id,version', formats)
    heads, revisions = {}, []
    for row in rows:
        heads[row['object_id']] = row['id']
        revisions.append(row['id'])
    files = {}
    for row in store.db.execute(
            "SELECT json_extract(payload,'$.components') AS components FROM revisions "
            "WHERE json_type(payload,'$.components')='array'"):
        for component in json.loads(row['components']):
            name = 'export/assets/' + component['file']
            if name in files and files[name] != component['sha256']:
                raise ValueError('conflicting original checksums: ' + name)
            files[name] = component['sha256']
    return {'format': 'production-export-index-v1', 'heads': heads,
            'revisions': sorted(revisions), 'files': files}


def verify_export_index(index, export_dir, formats):
    """Bind the small index to the exact complete bundle, including all history."""
    from review_desk.material_content_stream import members
    wanted = set(index['revisions'])
    found, heads = set(), {}
    versions = {}
    for row in members(export_dir / 'objects.json', 'revisions'):
        if json.loads(row['payload']).get('format') not in formats:
            continue
        found.add(row['id'])
        if row['version'] > versions.get(row['object_id'], 0):
            versions[row['object_id']] = row['version']
            heads[row['object_id']] = row['id']
    if found != wanted or heads != index['heads']:
        raise ValueError('complete export and production index describe different revisions')


@contextmanager
def historical_pcm_precision(root):
    """Apply the existing two-record exception only after verifying originals."""
    from material_model_io import read_framework
    from recover_song_publication import precision_validation
    from review_desk.production_media import physical_file_hash
    from review_desk.store import canonical
    checks = material_read_json(root / 'production/publications/songs-current-model-v2.json')['origin']['historical_pcm_precision_checks']
    wanted = {c['revision_id'] for c in checks}
    rows = read_framework(root / 'export/objects.json', revision_ids=wanted)['revisions']
    originals = {r['id']: r for r in rows}
    if set(originals) != wanted:
        raise ValueError('historical PCM revisions missing from export')
    for check in checks:
        path = root / 'export/assets' / check['file']
        if path.parent != root / 'export/assets' or path.is_symlink() or physical_file_hash(path) != path.stem:
            raise ValueError('historical PCM original changed')
        with wave.open(str(path)) as audio:
            duration = audio.getnframes() / audio.getframerate()
        if duration != check['pcm_duration'] or duration != check['range_end'] or not 0 < duration - check['recorded_duration'] < .0000005:
            raise ValueError('historical PCM precision evidence differs')
        row = originals[check['revision_id']]
        value = {'object_id': row['object_id'], 'version': row['version'], 'payload': json.loads(row['payload'])}
        if hashlib.sha256(canonical(value).encode()).hexdigest() != row['id']:
            raise ValueError('historical PCM revision checksum differs')
    with precision_validation(checks, originals) as validated:
        yield
    if validated != wanted:
        raise ValueError('historical PCM compatibility scope incomplete')


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    save = commands.add_parser('snapshot')
    save.add_argument('--instance', type=Path, required=True)
    recover = commands.add_parser('recover')
    recover.add_argument('--destination', type=Path, required=True)
    recover.add_argument('--historical-pcm-precision', action='store_true',
                         help='verify originals and reuse the two documented legacy WAV rounding exceptions')
    parser.add_argument('--workspace', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = generation_root(args.workspace)
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk import production
    from review_desk.store import Store
    from review_desk.bundle import restore
    from review_desk.production_media import file_hash, validate_component
    replay_path = contained(ROOT, 'production/replay.json')
    if args.command == 'snapshot':
        # Store initialization may migrate; run it only on our private snapshot.
        try:
            from .generation_publication import backup
        except ImportError:
            from generation_publication import backup
        runtime = contained(ROOT, '.runtime/generation/snapshots')
        runtime.mkdir(parents=True, exist_ok=True)
        snapshot = Path(tempfile.mkdtemp(dir=runtime)) / 'review.sqlite3'
        source = args.instance if args.instance.is_absolute() else ROOT / args.instance
        backup(source.resolve() / '.runtime/review.sqlite3', snapshot)
        store = Store(snapshot)
        try:
            complete = json.loads((ROOT / 'export/manifest.json').read_text()).get('schema_version', 1) >= 6
            if complete:
                data = complete_export_index(store, production)
                verify_export_index(data, ROOT / 'export', production.FORMATS)
                from review_desk.material_archives import read_scope
                # Reuse the consistent snapshot's content graph. Otherwise each
                # archived file rebuilds the same exported graph on disk.
                with read_scope(store, ROOT):
                    for name, expected in data['files'].items():
                        if Path(name).parts[:2] != ('export', 'assets') or len(Path(name).parts) != 3:
                            raise ValueError('unsafe production original path')
                        if file_hash(contained(ROOT, name)) != expected:
                            raise ValueError('original media checksum differs: ' + name)
            else:
                data = exact_replay(store, production)
                files = {}
                for batch in data['batches']:
                    for record in batch['records']:
                        for component in record['payload'].get('components', []):
                            validate_component(ROOT, component)
                            files['export/assets/' + component['file']] = component['sha256']
                data['files'] = files
            data['base_manifest_sha256'] = file_hash(ROOT / 'export/manifest.json')
            replay_path.parent.mkdir(parents=True, exist_ok=True)
            replay_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps({'objects': len(data['heads']), 'revisions': len(data['revisions']),
                              'batches': len(data.get('batches', [])), 'files': len(data['files'])}))
        finally:
            store.close()
        return
    destination = isolated_instance(ROOT, args.destination)
    if destination.exists():
        parser.error('recovery requires a new destination; no existing instance will be overwritten')
    if ROOT not in destination.parents or '.runtime' not in destination.relative_to(ROOT).parts:
        parser.error('use a new directory inside this task worktree .runtime for isolated recovery')
    data = material_read_json(replay_path)
    manifest=json.loads((ROOT/'export/manifest.json').read_text())
    schema6=manifest.get('schema_version',1)>=6
    indexed = data.get('format') == 'production-export-index-v1'
    if indexed:
        if not schema6 or file_hash(ROOT / 'export/manifest.json') != data['base_manifest_sha256']:
            parser.error('production index requires its exact complete export')
        verify_export_index(data, ROOT / 'export', production.FORMATS)
    if not schema6 and (data.get('format') != 'production-replay-v1' or file_hash(ROOT / 'export/manifest.json') != data['base_manifest_sha256']):
        parser.error('base export changed; review provenance before rebuilding the replay package')
    for relative, expected in data['files'].items():
        if Path(relative).parts[:2] != ('export', 'assets') or len(Path(relative).parts) != 3:
            parser.error('unsafe replay media path')
        if indexed:
            # Verify the physical container here; restore checks its decoded
            # original against the exact stored component and content graph.
            from review_desk.production_media import physical_file_hash
            expected_container = manifest['files'].get(str(Path(relative).relative_to('export')))
            valid = expected_container is not None and physical_file_hash(ROOT / relative) == expected_container
        else:
            valid = file_hash(ROOT / relative) == expected
        if not valid:
            parser.error('original media checksum differs: ' + relative)
    destination.mkdir(parents=True)
    for folder in ('config', 'content', 'export'):
        shutil.copytree(ROOT / folder, destination / folder)
    config_path = destination / 'config/instance.json'
    config = json.loads(config_path.read_text())
    config['title'] = '李寄斩蛇 · 制作准备隔离恢复'
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    store = Store(destination / '.runtime/review.sqlite3')
    try:
        precision = historical_pcm_precision(ROOT) if args.historical_pcm_precision else nullcontext()
        with precision:
            restore(store, destination / 'export')
        # Complete exports already contain production history and its comments.
        # Replay only a story-only base; an inconsistent populated base must fail
        # the exact comparison below, never be silently amended or overwritten.
        if not schema6 and not exact_replay(store, production)['heads']:
            production.restore_records(store, data['batches'])
        recovered = complete_export_index(store, production) if schema6 else exact_replay(store, production)
        if (indexed or not schema6) and (recovered['heads'] != data['heads'] or recovered['revisions'] != data['revisions']):
            raise ValueError('recovered exact revisions or selected heads differ')
        from review_desk.material_archives import read_scope
        with read_scope(store, destination):
            for relative, expected in data['files'].items():
                if file_hash(destination / relative) != expected:
                    raise ValueError('recovered file checksum mismatch')
        print(json.dumps({'recovered': True, 'production_objects': len(recovered['heads']),
                          'production_revisions': len(recovered['revisions']), 'files_verified': len(data['files']),
                          'comments': len(store.comments()), 'destination': str(destination)}, ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    main()
