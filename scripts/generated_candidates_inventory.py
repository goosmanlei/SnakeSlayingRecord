#!/usr/bin/env python3
"""Read-only local candidate inventory. Emit exact files, never delete by glob."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tarfile

MEDIA = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.wav', '.mp3', '.mp4', '.mov', '.webm', '.zip', '.svg'}
SKIP = {'.git', '.venv', 'node_modules', '__pycache__'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def paths(root):
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP and not (Path(base)/d).is_symlink()]
        for name in files:
            yield Path(base)/name


def components(payload):
    if payload.get('format') not in ('production-asset-v1', 'production-retirement-v1'):
        return
    for item in payload.get('components', []) + payload.get('former_components', []):
        if item.get('role') in ('original', 'preview', 'thumbnail', 'proxy'):
            yield item


def catalogue(root):
    from review_desk.material_content_stream import members
    known = {}
    failures = []
    for path in paths(root):
        if path.is_symlink():
            continue
        try:
            if path.name == 'objects.json' and path.parent.name == 'export':
                rows = members(path, 'revisions')
            elif path.suffix in ('.sqlite3', '.db'):
                connection = sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)
                try:
                    if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='revisions'").fetchone():
                        continue
                    for raw, in connection.execute("SELECT payload FROM revisions WHERE json_extract(payload,'$.format') IN ('production-asset-v1','production-retirement-v1')"):
                        for item in components(json.loads(raw)):
                            known[item['sha256']] = {**item, 'evidence': str(path.relative_to(root))}
                finally:
                    connection.close()
                continue
            else:
                continue
            for row in rows:
                for item in components(json.loads(row['payload'])):
                    known[item['sha256']] = {**item, 'evidence': str(path.relative_to(root))}
        except (ValueError, KeyError, sqlite3.DatabaseError) as exc:
            failures.append({'path': str(path.relative_to(root)), 'error': str(exc)})
    return known, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archives', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    known, failures = catalogue(root)
    (output/'media-catalogue.json').write_text(json.dumps(known, ensure_ascii=False, indent=2)+'\n')
    (output/'catalogue-errors.json').write_text(json.dumps(failures, ensure_ascii=False, indent=2)+'\n')
    known_sizes = {v['bytes'] for v in known.values()}
    counts = collections.Counter(); sizes = collections.Counter(); archive_paths = []
    with (output/'files.jsonl').open('w') as target:
        for path in paths(root):
            if output == path or output in path.parents:
                continue
            stat = path.lstat(); rel = str(path.relative_to(root))
            item = {'path': rel, 'bytes': stat.st_size, 'dev': stat.st_dev, 'ino': stat.st_ino,
                    'nlink': stat.st_nlink, 'mtime_ns': stat.st_mtime_ns}
            if path.is_symlink():
                item.update(disposition='symlink', target=os.readlink(path))
            else:
                suffix = path.suffix.lower()
                if path.name.endswith(('.tar', '.tar.gz', '.tgz')):
                    item['disposition'] = 'archive-review'; archive_paths.append(path)
                elif suffix in MEDIA or stat.st_size in known_sizes:
                    checksum = sha(path); item['sha256'] = checksum
                    item['disposition'] = 'candidate' if checksum in known else 'media-review' if suffix in MEDIA else 'other'
                    if checksum in known:
                        item['identity_evidence'] = known[checksum]['evidence']
                else:
                    item['disposition'] = 'other'
            counts[item['disposition']] += 1; sizes[item['disposition']] += stat.st_size
            target.write(json.dumps(item, ensure_ascii=False)+'\n')
    archive_counts = collections.Counter()
    if args.archives:
        with (output/'archive-members.jsonl').open('w') as target:
            for path in archive_paths:
                print('archive', str(path.relative_to(root)), flush=True)
                with tarfile.open(path, 'r|*') as archive:
                    for member in archive:
                        item = {'archive': str(path.relative_to(root)), 'member': member.name,
                                'bytes': member.size, 'type': member.type.decode('ascii', errors='replace')}
                        if member.isfile() and Path(member.name).suffix.lower() in MEDIA:
                            h = hashlib.sha256()
                            stream = archive.extractfile(member)
                            for block in iter(lambda: stream.read(1024*1024), b''):
                                h.update(block)
                            item['sha256'] = h.hexdigest()
                            item['disposition'] = 'candidate' if item['sha256'] in known else 'media-review'
                        else:
                            item['disposition'] = 'other'
                        archive_counts[item['disposition']] += 1
                        target.write(json.dumps(item, ensure_ascii=False)+'\n')
    summary = {'catalogue_media': len(known), 'catalogue_errors': len(failures), 'files': dict(counts),
               'bytes': dict(sizes), 'archives': len(archive_paths), 'archive_members': dict(archive_counts)}
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
