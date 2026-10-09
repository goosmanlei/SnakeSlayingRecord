#!/usr/bin/env python3
"""Publish exact author evidence as additive GUIDANCE; never copy a preview DB."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import autonomous_optimization_release as base

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'production/comment-review/evidence.json'


def preserved(before, after, identities):
    """Stream complete old rows; only the named evidence objects may be added."""
    result = {}
    with closing(sqlite3.connect(before)) as old, closing(sqlite3.connect(after)) as new:
        old.row_factory = new.row_factory = sqlite3.Row
        schemas = [dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")) for db in (old, new)]
        base.require(schemas[0] == schemas[1], 'database schema changed')
        revisions = set(row[0] for row in new.execute(
            'SELECT id FROM revisions WHERE object_id IN (%s)' % ','.join('?' * len(identities)), tuple(identities)))
        for table in schemas[0]:
            def included(row):
                if table == 'objects': return row['id'] not in identities
                if table == 'revisions': return row['object_id'] not in identities
                if table == 'dependencies': return row['from_revision'] not in revisions
                return True
            counts = []
            for db in (old, new):
                rows = db.execute('SELECT * FROM "' + table.replace('"', '""') + '"')
                counts.append(Counter(hashlib.sha256(base.canonical(
                    {'name': r['name']} if table == 'read_generations' else dict(r))).hexdigest()
                    for r in rows if included(r)))
            base.require(counts[0] == counts[1], 'unexpected historical row change: ' + table)
            result[table] = {'preserved': True, 'rows': sum(counts[0].values())}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--instance', type=Path)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--apply', action='store_true')
    a = p.parse_args()
    primary = base.primary(ROOT)
    target = a.instance.resolve() if a.instance else primary
    formal = target == primary
    receipt = (ROOT / a.receipt).resolve()
    base.require((ROOT / '.runtime').resolve() in receipt.parents and not receipt.is_symlink(), 'task-local receipt required')
    if not formal:
        base.require((ROOT / '.runtime').resolve() in target.parents and target != receipt, 'isolated task instance required')
    package_path = ROOT / PACKAGE
    raw = package_path.read_bytes()
    documents = json.loads(raw)
    for document in documents:
        source = (ROOT / document['provenance']['file']).resolve()
        base.require(ROOT in source.parents and not source.is_symlink(), 'managed evidence provenance required')
        base.require(hashlib.sha256(source.read_bytes()).hexdigest() == document['provenance']['sha256'], 'author source checksum differs')
    sys.path.insert(0, str(a.system.resolve()))
    from review_desk.store import Store
    from review_desk.comment_review import import_evidence
    if not a.apply:
        with closing(Store.open_readonly(target / '.runtime/review.sqlite3')) as store:
            result = import_evidence(store, documents, validate_only=True)
        print(json.dumps({'preflight_only': True, **result})); return
    with base.publication_locks({'story_main': str(primary), 'system_main': str(base.primary(a.system))}):
        if formal:
            head = base.git(primary, 'rev-parse', 'HEAD')
            for name in [PACKAGE, 'scripts/publish_comment_evidence.py', *{d['provenance']['file'] for d in documents}]:
                base.require(base.git_file(primary, head, name) == (ROOT / name).read_bytes(), 'unmerged publisher or evidence: ' + name)
        receipt.mkdir(parents=True, exist_ok=True)
        identity = hashlib.sha256(raw).hexdigest()
        if (receipt / 'intent.json').exists():
            intent = base.read(receipt / 'intent.json')
            base.require(intent['package_sha256'] == identity and intent['target'] == str(target), 'publication receipt differs')
        else:
            base.require(not (receipt / 'before.sqlite3').exists(), 'unidentified partial publication snapshot')
            base.snapshot(target / '.runtime/review.sqlite3', receipt / 'before.sqlite3')
            base.save(receipt / 'intent.json', {'task': 'task-20261009-0012', 'package_sha256': identity, 'target': str(target)})
        with closing(Store(target / '.runtime/review.sqlite3')) as store:
            result = import_evidence(store, documents)
        if not (receipt / 'after.sqlite3').exists():
            base.snapshot(target / '.runtime/review.sqlite3', receipt / 'after.sqlite3')
        history = preserved(receipt / 'before.sqlite3', receipt / 'after.sqlite3', {d['id'] for d in documents})
        base.save(receipt / 'result.json', {'package_sha256': identity, 'target': str(target), **result, 'history': history})
        print(json.dumps({**result, 'all_original_rows_preserved': True}))


if __name__ == '__main__': main()
