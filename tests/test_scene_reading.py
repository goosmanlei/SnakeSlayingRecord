import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from scene_reading import descriptor


class ReviewedSequence:
    def render(self, *_args, **_kwargs):
        return '动作：看她一眼🐍。\n声音（依序；注明同时者重叠）：\n1. 阿蘅：几天？\n动作：接回歌本。'


class SceneReadingTest(unittest.TestCase):
    def setUp(self):
        self.shot = {'id': 'exact-shot', 'object_id': 'shot', 'payload': {'sources': []}}
        self.sequence = ReviewedSequence().render()
        self.prompt = '技术前言\n' + self.sequence + '\n技术后文'
        self.need = {'object_id': 'video', 'payload': {
            'scope': {'object_id': 'shot', 'revision_id': 'exact-shot'},
            'generation': {'prompt': self.prompt}}}

    def test_ranges_bind_the_complete_reviewed_order_without_copying_or_rewriting(self):
        result = descriptor(self.shot, self.need, ReviewedSequence(), {}, True)
        self.assertEqual(result['sha256'], hashlib.sha256(self.prompt.encode()).hexdigest())
        self.assertEqual([self.prompt[p['start']:p['end']] for p in result['parts']],
                         ['看她一眼🐍。', '阿蘅：几天？', '接回歌本。'])
        self.assertTrue(all('text' not in p for p in result['parts']))
        self.assertEqual(self.need['payload']['generation']['prompt'], self.prompt)

    def test_missing_or_repeated_sequence_is_refused_instead_of_inventing_text(self):
        for prompt in ('只有新头', self.prompt + self.sequence):
            self.need['payload']['generation']['prompt'] = prompt
            with self.assertRaisesRegex(ValueError, 'not unique'):
                descriptor(self.shot, self.need, ReviewedSequence(), {}, True)

    def test_another_shot_revision_cannot_supply_the_reading(self):
        self.need['payload']['scope']['revision_id'] = 'latest-shot'
        with self.assertRaisesRegex(ValueError, 'outside exact shot'):
            descriptor(self.shot, self.need, ReviewedSequence(), {}, True)
