import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from scene_reading import descriptor, vocal_ranges
from types import SimpleNamespace


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

    def test_authored_prose_keeps_words_and_order_without_the_rendered_template(self):
        reviewed = ReviewedSequence()
        reviewed.voice = SimpleNamespace(VOICES={'a': ('阿蘅',), 'l': ('李寄',)}, LABELS={})
        reviewed.for_sources = lambda _: [
            {'speaker': 'l', 'words': 'exact', 'content': '最后那段，你还得看词呢。', 'source': 's001:27'},
            {'speaker': 'a', 'words': 'exact', 'content': '晚些你陪我一起练。', 'source': 's001:28'}]
        prompt = '相机同侧轻随，两人站定。\n李寄轻声说：“最后那段，你还得看词呢。”阿蘅答：“晚些你陪我一起练。”\n米袋仍归阿蘅。'
        self.need['payload']['generation']['prompt'] = prompt
        self.need['payload']['method_basis'] = {'execution': {'object_id':'actual-step', 'revision_id':'actual-method'}}
        result = descriptor(self.shot, self.need, reviewed, {}, True)
        self.assertEqual([prompt[p['start']:p['end']] for p in result['parts']], prompt.splitlines())
        for damaged in (prompt.replace('晚些你陪我一起练。', '明天再唱。'),
                        prompt + '\n晚些你陪我一起练。',
                        '阿蘅答：“晚些你陪我一起练。”李寄说：“最后那段，你还得看词呢。”',
                        prompt.replace('李寄轻声说', '老汉轻声说')):
            with self.assertRaises(ValueError):
                vocal_ranges(damaged, [], reviewed)
        self.assertTrue(all('text' not in p for p in result['parts']))
        self.assertEqual(self.need['payload']['generation']['prompt'], prompt)

    def test_missing_or_repeated_sequence_is_refused_instead_of_inventing_text(self):
        for prompt in ('只有新头', self.prompt + self.sequence):
            self.need['payload']['generation']['prompt'] = prompt
            with self.assertRaisesRegex(ValueError, 'not unique'):
                descriptor(self.shot, self.need, ReviewedSequence(), {}, True)

    def test_spoken_name_is_separate_from_visual_identity_mentions(self):
        reviewed = SimpleNamespace(voice=SimpleNamespace(
            VOICES={'z':('赵执事',), 'p':('河街路人',)}, LABELS={}),
            for_sources=lambda _: [{'speaker':'p','words':'exact','content':'赵执事','source':'s002:12'}])
        prompt = '赵执事在檐下，参考图约束赵执事身份。\n河街路人招呼：“赵执事”。赵执事只点头。'
        ranges = vocal_ranges(prompt, [], reviewed)
        self.assertEqual(prompt[ranges[0]['start']:ranges[0]['end']], '赵执事')
        self.assertGreater(ranges[0]['start'], prompt.index('河街路人'))
        with self.assertRaises(ValueError):
            vocal_ranges(prompt + '\n河街路人又喊：“赵执事”。', [], reviewed)
        with self.assertRaises(ValueError):
            vocal_ranges('河街路人只在参考段落。\n另一人招呼：“赵执事”。', [], reviewed)

    def test_another_shot_revision_cannot_supply_the_reading(self):
        self.need['payload']['scope']['revision_id'] = 'latest-shot'
        with self.assertRaisesRegex(ValueError, 'outside exact shot'):
            descriptor(self.shot, self.need, ReviewedSequence(), {}, True)

    def test_reviewed_offscreen_singer_without_reusable_voice_is_explicit(self):
        reviewed = SimpleNamespace(voice=SimpleNamespace(VOICES={}, LABELS={}),
            for_sources=lambda _: [{'speaker': '远处祈福戏歌者', 'words': 'exact',
                                   'content': '米饵献上，明月还乡——', 'source': 's010:10'}])
        self.assertEqual(len(vocal_ranges('远处祈福戏歌者唱：“米饵献上，明月还乡——”。', [], reviewed)), 1)
        with self.assertRaisesRegex(ValueError, 'speaker'):
            vocal_ranges('阿蘅唱：“米饵献上，明月还乡——”。', [], reviewed)

    def test_spoken_name_with_punctuation_does_not_count_reference_identity(self):
        reviewed = SimpleNamespace(voice=SimpleNamespace(
            VOICES={'t': ('陶伯',), 'l': ('李诞',)}, LABELS={}),
            for_sources=lambda _: [{'speaker': 'l', 'words': 'exact',
                                   'content': '陶伯。', 'source': 's025:2'}])
        prompt = '李诞叫：“陶伯。”@音频1约束李诞、@音频2约束陶伯。'
        ranges = vocal_ranges(prompt, [], reviewed)
        self.assertEqual(prompt[ranges[0]['start']:ranges[0]['end']], '陶伯。')
        with self.assertRaises(ValueError):
            vocal_ranges(prompt + '李诞又叫：“陶伯。”', [], reviewed)

    def test_longer_person_identity_cannot_pass_for_another_speaker(self):
        reviewed = SimpleNamespace(voice=SimpleNamespace(
            VOICES={'a': ('阿蘅',), 'm': ('阿蘅母亲',), 'c': ('程差役',),
                    's': ('另一名差役',)}, LABELS={'差役': 's'}),
            for_sources=lambda _: [{'speaker': 'a', 'words': 'exact',
                                   'content': '知道啦。', 'source': 's007:15'}])
        with self.assertRaisesRegex(ValueError, 'speaker'):
            vocal_ranges('阿蘅母亲答：“知道啦。”', [], reviewed)
        self.assertEqual(len(vocal_ranges('阿蘅答：“知道啦。”', [], reviewed)), 1)
        reviewed.for_sources = lambda _: [{'speaker': 's', 'words': 'exact',
                                          'content': '仓账守着。', 'source': 's024:7'}]
        with self.assertRaisesRegex(ValueError, 'speaker'):
            vocal_ranges('程差役说：“仓账守着。”', [], reviewed)
        self.assertEqual(len(vocal_ranges('另一名差役说：“仓账守着。”', [], reviewed)), 1)

    def test_short_reply_is_not_repeated_by_a_later_longer_utterance(self):
        reviewed = SimpleNamespace(voice=SimpleNamespace(
            VOICES={'z': ('赵执事',), 'a': ('阿蘅',)}, LABELS={}),
            for_sources=lambda _: [
                {'speaker': 'z', 'words': 'exact', 'content': '两升。', 'source': 's007:25'},
                {'speaker': 'a', 'words': 'exact', 'content': '一天两升。做一天，记一天。', 'source': 's007:26'}])
        prompt = '赵执事答：“两升。”阿蘅核定：“一天两升。做一天，记一天。”'
        ranges = vocal_ranges(prompt, [], reviewed)
        self.assertEqual([prompt[r['start']:r['end']] for r in ranges],
                         ['两升。', '一天两升。做一天，记一天。'])
        for damaged in (prompt + '\n两升。', prompt + '赵执事又答：“两升。”',
                        prompt.replace('赵执事答：“两升。”', '')):
            with self.assertRaises(ValueError):
                vocal_ranges(damaged, [], reviewed)

    def test_new_purpose_can_reuse_an_explicit_exact_product(self):
        self.need['id'] = 'accurate-video-plan'
        self.need['payload']['scope']['revision_id'] = 'earlier-shot'
        self.shot['payload']['products'] = [{'requirement': {'object_id':'video', 'revision_id':'accurate-video-plan'}}]
        result = descriptor(self.shot, self.need, ReviewedSequence(), {}, True)
        self.assertEqual(result['sha256'], hashlib.sha256(self.prompt.encode()).hexdigest())
