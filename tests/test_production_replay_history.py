import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from production_data import exact_replay


class ProductionReplayHistoryTest(unittest.TestCase):
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
        add('review','r3',3,'REPRESENTATION',review_model='entity-review-v1',entities=[ref('entity','e')],states=[ref('old-state','s')],status='withdrawn',merged_into=[ref('a-new-state','n')])
        add('scene','scene',1,'PREPARATION',state_model='complete-v1',occurrences=[])
        class Store:
            def revisions(self): return rows
            def objects(self): return [{'id':r['object_id'],'kind':json.loads(r['payload'])['format'].split('-')[1].upper()} for r in rows]
            def dependencies(self):
                return [{'from_revision':a,'to_revision':b} for a,b in [('s','e'),('n','e'),('r','e'),('r','s'),('j','r'),('r2','e'),('r2','s'),('r2','n'),('r3','e'),('r3','s'),('r3','n')]]
        class Production:
            FORMATS = {json.loads(r['payload'])['format'] for r in rows}
        replay = exact_replay(Store(),Production)
        order=[r['object_id']+str(r['expected_version']+1) for batch in replay['batches'] for r in batch['records']]
        self.assertLess(order.index('review1'),order.index('accept1'))
        self.assertLess(order.index('accept1'),order.index('a-new-state1'))
        self.assertLess(order.index('a-new-state1'),order.index('review2'))
        self.assertLess(order.index('a-new-state1'),order.index('review3'))


if __name__=='__main__': unittest.main()
