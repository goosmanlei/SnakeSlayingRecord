import copy
import json
import unittest

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
