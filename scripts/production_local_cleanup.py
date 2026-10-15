#!/usr/bin/env python3
"""Prepare and apply hash-pinned redactions of identified local production copies."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

from generated_candidates_inventory import paths, sha


def protected(path):
    parts = Path(path).parts
    return (any(p in parts for p in ('.git', 'imports', 'skills', 'filmcraft', 'seedance-handbook'))
            or any(p.startswith(('screenplay-', 'refinement-', 'novel-writing', 'reader-review',
                                  'story-structure', 'third-sacrifice', 'structure-comment-revision')) for p in parts)
            or '/reports/task-20261013-0010/' in '/'+path
            or '/.codex-task/inputs/' in '/'+path or '/.codex-task/launch/' in '/'+path
            or path.endswith('.codex-task/tasks.json')
            or any(p.startswith('skill-cold-reader') for p in parts)
            or '/output/pdf/' in '/'+path
            or 'content' in parts or path.endswith('source-lock.json'))


def story_author(path):
    return any(p.startswith(('screenplay-', 'refinement-', 'novel-writing', 'reader-review',
                             'third-sacrifice', 'structure-comment-revision')) for p in Path(path).parts)


def owned_runtime(root, path):
    return '/.codex-task/worktrees/task-20261015-0001/.runtime/' in str(path)


def safe(root, rel):
    path = root/rel
    if Path(rel).is_absolute() or '..' in Path(rel).parts or any(p.is_symlink() for p in [path, *path.parents] if p == root or root in p.parents):
        raise ValueError('unsafe cleanup path: '+rel)
    if not path.resolve().is_relative_to(root):
        raise ValueError('cleanup path escaped project')
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--inventory', type=Path, required=True)
    p.add_argument('--reset-plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('action', choices=('prepare', 'apply', 'verify'))
    p.add_argument('--only-prefix')
    p.add_argument('--resume', action='store_true')
    a = p.parse_args()
    root = a.root.resolve(strict=True)
    output = a.output.resolve()
    sys.path.insert(0, str(a.system.resolve(strict=True)))
    from production_history_cleanup import clean, configure, framework, content_index, redact_database, stream_redact, text_records
    if a.action != 'prepare':
        result = collections.Counter()
        with (output/'files.jsonl').open() as source:
            for line in source:
                item = json.loads(line)
                if protected(item['path']) and not item.get('targeted_production_inputs'):
                    result['protected_story_or_method'] += 1
                    continue
                if a.only_prefix and not item['path'].startswith(a.only_prefix):
                    continue
                target = safe(root, item['path'])
                if item['action'] == 'delete':
                    if not target.exists():
                        result['already_absent'] += 1
                        continue
                    if sha(target) != item['before']:
                        raise ValueError('delete target changed: '+item['path'])
                    if a.action == 'apply':
                        target.unlink()
                        result['deleted'] += 1
                        result['deleted_bytes'] += item['bytes']
                    else:
                        result['remaining'] += 1
                else:
                    if not target.exists():
                        result['already_absent'] += 1
                        continue
                    actual = sha(target)
                    if actual == item['after']:
                        result['already_redacted'] += 1
                        continue
                    if actual != item['before']:
                        raise ValueError('redaction target changed: '+item['path'])
                    if a.action == 'apply':
                        staged = output/item['staged']
                        if sha(staged) != item['after']:
                            raise ValueError('staged redaction changed')
                        temporary = target.with_name(target.name+'.production-erasure-tmp')
                        if temporary.exists():
                            raise ValueError('previous replacement is unresolved: '+str(temporary))
                        shutil.copyfile(staged, temporary)
                        if sha(temporary) != item['after']:
                            raise ValueError('replacement copy mismatch')
                        os.chmod(temporary, item['mode'])
                        os.replace(temporary, target)
                        result['redacted'] += 1
                        result['redacted_original_bytes'] += item['bytes']
                    else:
                        result['remaining'] += 1
        print(json.dumps(result), flush=True)
        return
    if (output/'files.jsonl').exists() and not a.resume:
        raise ValueError('cleanup plan already exists; preserve exact prepared inputs')
    output.mkdir(parents=True, exist_ok=True)
    known = set(json.loads((a.inventory/'media-catalogue.json').read_text()))
    plan = json.loads(a.reset_plan.read_text())
    configure(plan)
    known.update(v['physical_sha256'] for v in plan['erased_files'].values() if v.get('physical_sha256'))
    known.update(v['sha256'] for v in plan['erased_files'].values())
    for name in ('engineering-derived-hashes.json',):
        x = a.inventory.parent/name
        if x.exists():
            known.update(json.loads(x.read_text()))
    known.add('b60925b5e5d07d52eaca435c688838463dc7026c3475ff3475cffc9b5eea6df9')
    cache = {}
    counts = collections.Counter()
    done = set()
    if a.resume and (output/'files.jsonl').exists():
        for line in (output/'files.jsonl').open():
            item = json.loads(line); done.add(item['path']); counts[item['action']] += 1
            if item['action'] == 'redact':
                cache[item['before']] = (item['staged'], item['after'], item['details'])
    with (output/'files.jsonl').open('a' if a.resume else 'w') as manifest:
        for path in paths(root):
            if owned_runtime(root, path) or output == path or output in path.parents or path.is_symlink():
                continue
            rel = str(path.relative_to(root))
            if rel in done or protected(rel):
                continue
            suffix = path.suffix.lower()
            if path.name.endswith(('.tar', '.tar.gz', '.tgz')):
                counts['archives_pending'] += 1
                continue
            is_media = suffix in ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.wav', '.mp3', '.mp4', '.mov', '.zip', '.ogg', '.flac', '.m4a')
            is_db = suffix in ('.sqlite3', '.db')
            is_json = suffix == '.json'
            is_text = suffix in ('.jsonl', '.log', '.stdout', '.txt')
            author_text = ('/production/audiovisual/' in '/'+rel and
                           (path.name.startswith('e') and path.stem[1:].isdigit() or '/text-handoffs/' in '/'+rel)
                           or path.name in ('prompt.txt', 'lyrics.txt', 'direction.md') and
                           any(s in rel for s in ('/lyria/', '/production/requests/', '/production/song-stage/')))
            if not (is_media or is_db or is_json or is_text or author_text):
                continue
            before = sha(path)
            action, staged, details = None, None, None
            if before in known or author_text and suffix not in ('.py', '.js') or path.name == 'read-cache.sqlite3':
                action = 'delete'
            elif is_media:
                continue
            elif is_db:
                if rel == '.runtime/review.sqlite3':
                    continue
                if before not in cache:
                    temporary = output/'current-database.sqlite3'
                    for leftover in (temporary, Path(str(temporary)+'-journal'), Path(str(temporary)+'-wal'), Path(str(temporary)+'-shm')):
                        if leftover.exists(): leftover.unlink()
                    shutil.copyfile(path, temporary)
                    info = redact_database(temporary)
                    if info:
                        after = sha(temporary)
                        staged = output/(after+'.redacted')
                        temporary.rename(staged)
                        cache[before] = (staged.name, after, info)
                    else:
                        temporary.unlink()
                        cache[before] = None
                if cache[before]:
                    staged, after, details = cache[before]
                    action = 'redact'
            elif is_json or is_text:
                if before not in cache:
                    temporary = output/'current-json.tmp'
                    if is_text:
                        try:
                            changed = text_records(path, temporary)
                        except UnicodeDecodeError:
                            temporary.unlink()
                            continue
                        if not changed:
                            temporary.unlink(); cache[before] = None; continue
                        details = {'redacted_text_records': changed}
                    elif path.name == 'objects.json' and path.parent.name == 'export':
                        graph_path = path.with_name('material-content.json')
                        graph = None
                        index_path = output/'current-content.sqlite3'
                        try:
                            if graph_path.exists():
                                graph = content_index(graph_path, index_path)
                            changed = framework(path, temporary, graph)
                        finally:
                            if graph:
                                graph.db.close()
                                index_path.unlink()
                        details = {'framework_rows_changed': changed, 'recovery': 'disabled'}
                    elif path.name == 'material-content.json' and path.parent.name == 'export':
                        temporary.write_text('{"format":"material-content-v1","material_content":[],"production_history_redacted":true}\n')
                        details = {'old_production_content_graph': 'removed; old recovery disabled'}
                    else:
                        if path.stat().st_size > 64*1024*1024:
                            changed = stream_redact(path, temporary)
                            details = {'streamed_fields_changed': changed}
                            if not changed:
                                temporary.unlink()
                                cache[before] = None
                                continue
                        else:
                            try:
                                old = json.loads(path.read_text())
                            except (ValueError, UnicodeDecodeError):
                                continue
                            new = clean(old)
                            if old == new:
                                cache[before] = None
                                continue
                            temporary.write_text(json.dumps(new, ensure_ascii=False, indent=2)+'\n')
                            details = {'production_fields': 'redacted'}
                    after = sha(temporary)
                    staged = output/(after+'.redacted')
                    if staged.exists():
                        temporary.unlink()
                    else:
                        temporary.rename(staged)
                    cache[before] = (staged.name, after, details)
                if cache[before]:
                    staged, after, details = cache[before]
                    action = 'redact'
            if not action:
                continue
            stat = path.stat()
            if sha(path) != before:
                raise ValueError('source changed during cleanup preparation: '+rel)
            item = {'path': rel, 'action': action, 'before': before, 'bytes': stat.st_size,
                    'dev': stat.st_dev, 'ino': stat.st_ino, 'nlink': stat.st_nlink, 'mode': stat.st_mode & 0o777}
            if action == 'redact':
                item.update(staged=staged, after=after, details=details)
            manifest.write(json.dumps(item, ensure_ascii=False)+'\n')
            manifest.flush()
            counts[action] += 1
            if sum(counts.values()) % 100 == 0:
                print(json.dumps(counts), flush=True)
    (output/'summary.json').write_text(json.dumps(counts, indent=2)+'\n')
    print(json.dumps(counts), flush=True)


if __name__ == '__main__':
    main()
