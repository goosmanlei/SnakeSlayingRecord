import base64
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from generation_fixtures import make_worktree
from scripts import record_builtin_image

class RecorderTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.main,self.task=make_worktree(self.temp.name)

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
