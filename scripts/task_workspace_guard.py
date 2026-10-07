#!/usr/bin/env python3
"""Read-only cleanup guard: report exact Docker mounts and release references."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def overlaps(source, targets):
    path = Path(source).resolve()
    return any(path == target or target in path.parents or path in target.parents for target in targets)


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
        # These are retained recovery manifests, not arbitrary application data.
        data = path.read_text()
        if any(str(target) in data for target in targets):
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
