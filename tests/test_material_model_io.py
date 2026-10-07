import json
from pathlib import Path
import tempfile
import unittest
from scripts import generation_publication as publisher,material_model_io as io
from review_desk import material_storage as storage,material_archives as archives
from review_desk.store import Store


class MaterialModelIOTest(unittest.TestCase):
    def test_framework_hydrates_only_requested_heads_or_history(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);directory=root/'export';directory.mkdir()
            store=Store(root/'.runtime/review.sqlite3')
            try:
                with store.db:
                    old=storage.intern(store,{'prompt':'旧版😀'})
                    current=storage.intern(store,{'prompt':'准确当前版'})
                (directory/'material-content.json').write_text(json.dumps({'format':'material-content-v1','material_content':storage.dump(store)['material_content']}))
            finally:store.close()
            (root/'.runtime/review.sqlite3').unlink()
            framework={'objects':[{'id':'plan','kind':'REQUIREMENT','current_revision':'new'},
                                  {'id':'unused','kind':'ASSET','current_revision':'bad'}],
                       'revisions':[{'id':'old','payload':json.dumps({'_material_fields':old})},
                                    {'id':'new','payload':json.dumps({'_material_fields':current})},
                                    {'id':'bad','payload':json.dumps({'_material_fields':'missing'})}]}
            path=directory/'objects.json';path.write_text(json.dumps(framework))
            heads=io.read_framework(path,current_only=True,kinds={'REQUIREMENT'})
            self.assertEqual([r['id'] for r in heads['revisions']],['new'])
            self.assertEqual(json.loads(heads['revisions'][0]['payload']),{'prompt':'准确当前版'})
            history=io.read_framework(path,revision_ids=['old'])
            self.assertEqual([r['id'] for r in history['revisions']],['old'])
            self.assertEqual(json.loads(history['revisions'][0]['payload']),{'prompt':'旧版😀'})

    def test_original_bytes_reader_and_readonly_sqlite_hydration(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'config').mkdir();(root/'config/instance.json').write_text('{}')
            store=Store(root/'.runtime/review.sqlite3')
            try:
                raw=b'{ "prompt":"\\u4f60\\u597D", "n":1e00 }\r\n'
                path=root/'production/requests/input.json';path.parent.mkdir(parents=True)
                with store.db:container=archives.encode(store,raw)
                path.write_text(json.dumps(container))
                self.assertEqual(io.read_bytes(path),raw)
                self.assertEqual(io.read_json(path),json.loads(raw))
                self.assertEqual(io.logical_size(path),len(raw))
            finally:store.close()

    def test_independent_publication_can_share_concurrently_added_content(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);before=root/'before.sqlite3';after=root/'after.sqlite3'
            store=Store(before);store.close();publisher.backup(before,after)
            store=Store(after)
            with store.db:storage.intern(store,{'new field':'shared exact text'})
            store.close();delta=publisher.build_plan(before,after)
            store=Store(before)
            with store.db:storage.intern(store,{'unrelated field':'shared exact text'})
            existing=storage.dump(store)['material_content'];store.close()
            db=publisher.connect(before,readonly=False)
            try:
                result=publisher.apply_plan(db,delta)
                self.assertFalse(result['already_published'])
                actual=[dict(row) for row in db.execute('SELECT * FROM material_content')]
                self.assertTrue(all(row in actual for row in existing))
                self.assertTrue(publisher.apply_plan(db,delta)['already_published'])
            finally:db.close()
