import copy
import json
from pathlib import Path
import tempfile
import unittest
from review_desk.store import Store
from review_desk import production as p, production_current as current, production_current_migration as migration
from scripts.generation_publication import backup,build_plan,apply_plan

class CurrentPublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=Store(self.root/'source/.runtime/review.sqlite3');self.addCleanup(self.source.close)
        for name in ('one','other'):
            payload={'format':'production-entity-v1','title':name,'blocks':[{'id':'body','text':'old body '+name}],
                     'entity_type':'prop','aliases':[],'facts':[],'choices':[],'unknowns':[],'sources':[]}
            p.import_records(self.source,{'format':'production-import-v1','records':[{'object_id':name,'kind':'ENTITY','expected_version':0,'payload':payload}]})
        migration.apply(self.source,migration.plan(self.source))
        other=p.record(self.source,'other')
        self.source.create_comment({'id':'concurrent-opinion','target_object_id':'other','target_revision_id':other['id'],
            'expected_edit_token':other['edit_token'],'anchor':{'type':'global'},'body':'old feedback'})
        self.base=self.root/'baseline.sqlite3';backup(self.source.db_path,self.base)
        target=self.root/'formal/.runtime/review.sqlite3';target.parent.mkdir(parents=True);backup(self.base,target)
        self.formal=Store(target);self.addCleanup(self.formal.close)
        self.edit(self.source,'one','new current body')
        row=p.record(self.source,'one')
        self.source.create_comment({'id':'new-opinion','target_object_id':'one','target_revision_id':row['id'],
                                   'expected_edit_token':row['edit_token'],'anchor':{'type':'global'},'body':'new feedback'})
        self.plan=build_plan(self.base,self.source.db_path)
    def edit(self,store,oid,text):
        row=p.record(store,oid);payload=copy.deepcopy(row['payload']);payload['blocks'][0]['text']=text
        p.import_records(store,{'format':'production-import-v1','records':[{'object_id':oid,'kind':'ENTITY',
            'expected_version':row['version'],'expected_content':current.marker(row),'payload':payload}]})
    def test_current_increment_preserves_unrelated_feedback_and_replays(self):
        self.formal.change_comment('concurrent-opinion','EDIT',1,'live feedback')
        self.assertNotIn('old body one',json.dumps(self.plan))
        self.assertFalse(apply_plan(self.formal.db,self.plan)['already_published'])
        self.assertEqual(p.record(self.formal,'one')['payload']['blocks'][0]['text'],'new current body')
        self.assertEqual(self.formal.comment('concurrent-opinion')['body'],'live feedback')
        self.assertTrue(apply_plan(self.formal.db,self.plan)['already_published'])
        self.assertEqual(self.formal.db.execute("SELECT count(*) FROM revisions WHERE object_id='one'").fetchone()[0],1)
    def test_conflicting_current_change_is_atomic(self):
        self.edit(self.formal,'one','concurrent current body')
        before='\n'.join(self.formal.db.iterdump())
        with self.assertRaisesRegex(ValueError,'formal row changed'):apply_plan(self.formal.db,self.plan)
        self.assertEqual('\n'.join(self.formal.db.iterdump()),before)
    def test_corrupt_current_body_rolls_back(self):
        plan=copy.deepcopy(self.plan)
        row=plan['changes']['revisions'][0]['after'];body=json.loads(row['payload']);body['blocks'][0]['text']='forged body';row['payload']=json.dumps(body)
        before='\n'.join(self.formal.db.iterdump())
        with self.assertRaisesRegex(ValueError,'checksum'):apply_plan(self.formal.db,plan)
        self.assertEqual('\n'.join(self.formal.db.iterdump()),before)

if __name__=='__main__':unittest.main()
