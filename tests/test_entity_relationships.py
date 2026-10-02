import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import entity_relationships as relationships
import production_inventory as inventory


class EntityRelationshipsTest(unittest.TestCase):
    def compile(self, changed_episode=False):
        rows=[{**r,'id':r['object_id']+'-test','version':1} for r in inventory.compile_inventory()['records'] if r['kind']=='ENTITY']
        locked={r['object_id']:r for r in json.loads((ROOT/'production/source-lock.json').read_text())['episodes']}
        episodes={e['id']:e for e in json.loads((ROOT/'imports/screenplay-04.json').read_text())['episodes']}
        class Reader:
            @staticmethod
            def current_records(_store):return rows
            @staticmethod
            def ref_record(_store,ref):
                return {'object_id':ref['object_id'],'id':ref['revision_id'],'current_revision':'changed' if changed_episode else ref['revision_id'],'payload':episodes[ref['object_id']]}
            @staticmethod
            def record(_store,oid):raise KeyError(oid)
        return relationships.compile_relations(None,Reader),locked

    def test_sources_and_phase_specific_transfers_do_not_become_permanent_relations(self):
        value,locked=self.compile();rows={r['object_id']:r['payload'] for r in value['document']['records']}
        a=rows['relationship-zhao-keys-ownership'];b=rows['relationship-officer-cheng-keys-ownership']
        self.assertEqual(a['applies_to'][0]['scene_id'],'s002');self.assertEqual(b['applies_to'][0]['scene_id'],'s019')
        self.assertEqual(rows['relationship-offscreen-caller-li-ji-personal']['sources'][0]['scene_id'],'s040')
        self.assertEqual(rows['relationship-old-woman-thin-girl-personal']['label'],'带领同行')
        self.assertEqual(rows['relationship-li-ji-a-heng-personal']['direction'],'mutual')
        self.assertIn('↔',rows['relationship-li-ji-a-heng-personal']['blocks'][0]['text'])
        for r in rows.values():
            for source in r['sources']:
                self.assertEqual(source['revision_id'],locked[source['object_id']]['revision_id'])
                self.assertEqual(value['document']['expected_heads'][source['object_id']],source['revision_id'])
        self.assertTrue(all(r['kind']=='RELATION' for r in value['document']['records']))

    def test_new_script_revision_requires_rechecking_the_locked_input(self):
        with self.assertRaisesRegex(ValueError,'locked episode has a newer revision'):self.compile(changed_episode=True)

    def test_mutual_care_uses_both_actions_and_keeps_the_old_return_scene_as_context(self):
        value,_=self.compile()
        evidence=next(r for r in value['evidence'] if r['id']=='relationship-li-ji-a-heng-personal')
        self.assertEqual([s['scene_id'] for s in evidence['sources']],['s005','s040','s036'])
        self.assertIn('李寄：来，我给你撑着。',evidence['excerpts'][0]['text'])
        self.assertIn('阿蘅：拿这儿。别扯伤口。',evidence['excerpts'][0]['text'])
        self.assertIn('两个人各撑一端',evidence['excerpts'][0]['text'])
        self.assertIn('李寄掌心的新疤绷紧',evidence['excerpts'][1]['text'])
        self.assertIn('阿蘅：这一页我来。你念，慢一点。',evidence['excerpts'][1]['text'])
        self.assertIn('李寄看看没写完的半页，将笔交过去。',evidence['excerpts'][1]['text'])
        self.assertGreater(len(evidence['sources'][0]['block_ids']),1)

    def test_labels_follow_the_direction_and_do_not_claim_unwritten_performances(self):
        value,_=self.compile();rows={r['object_id']:r['payload'] for r in value['document']['records']}
        self.assertEqual(rows['relationship-meat-rice-bait-bait-basin-use']['label'],'盛在饵盆内')
        self.assertEqual(rows['relationship-troupe-workers-village-yard-performance']['label'],'参与搭台与散戏')
        self.assertEqual(rows['relationship-officer-cheng-stop-order-use']['label'],'持文书索取原祭册')
        self.assertEqual(rows['relationship-songbook-book-basket-spatial']['label'],'搁在倒扣竹篮上')


if __name__=='__main__':unittest.main()
