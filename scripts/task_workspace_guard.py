#!/usr/bin/env python3
"""Read-only cleanup guard: report runtime and recovery path dependencies."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def overlaps(source, targets):
    path = Path(source).resolve()
    return any(path == target or target in path.parents or path in target.parents for target in targets)


def mount_dependency(source, destination, root, targets):
    # The shared instance root doesn't imply use of every task directory in it.
    if destination == '/instance' and Path(source).resolve() == root:
        return False
    return overlaps(source, targets)


def release_dependencies(path, manifest, root, targets):
    blockers = []
    # story_worktree/system_worktree and task IDs are provenance. Only paths
    # consumed by restart/recovery can keep their source workspace alive.
    for name in ('previous_app', 'previous_nginx'):
        runtime = manifest.get(name, {})
        if not isinstance(runtime, dict) or not isinstance(runtime.get('mounts', []), list):
            raise RuntimeError(f'Invalid recovery runtime: {path}')
        for mount in runtime.get('mounts', []):
            source = mount.get('Source') if isinstance(mount, dict) else None
            if not isinstance(source, str) or not Path(source).is_absolute():
                raise RuntimeError(f'Invalid recovery mount: {path}')
            if mount_dependency(source, mount.get('Destination'), root, targets):
                blockers.append(f'recovery mount in {path}: {source}')
        for key in ('config_files', 'working_dir'):
            value = runtime.get(key)
            if isinstance(value, str):
                for source in value.split(',') if key == 'config_files' else [value]:
                    source_path = Path(source).resolve()
                    referenced = (any(source_path == target or target in source_path.parents for target in targets)
                                  if key == 'working_dir' else overlaps(source, targets))
                    if Path(source).is_absolute() and referenced:
                        blockers.append(f'recovery {key} in {path}: {source}')
    compose = path.parent / 'compose.release.json'
    if compose.exists():
        value = json.loads(compose.read_text())
        if not isinstance(value, dict) or not isinstance(value.get('services'), dict):
            raise RuntimeError(f'Invalid retained release compose: {compose}')
        for service in value['services'].values():
            if not isinstance(service, dict) or not isinstance(service.get('volumes', []), list):
                raise RuntimeError(f'Invalid release service: {compose}')
            for volume in service.get('volumes', []):
                if isinstance(volume, dict):
                    if volume.get('type') != 'bind':
                        continue
                    source, destination = volume.get('source'), volume.get('target')
                elif isinstance(volume, str):
                    parts = volume.split(':')
                    if len(parts) < 2 or not parts[0].startswith(('/', '.')):
                        continue  # Named/anonymous Docker volume, not a host path.
                    source, destination = parts[:2]
                else:
                    raise RuntimeError(f'Invalid release volume: {compose}')
                if not isinstance(source, str) or not source or not isinstance(destination, str):
                    raise RuntimeError(f'Invalid release bind mount: {compose}')
                source = str((compose.parent / source).resolve())
                if mount_dependency(source, destination, root, targets):
                    blockers.append(f'release mount in {compose}: {source}')
    return blockers


def check(paths, owner=None):
    targets = [Path(p).resolve() for p in paths]
    blockers = []
    root = (owner or Path(__file__).resolve().parents[1]).resolve()
    docker = shutil.which('docker')
    if docker is None:
        raise RuntimeError('Docker inventory unavailable; cannot confirm release of mounts')
    ids = subprocess.run([docker, 'ps', '-aq'], check=True, capture_output=True, text=True, timeout=10).stdout.split()
    # Inspect in bounded groups and keep only relevant mount identities.
    for offset in range(0, len(ids), 25):
        rows = json.loads(subprocess.run([docker, 'inspect', *ids[offset:offset + 25]], check=True,
                                        capture_output=True, text=True, timeout=10).stdout)
        for row in rows:
            for mount in row.get('Mounts', []):
                # The formal /instance mount contains the metadata directory,
                # but does not itself establish a dependency on each task tree.
                formal_parent = (row.get('Name', '').lstrip('/') == 'snakeslayingrecord-app-1'
                                 and mount.get('Destination') == '/instance'
                                 and Path(mount.get('Source', '/')).resolve() == root)
                if mount.get('Source') and not formal_parent and overlaps(mount['Source'], targets):
                    blockers.append(f"container {row['Id'][:12]} {row.get('Name', '')}: {mount['Source']}")
    for path in (root / '.runtime/service-releases').glob('*/manifest.json'):
        manifest = json.loads(path.read_text())
        if not isinstance(manifest, dict):
            raise RuntimeError(f'Invalid retained release manifest: {path}')
        blockers.extend(release_dependencies(path, manifest, root, targets))
    return {'blockers': blockers}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--paths-json', required=True)
    args = p.parse_args()
    paths = json.loads(args.paths_json)
    if not isinstance(paths, list) or not all(isinstance(x, str) and Path(x).is_absolute() for x in paths):
        p.error('absolute task paths required')
    print(json.dumps(check(paths), ensure_ascii=False))


if __name__ == '__main__':
    main()
