import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import production_inventory as inventory
import episode01_shots as shots


class FullFormsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=inventory.compile_inventory()
        cls.rows={r['object_id']:{**r,'id':'@'+r['object_id']} for r in cls.document['records']}
        class Reader:
            KINDS={'SHOT_DESIGN':'shot-design','REQUIREMENT':'requirement'}
            @staticmethod
            def record(_store,oid):return cls.rows[oid]
        cls.shots,cls.cues,cls.frames=shots.compile_shots(None,Reader)

    def form_keys(self,entity,sn):
        o=next(o for o in self.rows[f'preparation-s{sn:03d}']['payload']['occurrences'] if o['entity']['object_id']=='entity-'+entity)
        return [s['object_id'] for s in o['states']],o

    def test_every_actual_appearance_and_shot_entity_has_full_owned_form(self):
        entities={r['object_id'] for r in self.document['records'] if r['kind']=='ENTITY'}
        forms=[r for r in self.document['records'] if r['kind']=='STATE']
        self.assertEqual({r['payload']['entity']['object_id'] for r in forms},entities)
        self.assertEqual(len(entities),133)
        self.assertEqual(len([r for r in self.document['records'] if r['kind']=='PREPARATION']),42)
        groups=[]
        for r in self.document['records']:
            if r['kind']=='PREPARATION':groups.extend(([o['entity']],o['states']) for o in r['payload']['occurrences'])
        for r in self.shots['records']:
            if r['kind']=='SHOT_DESIGN':groups.append((r['payload']['entities'],r['payload']['states']))
        for es,ss in groups:
            self.assertEqual({e['object_id'] for e in es},{self.rows[s['object_id']]['payload']['entity']['object_id'] for s in ss})
            for s in ss:self.assertEqual(self.rows[s['object_id']]['payload']['state_model'],'complete-v1')

    def test_simultaneous_injuries_are_one_snapshot_and_wet_trousers_are_not_missed(self):
        keys,o=self.form_keys('li-ji',31)
        self.assertEqual(keys,['form-li-ji-healing','form-li-ji-blood'])
        for key in keys:
            body=self.rows[key]['payload']['blocks'][0]['text']
            self.assertIn('掌心',body);self.assertIn('额角',body)
        keys,o=self.form_keys('li-ji',6)
        self.assertEqual(keys,['form-li-ji-wrapped','form-li-ji-splash'])
        self.assertTrue(o['transitions'][0]['source']['block_ids'][0].endswith('b031'))

    def test_bag_and_book_changes_are_exact_first_and_last_frame_inputs(self):
        rows={r['object_id']:r['payload'] for r in self.shots['records']}
        self.assertIn('form-rice-bag-base',{s['object_id'] for s in rows['need-shot-e01-009-composition']['states']})
        self.assertIn('form-rice-bag-wages',{s['object_id'] for s in rows['need-shot-e01-009-end-keyframe']['states']})
        for number,expected in [(24,'form-songbook-papers-on-top'),(25,'form-songbook-inserted')]:
            self.assertIn(expected,{s['object_id'] for s in rows[f'need-shot-e01-{number:03d}-end-keyframe']['states']})
        self.assertEqual(self.form_keys('rice-bag',1)[0],['form-rice-bag-base','form-rice-bag-wages','form-rice-bag-advance'])

    def test_audio_also_binds_full_state_and_dog_actions_do_not_split_forms(self):
        for r in self.shots['records']:
            if r['kind']=='REQUIREMENT' and r['payload']['media_type']=='audio' and r['payload']['entities']:
                self.assertTrue(r['payload']['states'],r['object_id'])
        self.assertEqual(self.form_keys('mo-er',2)[0],['form-mo-er-base'])
        self.assertEqual(len(self.cues),37);self.assertEqual(self.frames,227*24)

    def test_mention_only_entities_get_facts_without_media_requirements(self):
        for key in ('xiao-man','xu-bride'):
            form=self.rows[f'form-{key}-base']['payload']
            self.assertEqual(form['reference_media'],'none')
            self.assertNotIn(f'need-form-{key}-base-overall',self.rows)
        ahe=self.rows['entity-a-he']['payload']['facts'][0]
        self.assertIn('李诞回忆',ahe);self.assertIn('没有阿禾台词',ahe);self.assertIn('陶伯当堂证词',ahe)

    def test_doors_can_return_to_same_state_with_ordered_evidence(self):
        keys,o=self.form_keys('cave-gate',18)
        self.assertEqual(keys,['form-cave-gate-base','form-cave-gate-up','form-cave-gate-base'])
        self.assertEqual([t['source']['block_ids'][0].rsplit('-',1)[-1] for t in o['transitions']],['b024','b034'])


if __name__=='__main__':unittest.main()
