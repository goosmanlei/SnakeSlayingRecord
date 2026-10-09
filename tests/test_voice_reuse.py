"""A reviewed identity never bypasses source, duration or actual-use boundaries."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import audiovisual_materials as m
from test_voice_candidates import sample


class VoiceReuseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.addCleanup(patch.stopall)
        patch.object(m, 'ROOT', self.root).start()
        evidence = self.root / 'production/voice-reuse/analysis'
        evidence.mkdir(parents=True)
        self.asset, self.call = sample()
        self.asset['payload']['components'][0]['duration_seconds'] = 4
        self.source = {'object_id': 'old-audio', 'revision_id': 'old-asset-revision',
                       'component_id': 'original', 'sha256': 'source-hash'}
        self.evidence = {'request_metadata': {'source': {'asset':
            {'object_id': 'old-audio', 'revision_id': 'old-asset-revision'},
            'sha256': 'source-hash', 'component': 'original'}}, 'receipt': {'state': 'completed'}}
        self.evidence_path = evidence / 'actual-analysis.json'
        self.write_evidence()
        self.builder = object.__new__(m.Builder)
        self.builder.store = None
        self.builder.voice = SimpleNamespace(VOICES={'a': ('发话者甲', '成年男中音，短句平实')},
                                            GROUP_ENTITIES={'a': 'group'})
        def record(store, **ref):
            if ref == {'object_id': 'old-audio', 'revision_id': 'old-asset-revision'}:
                return self.asset
            if ref == self.asset['payload']['production']:
                return self.call
            raise KeyError('no current-head fallback allowed')
        self.builder.p = SimpleNamespace(record=record)
        self.review = {'need_id': 'material-voice-a', 'source': self.source,
                       'analysis_attempts': ['actual-analysis'], 'decision': 'suitable_spoken_identity',
                       'range': {'start_seconds': 0, 'end_seconds': 3}}
        self.builder.voice_reviews = {'a': self.review}
        self.builder.voice_review_complete = False

    def write_evidence(self):
        self.evidence_path.write_text(json.dumps(self.evidence))

    def test_exact_historical_source_remains_selected_even_without_current_head(self):
        before = deepcopy((self.asset, self.call))
        choice = self.builder.voice_choice('a')
        self.assertEqual(choice['reference']['revision_id'], 'old-asset-revision')
        self.assertEqual((self.asset, self.call), before)

    def test_failed_or_other_original_analysis_cannot_authorise_a_choice(self):
        self.evidence['receipt']['state'] = 'failed'
        self.write_evidence()
        with self.assertRaises(ValueError):
            self.builder.voice_choice('a')
        self.evidence['receipt']['state'] = 'completed'
        self.evidence['request_metadata']['source']['sha256'] = 'another-original'
        self.write_evidence()
        with self.assertRaises(ValueError):
            self.builder.voice_choice('a')

    def test_short_source_and_overlong_selection_cannot_be_made_ready_by_numbers(self):
        self.asset['payload']['components'][0]['duration_seconds'] = 1.7
        self.review['range'] = {'start_seconds': 0, 'end_seconds': 2}
        with self.assertRaises(ValueError):
            self.builder.voice_choice('a')
        self.asset['payload']['components'][0]['duration_seconds'] = 19.78
        self.review['range']['end_seconds'] = 19.78
        with self.assertRaises(ValueError):
            self.builder.voice_choice('a')
        self.review['range'] = {'start_seconds': 5.2, 'end_seconds': 8.3}
        self.assertIsNotNone(self.builder.voice_choice('a'))

    def test_same_group_does_not_allow_a_different_speaker_direction(self):
        self.builder.voice.VOICES['a'] = ('发话者乙', '成年男中音，短句平实')
        with self.assertRaises(ValueError):
            self.builder.voice_choice('a')

    def test_unread_episode_keeps_future_slot_despite_reviewed_identity(self):
        b = self.builder
        b.voice_choices = {'a': b.voice_choice('a')}
        b.voice_uses, b.voices = {}, {'a': 'material-voice-a'}
        b.relation = lambda upstream, *args, **kwargs: {'upstream': upstream, 'selection_state': 'unselected'}
        item = b.voice_input('a', 'video', {'object_id': 'shot'}, [], 'shot')
        self.assertEqual(item['upstream'], 'material-voice-a')
        self.assertEqual(item['selection_state'], 'unselected')
        b.voice_review_complete = True
        with self.assertRaises(ValueError):
            b.voice_input('a', 'video', {'object_id': 'shot'}, [], 'shot')

    def test_changed_episode_or_screenplay_invalidates_reviewed_uses(self):
        (self.root / 'imports').mkdir()
        script = self.root / 'imports/screenplay-04.json'
        script.write_text('locked screenplay')
        (self.root / 'production/audiovisual').mkdir()
        episode = self.root / 'production/audiovisual/e01.md'
        episode.write_text('reviewed episode')
        doc = {'format': 'reviewed-voice-reuse-v1', 'audio_generation': False, 'reviews': {},
               'episode_reviews': [{'number': 1,
                   'authored_sha256': hashlib.sha256(episode.read_bytes()).hexdigest(),
                   'screenplay_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
                   'voices': {'a': 'reviewed purpose'},
                   'uses': [{'shot': 'shot', 'speaker': 'a'}]}]}
        (self.root / 'production/voice-reuse/reviews.json').write_text(json.dumps(doc))
        self.assertIn(('shot', 'a'), m.reviewed_voice_uses(self.root)[1])
        episode.write_text('changed purpose')
        with self.assertRaises(ValueError):
            m.reviewed_voice_uses(self.root)
        episode.write_text('reviewed episode')
        script.write_text('changed screenplay')
        with self.assertRaises(ValueError):
            m.reviewed_voice_uses(self.root)


if __name__ == '__main__':
    unittest.main()
