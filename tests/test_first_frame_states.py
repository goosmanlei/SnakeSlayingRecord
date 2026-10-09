"""A source paragraph may name a result that is not yet visible at its start."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from video_input_design import first_frame_states


class FirstFrameStateTests(unittest.TestCase):
    def setUp(self):
        # Isolated fixture: one paragraph contains dry shoes -> spilled water.
        self.dry = {'object_id': 'dry', 'id': 'dry-revision', 'payload': {'entity': {'object_id': 'person'}}}
        self.wet = {'object_id': 'wet', 'id': 'wet-revision', 'payload': {'entity': {'object_id': 'person'}}}
        self.bucket = {'object_id': 'bucket', 'id': 'bucket-revision', 'payload': {'entity': {'object_id': 'bucket'}}}
        self.states = {'dry': self.dry, 'wet': self.wet, 'bucket': self.bucket}
        self.choice = {'first_frame_states': {'person': {'state': 'dry', 'revision_id': 'dry-revision'}}}

    def test_authored_start_does_not_replace_whole_shot_result(self):
        source = [self.wet, self.bucket]
        self.assertEqual(first_frame_states(source, self.states, self.choice), [self.dry, self.bucket])
        self.assertEqual(source, [self.wet, self.bucket])
        self.assertEqual(first_frame_states(source, self.states, {}), source)

    def test_changed_start_reference_requires_review(self):
        available = deepcopy(self.states)
        available['dry']['id'] = 'later-revision'
        with self.assertRaisesRegex(ValueError, 'needs re-review'):
            first_frame_states([self.wet], available, self.choice)

    def test_cannot_borrow_another_identity_or_add_absent_person(self):
        available = deepcopy(self.states)
        available['dry']['payload']['entity']['object_id'] = 'someone-else'
        with self.assertRaisesRegex(ValueError, 'another subject'):
            first_frame_states([self.wet], available, self.choice)
        with self.assertRaisesRegex(ValueError, 'no subject'):
            first_frame_states([self.bucket], self.states, self.choice)


if __name__ == '__main__':
    unittest.main()
