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
