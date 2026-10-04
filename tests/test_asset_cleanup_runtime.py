import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import asset_cleanup_runtime as cleanup


class RuntimeCleanupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.story = self.root / 'story'
        self.workspace = self.root / 'task'
        self.story.mkdir()
        self.workspace.mkdir()
        self.containers = {}
        self.commands = []
        self.removed = []
        self.diff = b'A /app/review_desk/__pycache__\nA /app/review_desk/__pycache__/store.pyc\nC /app\nC /app/review_desk\nA /instance\n'
        self.fail_remove = None
        self.fail_after_remove = None
        self.fail_log = False
        self.image_exists = True
        for index in range(4):
            cid = f'{index + 1:064x}'
            self.containers[cid] = {
                'Id': cid, 'Name': '/snakeslayingrecord-production-task-0003-before-fixture-' + str(index),
                'Image': 'sha256:' + 'a' * 64, 'Created': '2026-10-01T00:00:00Z',
                'State': {'Status': 'exited', 'Running': False, 'StartedAt': 'before', 'FinishedAt': 'after', 'ExitCode': 0},
                'Config': {'Entrypoint': None, 'Cmd': ['python', '-m', 'review_desk'], 'WorkingDir': '/app',
                           'Env': ['OPENAI_API_KEY=do-not-export-fixture-secret']},
                'HostConfig': {'RestartPolicy': {'Name': 'no'}, 'NetworkMode': 'bridge', 'PortBindings': {}},
                'Mounts': [{'Type': 'bind', 'Source': str(self.story / cleanup.SOURCE),
                            'Destination': '/instance', 'Mode': '', 'RW': True, 'Propagation': 'rprivate'}]}
        changes = sorted(self.diff.decode().splitlines())
        self.manifest = {'format': 'retired-preview-cleanup-v1', 'containers': [
            {'identity': cleanup.identity(c, self.story),
             'layer_changes_sha256': cleanup.digest(cleanup.canonical(changes)), 'instance_state': 'empty'}
            for c in self.containers.values()]}
        self.manifest_path = self.workspace / 'manifest.json'
        self.save_manifest()
        for target, value in [('generation_root', self.workspace), ('primary_root', self.story)]:
            p = patch.object(cleanup, target, return_value=value)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(cleanup, 'docker', side_effect=self.docker)
        p.start()
        self.addCleanup(p.stop)

    def save_manifest(self):
        self.raw = json.dumps(self.manifest).encode()
        self.manifest_path.write_bytes(self.raw)
        self.sha = cleanup.digest(self.raw)

    def docker(self, *args):
        self.commands.append(args)
        raw, err, status = b'', b'', 0
        if args[:3] == ('inspect', '--type', 'container'):
            value = self.containers.get(args[3])
            if value:
                raw = json.dumps([value]).encode()
            else:
                status, err = 1, ('Error: No such container: ' + args[3]).encode()
        elif args[:2] == ('image', 'inspect'):
            if self.image_exists:
                raw = json.dumps([{'Id': args[2]}]).encode()
            else:
                status = 1
        elif args[0] == 'diff':
            raw = self.diff
        elif args[:2] == ('logs', '--timestamps'):
            status = 1 if self.fail_log is True or self.fail_log == args[2] else 0
            raw, err = b'GET / 200\n', b'stderr history\n'
        elif args[0] == 'rm':
            self.assertEqual(len(args), 2)
            if self.fail_remove == args[1]:
                status = 1
            else:
                del self.containers[args[1]]
                self.removed.append(args[1])
                if self.fail_after_remove == args[1]:
                    self.fail_after_remove = None
                    raise OSError('simulated interruption after Docker removed the container')
                raw = (args[1] + '\n').encode()
        else:
            self.fail('Unexpected Docker operation: ' + repr(args))
        return subprocess.CompletedProcess(['docker', *args], status, raw, err)

    def run_cleanup(self, apply=False, **kwargs):
        if apply:
            kwargs.setdefault('manifest_sha', self.sha)
            kwargs.setdefault('run_name', 'fixture')
        return cleanup.cleanup(self.workspace, self.manifest_path, apply=apply, **kwargs)

    def test_preflight_reads_all_members_without_writing_or_deleting(self):
        result = self.run_cleanup()
        self.assertFalse(result['applied'])
        self.assertEqual(len(result['previews']), 4)
        self.assertEqual(self.removed, [])
        self.assertEqual(list(self.workspace.iterdir()), [self.manifest_path])
        self.assertNotIn('do-not-export', json.dumps(result))

    def test_running_last_target_blocks_entire_apply(self):
        last = list(self.containers)[-1]
        self.containers[last]['State'].update(Status='running', Running=True)
        with self.assertRaisesRegex(ValueError, 'no longer stopped'):
            self.run_cleanup(apply=True)
        self.assertEqual(self.removed, [])

    def test_manifest_requires_explicit_sha_and_rejects_shell_like_ids(self):
        with self.assertRaisesRegex(ValueError, 'requires the exact'):
            self.run_cleanup(apply=True, manifest_sha=None)
        with self.assertRaisesRegex(ValueError, 'SHA-256 differs'):
            self.run_cleanup(apply=True, manifest_sha='0' * 64)
        self.manifest['containers'][0]['identity']['id'] = '--force'
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'not a retired'):
            self.run_cleanup(apply=True)
        self.assertEqual(self.commands, [])

    def test_formal_name_and_changed_command_are_rejected(self):
        first = next(iter(self.containers.values()))
        first['Name'] = '/snakeslayingrecord-app-1'
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            self.run_cleanup(apply=True)
        first['Name'] = self.manifest['containers'][0]['identity']['name']
        first['Config']['Cmd'] = ['python', '-m', 'another_service']
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            self.run_cleanup(apply=True)
        self.assertEqual(self.removed, [])

    def test_revived_mount_and_symlink_are_rejected(self):
        source = self.story / cleanup.SOURCE
        source.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'exists again'):
            self.run_cleanup(apply=True)
        source.rmdir()
        source.symlink_to(self.story / 'missing')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.run_cleanup(apply=True)
        self.assertEqual(self.removed, [])

    def test_changed_layer_nonempty_instance_and_missing_image_are_rejected(self):
        original = self.diff
        self.diff += b'A /app/business.sqlite3\n'
        with self.assertRaisesRegex(ValueError, 'non-cache'):
            self.run_cleanup(apply=True)
        self.diff = original
        self.diff += b'A /instance/business.sqlite3\n'
        with self.assertRaisesRegex(ValueError, 'non-cache'):
            self.run_cleanup(apply=True)
        self.diff = original
        self.image_exists = False
        with self.assertRaisesRegex(ValueError, 'Docker operation failed: image'):
            self.run_cleanup(apply=True)
        self.assertEqual(self.removed, [])

    def test_deleted_target_without_receipt_is_not_assumed_completed(self):
        del self.containers[next(iter(self.containers))]
        with self.assertRaisesRegex(ValueError, 'without a removal receipt'):
            self.run_cleanup(apply=True)
        self.assertEqual(self.removed, [])

    def test_archive_failure_prevents_removal(self):
        self.fail_log = True
        with self.assertRaisesRegex(ValueError, 'log archive failed'):
            self.run_cleanup(apply=True)
        self.assertEqual(self.removed, [])

    def test_apply_archives_credentials_free_identity_and_preserves_images(self):
        result = self.run_cleanup(apply=True)
        self.assertEqual(len(result['removed_ids']), 4)
        self.assertTrue(all(command[0] not in ('rmi', 'prune', 'stop', 'cp', 'start') for command in self.commands))
        receipt = json.loads((self.workspace / result['receipt']).read_text())
        run = (self.workspace / result['receipt']).parent
        for row in receipt['containers'].values():
            cleanup.verify_archive(run, row)
            data = (run / row['id'] / 'inspection.json').read_text()
            self.assertNotIn('do-not-export', data)
            self.assertEqual((run / row['id'] / 'stdout.log').stat().st_mode & 0o777, 0o600)
        repeated = self.run_cleanup(apply=True)
        self.assertEqual(result['removed_ids'], repeated['removed_ids'])
        self.assertEqual(len(self.removed), 4)

    def test_failed_remove_stops_and_resumes_without_redeleting_previous(self):
        self.fail_remove = list(self.containers)[2]
        with self.assertRaisesRegex(ValueError, 'Docker operation failed: rm'):
            self.run_cleanup(apply=True)
        self.assertEqual(len(self.removed), 2)
        self.fail_remove = None
        self.run_cleanup(apply=True)
        self.assertEqual(len(set(self.removed)), 4)
        self.assertEqual(len(self.removed), 4)

    def test_interruption_after_rm_recovers_from_durable_started_receipt(self):
        self.fail_after_remove = next(iter(self.containers))
        with self.assertRaisesRegex(OSError, 'simulated interruption'):
            self.run_cleanup(apply=True)
        self.assertEqual(len(self.removed), 1)
        self.run_cleanup(apply=True)
        self.assertEqual(len(self.removed), 4)

    def test_second_archive_failure_preserves_partial_archive_and_resumes(self):
        self.fail_log = list(self.containers)[1]
        with self.assertRaisesRegex(ValueError, 'log archive failed'):
            self.run_cleanup(apply=True)
        self.assertEqual(len(self.removed), 1)
        self.fail_log = False
        result = self.run_cleanup(apply=True)
        receipt = json.loads((self.workspace / result['receipt']).read_text())
        self.assertEqual(len(receipt['interrupted_archives']), 1)
        self.assertEqual(len(self.removed), 4)

    def test_partial_log_write_can_resume_after_previous_removal(self):
        original = cleanup.private_bytes
        count = 0

        def interrupted(path, raw):
            nonlocal count
            count += 1
            if count == 5:
                path.write_bytes(raw[:3])
                raise OSError('simulated incomplete log write')
            return original(path, raw)

        with patch.object(cleanup, 'private_bytes', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'incomplete log write'):
                self.run_cleanup(apply=True)
        self.assertEqual(len(self.removed), 1)
        result = self.run_cleanup(apply=True)
        receipt = json.loads((self.workspace / result['receipt']).read_text())
        self.assertEqual(len(receipt['interrupted_archives']), 1)
        self.assertEqual(len(self.removed), 4)

    def test_tampered_recovery_evidence_blocks_resume(self):
        self.fail_after_remove = next(iter(self.containers))
        with self.assertRaises(OSError):
            self.run_cleanup(apply=True)
        logfile = next((self.workspace / '.runtime').rglob('stdout.log'))
        logfile.write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'archive changed'):
            self.run_cleanup(apply=True)
        self.assertEqual(len(self.removed), 1)


if __name__ == '__main__':
    unittest.main()
