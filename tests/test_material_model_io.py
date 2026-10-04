import json
from pathlib import Path
import tempfile
import unittest
from scripts import generation_publication as publisher,material_model_io as io
from review_desk import material_storage as storage,material_archives as archives
from review_desk.store import Store


class MaterialModelIOTest(unittest.TestCase):
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
