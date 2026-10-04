#!/usr/bin/env python3
"""Task-specific, reviewable release draft. Does not confirm, push, or _complete.

prepare/preflight are read-only against live systems. build changes only a local
image. apply and recover require an explicit flag and reviewed manifest digests.
All subprocess output is captured: container environment values never go to logs.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, build_opener

TASK = 'task-20261004-0002'
PROJECT = 'snakeslayingrecord'
APP = PROJECT + '-app-1'
NGINX = PROJECT + '-nginx-1'
FIELDS = {'story_background', 'creative_background', 'current_stage'}
INSTANCE_FILES = ('config/instance.json', 'content/production-approach.json')
PORTS = {'3000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '3000'},
                      {'HostIp': '127.0.0.1', 'HostPort': '64401'}]}
DOCKER = shutil.which('docker')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_once(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(not path.is_symlink() and path.is_file() and path.read_bytes() == raw, 'immutable file differs: ' + str(path))
    else:
        # Exclusive create; never replace a previous reviewed result.
        with path.open('xb') as stream:
            stream.write(raw)
    return path


def save(path, value):
    return write_once(path, json.dumps(value, ensure_ascii=False, indent=2).encode() + b'\n')


def run(args, *, env=None):
    result = subprocess.run([str(a) for a in args], capture_output=True, env=env)
    if result.returncode:
        # Do not include command args, child stdout, stderr, or environment.
        raise RuntimeError(Path(str(args[0])).name + ' failed (exit ' + str(result.returncode) + '); output withheld')
    return result.stdout


def git(repo, *args):
    return run(['git', '-C', repo, *args]).decode().strip()


def inspect(name, image=False):
    require(DOCKER is not None, 'docker CLI unavailable')
    return json.loads(run([DOCKER, 'image' if image else 'container', 'inspect', name]))[0]


def env_values(container):
    return dict(item.split('=', 1) for item in container['Config'].get('Env', []))


def safe_container(container):
    """Exact operational identity excluding secrets and volatile health timestamps."""
    return {'image': container['Image'],
            'mounts': sorted([{k: m[k] for k in ('Type', 'Source', 'Destination', 'RW')}
                              for m in container['Mounts']], key=lambda m: m['Destination']),
            'ports': container['HostConfig']['PortBindings'] or {},
            'environment_names': sorted(env_values(container)),
            'config_files': container['Config']['Labels']['com.docker.compose.project.config_files'],
            'working_dir': container['Config']['Labels']['com.docker.compose.project.working_dir'],
            'command': container['Config'].get('Cmd'), 'entrypoint': container['Config'].get('Entrypoint'),
            'user': container['Config'].get('User'), 'container_workdir': container['Config'].get('WorkingDir'),
            'restart': container['HostConfig'].get('RestartPolicy')}


def http(path, body=None):
    request = Request('http://127.0.0.1:3000' + path,
                      data=canonical(body) if body is not None else None,
                      headers={'Content-Type': 'application/json'},
                      method='PATCH' if body is not None else 'GET')
    with build_opener(ProxyHandler({})).open(request, timeout=15) as response:
        return json.load(response)


def project():
    return http('/api/configurations')['values']['PROJECT']


def primary(worktree):
    return Path(git(worktree, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve().parent


def repo_check(worktree, main, candidate, target, *, system=False):
    require(re.fullmatch('[0-9a-f]{40}', candidate or '') is not None, 'full candidate SHA required')
    require(re.fullmatch('[0-9a-f]{40}', target or '') is not None, 'full target SHA required')
    require(primary(worktree) == Path(main).resolve(), 'worktree has wrong main repository')
    require(git(worktree, 'rev-parse', 'HEAD') == candidate, 'candidate HEAD changed')
    require(git(main, 'branch', '--show-current') == 'main', 'target is not main')
    require(git(main, 'rev-parse', 'HEAD') in ((target, candidate) if system else (target,)),
            'target changed or story already completed; stop')
    for repo in (worktree, main):
        require(not git(repo, 'status', '--porcelain', '--untracked-files=no'), 'tracked files changed')
    run(['git', '-C', worktree, 'merge-base', '--is-ancestor', target, candidate])


def git_file(repo, commit, path):
    entry = git(repo, 'ls-tree', commit, '--', path)
    require(entry.startswith(('100644 ', '100755 ')), 'candidate file missing or not a regular Git file: ' + path)
    return run(['git', '-C', repo, 'show', commit + ':' + path])


def update_package(root):
    request, before, after, manifest = (read(root / name) for name in (
        'request.json', 'before-project.json', 'expected-body.json', 'manifest.json'))
    require(set(request) == {'expected_version', 'updates'} and set(request['updates']) == FIELDS,
            'PROJECT request must contain only the three authorized fields')
    require(request['updates']['current_stage'] == 'MATERIAL_PREPARATION', 'PROJECT stage differs from user decision')
    guard, candidate = manifest['guard'], manifest['candidate']
    require(before['scope'] == 'PROJECT', 'wrong configuration scope')
    require(request['expected_version'] == before['version'] == guard['expected_version'] == 14,
            'unexpected original PROJECT version')
    require(sha(canonical(before)) == guard['full_old_project_sha256'], 'old PROJECT hash differs')
    require(sha(canonical(before['body'])) == guard['full_old_body_sha256'], 'old body hash differs')
    require(after == {**before['body'], **request['updates']}, 'extra PROJECT change')
    require(sha(canonical(after)) == candidate['expected_body_sha256'], 'new body hash differs')
    return request, before, after


def base_image_tag(image_id):
    require(re.fullmatch('sha256:[0-9a-f]{64}', image_id or '') is not None, 'full base image ID required')
    return 'ao-' + TASK + '-base:' + image_id.split(':', 1)[1]


def pin_base_image(image_id, tag):
    require(tag == base_image_tag(image_id), 'base image tag differs from fixed ID')
    require(inspect(image_id, image=True)['Id'] == image_id, 'fixed base image unavailable')
    existing = run([DOCKER, 'image', 'ls', '--no-trunc', '--format', '{{.ID}}', '--filter', 'reference=' + tag]).decode().splitlines()
    if existing:
        require(set(existing) == {image_id}, 'base image tag belongs to another image; do not replace')
    else:
        run([DOCKER, 'tag', image_id, tag])
    require(inspect(tag, image=True)['Id'] == image_id, 'base image tag changed before build')


def prepare(args):
    story, system = args.story_worktree.resolve(), args.system_worktree.resolve()
    story_main, system_main = primary(story), primary(system)
    repo_check(story, story_main, args.story_candidate, args.story_target)
    repo_check(system, system_main, args.system_candidate, args.system_target, system=True)
    require(not args.output.exists(), 'use a new immutable bundle directory')
    require((story / '.runtime').resolve() in args.output.resolve().parents, 'bundle must be inside this task runtime')
    update_package(args.project_update)
    config = json.loads(git_file(story, args.story_candidate, INSTANCE_FILES[0]))
    require(config['review_desk_commit'] == args.system_candidate, 'story candidate pin is not system candidate')
    app, nginx = inspect(APP), inspect(NGINX)
    app_safe, nginx_safe = safe_container(app), safe_container(nginx)
    for current in (app, nginx):
        base = inspect(current['Image'], image=True)
        process_keys = ('Cmd', 'Entrypoint', 'User', 'WorkingDir')
        process, base_process = ({key: config.get(key) for key in process_keys}
                                 for config in (current['Config'], base['Config']))
        # Docker reports an unspecified user as either null or an empty string.
        for config in (process, base_process):
            if config['User'] is None:
                config['User'] = ''
        require(process == base_process, 'nondefault service process configuration; revise plan')
        require(current['HostConfig']['RestartPolicy'] == {'Name': 'unless-stopped', 'MaximumRetryCount': 0}, 'restart policy changed')
    require(env_values(nginx) == env_values(inspect(nginx['Image'], image=True)), 'nginx custom environment requires explicit plan')
    require(not nginx['Mounts'], 'nginx custom mounts require explicit plan')
    require(app_safe['working_dir'] == str(story_main), 'formal app is another instance')
    require(nginx_safe['ports'] == PORTS, 'formal loopback ports changed')
    mounts = {m['Destination']: m for m in app_safe['mounts']}
    require(mounts.get('/instance') == {'Type': 'bind', 'Source': str(story_main), 'Destination': '/instance', 'RW': True}, 'normal instance mount differs')
    require(set(mounts) == {'/instance', '/instance/config/instance.json', '/run/local-ca/cacert.pem'},
            'unreviewed existing mounts; revise release plan')
    require(not mounts['/run/local-ca/cacert.pem']['RW'], 'CA must be read-only')
    old_project = project()
    require(old_project == read(args.project_update / 'before-project.json'), 'formal PROJECT drifted')
    require(app['State']['Running'] and app['State'].get('Health', {}).get('Status') == 'healthy', 'formal app is not healthy')
    bundle = args.output.resolve()
    hashes = {}
    def put(rel, raw):
        write_once(bundle / rel, raw); hashes[rel] = sha(raw)
    for name in INSTANCE_FILES:
        put('instance/' + name, git_file(story, args.story_candidate, name))
    for name in ('request.json', 'before-project.json', 'expected-body.json', 'manifest.json'):
        put('project-update/' + name, (args.project_update / name).read_bytes())
    source = {}
    for line in git(system, 'ls-tree', '-r', args.system_candidate, '--', 'review_desk').splitlines():
        header, name = line.split('\t', 1)
        require(header.split()[0] in ('100644', '100755'), 'system source symlink or special file')
        raw = run(['git', '-C', system, 'show', args.system_candidate + ':' + name])
        put('build/' + name, raw); source[name] = sha(raw)
    base_tag = base_image_tag(app['Image'])
    put('build/Dockerfile', ('FROM ' + base_tag + '\nRUN rm -rf /app/review_desk\nCOPY review_desk /app/review_desk\n').encode())
    helper = 'scripts/integrate_generation_review_system.py'
    require((story / helper).read_bytes() == git_file(story, args.story_candidate, helper), 'integrator differs from candidate')
    files = app_safe['config_files'].split(',')
    require(files == nginx_safe['config_files'].split(','), 'app and nginx compose sets differ')
    compose_hashes = {file: sha(Path(file).read_bytes()) for file in files}
    plan = {'format': 'generation-system-delivery-v1', 'task': TASK, 'push': False,
            'system_main_from_story_main': os.path.relpath(system_main, story_main),
            'system_worktree': os.path.relpath(system, story),
            'expected_target': args.system_target, 'candidate': args.system_candidate}
    put('system-delivery.json', json.dumps(plan, ensure_ascii=False, indent=2).encode() + b'\n')
    manifest = {'format': 'autonomous-release-v1', 'task': TASK, 'push': False,
                'story_worktree': str(story), 'system_worktree': str(system),
                'story_main': str(story_main), 'system_main': str(system_main),
                'story_candidate': args.story_candidate, 'story_target': args.story_target,
                'system_candidate': args.system_candidate, 'system_target': args.system_target,
                'release_name': 'autonomous-20261004-0002-' + args.story_candidate[:12] + '-' + args.system_candidate[:12],
                'hashes': hashes, 'source_hashes': source, 'base_image_tag': base_tag, 'previous_app': app_safe,
                'previous_nginx': nginx_safe, 'previous_compose_hashes': compose_hashes,
                'integrator_sha256': sha((story / helper).read_bytes()),
                'ca_sha256': sha(Path(mounts['/run/local-ca/cacert.pem']['Source']).read_bytes()),
                'wrapper_sha256': sha(Path(__file__).read_bytes()),
                'prepared_at': datetime.now(timezone.utc).isoformat()}
    save(bundle / 'manifest.json', manifest)
    print(json.dumps({'prepared': str(bundle), 'manifest_sha256': sha((bundle / 'manifest.json').read_bytes()),
                      'live_writes': False, 'build_required': True}, ensure_ascii=False))


def load_bundle(path):
    root = path.resolve(); m = read(root / 'manifest.json')
    require(m.get('format') == 'autonomous-release-v1' and m.get('task') == TASK and m.get('push') is False, 'unsupported bundle')
    require(sha(Path(__file__).read_bytes()) == m['wrapper_sha256'], 'release wrapper changed since preparation')
    for rel, expected in m['hashes'].items():
        require(not Path(rel).is_absolute() and '..' not in Path(rel).parts, 'invalid package path')
        require(sha((root / rel).read_bytes()) == expected, 'bundle file changed: ' + rel)
    update_package(root / 'project-update')
    return root, m


def source_check(image_id, expected, *, running=False):
    code = "import pathlib,hashlib,json;p=pathlib.Path('/app');print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'review_desk').rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'},sort_keys=True))"
    command = ([DOCKER, 'exec', APP, 'python', '-c', code] if running else
               [DOCKER, 'run', '--rm', '--network', 'none', '--entrypoint', 'python', image_id, '-c', code])
    require(json.loads(run(command)) == expected, 'actual image source tree differs from system candidate')


def build(args):
    root, m = load_bundle(args.bundle)
    require(not (root / 'image.json').exists(), 'image receipt already exists; do not rebuild reviewed bundle')
    base_id, base_tag = m['previous_app']['image'], m['base_image_tag']
    pin_base_image(base_id, base_tag)
    tag = 'story-review-desk:autonomous-' + m['system_candidate'][:12] + '-' + m['story_candidate'][:12]
    run([DOCKER, 'build', '--pull=false', '--network=none', '-t', tag, root / 'build'])
    require(inspect(base_tag, image=True)['Id'] == base_id, 'base image tag changed during build')
    image_id = inspect(tag, image=True)['Id']
    source_check(image_id, m['source_hashes'])
    save(root / 'image.json', {'image': image_id, 'tag': tag, 'source_verified': True,
                             'manifest_sha256': sha((root / 'manifest.json').read_bytes())})
    print(json.dumps({'image': image_id, 'image_receipt_sha256': sha((root / 'image.json').read_bytes()), 'formal_mutations': False}))


def common_checks(root, m):
    repo_check(m['story_worktree'], m['story_main'], m['story_candidate'], m['story_target'])
    repo_check(m['system_worktree'], m['system_main'], m['system_candidate'], m['system_target'], system=True)
    helper = Path(m['story_worktree']) / 'scripts/integrate_generation_review_system.py'
    require(sha(helper.read_bytes()) == m['integrator_sha256'], 'controlled integrator changed')
    for path, expected in m['previous_compose_hashes'].items():
        require(sha(Path(path).read_bytes()) == expected, 'previous compose input changed')
    ca = next(x['Source'] for x in m['previous_app']['mounts'] if x['Destination'] == '/run/local-ca/cacert.pem')
    require(sha(Path(ca).read_bytes()) == m['ca_sha256'], 'trusted CA changed')
    image = read(root / 'image.json')
    require(image['manifest_sha256'] == sha((root / 'manifest.json').read_bytes()) and image['source_verified'], 'image belongs to another bundle')
    require(inspect(image['image'], image=True)['Id'] == image['image'], 'candidate image unavailable')
    return image


def preflight(args):
    root, m = load_bundle(args.bundle); image = common_checks(root, m)
    require(safe_container(inspect(APP)) == m['previous_app'], 'formal app drifted')
    require(safe_container(inspect(NGINX)) == m['previous_nginx'], 'formal nginx drifted')
    require(project() == read(root / 'project-update/before-project.json'), 'formal PROJECT drifted')
    result = run([sys.executable, Path(m['story_worktree']) / 'scripts/integrate_generation_review_system.py', '--plan', root / 'system-delivery.json'])
    require(json.loads(result)['preflight_only'], 'unexpected integration result')
    print(json.dumps({'preflight_only': True, 'manifest_sha256': sha((root / 'manifest.json').read_bytes()),
                      'image_receipt_sha256': sha((root / 'image.json').read_bytes()), 'image': image['image']}))


@contextmanager
def publication_locks(m):
    with ExitStack() as stack:
        system_git = Path(git(m['system_main'], 'rev-parse', '--path-format=absolute', '--git-common-dir'))
        for path in (system_git / 'review-desk-integration.lock', Path(m['story_main']) / '.runtime/publication.lock'):
            lock = stack.enter_context(path.open('a')); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def snapshot(database, destination):
    require(not destination.exists(), 'snapshot path already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Read-only live connection; never restore or import this snapshot.
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as src:
        with sqlite3.connect(destination) as dst:
            src.backup(dst)


def rows(path):
    result = {}
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for (name, sql) in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
            quoted = '"' + name.replace('"', '""') + '"'
            values = [dict(row) for row in db.execute('SELECT * FROM ' + quoted)]
            require(all(not isinstance(value, bytes) for row in values for value in row.values()), 'unexpected BLOB history; review serializer')
            result[name] = {'schema': sha(sql.encode()), 'rows': values}
    return result


def verify_history(before_file, after_file, expected_body, expected_version, event_delta, expected_event_bodies=None):
    before, after = rows(before_file), rows(after_file)
    require(set(before) == set(after), 'database table set changed')
    result = {}
    for name in before:
        require(before[name]['schema'] == after[name]['schema'], 'database schema changed: ' + name)
        old, new = before[name]['rows'], after[name]['rows']
        if name == 'configurations':
            old = [row for row in old if row['scope'] != 'PROJECT']; new = [row for row in new if row['scope'] != 'PROJECT']
        a, b = Counter(sha(canonical(row)) for row in old), Counter(sha(canonical(row)) for row in new)
        require(not (a - b), 'previous rows changed or disappeared: ' + name)
        result[name] = {'before': len(old), 'after': len(new), 'old_rows_preserved': True}
        if name == 'configurations':
            require(a == b, 'another configuration changed')
    project_rows = [row for row in after['configurations']['rows'] if row['scope'] == 'PROJECT']
    require(len(project_rows) == 1 and project_rows[0]['schema_version'] == 4 and project_rows[0]['version'] == expected_version and
            json.loads(project_rows[0]['body']) == expected_body, 'PROJECT database readback differs')
    old_events = {row['id'] for row in before['configuration_events']['rows']}
    extra = sorted([row for row in after['configuration_events']['rows'] if row['id'] not in old_events], key=lambda row: row['version'])
    require(len(extra) == event_delta and all(row['scope'] == 'PROJECT' for row in extra), 'unexpected configuration event delta')
    require([row['version'] for row in extra] == list(range(expected_version - event_delta + 1, expected_version + 1)), 'configuration event version chain differs')
    require(extra[-1]['version'] == expected_version and json.loads(extra[-1]['body']) == expected_body, 'last PROJECT event differs')
    if expected_event_bodies is not None:
        require({row['version']: json.loads(row['body']) for row in extra} == expected_event_bodies, 'PROJECT event body chain differs')
    return result


def compose_definition(m, image, release):
    ca = next(x['Source'] for x in m['previous_app']['mounts'] if x['Destination'] == '/run/local-ca/cacert.pem')
    environment = {key: '${AO_RELEASE_ENV_' + str(i) + '?required}' for i, key in enumerate(m['previous_app']['environment_names'])}
    def volume(source, target, readonly):
        return {'type': 'bind', 'source': str(source), 'target': target, 'read_only': readonly}
    # Standalone fixed compose, no stale override merge semantics or expanded secrets.
    return {'services': {
        'app': {'image': image['image'], 'restart': 'unless-stopped', 'environment': environment,
                'volumes': [volume(m['story_main'], '/instance', False), volume(ca, '/run/local-ca/cacert.pem', True),
                            *[volume(release / 'instance' / name, '/instance/' + name, True) for name in INSTANCE_FILES]],
                'expose': ['8765'], 'healthcheck': {'test': ['CMD', 'python', '-c', "import urllib.request;urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://127.0.0.1:8765/api/instance',timeout=3)"], 'interval': '15s', 'timeout': '5s', 'retries': 3}},
        'nginx': {'image': m['previous_nginx']['image'], 'restart': 'unless-stopped',
                  'depends_on': {'app': {'condition': 'service_healthy'}},
                  'ports': ['127.0.0.1:3000:3000', '127.0.0.1:64401:3000']}}}


def install(root, m, image):
    release = Path(m['story_main']) / '.runtime/service-releases' / m['release_name']
    require(not release.is_symlink(), 'release directory must not be a symlink')
    for name in INSTANCE_FILES:
        write_once(release / 'instance' / name, (root / 'instance' / name).read_bytes())
    for name in ('manifest.json', 'image.json'):
        write_once(release / name, (root / name).read_bytes())
    write_once(release / 'release.py', Path(__file__).read_bytes())
    save(release / 'compose.release.json', compose_definition(m, image, release))
    write_once(release / 'README.md', ('# Permanent release '+m['release_name']+'\n\n'
      'This directory permanently supplies the exact config and production-approach files. '
      'Do not edit them in place. A future update needs a new immutable release and mount switch; editing main alone does not update these two running files. '
      'The normal instance database/assets remain on the main mount. Never restore the before database over the live instance.\n\n'
      'Restart only the existing exact containers (no recreation or new deployment):\n\n'
      '`python3 release.py restart --release . --apply`\n\n'
      'If the container has been removed, stop and recover environment through the existing operator channel; this release stores no secret values. '
      'Restart is a later maintenance action; do not execute after this task _complete as part of the same delivery.\n').encode())
    return release


def compose_up(m, compose_files, current_environment, *, release=False):
    require(sorted(current_environment) == m['previous_app']['environment_names'], 'environment names changed')
    child = os.environ.copy()
    if release:
        for i, key in enumerate(m['previous_app']['environment_names']):
            child['AO_RELEASE_ENV_' + str(i)] = current_environment[key]
    else:
        # The known original compose uses original env names. Subprocess receives
        # values in memory; no shell interpolation, output, file, or log copy.
        child.update(current_environment)
    command = [DOCKER, 'compose', '-p', PROJECT, '--project-directory', m['story_main']]
    for file in compose_files:
        command += ['-f', str(file)]
    run(command + ['up', '-d', '--no-build', '--force-recreate', 'app', 'nginx'], env=child)
    require(env_values(inspect(APP)) == current_environment, 'running app environment differs after switch')


def wait_healthy():
    deadline = time.monotonic() + 100
    while time.monotonic() < deadline:
        container = inspect(APP)
        if container['State'].get('Health', {}).get('Status') == 'healthy':
            return
        if not container['State']['Running']:
            raise RuntimeError('app stopped before healthy')
        time.sleep(1)
    raise RuntimeError('app health timed out; no further write performed')


def verify_service(m, image, release):
    wait_healthy()
    app, nginx = inspect(APP), inspect(NGINX)
    require(app['Image'] == image['image'] and nginx['Image'] == m['previous_nginx']['image'], 'wrong running image')
    require(safe_container(nginx)['ports'] == PORTS, 'formal loopback ports differ')
    expected = {str(v['target']): (str(v['source']), not v['read_only']) for v in compose_definition(m, image, release)['services']['app']['volumes']}
    actual = {v['Destination']: (v['Source'], v['RW']) for v in app['Mounts']}
    require(actual == expected and all(v['Type'] == 'bind' for v in app['Mounts']), 'running mounts differ')
    source_check(image['image'], m['source_hashes'], running=True)
    for name in INSTANCE_FILES:
        actual = run([DOCKER, 'exec', APP, 'cat', '/instance/' + name])
        require(sha(actual) == m['hashes']['instance/' + name], 'running instance file differs')
    for port in (3000, 64401):
        with build_opener(ProxyHandler({})).open('http://127.0.0.1:' + str(port) + '/api/instance', timeout=15) as response:
            require(response.status == 200, 'formal entry unavailable')
    return {'source_tree_equal': True, 'instance_files_equal': True, 'ports': [3000, 64401],
            'browser_acceptance': 'required separately before _complete'}


def update_project(root, *, compensate=False):
    request, before, after = update_package(root / 'project-update')
    current = project()
    if compensate:
        if current['scope'] == 'PROJECT' and current['schema_version'] == 4 and current['version'] == before['version'] + 2 and current['body'] == before['body']:
            return {'already_applied': True, 'record': current}
        require(current['schema_version'] == 4 and current['version'] == before['version'] + 1 and current['body'] == after, 'compensation refused: current PROJECT changed')
        wanted = before['body']; wanted_version = current['version'] + 1
        payload = {'expected_version': current['version'], 'updates': {key: before['body'][key] for key in FIELDS}}
    else:
        wanted, wanted_version, payload = after, before['version'] + 1, request
        if current['scope'] == 'PROJECT' and current['schema_version'] == 4 and current['version'] == wanted_version and current['body'] == wanted:
            return {'already_applied': True, 'record': current}
        require(current == before, 'original PROJECT record changed; do not increase expected_version')
    response_lost = False
    try:
        http('/api/configurations/PROJECT', payload)
    except Exception:
        # Includes truncated HTTP/JSON responses after a committed write.
        response_lost = True
    # One write attempt only. No blind retries, including on 409 or lost response.
    current = project()
    require(current['scope'] == 'PROJECT' and current['schema_version'] == 4 and current['version'] == wanted_version and current['body'] == wanted, 'PROJECT result is not exactly confirmed; stop, no retry')
    return {'already_applied': False, 'response_lost_or_rejected': response_lost, 'record': current}


def authorized_bundle(args):
    require(args.apply, 'explicit --apply is required; this flag does not replace user confirmation')
    root, m = load_bundle(args.bundle)
    require(sha((root / 'manifest.json').read_bytes()) == args.manifest_sha256, 'reviewed manifest digest differs')
    require(sha((root / 'image.json').read_bytes()) == args.image_receipt_sha256, 'reviewed image receipt digest differs')
    return root, m


def step(root, name):
    # Local operational receipt, never committed and never contains request bodies.
    path = root / 'run/steps.jsonl'
    with path.open('a') as stream:
        stream.write(json.dumps({'at': datetime.now(timezone.utc).isoformat(), 'step': name}) + '\n')


def apply(args):
    root, m = authorized_bundle(args)
    with publication_locks(m):
        image = common_checks(root, m)
        receipt = root / 'run'
        save(receipt / 'identity.json', {'manifest': args.manifest_sha256, 'image_receipt': args.image_receipt_sha256})
        step(root, 'preflight_passed')
        db = Path(m['story_main']) / '.runtime/review.sqlite3'
        before_file = receipt / 'before.sqlite3'
        if not before_file.exists():
            require(safe_container(inspect(APP)) == m['previous_app'] and safe_container(inspect(NGINX)) == m['previous_nginx'], 'formal service drifted before snapshot')
            require(project() == read(root / 'project-update/before-project.json'), 'formal PROJECT drifted before snapshot')
            snapshot(db, before_file)
            save(receipt / 'before.json', {'sha256': sha(before_file.read_bytes()), 'counts': {name: len(value['rows']) for name, value in rows(before_file).items()}})
        require(sha(before_file.read_bytes()) == read(receipt / 'before.json')['sha256'], 'before snapshot changed or incomplete')
        step(root, 'before_snapshot_verified')
        integration = run([sys.executable, Path(m['story_worktree']) / 'scripts/integrate_generation_review_system.py',
                           '--plan', root / 'system-delivery.json', '--apply', '--receipt', receipt / 'system-integration.json'])
        require(json.loads(integration)['target_after'] == m['system_candidate'], 'system integration mismatch')
        step(root, 'system_integrated')
        release = install(root, m, image)
        current = inspect(APP); environment = env_values(current)
        if current['Image'] != image['image']:
            _, app_safe, _, rollback_app, _, _ = recovery_runtime(m, image, release)
            require(app_safe in (m['previous_app'], rollback_app), 'runtime changed; refusing service switch')
            compose_up(m, [release / 'compose.release.json'], environment, release=True)
        step(root, 'service_switch_requested_or_already_exact')
        service = verify_service(m, image, release)
        save(receipt / 'service.json', {**service, 'release': str(release), 'image': image['image']})
        step(root, 'service_verified')
        result = update_project(root)
        step(root, 'project_exact_result_confirmed')
        # The exact snapshot captures all current rows, not just selected counts.
        fd, temp_name = tempfile.mkstemp(prefix='after-', suffix='.sqlite3', dir=receipt);os.close(fd);Path(temp_name).unlink()
        after_file = Path(temp_name);snapshot(db, after_file)
        history = verify_history(before_file, after_file, read(root / 'project-update/expected-body.json'), 15, 1)
        final = {'status': 'formal_browser_acceptance_pending', 'project_version': result['record']['version'],
                 'project_sha256': sha(canonical(result['record'])), 'history': history,
                 'after_snapshot': after_file.name, 'after_snapshot_sha256': sha(after_file.read_bytes()),
                 'system_main': m['system_candidate'], 'story_main_not_integrated': True,
                 'complete_invoked': False, 'push': False}
        # Resume records may differ only in observation file; keep each attempt.
        save(receipt / ('ready-' + str(time.time_ns()) + '.json'), final)
        step(root, 'history_verified_waiting_formal_browser')
        print(json.dumps(final, ensure_ascii=False))


def recovery_runtime(m, image, release):
    """Known per-service states for a partial switch; a foreign release is refused."""
    previous_files = list(m['previous_compose_hashes'])
    rollback = release / 'compose.previous.json'
    candidate_file = str(release / 'compose.release.json')
    rollback_files = ','.join([*previous_files, str(rollback)])
    candidate_app = {**m['previous_app'], 'image': image['image'], 'config_files': candidate_file,
        'mounts': sorted([{'Type': 'bind', 'Source': str(v['source']), 'Destination': v['target'], 'RW': not v['read_only']}
                          for v in compose_definition(m, image, release)['services']['app']['volumes']], key=lambda v: v['Destination'])}
    candidate_nginx = {**m['previous_nginx'], 'config_files': candidate_file}
    rollback_app = {**m['previous_app'], 'config_files': rollback_files}
    rollback_nginx = {**m['previous_nginx'], 'config_files': rollback_files}
    current_app, current_nginx = inspect(APP), inspect(NGINX)
    app_safe, nginx_safe = safe_container(current_app), safe_container(current_nginx)
    require(app_safe in (m['previous_app'], candidate_app, rollback_app), 'foreign or unknown app release; recovery refused before mutation')
    require(nginx_safe in (m['previous_nginx'], candidate_nginx, rollback_nginx), 'foreign or unknown nginx release; recovery refused before mutation')
    return current_app, app_safe, nginx_safe, rollback_app, rollback_nginx, rollback


def recovery_snapshot(root, m, prefix):
    fd, name = tempfile.mkstemp(prefix=prefix, suffix='.sqlite3', dir=root / 'run')
    os.close(fd);Path(name).unlink()
    snapshot(Path(m['story_main']) / '.runtime/review.sqlite3', Path(name))
    return Path(name)


def recover(args):
    root, m = authorized_bundle(args)
    with publication_locks(m):
        image = common_checks(root, m)  # Candidate, both mains, old Compose and CA still exact.
        require(read(root / 'run/identity.json') == {'manifest': args.manifest_sha256, 'image_receipt': args.image_receipt_sha256}, 'recovery is not bound to this started release')
        require(sha((root / 'run/before.sqlite3').read_bytes()) == read(root / 'run/before.json')['sha256'], 'recovery baseline changed or incomplete')
        release = Path(m['story_main']) / '.runtime/service-releases' / m['release_name']
        current, app_safe, nginx_safe, rollback_app, rollback_nginx, rollback = recovery_runtime(m, image, release)
        if args.action == 'config':
            request, before, after = update_package(root / 'project-update')
            initial = project()
            require(initial['version'] in (15, 16) and initial['schema_version'] == 4 and
                    initial['body'] == (after if initial['version'] == 15 else before['body']),
                    'compensation refused: PROJECT is neither the exact applied nor compensated state')
            # Validate old rows AND the exact preceding events before any PATCH.
            observed = recovery_snapshot(root, m, 'pre-compensation-')
            event_bodies = {15: after, **({16: before['body']} if initial['version'] == 16 else {})}
            verify_history(root / 'run/before.sqlite3', observed, initial['body'], initial['version'], initial['version'] - 14, event_bodies)
            result = update_project(root, compensate=True)
            final_snapshot = recovery_snapshot(root, m, 'compensated-')
            history = verify_history(root / 'run/before.sqlite3', final_snapshot, before['body'], 16, 2, {15: after, 16: before['body']})
            receipt = root / 'run/config-compensation.json'
            if receipt.exists():
                require(read(receipt)['record_sha256'] == sha(canonical(result['record'])), 'previous compensation receipt differs')
            else:
                save(receipt, {'record_sha256': sha(canonical(result['record'])), 'history': history})
        else:
            for image_id in (m['previous_app']['image'], m['previous_nginx']['image']):
                require(inspect(image_id, image=True)['Id'] == image_id, 'fixed previous image unavailable')
            already_old = app_safe in (m['previous_app'], rollback_app) and nginx_safe in (m['previous_nginx'], rollback_nginx)
            if not already_old:
                # The final override fixes BOTH exact image IDs before Compose can
                # resolve any mutable original tags. All app environment uses
                # the same in-memory placeholders as the forward switch.
                definition = {'services': {'app': {'image': m['previous_app']['image'],
                    'environment': compose_definition(m, image, release)['services']['app']['environment']},
                    'nginx': {'image': m['previous_nginx']['image']}}}
                save(rollback, definition)
                compose_up(m, [*m['previous_compose_hashes'], rollback], env_values(current), release=True)
            wait_healthy()
            require(safe_container(inspect(APP)) in (m['previous_app'], rollback_app), 'service recovery differs from fixed previous app')
            require(safe_container(inspect(NGINX)) in (m['previous_nginx'], rollback_nginx), 'service recovery differs from fixed previous nginx')
            save(root / 'run/service-recovered.json', {'old_image': m['previous_app']['image'], 'old_nginx_image': m['previous_nginx']['image'], 'database_restored': False})
        print(json.dumps({'recovery': args.action, 'complete_invoked': False, 'database_restored': False}))


def restart(args):
    # Permanent release maintenance entry, independent of the task worktree.
    require(args.apply, 'restart requires explicit --apply')
    release = args.release.resolve();m = read(release / 'manifest.json');image = read(release / 'image.json')
    require(sha(Path(__file__).read_bytes()) == m['wrapper_sha256'], 'restart wrapper differs')
    require(image['manifest_sha256'] == sha((release / 'manifest.json').read_bytes()), 'restart image receipt differs')
    for name in INSTANCE_FILES:
        require(sha((release / 'instance' / name).read_bytes()) == m['hashes']['instance/' + name], 'permanent file changed')
    require(read(release / 'compose.release.json') == compose_definition(m, image, release), 'permanent compose changed')
    with publication_locks(m):
        current = inspect(APP)
        require(current['Image'] == image['image'], 'another release is active; do not replace it')
        expected_mounts = {str(v['target']): (str(v['source']), not v['read_only']) for v in compose_definition(m, image, release)['services']['app']['volumes']}
        require({v['Destination']: (v['Source'], v['RW']) for v in current['Mounts']} == expected_mounts, 'another release mount is active; do not replace it')
        require(safe_container(inspect(NGINX)) == {**m['previous_nginx'], 'config_files': str(release / 'compose.release.json')}, 'another nginx release is active; do not restart it')
        # Existing-container restart preserves its environment and mounts without
        # reconstructing any deployment or reading secrets into a new Compose.
        run([DOCKER, 'restart', APP]);wait_healthy()
        run([DOCKER, 'restart', NGINX])
        verify_service(m, image, release)
    print(json.dumps({'restarted_exact_release': m['release_name'], 'database_restored': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    for name in ('story-worktree', 'system-worktree', 'project-update', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('story-candidate', 'system-candidate', 'story-target', 'system-target'):
        p.add_argument('--' + name, required=True)
    for command in ('build', 'preflight', 'apply', 'recover'):
        p = sub.add_parser(command);p.add_argument('--bundle', type=Path, required=True)
        if command in ('apply', 'recover'):
            p.add_argument('--apply', action='store_true')
            p.add_argument('--manifest-sha256', required=True)
            p.add_argument('--image-receipt-sha256', required=True)
        if command == 'recover':
            p.add_argument('--action', choices=('service', 'config'), required=True)
    p = sub.add_parser('restart');p.add_argument('--release', type=Path, required=True);p.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        globals()[args.command](args)
    except Exception as error:
        # Exception text comes from checks; subprocess output/HTTP bodies are never printed.
        print(json.dumps({'ok': False, 'type': type(error).__name__, 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
