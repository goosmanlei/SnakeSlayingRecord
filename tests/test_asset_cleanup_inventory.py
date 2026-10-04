"""Inventory safety using temporary repositories; never inspect formal resources."""
import gzip
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import asset_cleanup_inventory as inventory


class AssetInventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='asset-inventory-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.story, self.system = self.root / 'story', self.root / 'system'
        for repo in (self.story, self.system):
            self.git('init', '-qb', 'main', str(repo))
            self.git('-C', str(repo), 'config', 'user.name', 'Inventory Test')
            self.git('-C', str(repo), 'config', 'user.email', 'inventory@example.invalid')
            (repo / '.gitignore').write_text('.runtime/\n.codex-project/\n')
            (repo / 'tracked.txt').write_text('fixture')
            self.git('-C', str(repo), 'add', '.gitignore', 'tracked.txt')
            self.git('-C', str(repo), 'commit', '-qm', 'fixture')
        self.output = self.story / '.runtime/inventory'
        self.policies = {'rules': [{'id': 'retained', 'root': '*', 'prefix': '', 'decision': 'retain'}],
                         'exclude': [{'root': 'story', 'path': '.runtime/inventory'}]}

    @staticmethod
    def git(*args):
        return subprocess.check_output(['git', *args], stderr=subprocess.PIPE)

    def scan(self):
        summary = inventory.inventory(self.story, self.system, self.output, self.policies)
        with gzip.open(self.output / 'files.jsonl.gz', 'rt') as stream:
            rows = [json.loads(line) for line in stream]
        self.assertEqual(sum(summary['counts'].values()), len(rows))
        self.assertEqual(sum(summary['decisions'].values()), len(rows))
        return summary, rows

    def test_hidden_untracked_and_credentials_are_metadata_only_and_symlinks_not_followed(self):
        (self.story / '.env').write_text('PRIVATE_FIXTURE_VALUE_DO_NOT_COPY')
        (self.story / 'untracked.txt').write_text('untracked')
        outside = self.root / 'outside'
        outside.mkdir(); (outside / 'outside-secret.txt').write_text('PRIVATE_EXTERNAL_VALUE')
        (self.story / 'outside-link').symlink_to(outside, target_is_directory=True)
        (self.story / '.codex-project').mkdir()
        (self.story / '.codex-project/tasks.json').write_text('{"fixture":true}')
        read_bytes = Path.read_bytes
        def only_output_bytes(path):
            if path != self.output / 'files.jsonl.gz':
                raise AssertionError('inventory read file content: ' + str(path))
            return read_bytes(path)
        with patch.object(Path, 'read_bytes', only_output_bytes), \
             patch.object(Path, 'read_text', side_effect=AssertionError('inventory read text content')):
            summary = inventory.inventory(self.story, self.system, self.output, self.policies)
        with gzip.open(self.output / 'files.jsonl.gz', 'rt') as stream:
            rows = [json.loads(line) for line in stream]
        by = {r['path']: r for r in rows if r['root'] == 'story'}
        self.assertFalse(by['.env']['tracked'])
        self.assertFalse(by['untracked.txt']['tracked'])
        self.assertTrue(by['tracked.txt']['tracked'])
        self.assertIn('.codex-project/tasks.json', by)
        self.assertEqual(by['outside-link']['kind'], 'symlink')
        self.assertEqual(by['outside-link']['target'], {'external': True, 'name': 'outside'})
        self.assertFalse(any(r['path'].startswith('outside-link/') for r in rows))
        self.assertNotIn('PRIVATE_', json.dumps(summary) + json.dumps(rows))

    def test_nested_and_external_worktrees_are_scanned_once_with_their_own_git_index(self):
        task = self.story / '.codex-project/worktrees/task'
        external = self.root / 'other-place/跨层 task'
        system_task = task / '.runtime/system'
        for repo, branch, path in ((self.story, 'task', task), (self.story, 'external', external),
                                   (self.system, 'system-task', system_task)):
            self.git('-C', str(repo), 'worktree', 'add', '-qb', branch, str(path))
        (system_task / '.hidden').write_text('untracked')
        summary, rows = self.scan()
        locations = {name: (self.story / data['location']).resolve() for name, data in summary['roots'].items()}
        physical = [(locations[r['root']] / r['path']).resolve() for r in rows if r['kind'] != 'symlink']
        self.assertEqual(len(physical), len(set(physical)))
        self.assertEqual(len(summary['worktrees']), 5)
        for root in (self.story, self.system, task, external, system_task):
            item = next(r for r in rows if locations[r['root']] / r['path'] == root / 'tracked.txt')
            self.assertTrue(item['tracked'])
        hidden = next(r for r in rows if locations[r['root']] / r['path'] == system_task / '.hidden')
        self.assertFalse(hidden['tracked'])
        self.assertIn(external, locations.values())

    def test_excluded_and_unreadable_subtrees_are_explicit_and_unmatched_items_stay_pending(self):
        private = self.story / '.runtime/checkpoint'
        private.mkdir(parents=True); (private / 'private.json').write_text('{}')
        denied = self.story / '.runtime/denied'
        denied.mkdir(); (denied / 'hidden.json').write_text('{}')
        self.policies['exclude'].append({'root': 'story', 'path': '.runtime/checkpoint'})
        self.policies['rules'] = []
        scandir = os.scandir
        def guarded(path):
            if Path(path) == denied:
                raise PermissionError('PRIVATE_ERROR_MESSAGE')
            return scandir(path)
        with patch.object(inventory.os, 'scandir', side_effect=guarded):
            summary, rows = self.scan()
        self.assertIn({'root': 'story', 'path': '.runtime/denied', 'error': 'PermissionError'}, summary['errors'])
        self.assertIn({'root': 'story', 'path': '.runtime/checkpoint'}, summary['excluded'])
        self.assertTrue(next(r for r in rows if r['path'] == '.runtime/checkpoint')['children_excluded'])
        self.assertFalse(any(r['path'].endswith('private.json') or r['path'].endswith('hidden.json') for r in rows))
        self.assertEqual(summary['decisions'], {'pending': len(rows)})
        self.assertNotIn('PRIVATE_ERROR_MESSAGE', json.dumps(summary))

    def test_external_parent_discovered_after_other_repository_child_is_not_double_counted(self):
        parent = self.root / 'shared'
        child = parent / 'story-task'
        # The story worktree list is processed first, although its external
        # worktree is below a system worktree returned by the second list.
        self.git('-C', str(self.system), 'worktree', 'add', '-qb', 'system-parent', str(parent))
        self.git('-C', str(self.story), 'worktree', 'add', '-qb', 'story-child', str(child))
        summary, rows = self.scan()
        locations = {name: (self.story / data['location']).resolve() for name, data in summary['roots'].items()}
        physical = [locations[r['root']] / r['path'] for r in rows]
        self.assertEqual(len(physical), len(set(physical)))
        self.assertEqual(len(summary['worktrees']), 4)
        self.assertIn(parent, locations.values())
        self.assertNotIn(child, locations.values())
        record = next(r for r in rows if locations[r['root']] / r['path'] == child / 'tracked.txt')
        self.assertTrue(record['tracked'])

    def test_unexcluded_output_is_rejected(self):
        self.policies['exclude'] = []
        with self.assertRaisesRegex(ValueError, 'explicitly excluded'):
            inventory.inventory(self.story, self.system, self.output, self.policies)
        self.assertFalse((self.output / 'files.jsonl.gz').exists())


if __name__ == '__main__':
    unittest.main()
