import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from production_review import complete_export_index, verify_export_index


class CompleteExportIndexTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE revisions(id TEXT,object_id TEXT,version INTEGER,payload TEXT)')
        self.formats = {'production-requirement-v1', 'production-asset-v1'}
        self.rows = []
        self.add('older', 'material', 1, {'format': 'production-requirement-v1', '_material_fields': 'intentionally-unavailable'})
        self.add('newer', 'material', 2, {'format': 'production-requirement-v1', '_material_fields': 'not-hydrated'})
        self.add('script', 'scene', 1, {'format': 'screenplay-scene-v1'})
        component = {'file': 'abc.png', 'sha256': 'abc'}
        self.add('asset', 'asset', 1, {'format': 'production-asset-v1', 'components': [component, component]})

    def add(self, rid, oid, version, payload):
        row = {'id': rid, 'object_id': oid, 'version': version, 'payload': json.dumps(payload)}
        self.rows.append(row)
        self.db.execute('INSERT INTO revisions VALUES (:id,:object_id,:version,:payload)', row)

    def index(self):
        return complete_export_index(SimpleNamespace(db=self.db), SimpleNamespace(FORMATS=self.formats))

    def test_full_history_identity_without_hydrating_material_fields(self):
        index = self.index()
        self.assertEqual(index['heads'], {'material': 'newer', 'asset': 'asset'})
        self.assertEqual(index['revisions'], ['asset', 'newer', 'older'])
        self.assertEqual(index['files'], {'export/assets/abc.png': 'abc'})
        self.assertNotIn('batches', index)

    def test_same_export_passes_but_lost_historical_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            export = Path(directory)
            (export / 'objects.json').write_text(json.dumps({'revisions': self.rows}))
            verify_export_index(self.index(), export, self.formats)
            (export / 'objects.json').write_text(json.dumps({'revisions': self.rows[1:]}))
            with self.assertRaisesRegex(ValueError, 'different revisions'):
                verify_export_index(self.index(), export, self.formats)

    def test_changed_head_is_rejected_even_with_same_revision_set(self):
        with tempfile.TemporaryDirectory() as directory:
            export = Path(directory)
            (export / 'objects.json').write_text(json.dumps({'revisions': self.rows}))
            index = self.index()
            index['heads']['material'] = 'older'
            with self.assertRaisesRegex(ValueError, 'different revisions'):
                verify_export_index(index, export, self.formats)

    def test_shot_and_ordinary_entity_share_one_index_without_shadow_identity(self):
        self.formats.update(('production-entity-v1','production-av-shot-v1'))
        self.add('shot-current','ash001',1,{'format':'production-av-shot-v1'})
        self.add('entity-current','girl',1,{'format':'production-entity-v1','entity_type':'character'})
        index=self.index()
        self.assertEqual(index['entities'],{'ash001':{'revision_id':'shot-current','type':'shot'},'girl':{'revision_id':'entity-current','type':'character'}})
        with tempfile.TemporaryDirectory() as directory:
            destination=Path(directory)
            (destination/'objects.json').write_text(json.dumps({'revisions':self.rows}))
            verify_export_index(index,destination,self.formats)
            index['entities'].pop('ash001')
            with self.assertRaisesRegex(ValueError,'different entities'):verify_export_index(index,destination,self.formats)

    def test_conflicting_original_checksum_is_rejected(self):
        self.add('asset2', 'asset', 2, {'format': 'production-asset-v1', 'components': [{'file': 'abc.png', 'sha256': 'other'}]})
        with self.assertRaisesRegex(ValueError, 'conflicting original'):
            self.index()


if __name__ == '__main__':
    unittest.main()
