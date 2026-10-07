#!/usr/bin/env python3
"""Use codex.task CLI v1 for a frozen multi-repository release.

This adapter owns no task storage and never merges or pushes Git itself.
"""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess


def command():
    configured = os.environ.get('CODEX_TASK_CALLBACK')
    if configured:
        return shlex.split(configured)
    executable = shutil.which('codex.task')
    if not executable:
        raise ValueError('codex.task is required for native repository delivery')
    return [executable]


def scoped(prefix, owner):
    if '-C' in prefix:
        if Path(prefix[prefix.index('-C') + 1]).resolve() != Path(owner).resolve():
            raise ValueError('task callback belongs to another workspace')
        return prefix
    return [*prefix, '-C', str(owner)]


def query(prefix, owner, task):
    result = subprocess.run([*scoped(prefix, owner), 'show', '--task', task, '--json'],
                            check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    if payload.get('schemaVersion') != 1 or payload.get('kind') != 'task':
        raise ValueError('unsupported codex.task public query protocol')
    return payload['task']


def uses_native_backend(owner, task):
    record = query(command(), owner, task)
    entries = record.get('repositories', {})
    native = any(k != 'primary' and e.get('mode') == 'write' and e.get('backend') == 'native'
                 for k, e in entries.items())
    if native:
        return True
    if record.get('repository_management') == 'native':
        raise ValueError('register the required companion repository through the task session before preparing publication')
    return False  # An existing task keeps its original delivery backend.


def freeze(owner, task, story, system, story_candidate, system_candidate):
    prefix = command()
    record = query(prefix, owner, task)
    repos = record.get('repositories', {})
    matches = [key for key, entry in repos.items() if entry.get('mode') == 'write'
               and Path(owner, entry['worktree']['path']).resolve() == Path(system).resolve()]
    if len(matches) != 1 or repos[matches[0]].get('backend') != 'native':
        raise ValueError('system workspace is not owned by this native task')
    if Path(owner, repos['primary']['worktree']['path']).resolve() != Path(story).resolve():
        raise ValueError('story workspace differs from task ownership')
    value = {'backend': 'codex.task', 'command': prefix, 'owner': str(owner), 'task': task,
             'repositories': {'primary': story_candidate, matches[0]: system_candidate},
             'system_repository': matches[0]}
    validate(value)
    return value


def validate(value, delivered=False, require_push=False):
    if value.get('backend') != 'codex.task':
        raise ValueError('not a native delivery receipt')
    record = query(value['command'], value['owner'], value['task'])
    frozen = record.get('repository_preparation') or {}
    for key, candidate in value['repositories'].items():
        entry = record.get('repositories', {}).get(key, {})
        stage = entry.get('integration') or {}
        if stage.get('candidate_commit') != candidate or (frozen.get(key, {}).get('integration') or {}).get('candidate_commit') != candidate:
            raise ValueError('task candidate changed; prepare the publication bundle again')
        if delivered and stage.get('phase') != 'applied':
            raise ValueError('repository Git integration is incomplete')
        git_delivery = entry.get('git_delivery')
        if delivered and ((git_delivery and git_delivery.get('phase') != 'pushed') or
                          (require_push and not git_delivery)):
            raise ValueError('repository push is incomplete or was not prepared')
    return record


def apply(value, receipt=None):
    validate(value)
    subprocess.run([*scoped(value['command'], value['owner']), '_deliver', '--task', value['task'],
                    '--note', '执行已确认冻结发布包的多仓库 Git 交付；正式发布与验收随后完成'],
                   check=True, capture_output=True, text=True)
    record = validate(value, delivered=True)
    key = value['system_repository']
    result = {'backend': 'codex.task', 'candidate': value['repositories'][key],
              'target_after': value['repositories'][key], 'preflight_only': False,
              'repositories': record['repositories'], 'task_completed': False}
    if receipt:
        path = Path(receipt)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def push_receipt(value):
    record = validate(value, delivered=True, require_push=True)
    entry = record['repositories'][value['system_repository']]['git_delivery']
    return {'backend': 'codex.task', 'system_candidate': entry['candidate_commit'],
            'remote': entry['remote'], 'ref': entry['remote_ref'], 'remote_verified': True,
            'push_verified': True, 'force': False}
