"""Behavioral guards for shot boundaries and narrated sound; no formal DB writes."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from audiovisual_design import ROOT, read_score, coverage
from audiovisual_events import ReviewedEvents
from audiovisual_materials import casting


def sources(scene, *blocks):
    return [{'scene_id': scene, 'block_ids': [f'{scene}-b{n:03}' for n in blocks]}]


class EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.score = read_score()
        cls.reviewed = ReviewedEvents(ROOT, cls.score, casting())

    def test_entire_story_still_covered_exactly_once(self):
        report = coverage(self.score, json.loads((ROOT / 'imports/screenplay-04.json').read_text()))
        self.assertEqual(report['totals'], dict(story_scenes=42, audiovisual_scenes=65, shots=344, blocks=1114, planned_seconds=6033))

    def test_scene_events_cannot_leak_into_a_shot_through_replaced_fields(self):
        scene = deepcopy(self.score[7]['scenes'][1])
        scene['空间'] += '突然提起北闸，蛇撞门，然后退净落闸。'
        scene['声音'] += '一次播放整场门闸声。'
        fields, shared = self.reviewed.conditions(8, scene, 2)
        self.assertNotIn('突然', fields['空间'])
        self.assertNotIn('整场', fields['声音'])
        self.assertIn('北闸全镜不动', fields['连续性'])
        self.assertNotIn('空间', shared)
        opening, _ = self.reviewed.conditions(1, self.score[0]['scenes'][0], 1)
        self.assertNotIn('转调', opening['声音'])
        night, _ = self.reviewed.conditions(11, self.score[10]['scenes'][3], 1)
        self.assertIn('保持夜间', night['光线'])

    def test_changed_shared_condition_requires_human_rereview(self):
        changed = deepcopy(self.score)
        changed[0]['scenes'][0]['光线'] += '然后天黑。'
        with self.assertRaisesRegex(ValueError, 'inherited scene condition changed'):
            ReviewedEvents(ROOT, changed, casting())

    def test_narrated_readback_is_a_second_speaker_not_lost_or_tripled(self):
        src = sources('s026', 1, 2, 3)
        events = self.reviewed.for_sources(src)
        self.assertEqual([e['speaker'] for e in events], ['heng-mother', 'clerk-liang'])
        self.assertEqual(events[0]['content'], events[1]['content'])
        rendered = self.reviewed.render(src)
        self.assertEqual(rendered.count(events[0]['content']), 2)

    def test_humming_following_and_stopping_keep_both_voices_and_order(self):
        events = self.reviewed.for_sources(sources('s038', 9, 10, 11))
        self.assertEqual([(e['speaker'], e['mode']) for e in events],
                         [('heng-mother', '轻哼'), ('a-heng', '接调'), ('a-heng', '演唱'),
                          ('heng-mother', '收声'), ('a-heng', '收声')])
        self.assertEqual({e['song'] for e in events if e.get('song')}, {'entity-blue-awning-song'})
        ending = self.reviewed.for_sources(sources('s040', 10, 11, 12, 13))
        self.assertEqual(ending[-1]['speaker'], 'heng-mother')
        self.assertEqual(ending[-1]['words'], 'none')

    def test_narrated_overlap_and_call_answer_do_not_invent_identity_or_words(self):
        src = sources('s040', 1, 2, 3)
        self.assertEqual([e['speaker'] for e in self.reviewed.for_sources(src)], ['a-heng', 'heng-mother'])
        self.assertTrue(self.reviewed.blockers(src))
        src = sources('s040', 18, 19)
        events = self.reviewed.for_sources(src)
        self.assertEqual([e['speaker'] for e in events], ['offscreen-caller', 'li-ji'])
        self.assertEqual(events[0]['words'], 'meaning')
        self.assertEqual(events[1]['content'], '来了')
        self.assertEqual(self.reviewed.render(src).count('来了'), 1)
        self.assertNotIn('li-mother', [e['speaker'] for e in events])

    def test_two_narrated_witnesses_and_pure_visual_text_are_distinct(self):
        events = self.reviewed.for_sources(sources('s036', 12))
        self.assertEqual([e['speaker'] for e in events], ['delivery-worker', 'order-writer'])
        self.assertEqual(len(self.reviewed.blockers(sources('s036', 12))), 2)
        self.assertEqual(self.reviewed.for_sources(sources('s018', 21)), [])
        # The paper's printed invocation is seen, not sung by the person nearby.
        self.assertEqual(self.reviewed.for_sources(sources('s003', 14)), [])

    def test_time_title_can_leave_the_picture_prompt_without_losing_narrated_voice(self):
        src = sources('s037', 1, 2, 3)
        events = self.reviewed.for_sources(src)
        self.assertEqual([e['speaker'] for e in events], ['clerk-proclamation'])
        rendered = self.reviewed.render(src, {'s037:1': ''})
        self.assertNotIn('二十多天后', rendered)
        self.assertIn(self.reviewed.describe(events[0]), rendered)
        pending = sources('s037', 16, 17, 18)
        self.reviewed.render(pending, {'s037:18': '交纸并核印，末行未给原词。'})
        self.assertTrue(self.reviewed.blockers(pending))

    def test_paper_translation_does_not_create_speech_or_borrow_other_scene_words(self):
        src = sources('s003', 14)
        rendered = self.reviewed.render(src, {'s003:14': '旧纸翻出两列净纸区。'})
        self.assertIn('旧纸翻出两列净纸区', rendered)
        self.assertNotIn('米饵奉蛇神', rendered)
        self.assertNotIn('本段发声', rendered)
        with self.assertRaisesRegex(ValueError, 'outside the exact shot sources'):
            self.reviewed.render(src, {'s022:13': '后来揭出的条款'})

    def test_changed_source_cannot_reuse_semantic_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'imports').mkdir()
            (root / 'production/audiovisual').mkdir(parents=True)
            (root / 'imports/screenplay-04.json').write_bytes((ROOT / 'imports/screenplay-04.json').read_bytes() + b'\n')
            for name in ('shot-contexts.json', 'vocal-events.json'):
                (root / 'production/audiovisual' / name).write_bytes((ROOT / 'production/audiovisual' / name).read_bytes())
            with self.assertRaisesRegex(ValueError, 'reviewed event source changed'):
                ReviewedEvents(root, self.score, casting())


if __name__ == '__main__':
    unittest.main()
