"""Prepare the reviewed production delta; method configuration travels separately.

The initialization snapshot stays unchanged. Only managed method definitions and
private method executions are excluded from this production-only comparison.
Their exact definitions are delivered by method_migration, not by this package.
"""
import argparse
import json
from pathlib import Path
import sys


def production_tables(before, after):
    from method_migration import CONFIG_FORMATS
    ignored = set()
    revisions = before['revisions'] + after['revisions']
    for row in revisions:
        body = json.loads(row['payload'])
        if (body.get('format') in CONFIG_FORMATS or
                body.get('private') is True and body.get('format') in
                ('managed-method-execution-v1', 'managed-method-artifact-v1')):
            ignored.add(row['object_id'])
    rids = {row['id'] for row in revisions if row['object_id'] in ignored}
    for table, field in (('objects', 'id'), ('revisions', 'object_id')):
        after[table] = [r for r in after[table] if r[field] not in ignored] + [
            r for r in before[table] if r[field] in ignored]
    unpublished = rids - {r['id'] for r in before['revisions']}
    if any(r['to_revision'] in unpublished and r['from_revision'] not in rids
           and not any(v == r for v in before['dependencies']) for r in after['dependencies']):
        raise ValueError('production depends on newly changed method data; deliver its exact binding first')
    after['dependencies'] = [r for r in after['dependencies'] if r['from_revision'] not in rids] + [
        r for r in before['dependencies'] if r['from_revision'] in rids]
    return before, after, sorted(ignored)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    from generation_publication import tables, publication_id
    from production_current_publication import build
    from generation_workspace import generation_root, isolated_instance, contained, write_json
    from publish_generation import copy_media
    root = generation_root(Path(__file__).resolve().parents[1])
    instance = isolated_instance(root, args.instance)
    output = contained(root, args.output)
    if output.exists():
        raise ValueError('use a new reviewed publication filename')
    before, after, ignored = production_tables(
        tables(instance/'.runtime/generation-base.sqlite3'),
        tables(instance/'.runtime/review.sqlite3'))
    plan = build(before, after)
    plan['review_origin'] = json.loads((instance/'.runtime/generation-base.json').read_text())
    copy_media(instance, root, plan['media'])
    write_json(root, output, plan)
    result = {'publication_id': publication_id(plan), 'scope': len(plan['scope']),
              'media': len(plan['media']), 'excluded_method_objects': ignored,
              'changes': {k: len(v) for k, v in plan['changes'].items()}}
    write_json(root, args.report, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'excluded_method_objects'}))


if __name__ == '__main__':
    main()
