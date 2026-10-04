"""Read-only task-0009 verifier, independent of review_desk decoding code.

Inputs: original export, migrated instance, pre-migration source hash inventory.
The optional output file is the only write. No service or browser operations.
"""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import zlib


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def display_path(value):
    path = Path(value)
    try:
        return str(path.relative_to(Path.cwd())) if path.is_absolute() else str(path)
    except ValueError:
        return str(path)


class Decoder:
    def __init__(self, rows):
        self.nodes = {}
        self.cache = {}
        self.types = Counter()
        for row in rows:
            assert sha(row['body'].encode()) == row['id'], ('content checksum', row['id'])
            assert row['id'] not in self.nodes
            node = json.loads(row['body'])
            assert len(node) == 1
            self.types[next(iter(node))] += 1
            self.nodes[row['id']] = node

    def expand(self, key, visiting=None):
        if key in self.cache:
            return self.cache[key]
        visiting = set() if visiting is None else visiting
        assert key not in visiting, ('cycle', key)
        visiting.add(key)
        node = self.nodes[key]
        if 'value' in node:
            result = node['value']
        elif 'array' in node:
            result = [self.expand(child, visiting) for child in node['array']]
        elif 'object' in node:
            assert len({k for k, _ in node['object']}) == len(node['object'])
            result = {k: self.expand(child, visiting) for k, child in node['object']}
        elif 'archive_recipe' in node:
            result = node['archive_recipe']
        elif 'archive_recipe_zlib' in node:
            result = json.loads(zlib.decompress(base64.b64decode(node['archive_recipe_zlib'], validate=True)))
            if isinstance(result, dict):
                assert set(result) == {'tokens', 'order'}
                assert all(type(index) is int and 0 <= index < len(result['tokens']) for index in result['order'])
                result = [result['tokens'][index] for index in result['order']]
        else:
            raise AssertionError(('unknown node', key))
        visiting.remove(key)
        # Large recipes are deliberately not retained after their file check.
        if not any(name.startswith('archive_recipe') for name in node):
            self.cache[key] = result
        return result

    def archive(self, document):
        assert document['format'] == 'material-archive-reference-v1'
        pieces = document.get('pieces') if 'pieces' in document else self.expand(document['recipe'])
        parts = []
        for piece in pieces:
            assert set(piece) <= {'content', 'archive', 'encoding', 'edits'}
            assert ('content' in piece) != ('archive' in piece)
            value = self.archive(piece['archive']).decode('utf-8') if 'archive' in piece else self.expand(piece['content'])
            assert isinstance(value, str)
            encoding = piece['encoding']
            assert encoding in ('text', 'json-ascii', 'json-utf8')
            token = value if encoding == 'text' else json.dumps(value, ensure_ascii=encoding == 'json-ascii')
            previous = len(token) + 1
            for start, end, replacement in reversed(piece.get('edits', [])):
                assert isinstance(start, int) and isinstance(end, int) and 0 <= start <= end < previous
                token = token[:start] + replacement + token[end:]
                previous = start
            parts.append(token)
        raw = ''.join(parts).encode('utf-8')
        assert len(raw) == document['bytes'] and sha(raw) == document['sha256']
        return raw

    def payload(self, raw):
        value = json.loads(raw)
        if '_material_fields' not in value:
            return raw
        value = dict(value)
        fields = self.expand(value.pop('_material_fields'))
        original = value.pop('_material_raw', None)
        assert not set(value).intersection(fields)
        value.update(fields)
        if original:
            result = self.archive(self.expand(original)).decode('utf-8')
            assert json.loads(result) == value
            return result
        return canonical(value)


