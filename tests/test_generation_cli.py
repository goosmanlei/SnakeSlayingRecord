"""Exercise real CLI imports and recovery without contacting generation providers."""
import copy
import base64
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

import review_desk
from review_desk import production
from review_desk.production_media import ingest
from review_desk.store import Store
from generation_fixtures import make_worktree
from scripts.generation_publication import tables
from scripts import record_builtin_image

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = Path(review_desk.__file__).resolve().parent.parent


class GenerationCLITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.main, self.task = make_worktree(self.temp.name)
        self.target = self.task / '.runtime/target'
        (self.target / 'export/assets').mkdir(parents=True)
        self.db_path = self.target / '.runtime/review.sqlite3'
        Store(self.db_path).close()
        self.before = tables(self.db_path)
        audio = io.BytesIO()
        with wave.open(audio, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            wav.writeframes(b'\0\0' * 48000)
        audio.seek(0)
        self.component = ingest(self.task, audio, 'offline.wav')
        call = self.spec('call-offline', 'CALL', method='recording', tool='offline-fixture',
                         status='submitted', inputs=[], outputs=[])
        asset = self.spec('asset-offline', 'ASSET', media_type='audio', subjects=[], states=[],
                          components=[self.component], lineage={},
                          production={'object_id': 'call-offline', 'revision_id': '@call-offline'})
        second = copy.deepcopy(call)
        second['expected_version'] = 1
        second['payload']['title'] = 'Updated recording description'
        self.package = {'batches': [
            {'format': 'production-import-v1', 'records': [call, asset]},
            {'format': 'production-import-v1', 'records': [second]}]}
        self.package_path = self.task / 'registration.json'

    @staticmethod
    def spec(oid, kind, **fields):
        return {'object_id': oid, 'kind': kind, 'expected_version': 0, 'payload': {
            'format': 'production-' + production.KINDS[kind] + '-v1', 'title': oid,
            'blocks': [{'id': 'notes', 'text': 'Offline integration fixture'}], **fields}}

    def cli(self, run, *, apply=False):
        self.package_path.write_text(json.dumps(self.package))
        command = [sys.executable, str(ROOT / 'scripts/publish_full_generation.py'),
                   '--workspace', str(self.task), '--system', str(SYSTEM),
                   '--instance', '.runtime/target', '--registration', 'registration.json',
                   '--run-name', run]
        if apply:
            command.append('--apply')
        return subprocess.run(command, cwd=self.temp.name, capture_output=True, text=True, timeout=30)

    def test_batch_preflight_apply_and_retry_from_another_cwd(self):
        preflight = self.cli('preflight')
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        self.assertEqual(tables(self.db_path), self.before)
        result = self.cli('apply', apply=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        after = tables(self.db_path)
        self.assertEqual(len(after['objects']), 2)
        self.assertEqual(len(after['revisions']), 3)
        media = self.target / 'export/assets' / self.component['file']
        self.assertEqual(media.read_bytes(), (self.task / 'export/assets' / media.name).read_bytes())
        retried = self.cli('retry', apply=True)
        self.assertEqual(retried.returncode, 0, retried.stderr)
        self.assertTrue(json.loads(retried.stdout)['already_published'])
        self.assertEqual(tables(self.db_path), after)
        self.assertFalse((self.main / 'export').exists())

    def test_bad_second_batch_cannot_partially_publish_first_batch(self):
        self.package['batches'][1]['records'][0]['expected_version'] = 10
        result = self.cli('bad-batch', apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tables(self.db_path), self.before)
        self.assertEqual(list((self.target / 'export/assets').iterdir()), [])

    def test_offline_image_original_and_receipt_stay_in_task(self):
        home = self.task / '.runtime/test-home'
        originals = home / '.codex/generated_images'
        originals.mkdir(parents=True)
        source = originals / 'fixture.png'
        source.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='))
        requests = self.task / 'production/requests'
        requests.mkdir(parents=True)
        (requests / 'offline-image.json').write_text(json.dumps({'id':'offline-image','tool':'image_gen.imagegen'}))
        metadata = home / 'metadata.json'
        metadata.write_text(json.dumps({'response_keys':['image_url','output_hint'],
            'output_hint': 'Saved as ' + str(source) + ' by default.'}))
        argv = ['record_builtin_image.py','--workspace',str(self.task),'--id','offline-image',
                '--response-metadata',str(metadata)]
        with patch.object(record_builtin_image,'ROOT',self.task), patch.object(Path,'home',return_value=home), \
                patch.object(sys,'argv',argv), contextlib.redirect_stdout(io.StringIO()):
            record_builtin_image.main()
        receipt = json.loads((self.task/'production/receipts/offline-image-builtin-complete.json').read_text())
        self.assertEqual((receipt['width'],receipt['height']),(1,1))
        self.assertEqual((self.task / receipt['file']).read_bytes(),source.read_bytes())
        self.assertFalse((self.main / 'export').exists())


if __name__ == '__main__':
    unittest.main()
