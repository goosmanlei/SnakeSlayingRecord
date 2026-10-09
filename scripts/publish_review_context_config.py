#!/usr/bin/env python3
"""Publish the reviewed two-field configuration delta without importing a DB."""
import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import autonomous_optimization_release as base
from material_review_release import file_sha256


def verify_history(before, after, expected_body, expected_version):
    """Hash one complete row at a time; only PROJECT and its one event may change."""
    result = {}
    with closing(sqlite3.connect(before)) as old, closing(sqlite3.connect(after)) as new:
        old.row_factory = new.row_factory = sqlite3.Row
        schemas = [dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")) for db in (old, new)]
        base.require(schemas[0] == schemas[1], 'database schema changed')
        for table in schemas[0]:
            quoted = '"' + table.replace('"', '""') + '"'
            counters = []
            for db in (old, new):
                rows = db.execute('SELECT * FROM ' + quoted)
                counters.append(Counter(base.sha(base.canonical({'name': row['name']} if table == 'read_generations' else dict(row))) for row in rows
                    if not (table == 'configurations' and row['scope'] == 'PROJECT')
                    and not (table == 'configuration_events' and row['scope'] == 'PROJECT' and row['version'] == expected_version)))
            base.require(counters[0] == counters[1], 'unexpected row change: ' + table)
            result[table] = {'preserved': True, 'before': sum(counters[0].values()), 'after': sum(counters[1].values())}
            if table == 'read_generations':
                result[table]['derived_tokens_may_change'] = True
        record = new.execute("SELECT version,body FROM configurations WHERE scope='PROJECT'").fetchone()
        events = new.execute("SELECT body FROM configuration_events WHERE scope='PROJECT' AND version=?", (expected_version,)).fetchall()
        base.require(record['version'] == expected_version and json.loads(record['body']) == expected_body, 'PROJECT readback differs')
        base.require(len(events) == 1 and json.loads(events[0]['body']) == expected_body, 'PROJECT event differs')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--package', type=Path, default=Path('production/review-context/project-update.json'))
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    primary = base.primary(root)
    package_path = (root / args.package).resolve()
    package = base.read(package_path)
    base.require(package['format'] == 'review-context-project-update-v1' and package['scope'] == 'PROJECT', 'wrong package')
    base.require(set(package['updates']) == {'story_background', 'creative_background'}, 'unexpected configuration field')
    receipt = (root / args.receipt).resolve()
    base.require((root / '.runtime').resolve() in receipt.parents and not receipt.is_symlink(), 'task-local receipt required')
    with base.publication_locks({'story_main': str(primary), 'system_main': str(base.primary(args.system))}):
        before = base.project()
        expected = {**before['body'], **package['updates']}
        if before['version'] == package['expected_version'] + 1 and base.sha(base.canonical(before['body'])) == package['expected_result_sha256']:
            base.require((receipt / 'before.sqlite3').is_file(), 'applied configuration has no original receipt; verify its publisher')
        else:
            base.require(before['version'] == package['expected_version'] and base.sha(base.canonical(before['body'])) == package['expected_body_sha256'], 'PROJECT drifted; do not overwrite')
        base.require(base.sha(base.canonical(expected)) == package['expected_result_sha256'], 'candidate body differs')
        if not args.apply:
            print(json.dumps({'preflight_only': True, 'expected_version': package['expected_version'], 'fields': list(package['updates'])})); return
        relative = package_path.relative_to(root).as_posix()
        head = base.git(primary, 'rev-parse', 'HEAD')
        base.require(base.git_file(primary, head, relative) == package_path.read_bytes(), 'package is not merged into primary')
        base.require(base.git_file(primary, head, 'scripts/publish_review_context_config.py') == Path(__file__).read_bytes(), 'publisher differs from merged version')
        receipt.mkdir(parents=True, exist_ok=True)
        if not (receipt / 'before.sqlite3').exists():
            base.snapshot(primary / '.runtime/review.sqlite3', receipt / 'before.sqlite3')
            base.save(receipt / 'intent.json', {'task': package['task'], 'package_sha256': base.sha(package_path.read_bytes()), 'before_sha256': file_sha256(receipt / 'before.sqlite3')})
        intent = base.read(receipt / 'intent.json')
        base.require(intent['package_sha256'] == base.sha(package_path.read_bytes()) and intent['before_sha256'] == file_sha256(receipt / 'before.sqlite3'), 'receipt drifted')
        if (receipt / 'result.json').exists():
            result = base.read(receipt / 'result.json')
            base.require(result['project_sha256'] == base.sha(base.canonical(before)), 'completed result differs from current PROJECT')
            print(json.dumps({'status': 'already_published', 'project_version': before['version']})); return
        if before['version'] == package['expected_version']:
            base.http('/api/configurations/PROJECT', {'expected_version': package['expected_version'], 'updates': package['updates']})
        current = base.project()
        base.require(current['version'] == package['expected_version'] + 1 and current['body'] == expected, 'configuration result unknown; query before retry')
        after = receipt / 'after.sqlite3'
        if not after.exists():
            base.snapshot(primary / '.runtime/review.sqlite3', after)
        history = verify_history(receipt / 'before.sqlite3', after, expected, current['version'])
        result = {'status': 'published', 'task': package['task'], 'project_version': current['version'], 'project_sha256': base.sha(base.canonical(current)), 'history': history}
        base.save(receipt / 'result.json', result)
        print(json.dumps({'status': result['status'], 'project_version': current['version'], 'all_other_rows_preserved': True}))


if __name__ == '__main__':
    main()