def check(before, after, originals, coverage_path):
    export = after / 'export'
    package = json.loads((after / 'migration.json').read_text())
    plan = package['migration'] if package.get('format') == 'material-model-package-v1' else package
    inventory = json.loads(originals.read_text())
    # A completed evidence file embeds the original hashes, so later reviewers
    # can rerun against that committed evidence after the runtime inventory expires.
    original_files = inventory.get('files') or {row['path']: row for row in inventory['archives']}
    prior = json.loads((before / 'objects.json').read_text())
    current = json.loads((export / 'objects.json').read_text())
    content = json.loads((export / 'material-content.json').read_text())
    decoder = Decoder(content['material_content'])
    if package.get('format') == 'material-model-package-v1':
        source = after / package['content_source']
        assert sha(source.read_bytes()) == package['content_sha256']
        assert plan['id'] == package['migration_id']
        by_id = {row['id']: row for row in json.loads(source.read_text())['material_content']}
        plan['content']['material_content'] = [by_id[row['id']] for row in plan['content']['material_content']]
    assert sha(canonical({k: v for k, v in plan.items() if k != 'id'}).encode()) == plan['id']
    before_revisions = {row['id']: row for row in prior['revisions']}
    after_revisions = {row['id']: row for row in current['revisions']}
    assert before_revisions.keys() == after_revisions.keys()
    database = sqlite3.connect((after / '.runtime/review.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
    database.row_factory = sqlite3.Row
    database.execute('BEGIN')
    db_revisions = {row['id']: dict(row) for row in database.execute('SELECT * FROM revisions')}
    assert db_revisions == after_revisions, 'physical DB/export revisions differ'
    content_bytes = 0
    count = 0
    for row in database.execute('SELECT id,body FROM material_content'):
        raw = row['body'].encode()
        assert sha(raw) == row['id'] and json.loads(raw) == decoder.nodes[row['id']]
        content_bytes += len(raw)
        count += 1
    assert count == len(decoder.nodes)
    db_checked_tables = []
    for table in ('material_aliases', 'material_definitions', 'material_definition_versions', 'material_archive_files',
                  'material_plan_versions', 'material_plan_members', 'material_candidate_members'):
        rows = [dict(row) for row in database.execute('SELECT * FROM ' + table)]
        assert sorted(map(canonical, rows)) == sorted(map(canonical, current[table])), ('DB/export model table', table)
        db_checked_tables.append(table)
    database.close()
    hydrated = {}
    for rid, old in before_revisions.items():
        row = after_revisions[rid]
        assert {k: v for k, v in row.items() if k != 'payload'} == {k: v for k, v in old.items() if k != 'payload'}
        raw = decoder.payload(row['payload'])
        assert raw.encode() == old['payload'].encode(), ('payload bytes', rid)
        payload = json.loads(raw)
        assert sha(canonical({'object_id': row['object_id'], 'version': row['version'], 'payload': payload}).encode()) == rid
        hydrated[rid] = payload
    preserved = []
    for key in ('objects', 'dependencies', 'material_rounds', 'material_members', 'material_comment_scopes', 'material_feedback'):
        assert current[key] == prior[key], ('legacy table', key)
        preserved.append(key)
    assert (before / 'comments.json').read_bytes() == (export / 'comments.json').read_bytes()
    archives = []
    catalog = {row['path']: json.loads(row['container']) for row in current['material_archive_files']}
    assert set(catalog) == {row['path'] for row in plan['archives']}
    for row in plan['archives']:
        relative = row['path']
        document = json.loads((after / relative).read_bytes())
        assert document == row['container'] == catalog[relative]
        raw = decoder.archive(document)
        saved = original_files[relative]
        assert len(raw) == saved['bytes'] and sha(raw) == saved['sha256'] == row['before_sha256'], relative
        archives.append({'path': relative, 'bytes': len(raw), 'sha256': sha(raw)})
    assert len(archives) == 1855
    coverage = json.loads(coverage_path.read_text())
    assert set(coverage['selected_paths']) == {row['path'] for row in archives if row['path'].startswith('production/')}
    assert not coverage['unexpected_scheme_files_not_selected']
    def has_scheme(value):
        if isinstance(value, dict):
            if isinstance(value.get('generation'), dict) or isinstance(value.get('prompt'), str):
                return True
            return any(has_scheme(child) for child in value.values())
        if isinstance(value, list):
            return any(has_scheme(child) for child in value)
        if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
            try:
                return has_scheme(json.loads(value))
            except ValueError:
                return False
        return False
    production_files_checked = 0
    for path in (after / 'production').rglob('*.json'):
        value = json.loads(path.read_bytes())
        if isinstance(value, dict) and value.get('format') == 'material-archive-reference-v1':
            assert path.relative_to(after).as_posix() in catalog
        else:
            assert not has_scheme(value), ('unmanaged production scheme remains', str(path))
        production_files_checked += 1
    media_count = ordinary_json_count = 0
    archived_paths = {row['path'] for row in archives}
    for source in (before / 'assets').iterdir():
        relative = 'export/assets/' + source.name
        if relative in archived_paths:
            continue
        assert source.read_bytes() == (after / relative).read_bytes(), ('unchanged asset', relative)
        if source.suffix == '.json':
            ordinary_json_count += 1
        else:
            media_count += 1
    mid = 'need-form-li-ji-paste-voice'
    definition_row = next(row for row in current['material_definition_versions'] if row['material_id'] == mid and row['number'] == 2)
    definition = decoder.expand(definition_row['definition_id'])
    prompt = definition['generation']['prompt']
    exact_prompt_leaves = [key for key, node in decoder.nodes.items() if node.get('value') == prompt]
    containing_prompt_leaves = [key for key, node in decoder.nodes.items() if isinstance(node.get('value'), str) and prompt in node['value']]
    assert len(exact_prompt_leaves) == len(containing_prompt_leaves) == 1
    recipe_count = 0
    for key, node in decoder.nodes.items():
        if not any(name.startswith('archive_recipe') for name in node):
            continue
        recipe = decoder.expand(key)
        assert prompt not in canonical(recipe), ('prompt hidden in recipe', key)
        recipe_count += 1
    assert all(prompt not in row['payload'] for row in current['revisions'])
    aliases = [row for row in current['material_aliases'] if row['material_id'] == mid]
    ids = {mid, *(row['alias_id'] for row in aliases)}
    assert len(ids) == 13
    object_heads = {row['id']: row['current_revision'] for row in current['objects']}
    scopes = {canonical(hydrated[object_heads[oid]]['scope']) for oid in ids}
    assert len(scopes) == 13
    asset_revision = '4780bf06e1124ebac048ac6fe5f36322def8b0b30a1fb13ddf75f18c2c266677'
    assert {ref['object_id'] for ref in hydrated[asset_revision]['candidate_requirements']} == ids
    case_associations = []
    for oid in sorted(ids):
        case_associations.append({'requirement_id': oid, 'revision_id': object_heads[oid],
            'scope': hydrated[object_heads[oid]]['scope'], 'canonical_material_id': mid,
            'preserved_versions': [row for row in current['material_plan_versions'] if row['material_id'] == oid],
            'result_memberships': [row for row in current['material_plan_members'] if row['material_id'] == oid and row['revision_id'] == asset_revision]})
    return {'format': 'ui-material-independent-full-check-v1',
        'inputs': {'before': display_path(before), 'after': display_path(after), 'original_hash_inventory': display_path(originals), 'original_scope_audit': display_path(coverage_path),
            'system_head': plan['system_head'], 'migration_id': plan['id'],
            'hashes': {display_path(path): sha(path.read_bytes()) for path in (after / 'migration.json', export / 'objects.json', export / 'material-content.json', originals, coverage_path)}},
        'revision_count': len(before_revisions), 'exact_payload_bytes_equal': True, 'revision_ids_recomputed': True,
        'preserved_legacy_tables': preserved, 'comments_exact_bytes_equal': True,
        'content_node_count': len(decoder.nodes), 'content_node_hashes_valid': True, 'content_node_types': dict(decoder.types),
        'database_physical_revisions_equal_export': True, 'database_content_equal_export': True,
        'database_content_bytes': content_bytes, 'database_model_tables_equal_export': db_checked_tables,
        'archive_count': len(archives), 'archive_production_count': sum(r['path'].startswith('production/') for r in archives),
        'archive_export_count': sum(r['path'].startswith('export/') for r in archives),
        'all_archive_raw_bytes_equal': True, 'all_archive_catalogs_equal': True,
        'production_json_files_independently_scanned': production_files_checked,
        'unarchived_production_scheme_count': 0,
        'original_production_json_scope_scan': coverage['original_json_files_scanned'],
        'preserved_external_task_test_evidence': coverage['explicitly_preserved_test_evidence'],
        'media_files_bytes_equal': media_count, 'ordinary_json_files_bytes_equal': ordinary_json_count,
        'case': {'material_id': mid, 'number': 2, 'definition_id': definition_row['definition_id'], 'state_associations': len(scopes),
            'asset_revision': asset_revision, 'candidate_requirement_count': len(ids), 'prompt_physical_leaf_count': len(exact_prompt_leaves),
            'larger_leaf_containing_prompt_count': len(containing_prompt_leaves) - len(exact_prompt_leaves),
            'recipes_inspected_after_decompression': recipe_count, 'definition_gaps': json.loads(definition_row['gaps']),
            'definition_provenance': json.loads(definition_row['provenance']), 'associations': case_associations,
            'asset_originals': [component for component in hydrated[asset_revision]['components'] if component['role'] == 'original']},
        'archives': archives}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--originals', type=Path, required=True)
    parser.add_argument('--coverage', type=Path, default=Path(__file__).with_name('independent-archive-coverage.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check(args.before, args.after, args.originals, args.coverage)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'archives'}, ensure_ascii=False, indent=2))
