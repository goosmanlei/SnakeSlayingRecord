"""One-time cleanup with real method tables and exact comment anchors."""
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from scripts import method_history_cleanup as cleanup


@unittest.skipUnless(importlib.util.find_spec('review_desk'), 'requires pinned review-desk source')
class MethodHistoryCleanupTest(unittest.TestCase):
    def setUp(self):
        from review_desk import methods
        from review_desk.store import Store
        self.methods = methods
        self.tmp = tempfile.TemporaryDirectory(prefix='method-history-cleanup-')
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / '.runtime/review.sqlite3')
        self.addCleanup(self.store.close)
        self.old, self.heads = {}, {}
        for oid in sorted(cleanup.SKILLS):
            name = oid.removeprefix('method.skill.')
            work_type = 'example-' + name
            for version in (1, 2):
                row = methods.save(self.store, {'category': 'skill', 'name': name, 'expected_version': version - 1,
                    'payload': {'title': name, 'purpose': 'Read supplied text', 'applies': 'Example input',
                        'inputs': 'Text', 'outputs': 'Result', 'checks': 'Matches the input',
                        'work_types': [work_type], 'required_inputs': ['context'], 'steps': ['result'],
                        'files': {'SKILL.md': '---\nname: ' + name + '\ndescription: Read text.\n---\n\nBody ' + str(version) + '.\n'},
                        'resources': []}})
                methods.save(self.store, {'category': 'binding', 'name': work_type, 'expected_version': version - 1,
                    'payload': {'work_type': work_type, 'rules': [{**methods.reference(row), 'when': {}}]}})
                if version == 1:
                    self.old[oid] = row
                    if oid == 'method.skill.comment-polish-clear':
                        self.execution = self.prepare('old', work_type)
                        self.artifact = methods.artifact(self.store, {
                            **{key: self.execution['payload'][key] for key in ('work_type', 'run_id', 'step_id', 'target')},
                            'execution': methods.reference(self.execution), 'inputs': self.execution['payload']['inputs'],
                            'stage': 'result', 'output': 'Example result'})
                else:
                    self.heads[oid] = row
        self.old_comment = self.comment(self.old['method.skill.comment-polish-clear'])
        self.latest_comment = self.comment(self.heads['method.skill.story-structure'])

    def prepare(self, run, work_type='example-comment-polish-clear'):
        return self.methods.prepare(self.store, {'work_type': work_type, 'run_id': run, 'step_id': 'one',
            'target': 'sample', 'conditions': {}, 'inputs': {'context': 'Supplied text'}, 'private': True})

    def comment(self, row):
        from review_desk.method_document import project
        block = project(row['payload'])[0]
        return self.store.create_comment({'target_object_id': row['object_id'], 'target_revision_id': row['revision_id'],
            'anchor': {'file': 'SKILL.md', 'block_id': block['id'], 'end_block_id': block['id'],
                       'start': 0, 'end': len(block['text']), 'quote': block['text']}, 'body': 'Example comment'})

    def dump(self):
        return '\n'.join(self.store.db.iterdump())

    def test_latest_identity_comments_and_future_work_survive_one_time_cleanup(self):
        plan = cleanup.build_plan(self.store)
        receipt = cleanup.apply_plan(self.store, plan)
        self.assertEqual(receipt['counts']['execution'], 1)
        self.assertEqual(receipt['counts']['artifact'], 1)
        self.assertEqual(receipt['counts']['comments'], 1)
        for oid, expected in self.heads.items():
            self.assertEqual(self.methods.read(self.store, oid), expected)
            self.assertEqual(self.store.db.execute('SELECT count(*) FROM revisions WHERE object_id=?', (oid,)).fetchone()[0], 1)
        self.assertIsNone(self.store.comment(self.old_comment['id']))
        self.assertEqual(self.store.comment(self.latest_comment['id']), self.latest_comment)
        new = self.prepare('new')
        self.assertEqual(new['payload']['package']['method'], self.methods.reference(self.heads['method.skill.comment-polish-clear']))
        before_replay = self.dump()
        self.assertEqual(cleanup.apply_plan(self.store, plan), receipt)
        self.assertEqual(self.dump(), before_replay, 'retry must not delete later work')
        tampered = copy.deepcopy(plan)
        tampered['counts']['comments'] += 1
        with self.assertRaisesRegex(ValueError, '摘要不匹配'):
            cleanup.apply_plan(self.store, tampered)
        self.assertEqual(self.dump(), before_replay)

    def test_new_comment_invalidates_stale_plan_without_deleting_anything(self):
        plan = cleanup.build_plan(self.store)
        self.comment(self.old['method.skill.story-structure'])
        before = self.dump()
        with self.assertRaisesRegex(ValueError, '已变化'):
            cleanup.apply_plan(self.store, plan)
        self.assertEqual(self.dump(), before)
        self.assertFalse(self.store.db.in_transaction)

    def test_failure_after_deletion_rolls_back_history_comments_and_file_maps(self):
        plan = cleanup.build_plan(self.store)
        before = self.dump()
        with patch('review_desk.method_files.validate', side_effect=ValueError('injected validation failure')):
            with self.assertRaisesRegex(ValueError, 'injected validation failure'):
                cleanup.apply_plan(self.store, plan)
        self.assertEqual(self.dump(), before)
        self.assertFalse(self.store.db.in_transaction)
        cleanup.apply_plan(self.store, plan)

    def test_preservation_comparison_rejects_unrelated_comment_change(self):
        before = Path(self.tmp.name) / 'before.sqlite3'
        with sqlite3.connect(before) as db:
            self.store.db.backup(db)
        plan = cleanup.build_plan(self.store)
        cleanup.apply_plan(self.store, plan)
        cleanup.compare(before, self.store.db_path, plan)
        with self.store.db:
            self.store.db.execute('UPDATE comments SET body=? WHERE id=?', ('Unexpected rewrite', self.latest_comment['id']))
        with self.assertRaisesRegex(ValueError, '范围外数据：comments'):
            cleanup.compare(before, self.store.db_path, plan)


if __name__ == '__main__':
    unittest.main()
