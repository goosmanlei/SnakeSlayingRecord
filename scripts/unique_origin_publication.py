"""Prepare the reviewed production delta; method configuration travels separately.

The initialization snapshot stays unchanged. Only managed method definitions and
private method executions are excluded from this production-only comparison.
Their exact definitions are delivered by method_migration, not by this package.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def comparison_basis(root, instance, screenplay=None, method_registry=None, screenplay_records=None):
    """Rehearse separately published prerequisites on a copy of the old basis.

    This does not publish to the formal instance or alter the initialization
    snapshot. The content increment still checks exact prerequisite revisions.
    """
    from generation_publication import backup
    from generation_workspace import contained
    original = instance / '.runtime/generation-base.sqlite3'
    if not screenplay and not method_registry:
        return original, None
    before_hash = file_sha256(original)
    directory = contained(root, Path('.runtime/generation/prepares') / uuid.uuid4().hex / 'basis')
    (directory / '.runtime').mkdir(parents=True)
    derived = directory / '.runtime/review.sqlite3'
    backup(original, derived)
    prerequisites = {'initialization_sha256': before_hash}
    if screenplay:
        from publish_screenplay import publish
        documents = screenplay if isinstance(screenplay, (list, tuple)) else [screenplay]
        editions = []
        for document in documents:
            source = contained(root, document)
            receipt = publish(root, directory, apply=True, document_path=source.relative_to(root).as_posix(), records_path=screenplay_records)
            editions.append({
                'document': source.relative_to(root).as_posix(), 'sha256': file_sha256(source),
                'receipt': receipt,
            })
        # Preserve the existing single-edition receipt shape. Multiple immutable
        # editions must all be rehearsed, including earlier generation inputs.
        if len(editions) == 1:
            prerequisites['screenplay'] = editions[0]
        else:
            prerequisites['screenplays'] = editions
        if screenplay_records:
            source = contained(root, screenplay_records)
            prerequisites['screenplay_records'] = {'path':source.relative_to(root).as_posix(), 'sha256':file_sha256(source)}
    if method_registry:
        from method_migration import apply
        from material_model_io import read_json
        source = contained(root, method_registry)
        registry = read_json(source)
        result = apply(derived, registry)
        prerequisites['methods'] = {
            'registry': source.relative_to(root).as_posix(), 'sha256': file_sha256(source),
            'registry_sha256': registry['sha256'], 'receipt': result,
        }
    if file_sha256(original) != before_hash:
        raise ValueError('initialization snapshot changed during prerequisite rehearsal')
    return derived, {**prerequisites, 'rehearsal': directory.relative_to(root).as_posix()}


def production_tables(before, after):
    try: from .method_migration import CONFIG_FORMATS
    except ImportError: from method_migration import CONFIG_FORMATS
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
    # File histories travel with the same exact method registry. They are
    # configuration, not generation data, and must never be partly published.
    packages = {r['revision_id'] for side in (before, after)
                for r in side.get('method_file_packages', []) if r['object_id'] in ignored}
    for table, field, excluded in (
            ('method_file_versions', 'object_id', ignored),
            ('method_file_packages', 'object_id', ignored),
            ('method_file_members', 'package_revision', packages)):
        if table in before:
            after[table] = [r for r in after[table] if r[field] not in excluded] + [
                r for r in before[table] if r[field] in excluded]
    return before, after, sorted(ignored)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--screenplay', type=Path, action='append',
                        help='Reviewed screenplay appended separately before the production increment; repeat in publication order')
    parser.add_argument('--method-registry', type=Path,
                        help='Exact method registry delivered separately before the production increment')
    parser.add_argument('--screenplay-records', type=Path,
                        help='Reviewed immutable screenplay rows, avoiding export of private creative steps')
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
    basis, prerequisites = comparison_basis(root, instance, args.screenplay, args.method_registry, args.screenplay_records)
    before, after, ignored = production_tables(
        tables(basis),
        tables(instance/'.runtime/review.sqlite3'))
    plan = build(before, after)
    plan['review_origin'] = json.loads((instance/'.runtime/generation-base.json').read_text())
    if prerequisites:
        plan['prerequisites'] = {k: v for k, v in prerequisites.items() if k != 'rehearsal'}
    copy_media(instance, root, plan['media'])
    write_json(root, output, plan)
    result = {'publication_id': publication_id(plan), 'scope': len(plan['scope']),
              'media': len(plan['media']), 'excluded_method_objects': ignored,
              'changes': {k: len(v) for k, v in plan['changes'].items()}}
    if prerequisites:
        result['prerequisites'] = prerequisites
    write_json(root, args.report, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'excluded_method_objects'}))


if __name__ == '__main__':
    main()
