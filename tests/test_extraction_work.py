import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import extraction_work as work, unique_origin

try:
    from review_desk import production as p, production_current as current
    from review_desk import semantic_consolidation as semantic, business_relations
    sys.path.insert(0, str(Path(p.__file__).resolve().parents[1] / 'tests'))
    import test_production_current as fixture
except ImportError:
    fixture = None


@unittest.skipIf(fixture is None, 'run with the managed desk on PYTHONPATH')
class ExtractionTransactionTest(unittest.TestCase):
    if fixture:
        for name in ('setUp', 'tearDown', 'spec', 'put', 'ref', 'entity', 'full',
                     'need', 'setup_plans', 'media', 'migrate'):
            locals()[name] = getattr(fixture.CurrentProductionTest, name)

    def relation(self):
        endpoints = sorted(['need-full-overall', 'need-wet-overall'])
        oid = business_relations.identity(endpoints)
        self.put(self.spec(oid, 'RELATION', relation_type='business', direction='related',
                           endpoints=endpoints, summary='Independent forms to compare',
                           sources=[self.ref('wet')], contexts=[self.ref('wet')],
                           blocks=[{'id':'comparison','text':'Read the real separate papers'}]))
        return oid

    def test_identity_handoff_does_not_add_entity_fields_to_a_relation(self):
        self.migrate()
        self.put(self.entity('separate'))
        oid = self.relation()
        plan, _ = unique_origin.build(self.store, {'states': {'wet': {
            'action': 'remove', 'reason': 'A separate identity, not a form of songbook',
            'destination': 'entity', 'condition': 'Preserve the real independent paper',
            'condition_entity': 'separate', 'replace_entity': 'separate',
            'replace_consumer_entity': True, 'requirement_handoffs': [{
                'object_id': 'need-wet-overall', 'scope': 'separate',
                'title': 'Separate paper structure reference'}]}}})
        semantic.apply(self.store, plan)
        self.assertNotIn('entities', p.record(self.store, oid)['payload'])
        self.assertEqual(p.record(self.store, 'need-wet-overall')['payload']['scope'], self.ref('separate'))
        self.assertTrue(semantic.is_retired(p.record(self.store, 'wet')['payload']))

    def test_reparent_and_lost_receipt_resume_keep_originals_and_foreign_content(self):
        self.migrate()
        rows = {r['object_id']: r for r in p.current_records(self.store)
                if r['kind'] in ('ENTITY', 'STATE', 'REQUIREMENT')}
        value = {'episode': 1, 'objects': copy.deepcopy(rows)}
        decision = {'reviewed_ids': sorted(rows), 'assessment': 'Read the real identity',
                    'continuity': 'Keep the independent paper and its consumers',
                    'new_entities': {'separate': self.entity('separate')['payload']},
                    'state_owners': {'full': 'separate'}}
        folder = Path(self.tmp.name) / 'author'
        folder.mkdir()
        saved = semantic.apply
        def accepted_then_lost(*args):
            saved(*args)
            raise OSError('receipt interrupted after commit')
        with patch.object(semantic, 'apply', accepted_then_lost), self.assertRaises(OSError):
            work.apply(self.store, value, decision, {'sha256': 'exact', 'version': 8}, folder)
        count = self.store.db.execute('SELECT count(*) FROM production_current_operations').fetchone()[0]
        self.put(self.entity('foreign'))
        receipt = work.apply(self.store, value, decision, {'sha256': 'exact', 'version': 8}, folder)
        self.assertTrue(receipt['already_applied'])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM production_current_operations').fetchone()[0], count)
        self.assertEqual(p.record(self.store, 'full')['payload']['entity'], self.ref('separate'))
        self.assertEqual(p.record(self.store, 'need-full-overall')['payload']['entities'], [self.ref('separate')])
        self.assertEqual(p.record(self.store, 'wet')['payload']['entity'], self.ref('songbook'))
        self.assertEqual(p.record(self.store, 'foreign')['kind'], 'ENTITY')

    def test_released_pose_moves_to_continuity_without_retiring_its_real_need(self):
        self.migrate()
        from audiovisual_fixture import composition
        composition(self, shot_values={'states': [self.ref('full')],
                    'entities': [self.ref('songbook')]})
        rows = {r['object_id']: r for r in p.current_records(self.store)
                if r['kind'] in ('ENTITY', 'STATE', 'REQUIREMENT', 'AV_SHOT')}
        value = {'episode': 1, 'objects': copy.deepcopy(rows)}
        decision = {'reviewed_ids': sorted(rows), 'assessment': 'Read the release',
                    'continuity': 'Keep the earlier pose as history',
                    'released_states': {'shot': ['full']},
                    'release_conditions': {'shot': 'Hands have left the beam.'}}
        folder = Path(self.tmp.name) / 'release'; folder.mkdir()
        work.apply(self.store, value, decision, {'sha256': 'exact', 'version': 8}, folder)
        body = p.record(self.store, 'shot')['payload']
        self.assertEqual(body['states'], [])
        self.assertEqual(body['continuity_context'], [self.ref('full')])
        self.assertFalse(semantic.is_retired(p.record(self.store, 'full')['payload']))
        self.assertEqual(p.record(self.store, 'need-full-overall')['payload']['scope'], self.ref('full'))

    def test_current_name_prefix_survives_a_later_consumer_pass(self):
        self.migrate()
        row = p.record(self.store, 'songbook')
        body = copy.deepcopy(row['payload'])
        body['title'] = 'Songbook fragments'
        body['blocks'] = [{'id': 'description', 'text': 'Songbook fragments and Songbook'}]
        semantic.apply(self.store, semantic.prepare(self.store, {'updates': [{
            'object_id': 'songbook', 'payload': body, 'reason': 'Explicit reviewed name'}]}))
        row = p.record(self.store, 'songbook')
        folder = Path(self.tmp.name) / 'names'; folder.mkdir()
        work.apply(self.store, {'episode': 0, 'objects': {'songbook': row}}, {
            'reviewed_ids': ['songbook'], 'assessment': 'Update stale consumer names',
            'continuity': 'Already-current names must remain current',
            'text_replacements': {'Songbook': 'Songbook fragments'}},
            {'sha256': 'exact', 'version': 8}, folder)
        actual = p.record(self.store, 'songbook')['payload']
        self.assertEqual(actual['title'], 'Songbook fragments')
        self.assertEqual(actual['blocks'][0]['text'], 'Songbook fragments and Songbook fragments')


if __name__ == '__main__':
    unittest.main()
