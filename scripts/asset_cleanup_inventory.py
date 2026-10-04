#!/usr/bin/env python3
"""Read-only physical inventory. Decisions come from reviewed prefix rules.

Does not follow symlinks, read credentials, delete files, or infer obsolescence.
Git metadata and worktrees are inventoried, never treated as cleanup candidates.
Paths in the public output are relative to named roots. This inventory's own
outputs have an explicit exclusion to avoid self-reference.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)


def worktrees(root):
    result = []
    for section in git(root, 'worktree', 'list', '--porcelain').decode().split('\n\n'):
        row = dict(line.split(' ', 1) if ' ' in line else (line, True)
                   for line in section.splitlines())
        if 'worktree' in row:
            result.append(row)
    return result


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def inventory(story, system, output, policies):
    repositories = {'story': story.resolve(), 'system': system.resolve()}
    roots = dict(repositories)
    all_worktrees = []
    for repo, path in repositories.items():
        for row in worktrees(path):
            item = {**row, 'repository': repo}
            all_worktrees.append(item)
    # A registered external worktree can contain another repository's worktree.
    # Add ancestors first so no physical member is counted twice.
    for row in sorted(all_worktrees, key=lambda r: (len(Path(r['worktree']).parts), r['worktree'])):
        p = Path(row['worktree'])
        if p.exists() and not any(p == r or r in p.parents for r in roots.values()):
            roots[f"{row['repository']}-external-{len(roots)-1}"] = p
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Rules are reviewed conclusions, not deletion instructions. Longest path wins.
    rules = sorted(policies['rules'], key=lambda r: len(r['prefix']), reverse=True)
    rules_by_id = {r['id']: r for r in rules}
    if len(rules_by_id) != len(rules):
        raise ValueError('duplicate rule id')
    exclusions = [(repositories[e['root']] / e['path']).resolve() for e in policies.get('exclude', [])]
    if not any(output == e or e in output.parents for e in exclusions):
        raise ValueError('inventory output must be explicitly excluded')
    counts, sizes, decisions = Counter(), Counter(), Counter()
    errors, excluded, rule_counts = [], [], Counter()
    workspace_metadata = []
    for row in all_worktrees:
        p = Path(row['worktree'])
        owner = next(((name, root) for name, root in roots.items() if p == root or root in p.parents), None)
        workspace_metadata.append({k: v for k, v in row.items() if k != 'worktree'} | {
            'root': owner[0] if owner else None,
            'path': str(p.relative_to(owner[1])) if owner else p.name,
            'exists': p.exists(),
        })
    ws_paths = sorted([Path(x['worktree']) for x in all_worktrees if Path(x['worktree']).exists()], key=lambda p: len(p.parts), reverse=True)
    tracked = {}
    for path in ws_paths:
        tracked[path] = set(git(path, 'ls-files', '-z').decode().split('\0')) - {''}
    manifest = output / 'files.jsonl.gz'
    with manifest.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as archive:
        for alias, root in roots.items():
            stack = [root]
            while stack:
                folder = stack.pop()
                try:
                    entries = sorted(os.scandir(folder), key=lambda e: e.name)
                except OSError as exc:
                    errors.append({'root': alias, 'path': str(folder.relative_to(root)), 'error': type(exc).__name__})
                    continue
                for entry in entries:
                    path = Path(entry.path)
                    rel = path.relative_to(root).as_posix()
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        errors.append({'root': alias, 'path': rel, 'error': type(exc).__name__})
                        continue
                    kind = 'directory' if stat.S_ISDIR(info.st_mode) else 'symlink' if stat.S_ISLNK(info.st_mode) else 'file' if stat.S_ISREG(info.st_mode) else 'special'
                    rule = next((r for r in rules if r['root'] in (alias, '*') and (not r['prefix'] or rel == r['prefix'] or rel.startswith(r['prefix'].rstrip('/') + '/'))), None)
                    workspace = next((p for p in ws_paths if path == p or p in path.parents), None)
                    row = {'root': alias, 'path': rel, 'kind': kind, 'bytes': info.st_size,
                           'allocated_bytes': info.st_blocks * 512, 'mtime_ns': info.st_mtime_ns,
                           'mode': stat.S_IMODE(info.st_mode), 'links': info.st_nlink,
                           'tracked': bool(workspace and path.relative_to(workspace).as_posix() in tracked[workspace]),
                           'rule': rule['id'] if rule else None, 'decision': rule['decision'] if rule else 'pending'}
                    if kind == 'symlink':
                        target = Path(os.readlink(path))
                        if target.is_absolute():
                            owner = next(((n, r) for n, r in roots.items() if target == r or r in target.parents), None)
                            row['target'] = {'root': owner[0], 'path': target.relative_to(owner[1]).as_posix()} if owner else {'external': True, 'name': target.name}
                        else:
                            row['target'] = str(target)
                    skipped = any(path == e for e in exclusions)
                    if skipped:
                        row['children_excluded'] = True
                        excluded.append({'root': alias, 'path': rel})
                    elif kind == 'directory':
                        stack.append(path)
                    archive.write((canonical(row) + '\n').encode())
                    counts[kind] += 1
                    sizes[kind] += info.st_size
                    decisions[row['decision']] += 1
                    rule_counts[row['rule'] or 'UNRESOLVED'] += 1
    summary = {'format': 'asset-necessity-inventory-v1', 'captured_at': datetime.now(timezone.utc).isoformat(),
               'counting': 'Each directory entry is counted once by path; file logical bytes are not unique storage or reclaimable space. Hardlinks and APFS clones may share storage. Excluded subtree children are outside the denominator.',
               'roots': {name: {'repository': 'story' if name.startswith('story') else 'system',
                                'location': os.path.relpath(root, repositories['story'])} for name, root in roots.items()},
               'baseline_commits': {name: git(root, 'rev-parse', 'HEAD').decode().strip() for name, root in repositories.items()},
               'worktrees': workspace_metadata, 'counts': dict(counts), 'logical_bytes': dict(sizes),
               'decisions': dict(decisions), 'rule_counts': dict(rule_counts), 'errors': errors,
               'excluded': excluded, 'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest()}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--story-main', type=Path, required=True)
    parser.add_argument('--system-main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--policies', type=Path, required=True)
    args = parser.parse_args()
    summary = inventory(args.story_main, args.system_main, args.output, json.loads(args.policies.read_text()))
    print(json.dumps({k: summary[k] for k in ('counts', 'decisions', 'errors', 'excluded', 'manifest_sha256')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
