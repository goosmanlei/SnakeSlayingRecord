import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publish_review_context_config import verify_history


class ConfigurationPublicationTest(unittest.TestCase):
    def test_only_project_body_and_one_new_event_may_change(self):
        with tempfile.TemporaryDirectory() as folder:
            before, after = (Path(folder) / name for name in ('before.sqlite3', 'after.sqlite3'))
            with sqlite3.connect(before) as db:
                db.executescript('CREATE TABLE configurations(scope TEXT,version INTEGER,body TEXT); CREATE TABLE configuration_events(scope TEXT,version INTEGER,body TEXT); CREATE TABLE comments(id TEXT,body TEXT);')
                db.executemany('INSERT INTO configurations VALUES(?,?,?)', [('PROJECT', 15, '{}'), ('SYSTEM', 5, '{}')])
                db.execute('INSERT INTO configuration_events VALUES(?,?,?)', ('PROJECT', 15, '{}'))
                db.execute('INSERT INTO comments VALUES(?,?)', ('original', '用户原意见'))
            with sqlite3.connect(before) as src, sqlite3.connect(after) as dst:
                src.backup(dst)
                dst.execute("UPDATE configurations SET version=16,body=? WHERE scope='PROJECT'", (json.dumps({'story_background': '四首歌已入台'}),))
                dst.execute('INSERT INTO configuration_events VALUES(?,?,?)', ('PROJECT', 16, json.dumps({'story_background': '四首歌已入台'})))
            wanted = {'story_background': '四首歌已入台'}
            self.assertTrue(verify_history(before, after, wanted, 16)['comments']['preserved'])
            with sqlite3.connect(after) as db:
                db.execute("UPDATE comments SET body='被覆盖'")
            with self.assertRaisesRegex(ValueError, 'comments'):
                verify_history(before, after, wanted, 16)


if __name__ == '__main__':
    unittest.main()
