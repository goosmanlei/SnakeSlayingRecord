"""Release guards and preservation checks; no formal Docker/DB writes."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import material_review_release as r

class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.before=self.root/'before.sqlite3';self.after=self.root/'after.sqlite3'
        with sqlite3.connect(self.before) as db:
            db.executescript("CREATE TABLE revisions(id TEXT PRIMARY KEY,payload TEXT);CREATE TABLE comments(id TEXT PRIMARY KEY,body TEXT);CREATE TABLE comment_events(id INTEGER PRIMARY KEY,body TEXT);INSERT INTO revisions VALUES ('one','unchanged');INSERT INTO comments VALUES ('c','original');INSERT INTO comment_events VALUES (1,'CREATE');")
        shutil.copyfile(self.before,self.after)

    def test_concurrent_user_comment_edit_keeps_history_and_is_not_restored(self):
        with sqlite3.connect(self.after) as db:
            db.execute("UPDATE comments SET body='user edit'");db.execute("INSERT INTO comment_events VALUES (2,'EDIT')");db.execute('CREATE INDEX revision_lookup ON revisions(payload)')
        result=r.preserved(self.before,self.after);self.assertEqual(result['revisions']['before'],1);self.assertEqual(result['comment_events']['after'],2)
        self.assertEqual(sqlite3.connect(self.after).execute('SELECT body FROM comments').fetchone()[0],'user edit')

    def test_lost_revision_event_or_comment_identity_is_rejected(self):
        for table in ('revisions','comment_events','comments'):
            shutil.copyfile(self.before,self.after)
            with sqlite3.connect(self.after) as db:db.execute('DELETE FROM '+table)
            with self.assertRaisesRegex(ValueError,'lost'):r.preserved(self.before,self.after)

    def test_unconfirmed_flag_or_changed_digests_stop_before_action(self):
        args=argparse.Namespace(apply=False,bundle=self.root,manifest_sha256='wrong',image_receipt_sha256='wrong')
        with patch.object(r,'load_bundle') as load:
            with self.assertRaisesRegex(ValueError,'confirmation'):r.authorized(args)
            load.assert_not_called()
        (self.root/'manifest.json').write_text('{}');(self.root/'image.json').write_text('{}');args.apply=True
        with patch.object(r,'load_bundle',return_value=(self.root,{})):
            with self.assertRaisesRegex(ValueError,'digest'):r.authorized(args)

    def test_foreign_bundle_cannot_use_restart(self):
        r.save(self.root/'manifest.json',{'format':'another-task'});r.save(self.root/'image.json',{})
        with patch.object(r,'inspect') as inspect:
            with self.assertRaisesRegex(ValueError,'not this release'):r.restart(argparse.Namespace(apply=True,release=self.root))
            inspect.assert_not_called()

    def test_replacing_round_member_at_same_row_count_is_rejected(self):
        for path in (self.before,self.after):
            with sqlite3.connect(path) as db:
                db.executescript("CREATE TABLE material_members(material_id TEXT,number INTEGER,revision_id TEXT);INSERT INTO material_members VALUES ('need',1,'original');")
        with sqlite3.connect(self.after) as db:db.execute("UPDATE material_members SET revision_id='unrelated'")
        with self.assertRaisesRegex(ValueError,'identities lost: material_members'):r.preserved(self.before,self.after)

if __name__=='__main__':unittest.main()
