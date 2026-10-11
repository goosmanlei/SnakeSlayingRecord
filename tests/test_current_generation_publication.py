import copy
import json
from pathlib import Path
import tempfile
import unittest
from review_desk.store import Store
from review_desk import production as p, production_current as current, production_current_migration as migration
from scripts.generation_publication import backup,build_plan,apply_plan,publication_id
from scripts.production_current_publication import verify_applied
from scripts.publish_generation import formal_application_stopped

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

    def test_post_commit_readback_detects_missing_or_later_changed_content(self):
        identity=publication_id(self.plan)
        with self.assertRaisesRegex(ValueError, 'receipt is missing'):
            verify_applied(self.formal.db,self.plan,identity)
        apply_plan(self.formal.db,self.plan)
        self.assertEqual(verify_applied(self.formal.db,self.plan,identity)['integrity'],'ok')
        self.edit(self.formal,'one','different current content')
        with self.assertRaisesRegex(ValueError, 'readback differs'):
            verify_applied(self.formal.db,self.plan,identity)

    def test_host_publication_requires_exact_stopped_container(self):
        target=self.formal.db_path.parent.parent
        container={'Id':'exact-app','Mounts':[{'Destination':'/instance','Source':str(target)}],
                   'State':{'Running':True}}
        with self.assertRaisesRegex(ValueError,'stop the verified'):
            formal_application_stopped(target,lambda _:container)
        container['State']['Running']=False
        self.assertEqual(formal_application_stopped(target,lambda _:container)['container_id'],'exact-app')
        container['Mounts'][0]['Source']=str(self.root/'unrelated')
        with self.assertRaisesRegex(ValueError,'mount differs'):
            formal_application_stopped(target,lambda _:container)
    def test_corrupt_current_body_rolls_back(self):
        plan=copy.deepcopy(self.plan)
        row=plan['changes']['revisions'][0]['after'];body=json.loads(row['payload']);body['blocks'][0]['text']='forged body';row['payload']=json.dumps(body)
        before='\n'.join(self.formal.db.iterdump())
        with self.assertRaisesRegex(ValueError,'checksum'):apply_plan(self.formal.db,plan)
        self.assertEqual('\n'.join(self.formal.db.iterdump()),before)

    def test_semantic_merge_and_candidate_retirement_publish_without_rewriting_history(self):
        import io
        import wave
        from review_desk import semantic_consolidation as sem
        from review_desk.production_media import ingest
        source=Store(self.root/'semantic/.runtime/review.sqlite3');self.addCleanup(source.close)
        def put(oid,kind,**fields):
            payload={'format':'production-'+p.KINDS[kind]+'-v1','title':oid,
                     'blocks':[{'id':'body','text':oid}],**fields}
            p.import_records(source,{'format':'production-import-v1','records':[
                {'object_id':oid,'kind':kind,'expected_version':0,'payload':payload}]})
        def ref(oid):return {'object_id':oid,'revision_id':p.record(source,oid)['id']}
        put('subject','ENTITY',entity_type='prop',aliases=[],facts=[],choices=[],unknowns=[],sources=[])
        for oid in ('need-a','need-b'):
            put(oid,'REQUIREMENT',scope=ref('subject'),slot=oid,required=False,purpose='同一翻页声音',
                media_type='audio',usage='review_reference',entities=[ref('subject')],states=[],specification={})
        put('recording','CALL',method='recording',tool='test',status='submitted',inputs=[],outputs=[])
        audio=io.BytesIO()
        with wave.open(audio,'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(48000);wav.writeframes(b'\0\0'*480)
        audio.seek(0);component=ingest(source.db_path.parent.parent,audio,'voice.wav')
        put('voice','ASSET',media_type='audio',subjects=[],states=[],components=[component],
            production=ref('recording'),lineage={},candidate_requirements=[ref('need-b')])
        migration.apply(source,migration.plan(source))
        base=self.root/'semantic-base.sqlite3';backup(source.db_path,base)
        path=self.root/'semantic-formal/.runtime/review.sqlite3';path.parent.mkdir(parents=True)
        backup(base,path);formal=Store(path);self.addCleanup(formal.close)
        before_call=copy.deepcopy(p.record(formal,'recording')['payload'])
        sem.apply(source,sem.prepare(source,{'merges':[{'source':'need-b','target':'need-a','reason':'相同实际用途'}],
            'retire_candidates':[{'source':'voice','reason':'没有当前用途的试样','remove_files':False}]}))
        # Later cleanup preserves the first original hash, not the receipt hash.
        sem.apply(source,sem.prepare(source,{'retire_candidates':[
            {'source':'voice','reason':'确认无输入和原意见依赖，可清理原件','remove_files':True}]}))
        plan=build_plan(base,source.db_path)
        self.assertFalse(apply_plan(formal.db,plan)['already_published'])
        self.assertTrue(apply_plan(formal.db,plan)['already_published'])
        self.assertTrue(sem.is_retired(p.record(formal,'need-b')['payload']))
        self.assertTrue(sem.is_retired(p.record(formal,'voice')['payload']))
        self.assertEqual(p.record(formal,'recording')['payload'],before_call)
        self.assertFalse(formal.db.execute("SELECT 1 FROM production_candidates WHERE asset_object_id='voice'").fetchone())
        sem.validate(formal)

if __name__=='__main__':unittest.main()
