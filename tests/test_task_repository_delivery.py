import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import task_repository_delivery as adapter
import task_workspace_guard as guard
import integrate_generation_review_system as legacy


class TaskDeliveryTests(unittest.TestCase):
    def record(self):
        entries = {}
        for key, candidate in [('primary', 'a'*40), ('desk', 'b'*40)]:
            entries[key] = {'mode':'write', 'backend':'native', 'integration':{'phase':'prepared','candidate_commit':candidate},
                            'worktree':{'path':'.codex-task/worktrees/t' if key=='primary' else '.codex-task/linked-worktrees/t/desk'},
                            'git_delivery':{'phase':'prepared','remote':'origin','remote_ref':'refs/heads/main','candidate_commit':candidate}}
        return {'repositories':entries, 'repository_preparation':{k:{'integration':v['integration'].copy()} for k,v in entries.items()}}

    def value(self):
        return {'backend':'codex.task','command':['task','-C','/owner'],'owner':'/owner','task':'task-20261007-0001',
                'system_repository':'desk','repositories':{'primary':'a'*40,'desk':'b'*40}}

    def test_callback_workspace_is_preserved_without_duplicate_selector(self):
        prefix=['task','--config-dir','/config','-C','/owner','--data-dir','.codex-project']
        with patch.object(adapter.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps({'schemaVersion':1,'kind':'task','task':{}}),'')) as run:
            adapter.query(prefix,'/owner','task-id')
        self.assertEqual(run.call_args.args[0].count('-C'),1)
        with self.assertRaisesRegex(ValueError,'another workspace'):
                adapter.scoped(prefix,'/other')

    def test_existing_task_keeps_backend_but_native_missing_repo_is_an_error(self):
        with patch.object(adapter, 'command', return_value=['task']), patch.object(adapter, 'query', return_value={'attempts': 3}):
            self.assertFalse(adapter.uses_native_backend('/owner', 'task-20261006-0003'))
        with patch.object(adapter, 'command', return_value=['task']), patch.object(adapter, 'query', return_value={'repository_management': 'native'}):
            with self.assertRaisesRegex(ValueError, 'required companion'):
                adapter.uses_native_backend('/owner', 'task-20261007-0001')
        with patch.object(adapter, 'command', return_value=['task']), patch.object(adapter, 'query', return_value=self.record()):
            self.assertTrue(adapter.uses_native_backend('/owner', 'task-20261005-0007'))

    def test_candidate_drift_and_partial_delivery_are_rejected(self):
        value=self.value();record=self.record()
        record['repositories']['desk']['integration']['candidate_commit']='c'*40
        with patch.object(adapter,'query',return_value=record):
            with self.assertRaisesRegex(ValueError,'candidate changed'):adapter.validate(value)
        with patch.object(adapter,'query',return_value=self.record()):
            with self.assertRaisesRegex(ValueError,'integration is incomplete'):adapter.push_receipt(value)

    def test_native_apply_delegates_once_and_reads_group_receipts(self):
        record=self.record();value=self.value()
        def deliver(*args,**kwargs):
            for entry in record['repositories'].values():
                entry['integration']['phase']='applied';entry['git_delivery']['phase']='pushed'
            return subprocess.CompletedProcess([],0,'','')
        with patch.object(adapter,'query',return_value=record),patch.object(adapter.subprocess,'run',side_effect=deliver) as run:
            result=adapter.apply(value)
            push=adapter.push_receipt(value)
        self.assertEqual(run.call_count,1)
        self.assertIn('_deliver',run.call_args.args[0])
        self.assertNotIn('git',run.call_args.args[0])
        self.assertEqual(result['target_after'],'b'*40)
        self.assertTrue(push['remote_verified'])
        self.assertFalse(result['task_completed'])

    def test_native_failure_never_falls_back_to_legacy_integrator(self):
        with tempfile.TemporaryDirectory() as directory:
            plan=Path(directory)/'plan.json'
            plan.write_text(json.dumps({'format':'generation-system-delivery-v1','task_delivery':self.value()}))
            with patch.object(sys,'argv',['integrator','--plan',str(plan),'--apply']),patch.object(adapter,'apply',side_effect=ValueError('native failed')),patch.object(legacy,'integrate') as integrate:
                with self.assertRaisesRegex(ValueError,'native failed'):legacy.main()
                integrate.assert_not_called()

    def test_mount_guard_checks_stopped_containers_and_subdirectory_mounts(self):
        responses=[subprocess.CompletedProcess([],0,'abcdef\n',''),subprocess.CompletedProcess([],0,json.dumps([
            {'Id':'abcdef','Name':'preview','Mounts':[{'Source':'/owner/.codex-task/worktrees/task/.runtime/preview'}]}]),'')]
        with patch.object(guard.shutil,'which',return_value='docker'),patch.object(guard.subprocess,'run',side_effect=responses):
            result=guard.check(['/owner/.codex-task/worktrees/task'],owner=Path('/owner'))
        self.assertEqual(len(result['blockers']),1)
        with patch.object(guard.shutil,'which',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'unavailable'):guard.check(['/owner/task'])

    def test_formal_parent_mount_does_not_hide_a_task_specific_mount(self):
        rows = [{'Id': 'formal', 'Name': '/snakeslayingrecord-app-1', 'Mounts': [
            {'Source': '/owner', 'Destination': '/instance'},
            {'Source': '/owner/.codex-task/worktrees/task/config/instance.json', 'Destination': '/instance/config/instance.json'}]}]
        responses = [subprocess.CompletedProcess([],0,'formal\n',''),
                     subprocess.CompletedProcess([],0,json.dumps(rows),'')]
        with patch.object(guard.shutil, 'which', return_value='docker'), patch.object(guard.subprocess, 'run', side_effect=responses):
            result = guard.check(['/owner/.codex-task/worktrees/task'], owner=Path('/owner'))
        self.assertEqual(len(result['blockers']), 1)
        self.assertIn('config/instance.json', result['blockers'][0])
