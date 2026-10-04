#!/usr/bin/env python3
"""Save exact production revisions or recover a fresh, isolated review instance.

The complete export preserves story and production records, comments and events.
Older story-only exports can add production records through the shared import API;
neither path replaces a live database or copies any credentials.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import sys
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


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    save = commands.add_parser('snapshot')
    save.add_argument('--instance', type=Path, required=True)
    recover = commands.add_parser('recover')
    recover.add_argument('--destination', type=Path, required=True)
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
                              'batches': len(data['batches']), 'files': len(files)}))
        finally:
            store.close()
        return
    destination = isolated_instance(ROOT, args.destination)
    if destination.exists():
        parser.error('recovery requires a new destination; no existing instance will be overwritten')
    if ROOT not in destination.parents or '.runtime' not in destination.relative_to(ROOT).parts:
        parser.error('use a new directory inside this task worktree .runtime for isolated recovery')
    data = material_read_json(replay_path)
    schema6=json.loads((ROOT/'export/manifest.json').read_text()).get('schema_version',1)>=6
    if not schema6 and (data.get('format') != 'production-replay-v1' or file_hash(ROOT / 'export/manifest.json') != data['base_manifest_sha256']):
        parser.error('base export changed; review provenance before rebuilding the replay package')
    for relative, expected in data['files'].items():
        if Path(relative).parts[:2] != ('export', 'assets') or len(Path(relative).parts) != 3:
            parser.error('unsafe replay media path')
        if file_hash(ROOT / relative) != expected:
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
        restore(store, destination / 'export')
        # Complete exports already contain production history and its comments.
        # Replay only a story-only base; an inconsistent populated base must fail
        # the exact comparison below, never be silently amended or overwritten.
        if not exact_replay(store, production)['heads']:
            production.restore_records(store, data['batches'])
        recovered = exact_replay(store, production)
        if not schema6 and (recovered['heads'] != data['heads'] or recovered['revisions'] != data['revisions']):
            raise ValueError('recovered exact revisions or selected heads differ')
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
