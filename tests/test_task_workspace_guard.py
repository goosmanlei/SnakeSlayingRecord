import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('task_workspace_guard',Path(__file__).parents[1]/'scripts/task_workspace_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)


class FormalPredecessorMountTests(unittest.TestCase):
    def inspect(self,root,*,command=None,labels=None,extra=None):
        return {'Id':'old-runtime','Name':'/retained-previous-app','State':{'Running':False},
                'Config':{'Cmd':command or ['python','-m','review_desk','--instance','/instance','serve'],
                          'Labels':labels if labels is not None else {'com.docker.compose.project':'snakeslayingrecord',
                              'com.docker.compose.service':'app','com.docker.compose.project.working_dir':str(root)}},
                'Mounts':[{'Source':str(root),'Destination':'/instance'},*(extra or [])]}

    def check(self,root,row):
        def execute(args,**kwargs):
            value='old-runtime\n' if args[1:]==['ps','-aq'] else json.dumps([row])
            return subprocess.CompletedProcess(args,0,value,'')
        with patch.object(guard.shutil,'which',return_value='docker'),patch.object(guard.subprocess,'run',side_effect=execute):
            return guard.check([root/'.codex-task/worktrees/current-task'],owner=root)['blockers']

    def test_retained_formal_root_mount_does_not_depend_on_every_task(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();self.assertEqual(self.check(root,self.inspect(root)),[])

    def test_explicit_task_mount_on_same_formal_predecessor_still_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();task=root/'.codex-task/worktrees/current-task'
            row=self.inspect(root,extra=[{'Source':str(task/'actual-input'),'Destination':'/input'}])
            blockers=self.check(root,row);self.assertEqual(len(blockers),1);self.assertIn('actual-input',blockers[0])

    def test_custom_command_or_unverified_labels_keep_parent_mount_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            for row in [self.inspect(root,command=['python','-c','read task inputs']),self.inspect(root,labels={})]:
                with self.subTest(row=row):self.assertEqual(len(self.check(root,row)),1)


if __name__=='__main__':unittest.main()
