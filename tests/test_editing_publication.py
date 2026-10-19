"""Real editing output through the production CAS increment, including rejection."""
import copy
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_editing_recovery as fixtures
from review_desk import editing as edit,editing_worker as worker
from review_desk.store import Store,canonical
from review_desk.version_consolidation import new_identity
from scripts.generation_publication import backup,build_plan,apply_plan
from scripts.production_current_publication import publication_media,verify_applied


class EditingPublicationTest(unittest.TestCase):
    for name in ('tearDown','spec','put','ref','entity','full','need','setup_plans','media','migrate'):
        locals()[name]=getattr(fixtures.EditingRecoveryTest,name)

    def setUp(self):
        fixtures.EditingRecoveryTest.setUp(self)

    def test_actual_film_increment_replay_media_rejection_and_project_conflict(self):
        original=edit.save(self.store,self.root,self.project,0)
        self.store.create_comment({'id':'live-original-opinion','target_object_id':original['object_id'],'target_revision_id':original['id'],
            'anchor':{'type':'global'},'body':'正式工程上的原意见'})
        baseline=self.root/'editing-baseline.sqlite3';backup(self.store.db_path,baseline)
        revised=copy.deepcopy(self.project);revised['title']='修改后工程'
        saved=edit.save(self.store,self.root,revised,1)
        job=edit.submit(self.store,self.root,saved['object_id'],2,'publication-test','render')
        worker.work(self.root,once=True);result=worker.result(self.store,self.root,job['id'])
        self.assertEqual(result['status'],'succeeded',result)
        film=result['output'];clean=next(c for c in film['payload']['components'] if c['id']=='clean')
        comment=self.store.create_comment({'id':'new-film-opinion','target_object_id':film['object_id'],'target_revision_id':film['id'],
            'anchor':{'type':'time','component_id':'clean','asset_file':clean['file'],'start_seconds':.8,'end_seconds':1.2},'body':'准确成片范围'})
        plan=build_plan(baseline,self.store.db_path)
        def destination(name):
            root=self.root/name;dbfile=root/'.runtime/review.sqlite3';dbfile.parent.mkdir(parents=True)
            backup(baseline,dbfile);shutil.copytree(self.root/'export/assets',root/'export/assets')
            store=Store(dbfile);self.addCleanup(store.close);return store
        formal=destination('formal')
        # An unrelated opinion edited after the baseline survives publication.
        formal.change_comment('live-original-opinion','EDIT',1,'正式库后来补充的意见')
        opinion=formal.comment('live-original-opinion')
        real_probe=edit.probe_source;real_open=Path.open
        def probe(path):
            self.assertFalse(formal.db.in_transaction,'ffprobe under publication transaction')
            return real_probe(path)
        def opened(path,*args,**kwargs):
            if path.suffix=='.mp4':self.assertFalse(formal.db.in_transaction,'movie bytes read under publication transaction')
            return real_open(path,*args,**kwargs)
        with patch.object(edit,'probe_source',probe),patch.object(Path,'open',opened):
            receipt=apply_plan(formal.db,plan)
        self.assertFalse(receipt['already_published'])
        self.assertTrue(apply_plan(formal.db,plan)['already_published'])
        self.assertEqual(edit.read(formal,saved['object_id'])['payload'],revised)
        self.assertEqual(edit.read(formal,film['object_id'])['payload'],film['payload'])
        self.assertEqual(formal.comment(opinion['id']),opinion)
        self.assertEqual(formal.comment(comment['id']),comment)
        self.assertEqual(verify_applied(formal.db,plan,receipt['publication_id'])['integrity'],'ok')
        rejected=destination('rejected');bad=copy.deepcopy(plan)
        payload=copy.deepcopy(film['payload']);component=copy.deepcopy(self.project['sources'][0]['component']);component['id']='clean'
        payload['components']=[component if c['id']=='clean' else c for c in payload['components']]
        new_id=new_identity(self.store,film['object_id'],1,payload)
        for change in bad['changes']['revisions']:
            if change['after']['id']==film['id']:change['after']['payload']=canonical(payload)
        def replace(value):
            if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
            if isinstance(value,list):return [replace(v) for v in value]
            return new_id if value==film['id'] else value
        bad=replace(bad);bad['media']=publication_media(bad['changes'])
        before='\n'.join(rejected.db.iterdump())
        with self.assertRaisesRegex(ValueError,'film audio must be stereo 48 kHz|film frame count or duration differs'):
            apply_plan(rejected.db,bad)
        self.assertEqual('\n'.join(rejected.db.iterdump()),before)
        conflict=destination('conflict');concurrent=copy.deepcopy(self.project);concurrent['title']='正式库独立修改'
        edit.save(conflict,conflict.db_path.parent.parent,concurrent,1)
        before='\n'.join(conflict.db.iterdump())
        with self.assertRaisesRegex(ValueError,'formal row changed'):
            apply_plan(conflict.db,plan)
        self.assertEqual('\n'.join(conflict.db.iterdump()),before)


if __name__=='__main__':unittest.main()
