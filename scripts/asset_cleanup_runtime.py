#!/usr/bin/env python3
"""Inspect, then explicitly remove the reviewed retired task-0003 previews."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4

try:
    from .generation_workspace import contained, generation_root, primary_root, write_json
except ImportError:
    from generation_workspace import contained, generation_root, primary_root, write_json


ROOT = Path(__file__).resolve().parents[1]
SOURCE = '.codex-project/worktrees/task-20260929-0003/.runtime/production/review-instance'
NAME = re.compile(r'/snakeslayingrecord-production-task-0003(?:-before-[a-z0-9-]+)?')
HEX = re.compile(r'[0-9a-f]{64}')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def docker(*args):
    return subprocess.run(['docker', *args], capture_output=True, timeout=120)


def checked(*args):
    result = docker(*args)
    if result.returncode:
        # Do not echo Docker inspect output or environment values on failure.
        raise ValueError('Docker operation failed: ' + args[0])
    return result.stdout


def inspect_container(cid):
    result = docker('inspect', '--type', 'container', cid)
    if result.returncode:
        error = result.stderr.decode(errors='replace').strip()
        if error in ('Error: No such container: ' + cid, 'Error: No such object: ' + cid):
            return None
        raise ValueError('container inspection failed: ' + cid)
    rows = json.loads(result.stdout)
    if len(rows) != 1 or rows[0]['Id'] != cid:
        raise ValueError('container identity differs')
    return rows[0]


def identity(container, story):
    """Allowlisted, credential-free facts needed to identify these previews."""
    mounts = []
    for mount in container['Mounts']:
        try:
            source = str(Path(mount['Source']).relative_to(story))
        except (KeyError, ValueError):
            raise ValueError('preview mount is outside the story') from None
        mounts.append({key: mount.get(key) for key in
                       ('Type', 'Destination', 'Mode', 'RW', 'Propagation')})
        mounts[-1]['Source'] = {'root': 'story', 'path': source}
    config = container['Config']
    host = container['HostConfig']
    return {'id': container['Id'], 'name': container['Name'], 'image': container['Image'],
            'created': container['Created'],
            'command': {key: config.get(key) for key in ('Entrypoint', 'Cmd', 'WorkingDir')},
            'last_execution': {key: container['State'].get(key) for key in
                               ('StartedAt', 'FinishedAt', 'ExitCode', 'OOMKilled')},
            'mounts': mounts, 'restart_policy': host.get('RestartPolicy'),
            'network_mode': host.get('NetworkMode'), 'port_bindings': host.get('PortBindings')}


def layer_changes(cid):
    changes = sorted(checked('diff', cid).decode().splitlines())
    for line in changes:
        if len(line) < 3 or line[0] not in 'ACD':
            raise ValueError('unrecognized container layer diff')
        operation, path = line[0], line[2:]
        cache = '/__pycache__' in path
        parent = operation == 'C' and any(
            other[2:].startswith(path + '/') and '/__pycache__' in other[2:]
            for other in changes)
        if operation == 'D' or not (cache or parent or line == 'A /instance'):
            raise ValueError('container has a non-cache layer change: ' + path)
    return changes


def validate_manifest(raw, expected_sha=None):
    actual = digest(raw)
    if expected_sha is not None and (not HEX.fullmatch(expected_sha) or expected_sha != actual):
        raise ValueError('manifest SHA-256 differs')
    manifest = json.loads(raw)
    if manifest.get('format') != 'retired-preview-cleanup-v1':
        raise ValueError('unsupported cleanup manifest')
    entries = manifest.get('containers', [])
    if len(entries) != 4 or len({row['identity']['id'] for row in entries}) != 4:
        raise ValueError('manifest must identify the four distinct reviewed previews')
    for entry in entries:
        item = entry['identity']
        if not HEX.fullmatch(item['id']) or not NAME.fullmatch(item['name']):
            raise ValueError('cleanup target is not a retired task-0003 preview')
        mounts = item['mounts']
        if (len(mounts) != 1 or mounts[0]['Type'] != 'bind'
                or mounts[0]['Source'] != {'root': 'story', 'path': SOURCE}
                or mounts[0]['Destination'] != '/instance'
                or not HEX.fullmatch(entry['layer_changes_sha256'])
                or entry['instance_state'] not in ('empty', 'absent')):
            raise ValueError('unexpected preview manifest boundary')
    return manifest, actual


def assess(entry, story):
    item = entry['identity']
    container = inspect_container(item['id'])
    if container is None:
        raise ValueError('reviewed container is missing without a removal receipt')
    if container['State']['Status'] != 'exited' or container['State'].get('Running'):
        raise ValueError('preview is no longer stopped')
    if identity(container, story) != item:
        raise ValueError('container identity, command, mount or host configuration changed')
    source = contained(story, SOURCE)
    if source.exists():
        raise ValueError('retired preview source exists again')
    image = json.loads(checked('image', 'inspect', item['image']))
    if len(image) != 1 or image[0]['Id'] != item['image']:
        raise ValueError('preview recovery image is missing')
    changes = layer_changes(item['id'])
    if digest(canonical(changes)) != entry['layer_changes_sha256']:
        raise ValueError('container writable layer changed')
    # The approved audit inspected /instance as absent/empty. Its image and
    # complete writable-layer diff must remain identical, and its host bind
    # source must remain absent. Do not docker cp the stopped mount: Docker
    # Desktop can recreate a missing host bind source even for that read.
    return {'identity': item, 'state': 'exited', 'layer_changes': changes,
            'instance_state': entry['instance_state'], 'image_retained': True}


def private_bytes(path, raw):
    with path.open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return digest(raw)


def save_state(workspace, path, state):
    write_json(workspace, path, state, replace=path.exists())
    path.chmod(0o600)
    with path.open('rb') as stream:
        os.fsync(stream.fileno())


def verify_archive(run, row):
    files = row.get('archives', {})
    if set(files) != {'inspection.json', 'stdout.log', 'stderr.log'}:
        raise ValueError('removal recovery archive is incomplete')
    for name, expected in files.items():
        path = contained(run, Path(row['id']) / name)
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError('removal recovery archive changed')


def cleanup(workspace, manifest_path, *, apply=False, manifest_sha=None, run_name=None):
    workspace = generation_root(workspace)
    story = primary_root(workspace)
    raw = contained(workspace, manifest_path).read_bytes()
    manifest, sha = validate_manifest(raw, manifest_sha)
    if apply and (manifest_sha is None or not run_name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', run_name)):
        raise ValueError('apply requires the exact manifest SHA-256 and a safe run name')
    entries = manifest['containers']
    if not apply:
        return {'applied': False, 'manifest_sha256': sha,
                'previews': [assess(entry, story) for entry in entries]}
    runtime = contained(workspace, '.runtime/asset-cleanup')
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / 'runtime-cleanup.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = contained(workspace, runtime / 'runtime-removal' / run_name)
        run.mkdir(parents=True, exist_ok=True, mode=0o700)
        state_path = contained(workspace, run / 'receipt.json')
        state = json.loads(state_path.read_text()) if state_path.exists() else {
            'manifest_sha256': sha, 'containers': {}}
        if state['manifest_sha256'] != sha or set(state['containers']) - {e['identity']['id'] for e in entries}:
            raise ValueError('run name belongs to a different cleanup manifest')
        # Check the entire remaining set before the first destructive operation.
        for entry in entries:
            cid = entry['identity']['id']
            row = state['containers'].get(cid)
            if row and row.get('id') != cid:
                raise ValueError('removal receipt identity differs')
            if row and row.get('status') in ('remove_started', 'removed'):
                verify_archive(run, row)
                if inspect_container(cid) is None:
                    # An interrupted rm may have succeeded before its receipt write.
                    row['status'] = 'removed'
                    continue
                if row['status'] == 'removed':
                    raise ValueError('removed container still exists')
            assess(entry, story)
        save_state(workspace, state_path, state)
        for entry in entries:
            cid = entry['identity']['id']
            row = state['containers'].get(cid)
            if row and row.get('status') == 'removed':
                continue
            inspection = assess(entry, story)
            if row:
                verify_archive(run, row)
            else:
                archive = contained(workspace, run / cid)
                if archive.exists():
                    # A previous interruption may have left a partial archive
                    # before its archived receipt. Preserve it and retry in the
                    # same run; earlier removals still use that run's receipts.
                    if not archive.is_dir():
                        raise ValueError('unexpected partial archive path')
                    previous = contained(workspace, run / (cid + '.interrupted-' + uuid4().hex))
                    archive.rename(previous)
                    state.setdefault('interrupted_archives', []).append(previous.name)
                    save_state(workspace, state_path, state)
                archive.mkdir(mode=0o700, exist_ok=False)
                logs = docker('logs', '--timestamps', cid)
                if logs.returncode:
                    raise ValueError('preview log archive failed; nothing removed for ' + cid)
                files = {'inspection.json': canonical(inspection) + b'\n',
                         'stdout.log': logs.stdout, 'stderr.log': logs.stderr}
                row = {'id': cid, 'status': 'archived', 'archives': {
                    name: private_bytes(archive / name, content) for name, content in files.items()}}
                state['containers'][cid] = row
                save_state(workspace, state_path, state)
            # Logs may take time. Recheck all mutable safety facts immediately before rm.
            assess(entry, story)
            row['status'] = 'remove_started'
            save_state(workspace, state_path, state)
            checked('rm', cid)  # No force, volume removal, image deletion, or global pruning.
            if inspect_container(cid) is not None:
                raise ValueError('container removal was not confirmed')
            row['status'] = 'removed'
            save_state(workspace, state_path, state)
        return {'applied': True, 'manifest_sha256': sha,
                'removed_ids': sorted(state['containers']), 'receipt': str(state_path.relative_to(workspace))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--run-name')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = cleanup(args.workspace, args.manifest, apply=args.apply,
                     manifest_sha=args.manifest_sha256, run_name=args.run_name)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
