#!/usr/bin/env python3
"""Initialize, serve, export and prepare an isolated generation review instance."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import uuid

try:
    from .generation_workspace import generation_root, contained, isolated_instance, primary_root, git, write_json
    from .generation_publication import backup, build_plan, tables
    from .publish_generation import copy_media
except ImportError:
    from generation_workspace import generation_root, contained, isolated_instance, primary_root, git, write_json
    from generation_publication import backup, build_plan, tables
    from publish_generation import copy_media

try:
    from .material_model_io import read_bytes as material_read_bytes
except ImportError:
    from material_model_io import read_bytes as material_read_bytes

ROOT = Path(__file__).resolve().parents[1]


def existing_instance(root, path):
    instance = isolated_instance(root, path)
    if not (instance / '.runtime/review.sqlite3').is_file():
        raise ValueError('review database missing; initialize or recover the isolated instance first')
    return instance


def initialize(root, instance):
    root = generation_root(root)
    instance = isolated_instance(root, instance)
    if instance.exists():
        raise ValueError('review instance already exists; resume it instead of initializing again')
    primary = primary_root(root)
    instance.mkdir(parents=True)
    for folder in ('config', 'content'):
        shutil.copytree(root / folder, instance / folder)
    config_path = instance / 'config/instance.json'
    config = json.loads(config_path.read_text())
    config['title'] += ' · 任务预览'
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    (instance / '.runtime').mkdir()
    baseline = instance / '.runtime/generation-base.sqlite3'
    backup(primary / '.runtime/review.sqlite3', baseline)
    backup(baseline, instance / '.runtime/review.sqlite3')
    # Export validates references from this consistent snapshot. Files are copied,
    # not linked to the mutable formal instance.
    shutil.copytree(primary / 'export/assets', instance / 'export/assets')
    write_json(root, instance / '.runtime/generation-base.json', {
        'format': 'generation-review-base-v1', 'instance_id': uuid.uuid4().hex,
        'main_commit': git(primary, 'rev-parse', 'HEAD').decode().strip(),
        'workspace_commit': git(root, 'rev-parse', 'HEAD').decode().strip(),
        'baseline': 'generation-base.sqlite3'})
    return instance


def export_review(root, instance):
    from review_desk.store import Store
    from review_desk.bundle import export
    root = generation_root(root)
    instance = existing_instance(root, instance)
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        manifest = export(store, instance / 'export')
    finally:
        store.close()
    for name in [*manifest['files'], 'manifest.json']:
        target = contained(root, Path('export') / name)
        source = contained(root, instance / 'export' / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if name.startswith('assets/') and target.exists() and material_read_bytes(target) != material_read_bytes(source):
            raise ValueError('existing managed original differs')
        shutil.copyfile(source, target)
    return manifest


def prepare(root, instance, output):
    root = generation_root(root)
    instance = existing_instance(root, instance)
    output = contained(root, output)
    if output.exists():
        raise ValueError('publication package exists; use a new reviewed version')
    baseline = instance / '.runtime/generation-base.sqlite3'
    if not baseline.is_file():
        raise ValueError('review has no initialization baseline')
    run = contained(root, Path('.runtime/generation/prepares') / uuid.uuid4().hex)
    run.mkdir(parents=True)
    backup(instance / '.runtime/review.sqlite3', run / 'candidate.sqlite3')
    plan = build_plan(baseline, run / 'candidate.sqlite3')
    plan['review_origin'] = json.loads((instance / '.runtime/generation-base.json').read_text())
    copy_media(instance, root, plan['media'])
    write_json(root, output, plan)
    return {'package': output.relative_to(root).as_posix(), 'objects': len(plan['scope']), 'media': len(plan['media'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--system', type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init')
    commands.add_parser('export')
    freeze = commands.add_parser('prepare')
    freeze.add_argument('--output', type=Path, required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    root = generation_root(args.workspace)
    instance = isolated_instance(root, args.instance)
    if args.command in ('init', 'export', 'serve'):
        if args.system is None:
            parser.error('--system is required for the review interface')
        sys.path.insert(0, str(args.system.resolve(strict=True)))
    if args.command == 'init':
        initialize(root, instance)
        from review_desk.store import Store
        from review_desk.bundle import export
        store = Store(instance / '.runtime/review.sqlite3')
        try:
            export(store, instance / 'export')
        finally:
            store.close()
        result = {'instance': str(instance), 'initialized': True}
    elif args.command == 'prepare':
        result = prepare(root, instance, args.output)
    elif args.command == 'export':
        result = export_review(root, instance)
    else:
        instance = existing_instance(root, instance)
        from review_desk.server import ReviewServer
        server = ReviewServer(('127.0.0.1', args.port), instance,
                              json.loads((instance / 'config/instance.json').read_text()))
        print('任务预览：http://127.0.0.1:%s/' % server.server_port, flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
