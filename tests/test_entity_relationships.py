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


if __name__=='__main__':unittest.main()
