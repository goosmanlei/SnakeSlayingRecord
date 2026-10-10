#!/usr/bin/env python3
"""Rehearse a generation increment; publish only files already merged into main."""
import argparse
import fcntl
import json
from pathlib import Path
import re

try:
    from .generation_workspace import (generation_root, contained, publication_target,
                                       verify_integrated, verify_media, write_json)
    from .generation_publication import apply_plan, backup, connect, publication_id, receipt
except ImportError:
    from generation_workspace import (generation_root, contained, publication_target,
                                      verify_integrated, verify_media, write_json)
    from generation_publication import apply_plan, backup, connect, publication_id, receipt

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility

ROOT = Path(__file__).resolve().parents[1]


def copy_media(root, target, entries):
    """Used only for an isolated review/rehearsal target."""
    verify_media(root, entries)
    for entry in entries:
        path = contained(target, Path('export/assets') / entry['file'])
        path.parent.mkdir(parents=True, exist_ok=True)
        source = contained(root, Path('export/assets') / entry['file'])
        if path.exists():
            if material_read_bytes(path) != material_read_bytes(source):
                raise ValueError('existing original differs')
        else:
            with path.open('xb') as stream:
                stream.write(material_read_bytes(source))


def run_publication(root, target, package, run_name, *, apply=False, source_commit=None,
                    apply_fn=apply_plan, prepare_fn=None, entries=None):
    root = generation_root(root)
    package = contained(root, package)
    document = material_read_json(package)
    target, formal = publication_target(root, target)
    db_path = target / '.runtime/review.sqlite3'
    if not db_path.is_file():
        raise ValueError('publication requires an existing review database')
    entries = entries if entries is not None else document['media']
    if document.get('format')=='production-current-publication-v1' and apply_fn is apply_plan:
        apply_fn=lambda db,plan:apply_plan(db,plan,media_root=root)
    verify_media(root, entries)
    if apply and formal:
        verify_integrated(root, target, source_commit, package, entries)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', run_name):
        raise ValueError('run name must be a safe, unique directory name')
    run = contained(root, Path('.runtime/generation/publications') / run_name)
    run.mkdir(parents=True, exist_ok=False)
    pid = publication_id(document)
    with contained(target, '.runtime/publication.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Recheck the merged bytes while holding the publisher lock.
        if apply and formal:
            verify_integrated(root, target, source_commit, package, entries)
        backup(db_path, run / 'before.sqlite3')
        db = connect(run / 'before.sqlite3')
        try:
            previous = receipt(db, pid)
        finally:
            db.close()
        if previous is not None:
            result = {'applied': True, 'already_published': True, 'scope': previous,
                      'publication_id': pid, 'source_commit': source_commit}
            write_json(root, run / 'applied.json', result)
            return result
        prepared = prepare_fn(run / 'before.sqlite3', run, document) if prepare_fn else document
        backup(run / 'before.sqlite3', run / 'rehearsal.sqlite3')
        db = connect(run / 'rehearsal.sqlite3', readonly=False)
        try:
            rehearsal = apply_fn(db, prepared)
        finally:
            db.close()
        result = {'applied': False, 'already_published': False, 'publication_id': pid,
                  'source_commit': source_commit, 'scope': rehearsal}
        write_json(root, run / 'preflight.json', result)
        if apply:
            if not formal:
                copy_media(root, target, entries)
            db = connect(db_path, readonly=False)
            try:
                result['scope'] = apply_fn(db, prepared)
            finally:
                db.close()
            # This external receipt is recoverable from the transaction journal.
            result['applied'] = True
            write_json(root, run / 'transaction.json', result)
            backup(db_path, run / 'after.sqlite3')
            write_json(root, run / 'applied.json', result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--source-commit')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = run_publication(args.workspace, args.instance, args.package, args.run_name,
                             apply=args.apply, source_commit=args.source_commit)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
