import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.unique_origin_publication import production_tables


class MethodPrerequisiteTest(unittest.TestCase):
    def snapshot(self, published):
        definition = {'id': 'definition', 'object_id': 'method', 'payload': json.dumps({'format': 'managed-method-skill-v1'})}
        return {'objects': [{'id': 'method'}] if published else [],
                'revisions': [definition] if published else [], 'dependencies': []}

    def test_public_step_can_reference_published_exact_definition(self):
        before = self.snapshot(True)
        after = copy.deepcopy(before)
        after['dependencies'].append({'from_revision': 'public-step', 'to_revision': 'definition', 'role': 'method'})
        _, filtered, _ = production_tables(before, after)
        self.assertEqual(filtered['dependencies'], after['dependencies'])

    def test_unpublished_method_reference_still_rejected(self):
        before = self.snapshot(False)
        after = self.snapshot(True)
        after['dependencies'].append({'from_revision': 'public-step', 'to_revision': 'definition', 'role': 'method'})
        with self.assertRaisesRegex(ValueError, 'deliver its exact binding first'):
            production_tables(before, after)

    def test_exact_file_histories_travel_with_configuration_not_production(self):
        before = self.snapshot(True)
        before.update(method_file_versions=[{'object_id':'method','id':'old-file'}],
                      method_file_packages=[{'object_id':'method','revision_id':'definition'}],
                      method_file_members=[{'package_revision':'definition','path':'SKILL.md'}])
        after = copy.deepcopy(before)
        after['method_file_versions'].append({'object_id':'method','id':'new-file'})
        after['method_file_packages'].append({'object_id':'method','revision_id':'new-definition'})
        after['method_file_members'].append({'package_revision':'new-definition','path':'SKILL.md'})
        after['method_file_versions'].append({'object_id':'unrelated','id':'must-remain-visible'})
        _, filtered, _ = production_tables(before, after)
        self.assertEqual(filtered['method_file_packages'],before['method_file_packages'])
        self.assertEqual(filtered['method_file_members'],before['method_file_members'])
        self.assertIn({'object_id':'unrelated','id':'must-remain-visible'},filtered['method_file_versions'])


class ScreenplayBasisTest(unittest.TestCase):
    def test_all_immutable_input_editions_are_rehearsed_without_changing_origin(self):
        from review_desk.bundle import export
        from review_desk.screenplay import import_screenplay
        from review_desk.store import Store
        from scripts.generation_publication import backup
        from scripts.unique_origin_publication import comparison_basis, file_sha256
        with tempfile.TemporaryDirectory(prefix='screenplay-basis-test-') as temp:
            root = Path(temp).resolve()
            instance = root / '.runtime/generation/review'
            (root / 'imports').mkdir()
            prepared = Store(root / '.runtime/candidate.sqlite3')
            try:
                prepared.put_source({'id': 'story-source', 'title': 'Story', 'version_type': 'test',
                    'origin': 'synthetic fixture', 'source_url': 'https://example.invalid/story',
                    'collected_at': '2026-01-01', 'blocks': [{'id': 'source-b1', 'text': 'Story'}],
                    'notes': 'Fixture', 'assets': []})
                story = {'revision': prepared.db.execute(
                    'SELECT current_revision FROM objects WHERE id=?', ('story-source',)).fetchone()[0]}
                structure = prepared.put_object('story-structure', 'STORY', {'title': 'Structure', 'sections': []})
                origin = instance / '.runtime/generation-base.sqlite3'
                origin.parent.mkdir(parents=True)
                backup(prepared.db_path, origin)
                before = file_sha256(origin)
                paths = []
                for number in (5, 6):
                    edition = 'screenplay-' + str(number)
                    document = {'format': 'screenplay-edition-v1', 'id': edition,
                        'title': edition, 'notes': 'Exact input history',
                        'review_status': 'pending', 'duration_kind': 'estimate',
                        'basis': {'story': {'object_id': 'story-source', 'revision_id': story['revision']},
                                  'structure': {'object_id': 'story-structure', 'revision_id': structure['revision']}},
                        'episodes': [{'id': edition + '-e01', 'number': 1, 'title': 'One',
                            'estimated_seconds': 2,
                            'blocks': [{'id': 'b1', 'text': 'Placement ' + str(number)}],
                            'scenes': [{'id': 's1', 'heading': 'Scene', 'location': 'Shop',
                                'time': 'Day', 'estimated_seconds': 2, 'block_ids': ['b1']}]}]}
                    path = Path('imports') / (edition + '.json')
                    (root / path).write_text(json.dumps(document))
                    paths.append(path)
                    import_screenplay(prepared, document)
                export(prepared, root / 'export')
                derived, receipt = comparison_basis(root, instance, paths)
                self.assertEqual(file_sha256(origin), before)
                self.assertEqual([x['document'] for x in receipt['screenplays']], [str(p) for p in paths])
                check = Store.open_existing(derived)
                try:
                    for number in (5, 6):
                        self.assertIsNotNone(check.db.execute('SELECT id FROM objects WHERE id=?',
                            ('screenplay-' + str(number),)).fetchone())
                finally:
                    check.close()
                # A narrow, reviewed record package permits publication while
                # the private working DB still contains non-public method work.
                exact = {'format':'screenplay-publication-records-v1'}
                ids = {f'screenplay-{n}{suffix}' for n in (5,6) for suffix in ('','-e01')}
                exact['objects'] = [dict(row) for row in prepared.db.execute('SELECT * FROM objects') if row['id'] in ids]
                exact['revisions'] = [dict(row) for row in prepared.db.execute('SELECT * FROM revisions') if row['object_id'] in ids]
                rids = {row['id'] for row in exact['revisions']}
                exact['dependencies'] = [dict(row) for row in prepared.db.execute('SELECT * FROM dependencies') if row['from_revision'] in rids]
                package = Path('screenplay-records.json')
                (root/package).write_text(json.dumps(exact))
                derived, receipt = comparison_basis(root, instance, paths, screenplay_records=package)
                self.assertEqual(receipt['screenplay_records']['sha256'], file_sha256(root/package))
                self.assertEqual(file_sha256(origin), before)
                check = Store.open_existing(derived)
                try:
                    for row in exact['revisions']:
                        self.assertEqual(dict(check.db.execute('SELECT * FROM revisions WHERE id=?',(row['id'],)).fetchone()),row)
                finally:
                    check.close()
                damaged = copy.deepcopy(exact)
                damaged['revisions'].pop()
                (root/package).write_text(json.dumps(damaged))
                with self.assertRaisesRegex(ValueError, 'does not match reviewed edition'):
                    comparison_basis(root, instance, paths, screenplay_records=package)
                self.assertEqual(file_sha256(origin), before)
            finally:
                prepared.close()
