import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_full_generation as prep
from material_model_io import read_framework,read_json,read_bytes
from register_full_generation import image_spec


def current_rows():
    data = read_framework(ROOT / 'export/objects.json')
    revisions = {r['id']: r for r in data['revisions']}
    return [{**o, 'payload': json.loads(revisions[o['current_revision']]['payload'])} for o in data['objects']]


class FullGenerationTest(unittest.TestCase):
    def setUp(self):
        self.rows = current_rows(); self.by = {r['id']: r for r in self.rows}

    def test_scope_and_reference_dependencies_exclude_non_image_states(self):
        # This planner intentionally guards the approved task-20261002-0003
        # scope. Replay its exact saved heads; newer story states are not an
        # authorization to expand that historical generation batch.
        data = read_framework(ROOT / 'export/objects.json')
        revisions = {r['id']: r for r in data['revisions']}
        heads = read_json(ROOT / 'production/full-generation/source-lock.json')['formal_heads']
        rows = [{**self.by[h['object_id']], 'current_revision':h['revision_id'],
                 'current_version':h['version'], 'payload':json.loads(revisions[h['revision_id']]['payload'])}
                for h in heads]
        by = {r['id']: r for r in rows}
        images, states = prep.image_plans(rows, by)
        self.assertEqual(len(images), 251)
        self.assertEqual(len({i['state']['object_id'] for i in images}), 251)
        self.assertEqual(sum(i['is_baseline'] for i in images), 125)
        excluded = {s['id'] for s in states} - {i['id'] for i in images}
        self.assertEqual(len(excluded), 16)
        self.assertTrue({'form-offscreen-caller-base','form-stage-drum-audible','form-xiao-man-base','form-xu-bride-base'} <= excluded)
        self.assertTrue({'form-bandage-base','form-bandage-head','form-bandage-blood','form-bandage-new'} <= excluded)
        original,_=prep.image_plans(rows,by,apply_scope_amendment=False)
        self.assertEqual({i['id'] for i in original}-{i['id'] for i in images},
                         {'form-bandage-base','form-bandage-head','form-bandage-blood','form-bandage-new'})
        for i in images:
            self.assertEqual(bool(i['generation']['inputs']), not i['is_baseline'])
            if not i['is_baseline']:
                self.assertEqual(i['execution']['binding_status'], 'pending_approved_master')
                self.assertTrue(i['generation']['blockers'])
                self.assertEqual(i['generation']['inputs'][0]['reference']['object_id'], 'need-'+i['baseline_state']['object_id']+'-overall')

    def test_scope_or_screenplay_drift_fails_before_generation(self):
        locked = read_json(ROOT / 'production/full-generation/source-lock.json')
        old_ids = {r['object_id'] for r in locked['formal_heads']}
        added_states = {r['id'] for r in self.rows if r['kind']=='STATE'
                        and r['payload'].get('state_model')=='complete-v1' and r['id'] not in old_ids}
        self.assertTrue({'form-blue-awning-song-recited','form-granary-rice-measure-base'} <= added_states)
        with self.assertRaisesRegex(AssertionError, 'scope changed'):
            prep.image_plans(self.rows, self.by)
        rows = copy.deepcopy(self.rows)
        rows.append({**next(r for r in rows if r['id']=='form-li-ji-paste'), 'id':'form-unreviewed'})
        with self.assertRaisesRegex(AssertionError, 'scope changed'):
            prep.image_plans(rows,self.by)
        locked=json.loads((ROOT/'production/source-lock.json').read_text())
        self.by[locked['episodes'][0]['object_id']]['current_revision']='unexpected-revision'
        with self.assertRaisesRegex(AssertionError,'formal episode changed'):
            prep.source_map(self.by)

    def test_voiced_identities_samples_and_changed_voice_coverage(self):
        _, _, blocks = prep.source_map(self.by)
        voices, _, _ = prep.voice_plans(self.rows,self.by,blocks)
        self.assertEqual(len(voices),42)
        self.assertEqual(sum(v['kind']=='base' for v in voices),40)
        self.assertEqual(sum(len(v['coverage']) for v in voices),76)
        base=next(v for v in voices if v['id']=='voice-a-heng-base')
        self.assertNotIn('form-a-heng-hoarse',[r['object_id'] for r in base['coverage']])
        self.assertNotIn('form-a-heng-tears',[r['object_id'] for r in base['coverage']])
        self.assertFalse(any(r['object_id']=='form-li-dan-memory' for v in voices for r in v['coverage']))
        for v in voices:
            for s in v['samples']:
                self.assertIn(s['text'],blocks[s['source']['block_ids'][0]]['text'])
        self.assertEqual(sum('借用' in v['sample_policy'] for v in voices),7)

    def test_native_size_policy_does_not_rewrite_old_requirement(self):
        old={'native_4k':True,'minimum_long_edge':3840,'reference_role':'overall'}
        new=image_spec(old)
        self.assertEqual(old['minimum_long_edge'],3840)
        self.assertNotIn('minimum_long_edge',new)
        self.assertFalse(new['native_4k'])
        self.assertEqual(new['native_resolution_policy'],'highest_provider_native')

    def test_registered_actual_inputs_and_originals_match_saved_requests(self):
        directory=ROOT/'production/full-generation'
        locked=json.loads((directory/'call-input-lock.json').read_text())
        digest=hashlib.sha256(json.dumps(locked,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        request=read_json(ROOT/'production/requests/fg3-liji-image-01.json')
        self.assertEqual(request['source_lock_sha256'],digest)
        registration=read_json(directory/'registration.json')
        records=[r for batch in registration['batches'] for r in batch['records']]
        calls={r['object_id']:r['payload'] for r in records if r['kind']=='CALL' and r['expected_version']==0}
        assets=[r['payload'] for r in records if r['kind']=='ASSET']
        self.assertEqual(len(calls),6);self.assertEqual(len(assets),6)
        for asset in assets:
            call=calls[asset['production']['object_id']]
            components={c['id']:c for c in asset['components']}
            for component in components.values():
                content=read_bytes(ROOT/'export/assets'/component['file'])
                self.assertEqual(hashlib.sha256(content).hexdigest(),component['sha256'])
            actual=read_json(ROOT/'export/assets'/components['request']['file'])
            submitted=actual['request']['params']['prompt'] if asset['media_type']=='image' else actual['text_prompt']
            self.assertEqual(call['prompt'],submitted)
            self.assertEqual(call['request_file_sha256'],components['request']['sha256'])


if __name__ == '__main__':unittest.main()
