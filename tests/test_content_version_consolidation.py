import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import content_version_consolidation as migration
import content_version_release as release


class FrozenContentTest(unittest.TestCase):
    def test_lfs_original_must_match_committed_hash_and_size(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'export/material-content.json';path.parent.mkdir();path.write_bytes(b'content graph')
            pointer=('version https://git-lfs.github.com/spec/v1\noid sha256:'+migration.sha(path)+'\nsize 13\n').encode()
            with patch.object(release.base,'git_file',return_value=pointer):
                release.verify_committed_file(root,'candidate','export/material-content.json')
                path.write_bytes(b'changed graph')
                with self.assertRaisesRegex(ValueError,'LFS original differs'):
                    release.verify_committed_file(root,'candidate','export/material-content.json')

    def test_ordinary_file_cannot_use_a_pointer_as_an_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'plan.json';path.write_bytes(b'plan')
            with patch.object(release.base,'git_file',return_value=b'previous plan'):
                with self.assertRaisesRegex(ValueError,'uncommitted migration input'):
                    release.verify_committed_file(root,'candidate','plan.json')


class FileRecoveryTest(unittest.TestCase):
    def test_metadata_counts_and_hashes_are_not_discarded_business_bodies(self):
        self.assertFalse(migration.business_copy({'revisions':{'count':12,'sha256':'abc'},'material_content':42,'recipes':3}))
        self.assertTrue(migration.business_copy({'revisions':[{'payload':json.dumps({'format':'production-state-v1','description':'old full state'})}]}))
        self.assertTrue(migration.business_copy({'format':'full-generation-recipes-v1','images':[]}))
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'production').mkdir();(self.root/'.runtime').mkdir()
        self.rows=[]
        for name,action in [('old.json','delete'),('package.json','retire')]:
            path=self.root/'production'/name;path.write_text('old business content')
            row={'path':'production/'+name,'action':action,'before_sha256':migration.sha(path),'before_bytes':path.stat().st_size}
            if action=='retire':
                row['receipt']={'format':'retired-production-package-v1','source_sha256':row['before_sha256']}
                row['after_sha256']=hashlib.sha256((json.dumps(row['receipt'],ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
            self.rows.append(row)
        self.plan={'id':'approved','files':{'operations':self.rows,'retained':[],'counts':{'delete_files':1,'retire_packages':1}}}
        db=sqlite3.connect(self.root/'.runtime/review.sqlite3');db.execute('CREATE TABLE consolidation_runs(id TEXT PRIMARY KEY,receipt TEXT)');db.execute("INSERT INTO consolidation_runs VALUES ('approved','{}')");db.commit();db.close()

    def test_files_are_checked_as_one_set_before_changes(self):
        (self.root/'production/package.json').write_text('concurrent change')
        with self.assertRaisesRegex(ValueError,'drift'):migration.check_files(self.root,self.plan)
        self.assertTrue((self.root/'production/old.json').exists())

    def test_paths_cannot_escape_through_a_symlink(self):
        (self.root/'linked').symlink_to('/tmp',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):migration.safe(self.root,'linked/a')
        with self.assertRaises(ValueError):migration.safe(self.root,'../a')

    def committed_head(self):
        import os
        system=os.environ.get('REVIEW_DESK_SYSTEM')
        if not system:self.skipTest('REVIEW_DESK_SYSTEM points to the managed system candidate')
        sys.path.insert(0,system)
        from review_desk import version_consolidation as vc
        from review_desk.store import Store,canonical,digest
        db=Store.open_readonly(self.root/'.runtime/review.sqlite3')
        current=digest(canonical({k:v for k,v in vc.fingerprint(db).items() if k!='consolidation_runs'}).encode());db.close()
        with sqlite3.connect(self.root/'.runtime/review.sqlite3') as db:
            db.execute('UPDATE consolidation_runs SET receipt=?',(json.dumps({'database_head_sha256':current}),))

    def test_file_failure_resumes_after_committed_database(self):
        self.committed_head()
        with self.assertRaisesRegex(RuntimeError,'injected'):
            migration.apply_files(self.root,self.plan,self.root/'receipt.json',fault_after=1)
        self.assertFalse((self.root/'production/old.json').exists())
        result=migration.apply_files(self.root,self.plan,self.root/'receipt.json')
        self.assertEqual(result['additional_changed_files'],1)
        self.assertEqual(migration.apply_files(self.root,self.plan,self.root/'receipt.json')['additional_changed_files'],0)

    def test_a_post_commit_writer_stops_remaining_file_deletions(self):
        self.committed_head()
        with self.assertRaises(RuntimeError):migration.apply_files(self.root,self.plan,self.root/'receipt.json',fault_after=1)
        with sqlite3.connect(self.root/'.runtime/review.sqlite3') as db:
            db.execute('CREATE TABLE reviewer_change(value TEXT)');db.execute("INSERT INTO reviewer_change VALUES ('new content')")
        with self.assertRaisesRegex(ValueError,'database drift'):migration.apply_files(self.root,self.plan,self.root/'receipt.json')
        self.assertEqual((self.root/'production/package.json').read_text(),'old business content')

if __name__=='__main__':unittest.main()
