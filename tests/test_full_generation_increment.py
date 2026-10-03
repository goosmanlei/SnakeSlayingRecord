import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_full_generation import verify


class GenerationIncrementTest(unittest.TestCase):
    def setUp(self):
        self.before = {
            'objects': [('need-a', 'REQUIREMENT', 'r-a'), ('need-b', 'REQUIREMENT', 'r-b')],
            'revisions': [('r-a', 'need-a', 1, '{}'), ('r-b', 'need-b', 1, '{}')],
            'dependencies': [], 'material_members': [],
            'material_rounds': [('need-a', 1, 'preparing', 'original-time'), ('need-b', 1, 'preparing', 'original-time')],
            'comments': [('user-comment', 'original-opinion')],
        }
        payload = {'candidate_requirements': [{'object_id': 'need-a', 'revision_id': 'r-a'}]}
        self.registration = {'batches': [{'records': [{'object_id': 'asset-new', 'kind': 'ASSET',
            'expected_version': 0, 'payload': payload}]}]}
        self.after = copy.deepcopy(self.before)
        self.after['objects'].append(('asset-new', 'ASSET', 'r-new'))
        self.after['revisions'].append(('r-new', 'asset-new', 1, json.dumps(payload)))
        self.after['material_rounds'][0] = ('need-a', 1, 'produced', 'original-time')

    def check(self):
        with patch('verify_full_generation.read_tables', side_effect=[self.before, self.after]):
            return verify(Path('before'), Path('after'), self.registration)

    def test_new_candidate_advances_only_its_existing_round(self):
        self.assertEqual(self.check()['new_rounds'], 0)
        self.after['material_rounds'][1] = ('need-b', 1, 'produced', 'original-time')
        with self.assertRaisesRegex(ValueError, 'old material round changed'):
            self.check()

    def test_round_identity_and_user_comments_remain_protected(self):
        self.after['material_rounds'][0] = ('need-a', 1, 'produced', 'rewritten-time')
        with self.assertRaisesRegex(ValueError, 'old material round changed'):
            self.check()
        self.after['material_rounds'][0] = ('need-a', 1, 'produced', 'original-time')
        self.after['comments'][0] = ('user-comment', 'overwritten-opinion')
        with self.assertRaisesRegex(ValueError, 'protected table changed: comments'):
            self.check()

    def test_agent_review_cannot_be_imported_as_user_master_approval(self):
        record = self.registration['batches'][0]['records'][0]
        record['kind'] = 'JUDGMENT'
        record['payload'].update(actor='Codex', verdict='accepted', review_type='generation_master',
                                 evidence={'source': 'user_conversation'})
        self.registration['user_master_decisions'] = ['asset-new']
        with self.assertRaisesRegex(ValueError, 'ungrounded master decision'):
            self.check()


if __name__ == '__main__': unittest.main()
