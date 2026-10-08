"""File identity and frozen-release guards; never touch a formal instance."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import audiovisual_release as r


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'export/assets').mkdir(parents=True)

    def original(self, name='a.png', raw=b'original'):
        path = self.root / 'export/assets' / name
        path.write_bytes(raw)
        return dict(path=str(path.relative_to(self.root)), sha256=hashlib.sha256(raw).hexdigest())

    def test_entire_file_set_is_checked_before_any_deletion(self):
        first = self.original(); second = self.original('b.png')
        (self.root / second['path']).write_bytes(b'concurrent change')
        with self.assertRaisesRegex(ValueError, 'retired file changed'):
            r.retire_files(self.root, {'files': [first, second]})
        self.assertEqual((self.root / first['path']).read_bytes(), b'original')

    def test_exact_deletion_and_retry_never_touch_unlisted_originals(self):
        selected = self.original(); other = self.original('keep.png')
        self.assertEqual(r.retire_files(self.root, {'files': [selected]})['removed'], [selected['path']])
        self.assertEqual(r.retire_files(self.root, {'files': [selected]})['already_absent'], [selected['path']])
        self.assertTrue((self.root / other['path']).is_file())

    def test_traversal_and_broken_symlink_are_refused(self):
        for name in ['../foreign.png', 'export/assets/../foreign.png', '/export/assets/x.png']:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'unsafe retirement'):
                r.retire_files(self.root, {'files': [dict(path=name, sha256='x')]})
        (self.root / 'export/assets/link.png').symlink_to(self.root / 'absent')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            r.retire_files(self.root, {'files': [dict(path='export/assets/link.png', sha256='x')]})

    def test_lfs_input_is_bound_to_actual_media_bytes(self):
        item = self.original(); raw = (self.root / item['path']).read_bytes()
        pointer = f'version https://git-lfs.github.com/spec/v1\noid sha256:{item["sha256"]}\nsize {len(raw)}\n'.encode()
        with patch.object(r.base, 'git_file', return_value=pointer):
            r.committed(self.root, 'candidate', item['path'])
            (self.root / item['path']).write_bytes(b'replaced')
            with self.assertRaisesRegex(ValueError, 'LFS input differs'):
                r.committed(self.root, 'candidate', item['path'])

    def test_mutated_frozen_service_manifest_is_rejected(self):
        (self.root / 'manifest.json').write_text('{}')
        (self.root / 'audiovisual-manifest.json').write_text(json.dumps(dict(
            format='audiovisual-release-v1', service_manifest_sha256='not the actual digest')))
        args = type('Args', (), {'bundle': self.root})()
        with patch.object(r.service, 'load_bundle', return_value=(self.root, {'task': r.TASK})):
            with self.assertRaisesRegex(ValueError, 'service manifest changed'):
                r.load(args)
