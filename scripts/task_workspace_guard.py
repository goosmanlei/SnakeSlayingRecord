#!/usr/bin/env python3
"""Read-only cleanup guard: report exact Docker mounts and release references."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess


def overlaps(source, targets):
    path = Path(source).resolve()
    return any(path == target or target in path.parents or path in target.parents for target in targets)


def retained_task_ids(root, targets):
    """Resolve task ownership through the public query, independent of layout."""
    executable = shutil.which('codex.task')
    if executable is None:
        raise RuntimeError('Task inventory unavailable; cannot confirm release references')
    result = subprocess.run([executable, '-C', str(root), 'inspect', '--json'],
                            check=True, capture_output=True, text=True, timeout=10)
    value = json.loads(result.stdout)
    if (not isinstance(value, dict) or type(value.get('schemaVersion')) is not int
            or value['schemaVersion'] != 1 or value.get('kind') != 'workspace_inspection'
            or value.get('workspace') != str(root)
            or not isinstance(value.get('retainedWorktrees'), list)):
        raise RuntimeError('Invalid task inventory; cannot confirm release references')
    matched = set()
    for entry in value['retainedWorktrees']:
        if (not isinstance(entry, dict) or not isinstance(entry.get('taskId'), str)
                or not re.fullmatch(r'task-\d{8}-\d{4}', entry['taskId'])
                or not isinstance(entry.get('path'), str)
                or not Path(entry['path']).is_absolute()
                or root not in Path(entry['path']).resolve().parents):
            raise RuntimeError('Invalid task worktree identity; cannot confirm release references')
        if overlaps(entry['path'], targets):
            matched.add(entry['taskId'])
    return matched


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
    affected_tasks = None
    for path in (root / '.runtime/service-releases').glob('*/manifest.json'):
        # These are retained recovery manifests, not arbitrary application data.
        data = path.read_text()
        manifest = json.loads(data)
        if not isinstance(manifest, dict):
            raise RuntimeError(f'Invalid retained release manifest: {path}')
        referenced = any(str(target) in data for target in targets)
        owner_path = manifest.get('story_main')
        # Frozen release files retain their original bytes and digest. A moved
        # task is still retained by its owner and task ID, even if old paths
        # recorded when the release was prepared no longer exist.
        if (isinstance(owner_path, str) and Path(owner_path).is_absolute()
                and Path(owner_path).resolve() == root and manifest.get('task')):
            if affected_tasks is None:
                affected_tasks = retained_task_ids(root, targets)
            referenced = referenced or manifest['task'] in affected_tasks
        if referenced:
            blockers.append(f'retained release manifest: {path}')
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
