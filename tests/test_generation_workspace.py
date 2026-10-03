import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from generation_fixtures import make_worktree, git
from scripts.generation_workspace import (contained, generation_root, isolated_instance,
                                          primary_root, verify_integrated, verify_media)
from scripts import lyria_music, seed_audio


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.main, self.task = make_worktree(self.temp.name)

    def test_main_subdirectory_and_detached_checkout_refused(self):
        for root in (self.main, self.main / '.git'):
            with self.assertRaises(ValueError):
                generation_root(root)
        self.assertEqual(generation_root(self.task), self.task)
        git(self.task, 'checkout', '--detach')
        with self.assertRaises(ValueError):
            generation_root(self.task)

    def test_path_and_symlink_escape_refused_before_write(self):
        (self.task / 'export').mkdir()
        (self.task / 'export/assets').symlink_to(self.main, target_is_directory=True)
        with self.assertRaises(ValueError):
            generation_root(self.task)
        for path in (self.main / 'unexpected', self.task / '../main/unexpected', self.task / '.git/config'):
            with self.assertRaises(ValueError):
                contained(self.task, path)
        self.assertFalse((self.main / 'unexpected').exists())

    def test_instance_must_be_in_task_runtime(self):
        for path in (self.main, self.task, self.task / 'production/preview'):
            with self.assertRaises(ValueError):
                isolated_instance(self.task, path)
        self.assertEqual(isolated_instance(self.task, '.runtime/review'), self.task / '.runtime/review')

    def test_lyria_rejects_main_before_credentials_network_or_receipts(self):
        with patch.object(lyria_music, 'request_json') as request:
            with self.assertRaisesRegex(ValueError, 'worktree'):
                lyria_music.submit({}, {}, self.main, '0.08', 10)
            request.assert_not_called()
        self.assertFalse((self.main / '.runtime').exists())

    def test_seed_main_rejected_before_loading_request_or_creating_output(self):
        script = Path(seed_audio.__file__)
        result = subprocess.run([sys.executable, str(script), 'missing.json', '--workspace', str(self.main), '--submit'],
                                cwd=self.temp.name, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('independent Git worktree', result.stderr)
        self.assertFalse((self.main / '.runtime').exists())

    def test_seed_output_with_another_cwd_stays_in_selected_worktree(self):
        spec = self.task / 'request.json'
        spec.write_text(json.dumps({'id': 'offline-test', 'text_prompt': 'hello'}))
        with patch.object(seed_audio, 'ROOT', self.task):
            output, sha = seed_audio.save_original(b'offline-audio')
        self.assertTrue(output.is_relative_to(self.task))
        self.assertFalse((self.main / 'export').exists())

    def package(self):
        raw = b'original-media'
        sha = hashlib.sha256(raw).hexdigest()
        name = sha + '.wav'
        (self.task / 'export/assets').mkdir(parents=True)
        (self.task / 'export/assets' / name).write_bytes(raw)
        package = self.task / 'package.json'
        package.write_text('{}\n')
        entries = [{'file': name, 'sha256': sha, 'bytes': len(raw)}]
        git(self.task, 'add', 'package.json', 'export')
        git(self.task, 'commit', '-qm', 'candidate')
        return git(self.task, 'rev-parse', 'HEAD'), package, entries

    def test_formal_publication_requires_merge_and_exact_committed_bytes(self):
        commit, package, entries = self.package()
        with self.assertRaisesRegex(ValueError, 'not been integrated'):
            verify_integrated(self.task, self.main, commit, package, entries)
        git(self.main, 'merge', '--ff-only', commit)
        self.assertEqual(verify_integrated(self.task, self.main, commit, package, entries), commit)
        package.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError, 'differs'):
            verify_integrated(self.task, self.main, commit, package, entries)

    def test_untracked_media_cannot_be_published(self):
        commit, package, entries = self.package()
        git(self.main, 'merge', '--ff-only', commit)
        extra = hashlib.sha256(b'new').hexdigest()
        (self.task / 'export/assets' / (extra + '.wav')).write_bytes(b'new')
        entries.append({'file': extra + '.wav', 'sha256': extra, 'bytes': 3})
        with self.assertRaises(ValueError):
            verify_integrated(self.task, self.main, commit, package, entries)

    def test_media_size_is_verified_in_addition_to_its_hash(self):
        _, _, entries = self.package()
        entries[0]['bytes'] += 1
        with self.assertRaisesRegex(ValueError, 'byte count differs'):
            verify_media(self.task, entries)

    def test_generation_entrypoints_contain_workspace_gate(self):
        # Prevent a later add/add resolution from restoring the pre-isolation CLI.
        import ast
        root = Path(__file__).resolve().parents[1]
        for name in ('seed_audio', 'lyria_music', 'record_builtin_image', 'register_full_generation',
                     'register_generation_batch', 'register_production_candidates', 'production_review'):
            tree = ast.parse((root / 'scripts' / (name + '.py')).read_text())
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
            self.assertTrue(any(isinstance(c.func, ast.Name) and c.func.id == 'generation_root' for c in calls), name)


if __name__ == '__main__':
    unittest.main()
