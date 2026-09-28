import json
import tempfile
import unittest
from pathlib import Path

from review_desk.bundle import export, restore
from review_desk.store import Conflict, Store
from scripts.publish_screenplay import publish


class ScreenplayPublicationTest(unittest.TestCase):
    def setUp(self):
        self.candidate = Path(__file__).resolve().parents[1]
        self.temp = tempfile.TemporaryDirectory(prefix='screenplay-publish-test-')
        self.target = Path(self.temp.name)
        out = self.target / 'export'; out.mkdir()
        (out / 'assets').symlink_to(self.candidate / 'export/assets', target_is_directory=True)
        self.store = Store(self.target / '.runtime/review.sqlite3')
        restore(self.store, self.candidate / 'export')
        document = json.loads((self.candidate / 'imports/screenplay-01.json').read_text())
        ids = [document['id']] + [e['id'] for e in document['episodes']]
        # Only this disposable restored fixture is reduced to the prepublication state.
        with self.store.db:
            for id in ids:
                self.store.db.execute('DELETE FROM dependencies WHERE from_revision IN (SELECT id FROM revisions WHERE object_id=?)', (id,))
                self.store.db.execute('DELETE FROM revisions WHERE object_id=?', (id,))
                self.store.db.execute('DELETE FROM objects WHERE id=?', (id,))

    def tearDown(self):
        self.store.close(); self.temp.cleanup()

    def dump(self):
        return '\n'.join(self.store.db.iterdump())

    def test_dry_run_append_idempotence_and_exact_export(self):
        before = self.dump()
        self.assertTrue(publish(self.candidate, self.target)['dry_run'])
        self.assertEqual(before, self.dump())
        result = publish(self.candidate, self.target, True)
        self.assertEqual(result['objects'], 18)
        self.assertFalse(result['already_present'])
        self.assertTrue(publish(self.candidate, self.target, True)['already_present'])
        export(self.store, self.target / 'export')
        files = list(json.loads((self.candidate / 'export/manifest.json').read_text())['files']) + ['manifest.json']
        self.assertTrue(all((self.target / 'export' / f).read_bytes() == (self.candidate / 'export' / f).read_bytes() for f in files))

    def test_new_formal_comment_is_preserved(self):
        source = self.store.source('refinement-09-lantern-home-v9')
        block = source['blocks'][0]
        self.store.create_comment({'id':'publication-preservation-test', 'source_id':source['id'],
                                  'body':'Disposable preservation test',
                                  'anchor':{'block_id':block['id'],'end_block_id':block['id'],
                                            'start':0,'end':5,'quote':block['text'][:5]}})
        comments, events = self.store.comments(), self.store.events()
        publish(self.candidate, self.target, True)
        self.assertEqual(comments, self.store.comments())
        self.assertEqual(events, self.store.events())

    def test_newer_story_stops_before_write(self):
        source = self.store.source('refinement-09-lantern-home-v9')
        self.store.put_source({**source, 'id':'newer-published-story', 'order':source.get('order', 0) + 1})
        before = self.dump()
        with self.assertRaises(ValueError):
            publish(self.candidate, self.target, True)
        self.assertEqual(before, self.dump())

    def test_collision_never_overwrites_or_partially_appends(self):
        self.store.put_object('screenplay-01-lantern-home-e02', 'NOTE', {'body':'Existing unrelated content'})
        before = self.dump()
        with self.assertRaises(Conflict):
            publish(self.candidate, self.target, True)
        self.assertEqual(before, self.dump())


if __name__ == '__main__':
    unittest.main()
