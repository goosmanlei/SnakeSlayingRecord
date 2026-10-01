import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from production_data import exact_replay
from prepare_entity_reviews import build


class EntityReviewPreparationTest(unittest.TestCase):
    def test_initial_submissions_never_infer_candidates_or_overwrite_existing_review(self):
        entity = {'object_id':'entity-a','id':'e1','kind':'ENTITY','payload':{'title':'甲'}}
        state = {'object_id':'state-a','id':'s1','kind':'STATE','payload':{'entity':{'object_id':'entity-a'},'state_model':'complete-v1','sources':[{'scene_id':'s001'}]}}
        rows = [entity,state,{'object_id':'candidate','kind':'ASSET','payload':{'states':[{'object_id':'state-a'}]}}]
        class Production:
            @staticmethod
            def current_records(store): return rows
        class Review:
            @staticmethod
            def full_states(data, entity_id): return [r for r in data if r['kind']=='STATE' and r['payload']['entity']['object_id']==entity_id]
            @staticmethod
            def submission(row): return row['payload'].get('review_model')=='entity-review-v1'
        first = build(None,Production,Review)
        self.assertEqual(first['records'][0]['payload']['media'],[])
        self.assertEqual(first['expected_heads'],{'entity-a':'e1','state-a':'s1'})
        rows.append(first['records'][0])
        self.assertEqual(build(None,Production,Review)['records'],[])

    def test_replay_keeps_whole_collection_acceptance_before_later_state_and_submission(self):
        ref=lambda oid,rid:{'object_id':oid,'revision_id':rid}
        rows=[]
        def add(oid,rid,version,kind,**payload):
            rows.append({'object_id':oid,'id':rid,'version':version,'created_at':'same-second','payload':json.dumps({'format':'production-'+kind.lower()+'-v1',**payload})})
        add('entity','e',1,'ENTITY')
        add('old-state','s',1,'STATE',state_model='complete-v1',entity=ref('entity','e'))
        add('review','r',1,'REPRESENTATION',review_model='entity-review-v1',entities=[ref('entity','e')],states=[ref('old-state','s')])
        add('accept','j',1,'JUDGMENT',verdict='accepted',target=ref('review','r'))
        add('a-new-state','n',1,'STATE',state_model='complete-v1',entity=ref('entity','e'))
        add('review','r2',2,'REPRESENTATION',review_model='entity-review-v1',entities=[ref('entity','e')],states=[ref('old-state','s'),ref('a-new-state','n')])
        add('scene','scene',1,'PREPARATION',state_model='complete-v1',occurrences=[])
        class Store:
            def revisions(self): return rows
            def objects(self): return [{'id':r['object_id'],'kind':json.loads(r['payload'])['format'].split('-')[1].upper()} for r in rows]
            def dependencies(self):
                return [{'from_revision':a,'to_revision':b} for a,b in [('s','e'),('n','e'),('r','e'),('r','s'),('j','r'),('r2','e'),('r2','s'),('r2','n')]]
        class Production:
            FORMATS = {json.loads(r['payload'])['format'] for r in rows}
        replay = exact_replay(Store(),Production)
        order=[r['object_id']+str(r['expected_version']+1) for batch in replay['batches'] for r in batch['records']]
        self.assertLess(order.index('review1'),order.index('accept1'))
        self.assertLess(order.index('accept1'),order.index('a-new-state1'))
        self.assertLess(order.index('a-new-state1'),order.index('review2'))


if __name__=='__main__': unittest.main()
