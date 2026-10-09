"""Discovery never turns a recorded direction or old approval into listening."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from audiovisual_materials import Builder, recorded_voice_identity


def sample(speaker='发话者甲', direction='成年男中音，短句平实'):
    prompt = f'生成一份单人干净音色核对录音。说话身份：{speaker}。声音方向：{direction}。\n旧试读原词。'
    call = dict(id='old-call-revision', kind='CALL', payload=dict(method='generation', prompt=prompt,
        receipt=dict(status='completed', sha256='source-hash', input=dict(text_prompt=prompt))))
    asset = dict(object_id='old-audio', id='old-asset-revision', payload=dict(media_type='audio',
        production=dict(object_id='old-call', revision_id='old-call-revision'),
        subjects=[dict(object_id='entity-group', revision_id='old-entity')],
        components=[dict(id='original', role='original', has_audio=True, sha256='source-hash')]))
    return asset, call


class VoiceCandidatesTests(unittest.TestCase):
    def test_direction_is_from_completed_receipt_and_does_not_require_new_trial_words(self):
        asset, call = sample()
        self.assertEqual(recorded_voice_identity(asset, call), ('发话者甲', '成年男中音，短句平实'))
        self.assertNotIn('verification', asset['payload'])

    def test_failed_or_unproven_call_cannot_supply_recorded_identity(self):
        for status in ('pending', 'failed', None):
            asset, call = sample()
            call['payload']['receipt']['status'] = status
            self.assertIsNone(recorded_voice_identity(asset, call))

    def test_new_description_cannot_override_actual_request_or_original_hash(self):
        asset, call = sample()
        altered = deepcopy(call)
        altered['payload']['prompt'] = altered['payload']['prompt'].replace('发话者甲', '发话者乙')
        self.assertIsNone(recorded_voice_identity(asset, altered))
        asset['payload']['components'][0]['sha256'] = 'other-source'
        self.assertIsNone(recorded_voice_identity(asset, call))

    def test_placeholder_or_mixed_originals_are_not_discovered_as_single_voice(self):
        asset, call = sample()
        asset['payload']['placeholder'] = True
        self.assertIsNone(recorded_voice_identity(asset, call))
        asset['payload']['placeholder'] = False
        asset['payload']['components'].append(deepcopy(asset['payload']['components'][0]))
        self.assertIsNone(recorded_voice_identity(asset, call))

    def test_duration_is_not_listening_or_permission_to_submit_a_candidate(self):
        for duration in (1.7, 14.5, 19.78):
            asset, call = sample()
            asset['payload']['components'][0]['duration_seconds'] = duration
            self.assertIsNotNone(recorded_voice_identity(asset, call))
            self.assertNotIn('selection', asset['payload'])
            self.assertNotIn('verification', asset['payload'])

    def test_group_speakers_and_directions_stay_distinct_and_call_revision_is_exact(self):
        asset, call = sample()
        requested = []
        class Production:
            @staticmethod
            def record(store, **ref):
                requested.append(ref)
                return call
        class Voices:
            VOICES = {'a': ('发话者甲', '成年男中音，短句平实'),
                      'b': ('发话者乙', '成年男中音，短句平实'),
                      'c': ('发话者甲', '年轻男中高音')}
        builder = object.__new__(Builder)
        builder.p, builder.store, builder.voice = Production, None, Voices
        builder.voices = {key: 'voice-' + key for key in Voices.VOICES}
        builder.generated = {oid: dict(payload=dict(scope=dict(object_id='entity-group')))
                             for oid in builder.voices.values()}
        before = deepcopy(asset)
        self.assertEqual(builder.existing_voice_targets(asset), {'voice-a'})
        self.assertEqual(requested, [asset['payload']['production']])
        self.assertEqual(asset, before)
        asset['payload']['subjects'][0]['object_id'] = 'another-entity'
        self.assertEqual(builder.existing_voice_targets(asset), set())

    def test_missing_exact_call_does_not_fall_back_to_the_current_call(self):
        asset, _ = sample()
        class Production:
            @staticmethod
            def record(store, **ref):
                raise KeyError('missing exact historical revision')
        builder = object.__new__(Builder)
        builder.p, builder.store = Production, None
        self.assertEqual(builder.existing_voice_targets(asset), set())


if __name__ == '__main__':
    unittest.main()
