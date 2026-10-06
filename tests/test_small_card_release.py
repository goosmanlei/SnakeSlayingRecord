"""Small-card delivery order and ordinary fast-forward system push guards."""
import argparse
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import material_review_release as r


class SmallCardReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.work=self.root/'system';self.remote=self.root/'remote.git'
        subprocess.run(['git','init','--bare',str(self.remote)],check=True,capture_output=True)
        self.work.mkdir();self.git('init','-b','main');self.git('config','user.name','Fixture');self.git('config','user.email','fixture@example.invalid')
        (self.work/'code').write_text('base');self.git('add','code');self.git('commit','-m','base')
        self.target=self.git('rev-parse','HEAD');self.git('remote','add','origin',str(self.remote));self.git('push','-u','origin','main')
        (self.work/'code').write_text('candidate');self.git('commit','-am','candidate');self.candidate=self.git('rev-parse','HEAD')

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.work),*args],stderr=subprocess.DEVNULL,text=True).strip()

    def manifest(self):
        return {'system_worktree':str(self.work),'system_main':str(self.work),'system_candidate':self.candidate,'system_target':self.target,
                'system_upstream':r.system_upstream(self.work,self.target,self.candidate)}

    def test_serial_delivery_can_verify_a_normal_push_and_resume_same_candidate(self):
        m=self.manifest();args=argparse.Namespace(apply=True,bundle=self.root)
        with patch.object(r,'authorized',return_value=(self.root,m)),contextlib.redirect_stdout(io.StringIO()):
            r.publish_system(args);r.publish_system(args)
        self.assertEqual(self.git('ls-remote','origin','refs/heads/main').split()[0],self.candidate)
        receipt=r.read(self.root/'run/system-push.json');self.assertTrue(receipt['remote_verified']);self.assertFalse(receipt['force'])

    def test_remote_divergence_or_multiple_destinations_stop_before_push(self):
        m=self.manifest();other=self.root/'other'
        subprocess.run(['git','clone','-b','main',str(self.remote),str(other)],check=True,capture_output=True)
        def git(*args):return subprocess.check_output(['git','-C',str(other),*args],stderr=subprocess.DEVNULL,text=True).strip()
        git('config','user.name','Other');git('config','user.email','other@example.invalid');(other/'new').write_text('other');git('add','new');git('commit','-m','other');git('push','origin','main')
        with patch.object(r,'authorized',return_value=(self.root,m)),patch.object(r,'run') as push:
            with self.assertRaisesRegex(ValueError,'remote changed'):r.publish_system(argparse.Namespace())
            push.assert_not_called()
        self.git('config','--add','remote.origin.pushurl',str(self.remote));self.git('config','--add','remote.origin.pushurl',str(self.root/'another'))
        with self.assertRaisesRegex(ValueError,'one destination'):r.system_upstream(self.work,self.target,self.candidate)

    def test_task_name_and_code_first_exception_are_specific(self):
        self.assertTrue(r.release_name('task-20261005-0003',self.candidate,self.target).startswith('small-cards-20261005-0003-'))
        m={'task':'task-20261005-0003','story_worktree':'w','story_main':'m','story_candidate':self.candidate,'story_target':self.target}
        with patch.object(r.base,'repo_check',side_effect=RuntimeError('stop before any service read')) as check:
            with self.assertRaisesRegex(RuntimeError,'stop before'):r.checks(self.root,m)
            self.assertTrue(check.call_args.kwargs['system'])

    def test_breakdown_page_release_can_apply_after_controlled_story_delivery(self):
        self.assertTrue(r.release_name('task-20261005-0004',self.candidate,self.target).startswith('breakdown-page-20261005-0004-'))
        m={'task':'task-20261005-0004','story_worktree':'w','story_main':'m','story_candidate':self.candidate,'story_target':self.target}
        with patch.object(r.base,'repo_check',side_effect=RuntimeError('stop before any service read')) as check:
            with self.assertRaisesRegex(RuntimeError,'stop before'):r.checks(self.root,m)
            self.assertTrue(check.call_args.kwargs['system'])
