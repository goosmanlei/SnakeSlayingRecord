import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from register_generation_batch import validate_reference_authorization


class ReferenceGuardTests(unittest.TestCase):
    def setUp(self):
        self.asset = {'object_id': 'asset-river-03', 'revision_id': 'source-revision'}
        self.state = {'object_id': 'river-day', 'revision_id': 'state-revision'}
        self.entity = {'object_id': 'river', 'revision_id': 'entity-revision'}
        self.payload = {'media_type': 'image', 'states': [self.state], 'subjects': [self.entity],
                        'verification': {'self_review_status': 'changes_requested'}, 'lineage': {'i2i_depth': 0}}
        self.request = {'same_state_repair': {'source': self.asset, 'reason': 'Move the misplaced stall only'},
                        'lineage': {'i2i_depth': 1, 'references': [self.asset]}}

    def validate(self, request=None, state=None):
        def resolve(reference, kinds):
            self.assertEqual(reference, self.asset)
            self.assertEqual(kinds, {'ASSET'})
            return {'payload': self.payload}
        validate_reference_authorization(resolve, request or self.request, [self.asset], [state or self.state], self.entity, 'image')

    def test_unaccepted_candidate_can_only_repair_its_own_complete_state(self):
        self.validate()
        with self.assertRaisesRegex(AssertionError, 'cannot change'):
            self.validate(state={'object_id': 'river-night', 'revision_id': 'other-state'})

    def test_missing_approval_cannot_be_silently_treated_as_a_repair(self):
        request = copy.deepcopy(self.request); request.pop('same_state_repair')
        with self.assertRaisesRegex(AssertionError, 'approved master required'):
            self.validate(request)

    def test_same_state_repair_does_not_reset_lineage(self):
        self.payload['lineage']['i2i_depth'] = 2
        self.request['lineage']['i2i_depth'] = 3
        with self.assertRaises(AssertionError):
            self.validate()


if __name__ == '__main__': unittest.main()
