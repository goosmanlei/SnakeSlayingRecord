"""Offline release review: stubbed processes/services and isolated temporary SQLite."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import ui_material_model_release as r


class ReleaseHarness:
    def __init__(self, root, *, candidate_running=False, failure=None, open_failure=False, checkpoint=(0, 0, 0)):
        self.root = root
        self.events = []
        self.doc = {'id': 'exact-migration'}
        old_mounts = [{'Destination': '/instance', 'Source': str(root / 'story-main'), 'RW': True}]
        candidate_mounts = [*old_mounts, {'Destination': '/instance/config/instance.json', 'Source': str(root / 'release/config'), 'RW': False}]
        self.m = {'story_main': str(root / 'story-main'), 'story_worktree': str(root / 'story'),
                  'story_target': 'old-story', 'system_candidate': 'reviewed-system', 'release_name': 'candidate',
                  'previous_app': {'image': 'old-image', 'mounts': old_mounts},
                  'previous_nginx': {'image': 'proxy-image', 'mounts': [], 'config_files': 'old-compose'}}
        self.image = {'image': 'candidate-image'}
        self.current = {'Image': 'candidate-image' if candidate_running else 'old-image',
                        'Mounts': candidate_mounts if candidate_running else old_mounts}
        self.proxy = {'image': 'proxy-image', 'mounts': [], 'config_files': 'old-compose'}
        self.volumes = [{'target': v['Destination'], 'source': v['Source'], 'read_only': not v['RW']} for v in candidate_mounts]
        def execute(sql):
            if sql != 'PRAGMA wal_checkpoint(TRUNCATE)':
                raise AssertionError('unexpected release SQL: ' + sql)
            self.events.append('checkpoint')
            return SimpleNamespace(fetchone=lambda: checkpoint)
        self.store = SimpleNamespace(db=SimpleNamespace(execute=Mock(side_effect=execute), close=lambda: self.events.append('close')))
        def store_factory(path):
            self.events.append('open-db')
            if open_failure:
                raise OSError('fixture database unavailable')
            return self.store
        self.Store = Mock(side_effect=store_factory)
        self.model = SimpleNamespace(migrate=Mock(side_effect=lambda *a, **kw: self.events.append('migrate') or {'already_applied': candidate_running}),
                                     verify=Mock(side_effect=lambda *a: self.events.append('verify-db') or {'ok': True}),
                                     rollback=Mock(side_effect=lambda *a, **kw: self.events.append('validate-inverse' if kw.get('validate_only') else 'rollback') or {'inverse': True}),
                                     prepare_legacy_runtime=Mock(side_effect=lambda *a: self.events.append('prepare-legacy') or {'legacy_compatible': True}))
        def run(command, *a, **kw):
            command = [str(item) for item in command]
            if command[:2] == [str(r.base.DOCKER), 'stop']:
                self.events.append('stop'); return b''
            if len(command) > 1 and command[1].endswith('/integrate_generation_review_system.py'):
                self.events.append('integrate-system'); return json.dumps({'target_after': self.m['system_candidate']}).encode()
            raise AssertionError('Forbidden external command in offline test: ' + repr(command))
        def verify(*a):
            self.events.append('verify-service')
            if failure:
                raise RuntimeError(failure)
            return {'ok': True}
        self.stack = contextlib.ExitStack()
        entries = [
            patch.object(r, 'authorized', return_value=(root, self.m, self.Store, self.model, self.doc)),
            patch.object(r.base, 'publication_locks', side_effect=lambda m: contextlib.nullcontext()),
            patch.object(r.service, 'checks', side_effect=lambda *a, **kw: self.events.append('checks-live' if kw.get('live', True) else 'checks-code') or self.image),
            patch.object(r.base, 'inspect', side_effect=lambda name, **kw: self.current if name == r.base.APP else self.proxy),
            patch.object(r.base, 'safe_container', side_effect=lambda v: {'image': v['Image'], 'mounts': v['Mounts']} if 'Image' in v else v),
            patch.object(r.base, 'compose_definition', return_value={'services': {'app': {'volumes': self.volumes}}}),
            patch.object(r, 'shadow_validate', side_effect=lambda *a: self.events.append('shadow')),
            patch.object(r.base, 'env_values', return_value={}), patch.object(r.base, 'run', side_effect=run),
            patch.object(r.service, 'install', side_effect=lambda *a: self.events.append('install') or root / 'release'),
            patch.object(r.base, 'compose_up', side_effect=lambda *a, **kw: self.events.append('start-candidate')),
            patch.object(r.base, 'verify_service', side_effect=verify),
            patch.object(r, 'restore_runtime', side_effect=lambda *a: self.events.append('restore-old')),
            patch.object(r.base, 'git', return_value='old-story'),
            patch.object(r.base, 'snapshot', side_effect=AssertionError('No direct live snapshot in apply/recover fixture')),
            contextlib.redirect_stdout(io.StringIO()),
        ]
        for item in entries:
            self.stack.enter_context(item)
        r.base.save(root / 'image.json', self.image)

    def close(self):
        self.stack.close()


class ModelReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = argparse.Namespace(bundle=self.root, apply=True)

    def harness(self, **kw):
        h = ReleaseHarness(self.root, **kw)
        self.addCleanup(h.close)
        return h

    def test_old_reader_stops_before_single_migration_and_archives_remain_deferred(self):
        h = self.harness()
        r.apply(self.args)
        self.assertEqual(h.events, ['checks-code', 'checks-live', 'shadow', 'integrate-system', 'stop', 'open-db', 'migrate', 'checkpoint', 'verify-db', 'install', 'start-candidate', 'verify-service', 'close'])
        h.model.migrate.assert_called_once_with(h.store, h.doc, system_head='reviewed-system', apply_archives=False)
        h.store.db.execute.assert_called_once_with('PRAGMA wal_checkpoint(TRUNCATE)')
        h.model.rollback.assert_not_called()
        h.model.prepare_legacy_runtime.assert_not_called()
        receipt = json.loads(next((self.root / 'run').glob('service-*.json')).read_text())
        self.assertEqual(receipt['archives'], 'deferred_until_story_complete')
        self.assertEqual(receipt['checkpoint'], {'busy': 0, 'log_frames': 0, 'checkpointed_frames': 0})
        self.assertFalse(receipt['complete_invoked'])
        self.assertFalse(receipt['push'])

    def test_busy_checkpoint_rolls_back_before_candidate_install_or_start(self):
        h = self.harness(checkpoint=(1, 24, 12))
        with self.assertRaisesRegex(ValueError, 'WAL checkpoint busy'):
            r.apply(self.args)
        self.assertEqual(h.events[-6:], ['migrate', 'checkpoint', 'stop', 'rollback', 'restore-old', 'close'])
        h.store.db.execute.assert_called_once_with('PRAGMA wal_checkpoint(TRUNCATE)')
        h.model.rollback.assert_called_once_with(h.store, h.doc, require_legacy=True)
        h.model.verify.assert_not_called()
        self.assertNotIn('install', h.events)
        self.assertNotIn('start-candidate', h.events)
        self.assertFalse(list((self.root / 'run').glob('service-*.json')))
        self.assertTrue(list((self.root / 'run').glob('recovery-*.json')))

    def test_real_wal_is_truncated_on_migration_connection_before_service_start(self):
        h = self.harness()
        path = self.root / 'checkpoint.sqlite3'
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        self.addCleanup(db.close)
        self.assertEqual(db.execute('PRAGMA journal_mode=WAL').fetchone()[0], 'wal')
        db.execute('PRAGMA wal_autocheckpoint=0')
        db.execute('CREATE TABLE fixture(payload TEXT)')
        db.execute('INSERT INTO fixture VALUES (?)', ('old-full-content' * 4096,))
        db.commit()
        wal = Path(str(path) + '-wal')
        self.assertGreater(wal.stat().st_size, 0)
        h.store.db = db
        def migrate(store, document, **kwargs):
            self.assertIs(store.db, db)
            db.execute('UPDATE fixture SET payload=?', ('deduplicated-reference',))
            db.commit()
            self.assertGreater(wal.stat().st_size, 0)
            return {'already_applied': False}
        def start(*args, **kwargs):
            self.assertEqual(wal.stat().st_size, 0)
            self.assertEqual(db.execute('SELECT payload FROM fixture').fetchone()[0], 'deduplicated-reference')
            h.events.append('start-candidate')
        h.model.migrate.side_effect = migrate
        with patch.object(r.base, 'compose_up', side_effect=start) as compose:
            r.apply(self.args)
            compose.assert_called_once()
        receipt = json.loads(next((self.root / 'run').glob('service-*.json')).read_text())
        self.assertEqual(receipt['checkpoint'], {'busy': 0, 'log_frames': 0, 'checkpointed_frames': 0})

    def test_failed_candidate_uses_exact_inverse_before_old_reader_restarts(self):
        h = self.harness(failure='health failed')
        with self.assertRaisesRegex(RuntimeError, 'health failed'):
            r.apply(self.args)
        self.assertEqual(h.events[-4:], ['stop', 'rollback', 'restore-old', 'close'])
        h.model.rollback.assert_called_once_with(h.store, h.doc, require_legacy=True)
        h.model.prepare_legacy_runtime.assert_not_called()
        self.assertTrue(list((self.root / 'run').glob('recovery-*.json')))

    def test_inverse_refusal_leaves_database_for_forward_recovery_without_old_runtime(self):
        h = self.harness(failure='health failed')
        h.model.rollback.side_effect = ValueError('fixture concurrent material changed')
        with self.assertRaisesRegex(RuntimeError, 'exact inverse recovery was refused'):
            r.apply(self.args)
        h.model.rollback.assert_called_once_with(h.store, h.doc, require_legacy=True)
        self.assertNotIn('restore-old', h.events)
        receipt = json.loads(next((self.root / 'run').glob('recovery-blocked-*.json')).read_text())
        self.assertFalse(receipt['database_snapshot_restored'])
        self.assertFalse(receipt['git_reset'])

    def test_same_exact_running_candidate_can_repeat_without_stopping_or_recreating_it(self):
        h = self.harness(candidate_running=True)
        r.apply(self.args)
        self.assertNotIn('stop', h.events)
        self.assertNotIn('start-candidate', h.events)
        h.model.migrate.assert_called_once_with(h.store, h.doc, system_head='reviewed-system', apply_archives=False)
        h.model.rollback.assert_not_called()

    def test_database_open_failure_prepares_legacy_database_before_old_reader_restarts(self):
        h = self.harness(open_failure=True)
        with self.assertRaisesRegex(OSError, 'database unavailable'):
            r.apply(self.args)
        self.assertEqual(h.events, ['checks-code', 'checks-live', 'shadow', 'integrate-system', 'stop', 'open-db', 'stop', 'prepare-legacy', 'restore-old'])
        h.model.prepare_legacy_runtime.assert_called_once_with(Path(h.m['story_main']) / '.runtime/review.sqlite3')
        h.model.rollback.assert_not_called()
        receipt = json.loads(next((self.root / 'run').glob('recovery-*.json')).read_text())
        self.assertEqual(receipt, {'legacy_compatible': True})
        self.assertFalse(list((self.root / 'run').glob('recovery-blocked-*.json')))

    def test_database_open_failure_and_legacy_guard_refusal_cannot_start_old_reader(self):
        h = self.harness(open_failure=True)
        def refuse(path):
            h.events.append('prepare-legacy')
            raise ValueError('fixture database still has material references')
        h.model.prepare_legacy_runtime.side_effect = refuse
        with self.assertRaisesRegex(RuntimeError, 'exact inverse recovery was refused') as error:
            r.apply(self.args)
        self.assertIsInstance(error.exception.__cause__, ValueError)
        self.assertEqual(h.events[-3:], ['open-db', 'stop', 'prepare-legacy'])
        self.assertNotIn('restore-old', h.events)
        h.model.prepare_legacy_runtime.assert_called_once_with(Path(h.m['story_main']) / '.runtime/review.sqlite3')
        h.model.rollback.assert_not_called()
        receipt = json.loads(next((self.root / 'run').glob('recovery-blocked-*.json')).read_text())
        self.assertEqual(receipt['status'], 'manual_forward_recovery_required')
        self.assertEqual(receipt['error_type'], 'ValueError')
        self.assertFalse(receipt['database_snapshot_restored'])
        self.assertFalse(receipt['git_reset'])
        self.assertEqual(len(list((self.root / 'run').glob('*.json'))), 1)

    def test_recovery_rejects_another_mount_even_when_the_image_matches(self):
        h = self.harness(candidate_running=True)
        h.current['Mounts'] = [{'Destination': '/instance', 'Source': str(self.root / 'another-story'), 'RW': True}]
        with self.assertRaisesRegex(ValueError, 'another|mount|runtime'):
            r.recover(self.args)
        self.assertNotIn('stop', h.events)
        h.model.rollback.assert_not_called()

    def test_repeat_apply_rejects_a_changed_proxy_before_migration(self):
        h = self.harness(candidate_running=True)
        h.proxy = {'image': 'unrelated-proxy', 'mounts': [], 'config_files': 'foreign-compose'}
        with self.assertRaisesRegex(ValueError, 'another|proxy|runtime'):
            r.apply(self.args)
        h.model.migrate.assert_not_called()
        self.assertNotIn('stop', h.events)

    def test_candidate_database_open_failure_does_not_interrupt_an_already_running_candidate(self):
        h = self.harness(candidate_running=True, open_failure=True)
        with self.assertRaisesRegex(OSError, 'database unavailable'):
            r.apply(self.args)
        self.assertNotIn('stop', h.events)
        self.assertNotIn('restore-old', h.events)
        h.model.rollback.assert_not_called()
        h.model.prepare_legacy_runtime.assert_not_called()

    def test_explicit_recovery_validates_exact_inverse_before_stopping_the_reader(self):
        h = self.harness(candidate_running=True)
        r.recover(self.args)
        self.assertEqual(h.events, ['open-db', 'validate-inverse', 'stop', 'rollback', 'restore-old', 'close'])
        self.assertEqual(h.model.rollback.call_args_list, [
            call(h.store, h.doc, validate_only=True, require_legacy=True),
            call(h.store, h.doc, require_legacy=True),
        ])

    def test_recovery_validation_refusal_preserves_the_running_candidate(self):
        h = self.harness(candidate_running=True)
        h.model.rollback.side_effect = ValueError('concurrent material change')
        with self.assertRaisesRegex(ValueError, 'concurrent material change'):
            r.recover(self.args)
        h.model.rollback.assert_called_once_with(h.store, h.doc, validate_only=True, require_legacy=True)
        self.assertNotIn('stop', h.events)
        self.assertNotIn('restore-old', h.events)
        self.assertEqual(h.events[-1], 'close')

    def test_recovery_after_story_completion_is_rejected_before_locks_or_database(self):
        h = self.harness(candidate_running=True)
        with patch.object(r.base, 'git', return_value='integrated-story'), patch.object(r.base, 'publication_locks') as locks:
            with self.assertRaisesRegex(ValueError, 'story already integrated'):
                r.recover(self.args)
            locks.assert_not_called()
        self.assertEqual(h.events, [])
        h.Store.assert_not_called()

    def test_story_candidate_drift_dirty_files_and_early_completion_stop_before_service_checks(self):
        worktree, main = self.root / 'worktree', self.root / 'main'
        candidate, target = 'a' * 40, 'b' * 40
        manifest = {'task': r.TASK, 'story_worktree': worktree, 'story_main': main, 'story_candidate': candidate, 'story_target': target}
        for problem in ('candidate', 'dirty', 'completed'):
            def git(repo, *args):
                if args == ('rev-parse', 'HEAD'):
                    if repo == worktree:
                        return 'c' * 40 if problem == 'candidate' else candidate
                    return candidate if problem == 'completed' else target
                if args == ('branch', '--show-current'):
                    return 'main'
                if args == ('status', '--porcelain', '--untracked-files=no'):
                    return ' M reviewed.py' if problem == 'dirty' else ''
                self.fail('unexpected read after guard: ' + repr(args))
            with self.subTest(problem=problem), patch.object(r.base, 'primary', return_value=main.resolve()), patch.object(r.base, 'git', side_effect=git), patch.object(r.base, 'run') as run, patch.object(r.base, 'inspect') as inspect:
                with self.assertRaisesRegex(ValueError, 'changed|completed'):
                    r.service.checks(self.root, manifest)
                run.assert_not_called()
                inspect.assert_not_called()

    def test_shadow_validation_opens_only_snapshot_and_defers_all_archive_writes(self):
        m = {'story_main': str(self.root / 'main'), 'system_candidate': 'candidate'}
        live = Path(m['story_main']) / '.runtime/review.sqlite3'
        store = SimpleNamespace(db=SimpleNamespace(close=Mock()))
        Store = Mock(return_value=store)
        model = SimpleNamespace(migrate=Mock(return_value={'validated_only': True}))
        with patch.object(r.base, 'snapshot') as snapshot:
            r.shadow_validate(self.root, m, Store, model, {'id': 'exact'})
        self.assertEqual(snapshot.call_args.args[0], live)
        self.assertNotEqual(Store.call_args.args[0], live)
        self.assertEqual(Store.call_args.args[0], snapshot.call_args.args[1])
        self.assertEqual(store.db_path, live)
        model.migrate.assert_called_once_with(store, {'id': 'exact'}, validate_only=True, system_head='candidate', apply_archives=False)
        store.db.close.assert_called_once()

    def test_changed_delivery_hash_fails_before_model_loading(self):
        story = self.root / 'story'
        helper = story / 'scripts/ui_material_model_release.py'
        helper.parent.mkdir(parents=True)
        helper.write_bytes(Path(r.__file__).read_bytes())
        package = story / r.PACKAGE
        package.parent.mkdir(parents=True)
        package.write_text('{}')
        r.base.save(self.root / 'manifest.json', {})
        manifest = {'format': 'ui-material-model-release-v1', 'service_manifest_sha256': r.base.sha((self.root / 'manifest.json').read_bytes()),
                    'migration_id': 'migration', 'package': r.PACKAGE,
                    'hashes': {r.PACKAGE: r.base.sha(package.read_bytes()), 'scripts/ui_material_model_release.py': r.base.sha(helper.read_bytes())}}
        r.base.save(self.root / 'model-manifest.json', manifest)
        package.write_text('{"drift":true}')
        with patch.object(r.service, 'load_bundle', return_value=(self.root, {'task': r.TASK, 'story_worktree': story})), patch.object(r, 'model_api') as api:
            with self.assertRaisesRegex(ValueError, 'model delivery changed'):
                r.load(self.root)
            api.assert_not_called()

    def test_each_approved_digest_is_required_before_apply_can_acquire_locks(self):
        for name in ('manifest.json', 'image.json', 'model-manifest.json'):
            (self.root / name).write_text('{}')
        digest = r.base.sha(b'{}')
        for key in ('manifest_sha256', 'image_receipt_sha256', 'model_manifest_sha256'):
            args = argparse.Namespace(bundle=self.root, apply=True, manifest_sha256=digest, image_receipt_sha256=digest, model_manifest_sha256=digest)
            setattr(args, key, 'unapproved')
            with patch.object(r, 'load', return_value=(self.root, {}, None, None, {})), patch.object(r.base, 'publication_locks') as locks:
                with self.assertRaisesRegex(ValueError, 'approved digest differs'):
                    r.apply(args)
                locks.assert_not_called()


if __name__ == '__main__':
    unittest.main()
