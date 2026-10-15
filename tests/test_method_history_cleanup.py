"""Explicit cleanup passes with real method tables and exact comment anchors."""
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

    def comment(self, row, filename='SKILL.md'):
        from review_desk.method_document import project
        block = project(row['payload'], filename)[0]
        return self.store.create_comment({'target_object_id': row['object_id'], 'target_revision_id': row['revision_id'],
            'anchor': {'file': filename, 'block_id': block['id'], 'end_block_id': block['id'],
                       'start': 0, 'end': len(block['text']), 'quote': block['text']}, 'body': 'Example comment'})

    def review_resource_history(self):
        versions = []
        for version in (1, 2):
            versions.append(self.methods.save(self.store, {'category': 'resource',
                'name': 'creative-system-review-texts', 'expected_version': version - 1,
                'payload': {'title': 'Review and vision', 'files': {
                    'skills/creative-system-review/SKILL.md': 'Review method ' + str(version) + '.\n',
                    'production/system-vision.md': 'Protected vision ' + str(version) + '.\n'},
                    'sections': {'review': 'skills/creative-system-review/SKILL.md',
                                 'vision': 'production/system-vision.md'}}}))
        old = self.heads['method.skill.creative-system-review']
        payload = copy.deepcopy(old['payload'])
        payload['resources'] = [{**self.methods.reference(versions[-1]), 'section': 'review'}]
        new = self.methods.save(self.store, {'category': 'skill', 'name': 'creative-system-review',
            'expected_version': old['version'], 'payload': payload})
        self.methods.save(self.store, {'category': 'binding', 'name': 'example-creative-system-review',
            'expected_version': 2, 'payload': {'work_type': 'example-creative-system-review',
                'rules': [{**self.methods.reference(new), 'when': {}}]}})
        self.heads[new['object_id']] = new
        return versions

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

    def test_later_authorized_plan_preserves_legacy_receipt_and_retries_only_itself(self):
        legacy = cleanup.build_plan(self.store, legacy=True)
        first_receipt = cleanup.apply_plan(self.store, legacy)
        first_row = dict(self.store.db.execute('SELECT * FROM production_current_operations WHERE id=?',
                         (cleanup.plan_operation_id(legacy),)).fetchone())
        new = self.prepare('before-second-cleanup')
        second = cleanup.build_plan(self.store)
        self.assertNotEqual(cleanup.plan_operation_id(legacy), cleanup.plan_operation_id(second))
        before = Path(self.tmp.name) / 'second-before.sqlite3'
        cleanup.snapshot(self.store.db_path, before)
        second_receipt = cleanup.apply_plan(self.store, second)
        self.assertEqual(second_receipt['counts']['execution'], 1)
        self.assertIsNone(self.store.db.execute('SELECT id FROM objects WHERE id=?', (new['object_id'],)).fetchone())
        cleanup.compare(before, self.store.db_path, second)
        future = self.prepare('after-second-cleanup')
        before_replay = self.dump()
        self.assertEqual(cleanup.apply_plan(self.store, legacy), first_receipt)
        self.assertEqual(cleanup.apply_plan(self.store, second), second_receipt)
        self.assertEqual(self.dump(), before_replay)
        self.assertEqual(self.methods.read(self.store, future['object_id']), future)
        self.assertEqual(dict(self.store.db.execute('SELECT * FROM production_current_operations WHERE id=?',
                         (cleanup.plan_operation_id(legacy),)).fetchone()), first_row)

    def test_plan_identity_cannot_reuse_a_different_cleanup_receipt(self):
        plan = cleanup.build_plan(self.store)
        plan['operation_id'] = cleanup.TASK + '-method-history-cleanup'
        plan['sha256'] = self.methods.checksum({key: value for key, value in plan.items() if key != 'sha256'})
        before = self.dump()
        with self.assertRaisesRegex(ValueError, '操作身份'):
            cleanup.apply_plan(self.store, plan)
        self.assertEqual(self.dump(), before)

    def test_current_vision_comment_survives_while_old_review_files_are_removed(self):
        from scripts import method_migration
        from review_desk.store import Store
        old, latest = self.review_resource_history()
        vision_comment = self.comment(latest, 'production/system-vision.md')
        old_review_comment = self.comment(old, 'skills/creative-system-review/SKILL.md')
        before = Path(self.tmp.name) / 'resource-before.sqlite3'
        with sqlite3.connect(before) as db:
            self.store.db.backup(db)
        plan = cleanup.build_plan(self.store)
        self.assertIn(latest['object_id'], plan['heads'])
        self.assertNotIn(vision_comment['id'], [row['id'] for row in plan['remove_comments']])
        cleanup.apply_plan(self.store, plan)
        self.assertEqual(self.store.comment(vision_comment['id']), vision_comment)
        self.assertIsNone(self.store.comment(old_review_comment['id']))
        self.assertEqual(self.methods.read(self.store, latest['object_id']), latest)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM revisions WHERE object_id=?',
                                             (latest['object_id'],)).fetchone()[0], 1)
        files = self.store.db.execute('SELECT path,version FROM method_file_versions WHERE object_id=? ORDER BY path',
                                      (latest['object_id'],)).fetchall()
        self.assertEqual([tuple(row) for row in files], [('production/system-vision.md', 1),
                         ('skills/creative-system-review/SKILL.md', 1)])
        cleanup.compare(before, self.store.db_path, plan)
        recovered = Store(Path(self.tmp.name) / 'resource-restored/.runtime/review.sqlite3')
        self.addCleanup(recovered.close)
        method_migration.restore_configuration(recovered, method_migration.configuration_registry(self.store))
        self.assertEqual(self.methods.read(recovered, latest['object_id']), latest)

    def test_historical_vision_comment_still_preserves_its_exact_package(self):
        old, latest = self.review_resource_history()
        vision_comment = self.comment(old, 'production/system-vision.md')
        plan = cleanup.build_plan(self.store)
        self.assertNotIn(latest['object_id'], plan['heads'])
        kept = next(item for item in plan['preserved_resource_history'] if item['object_id'] == latest['object_id'])
        self.assertEqual(kept['protected_system_vision_comments'], [vision_comment['id']])
        cleanup.apply_plan(self.store, plan)
        self.assertEqual(self.store.comment(vision_comment['id']), vision_comment)
        self.assertEqual(self.methods.read(self.store, old['object_id'], old['revision_id']), old)
        self.assertEqual(self.methods.read(self.store, latest['object_id']), latest)

    def test_failure_after_deletion_rolls_back_history_comments_and_file_maps(self):
        plan = cleanup.build_plan(self.store)
        before = self.dump()
        with patch('review_desk.method_files.validate', side_effect=ValueError('injected validation failure')):
            with self.assertRaisesRegex(ValueError, 'injected validation failure'):
                cleanup.apply_plan(self.store, plan)
        self.assertEqual(self.dump(), before)
        self.assertFalse(self.store.db.in_transaction)
        cleanup.apply_plan(self.store, plan)

    def test_archived_original_is_checked_inside_the_cleanup_transaction(self):
        import hashlib
        from review_desk import material_archives, production_current_bundle
        from review_desk.production_media import validate_component
        raw = b'{"request": "preserve the exact original request"}\n'
        digest = hashlib.sha256(raw).hexdigest()
        path = Path(self.tmp.name) / 'export/assets' / (digest + '.json')
        path.parent.mkdir(parents=True)
        with self.store.db:
            document = material_archives.encode(self.store, raw)
        path.write_text(json.dumps(document))
        component = {'id': 'metadata', 'role': 'metadata', 'file': path.name,
                     'sha256': digest, 'bytes': len(raw)}
        original_validate = production_current_bundle.validate

        def validate_with_original(store):
            original_validate(store)
            self.assertTrue(store.db.in_transaction)
            validate_component(Path(self.tmp.name), component, inspect=False)

        # The real publication reaches this lock state after many dirty pages.
        # Force it deterministically without constructing a large test database.
        self.store.db.execute('PRAGMA locking_mode=EXCLUSIVE')
        plan = cleanup.build_plan(self.store)
        with patch.object(production_current_bundle, 'validate', validate_with_original):
            cleanup.apply_plan(self.store, plan)
        with material_archives.read_scope(self.store):
            self.assertEqual(material_archives.read_bytes(path), raw)
        self.assertEqual(json.loads(path.read_text()), document)

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

    def test_nested_method_cleanup_preserves_semantic_migration_evidence(self):
        method_basis = {
            'execution': self.methods.reference(self.execution),
            'artifact': self.methods.reference(self.artifact),
            'run_id': 'old', 'step_id': 'one'}
        semantic_basis = {
            'history': 'reviewed-semantic-migration',
            'semantic_operation': 'existing-semantic-operation',
            'before_sha256': 'a' * 64,
            'extraction_assessment': {'episode': 1, 'result_path': 'production/extraction/episodes/e01.json',
                                      'result_sha256': 'b' * 64},
            'original_media_plan_basis': method_basis}
        result = {'basis': semantic_basis, 'before': {'input_mode': 'interval'},
                  'after': {'input_mode': 'whole-reference'}}
        with self.store.db:
            self.store.db.execute('INSERT INTO production_current_operations VALUES (?,?,?)',
                ('whole-reference-example', 'c' * 64, json.dumps(result)))
        before = Path(self.tmp.name) / 'semantic-before.sqlite3'
        with sqlite3.connect(before) as db:
            self.store.db.backup(db)
        plan = cleanup.build_plan(self.store)
        cleanup.apply_plan(self.store, plan)
        saved = json.loads(self.store.db.execute(
            'SELECT result FROM production_current_operations WHERE id=?', ('whole-reference-example',)).fetchone()[0])
        expected = copy.deepcopy(result)
        expected['basis']['original_media_plan_basis'] = {'history': 'cleared-by-user', 'cleanup_task': cleanup.TASK}
        self.assertEqual(saved, expected)
        cleanup.compare(before, self.store.db_path, plan)

    def release_package(self, advance=False):
        from scripts import method_migration
        candidate = self.store
        if advance:
            from review_desk.store import Store
            old = self.methods.read(self.store, 'method.skill.story-structure')
            path = Path(self.tmp.name)/('candidate-' + str(old['version']))/'.runtime/review.sqlite3'
            cleanup.snapshot(self.store.db_path, path)
            candidate = Store.open_existing(path)
            self.addCleanup(candidate.close)
            payload = copy.deepcopy(old['payload'])
            payload['files']['SKILL.md'] += 'A separately reviewed final improvement.\n'
            new = self.methods.save(candidate, {'category':'skill', 'name':'story-structure',
                'expected_version':old['version'], 'payload':payload})
            self.methods.save(candidate, {'category':'binding', 'name':'example-story-structure',
                'expected_version':self.methods.read(candidate, 'method.binding.example-story-structure')['version'],
                'payload':{'work_type':'example-story-structure',
                    'rules':[{**self.methods.reference(new), 'when':{}}]}})
        registry = method_migration.configuration_registry(candidate)
        plan = cleanup.build_plan(candidate)
        latest = cleanup.retained_registry(registry, plan)
        before = self.dump()
        package = cleanup.prepare_release(self.store.db_path, registry, latest)
        self.assertEqual(self.dump(), before, 'preparing a package must only read the live instance')
        return package, latest

    def test_publication_retry_never_reinstalls_deleted_versions_or_removes_new_work(self):
        package, latest = self.release_package(advance=True)
        directory = Path(self.tmp.name) / 'release'
        result = cleanup.apply_release(self.store.db_path, package, latest, directory)
        # The prior version-2 comment is now historical after version 3 lands.
        self.assertEqual(result['cleanup']['counts']['comments'], 2)
        new = self.prepare('after-publication')
        before_retry = self.dump()
        self.assertEqual(cleanup.apply_release(self.store.db_path, package, latest, directory), result)
        self.assertEqual(self.dump(), before_retry)
        self.assertEqual(self.methods.read(self.store, new['object_id']), new)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM revisions WHERE object_id=?',
                                             ('method.skill.story-structure',)).fetchone()[0], 1)
        self.assertEqual(self.methods.read(self.store, 'method.skill.story-structure')['version'], 3)

    def test_second_publication_cleans_new_history_and_rejects_old_package_replay(self):
        first, first_latest = self.release_package(advance=True)
        first_dir = Path(self.tmp.name) / 'first-release'
        cleanup.apply_release(self.store.db_path, first, first_latest, first_dir)
        self.prepare('between-publications')
        second, second_latest = self.release_package(advance=True)
        second_dir = Path(self.tmp.name) / 'second-release'
        result = cleanup.apply_release(self.store.db_path, second, second_latest, second_dir)
        self.assertEqual(result['cleanup']['counts']['execution'], 1)
        self.assertEqual(self.methods.read(self.store, 'method.skill.story-structure')['version'], 4)
        for oid in cleanup.SKILLS:
            self.assertEqual(self.store.db.execute('SELECT count(*) FROM revisions WHERE object_id=?', (oid,)).fetchone()[0], 1)
        before_replay = self.dump()
        with self.assertRaisesRegex(ValueError, '版本已前进'):
            cleanup.apply_release(self.store.db_path, first, first_latest, first_dir)
        self.assertEqual(self.dump(), before_replay)
        self.assertEqual(cleanup.apply_release(self.store.db_path, second, second_latest, second_dir), result)
        self.assertEqual(self.dump(), before_replay)

    def test_publication_resumes_committed_cleanup_before_receipt_snapshot(self):
        package, latest = self.release_package()
        directory = Path(self.tmp.name) / 'interrupted-release'
        real_snapshot = cleanup.snapshot
        def interrupted_snapshot(database, path):
            if path.name == 'cleaned.sqlite3':
                raise ValueError('injected evidence interruption')
            return real_snapshot(database, path)
        with patch.object(cleanup, 'snapshot', side_effect=interrupted_snapshot):
            with self.assertRaisesRegex(ValueError, 'evidence interruption'):
                cleanup.apply_release(self.store.db_path, package, latest, directory)
        self.assertIsNone(self.store.comment(self.old_comment['id']))
        result = cleanup.apply_release(self.store.db_path, package, latest, directory)
        self.assertEqual(result['cleanup']['counts']['execution'], 1)
        cleanup.compare(directory/'configuration-after.sqlite3', directory/'cleaned.sqlite3', package['plan'])

    def test_publication_candidate_mismatch_and_stale_comment_refuse_deletion(self):
        package, latest = self.release_package()
        wrong = copy.deepcopy(latest)
        wrong['records'].pop()
        with self.assertRaisesRegex(ValueError, '准确最新版'):
            cleanup.verify_release_package(package, wrong)
        self.comment(self.old['method.skill.story-structure'])
        before = self.dump()
        with self.assertRaisesRegex(ValueError, '已变化'):
            cleanup.apply_release(self.store.db_path, package, latest, Path(self.tmp.name)/'stale-release')
        self.assertEqual(self.dump(), before)


if __name__ == '__main__':
    unittest.main()
