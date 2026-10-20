import argparse
from contextlib import ExitStack
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import oss_snapshot_release as release


class SnapshotPublicationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.control=self.root/'control';self.control.mkdir()
        self.target=self.root/'www/lijizhanshe';self.target.mkdir(parents=True)
        self.publication='lijizhanshe-test-r1'
        self.path=self.control/'snapshot-releases'/self.publication
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(release.vps,'CONTROL',self.control))
        self.stack.enter_context(patch.object(release.vps,'TARGET',self.target))

    def archive(self, members):
        path=self.control/'incoming'/self.publication/'bundle.tar.gz'
        path.parent.mkdir(parents=True)
        with tarfile.open(path,'w:gz') as tar:
            for name,data,kind in members:
                member=tarfile.TarInfo(name);member.size=len(data);member.type=kind
                tar.addfile(member,io.BytesIO(data) if kind==tarfile.REGTYPE else None)
        return path

    def test_selected_task_is_recorded_and_cannot_read_another_tasks_receipt(self):
        task='task-20261020-0009'
        self.path.mkdir(parents=True)
        release.save(self.path/'receipt.json',{'task':task,'publication_id':self.publication,'phase':'staged'})
        with patch.object(release,'TASK',release.TASK),patch.object(release.code,'TASK',release.code.TASK):
            with patch.object(sys,'argv',['publisher','--task',task,'status','--release',str(self.path)]):
                release.main()
            self.assertEqual(release.code.TASK,task)
            self.assertEqual(release.receipt(self.path)['task'],task)
            release.save(self.path/'receipt.json',{'task':'task-20261020-0004','publication_id':self.publication})
            with self.assertRaisesRegex(ValueError,'wrong release receipt'):
                release.receipt(self.path)

    def test_invalid_task_rejects_before_freezing_or_creating_control_directory(self):
        with patch.object(sys,'argv',['publisher','--task','../other','prepare','--story',str(self.root),
            '--desk',str(self.root),'--formal',str(self.root),'--output',str(self.root/'out'),
            '--publication',self.publication]),patch.object(release,'prepare') as prepare:
            with self.assertRaises(SystemExit):release.main()
            prepare.assert_not_called()
        self.assertFalse((self.root/'out').exists())

    def test_incomplete_or_changed_archive_keeps_old_service_untouched(self):
        path=self.archive([('file',b'complete',tarfile.REGTYPE)])
        for selected,digest in [(path.with_suffix('.part'),release.code.sha(path)),(path,'0'*64)]:
            with self.subTest(path=selected),patch.object(release.vps,'preflight') as preflight:
                with self.assertRaises(ValueError):
                    release.stage(argparse.Namespace(publication=self.publication,archive=selected,sha256=digest))
                preflight.assert_not_called()
                self.assertFalse(self.path.exists())

    def test_archive_traversal_symlink_duplicates_and_member_limit_are_rejected(self):
        for members in [[('../escape',b'',tarfile.REGTYPE)],[('link',b'',tarfile.SYMTYPE)],
                        [('same',b'a',tarfile.REGTYPE),('same',b'b',tarfile.REGTYPE)],
                        [(str(n),b'',tarfile.REGTYPE) for n in range(101)]]:
            path=self.archive(members)
            with self.subTest(members=members),patch.object(release.vps,'preflight'):
                with self.assertRaises(ValueError):
                    release.stage(argparse.Namespace(publication=self.publication,archive=path,sha256=release.code.sha(path)))
                self.assertFalse(self.path.exists())
            path.unlink();path.parent.rmdir()

    def setup_cutover(self):
        self.path.mkdir(parents=True)
        candidate=self.path/'candidate';(candidate/'.runtime').mkdir(parents=True)
        (self.target/'.runtime').mkdir()
        (candidate/'.runtime/review.sqlite3').write_text('new-business-data')
        (self.target/'.runtime/review.sqlite3').write_text('old-vps-comments')
        usage=self.control/'usage';usage.mkdir();(usage/'attempts.json').write_text('{"attempts":2,"total_attempts":6}')
        for name in ('state.json','storage-runtime.json'):
            (self.control/name).write_text(json.dumps({'phase':'complete','publication_id':'old-publication'}))
        old={'Id':'old-id','Image':'image-id','Name':'/lijizhanshe-app','State':{'Running':True},
             'Config':{'Labels':{'org.leiguoguo.instance':'lijizhanshe'},'Cmd':['python'],'Env':[]},
             'Mounts':[{'Source':str(self.target),'Destination':'/instance','Type':'bind','RW':True}],
             'HostConfig':{'NetworkMode':'host','Memory':1024**3,'MemorySwap':1536*1024**2,'NanoCpus':10**9,'PidsLimit':64}}
        self.containers={'old-id':old}
        value={'task':release.TASK,'publication_id':self.publication,'phase':'prepared','image_id':'image-id',
               'manifest_sha256':'manifest','commits':{'story':'story','desk':'desk'}}
        release.save(self.path/'receipt.json',value)
        def inspect(name):
            for container in self.containers.values():
                if container['Id']==name or container['Name']=='/'+name:return container
            raise ValueError('missing container')
        def optional(name):
            try:return inspect(name)
            except ValueError:return None
        def execute(args,**kwargs):
            if args[:2]==['docker','stop']:inspect(args[-1])['State']['Running']=False
            elif args[:2]==['docker','start']:inspect(args[-1])['State']['Running']=True
            elif args[:2]==['docker','rename']:inspect(args[2])['Name']='/'+args[3]
            elif args[:2]==['docker','rm']:del self.containers[inspect(args[2])['Id']]
            else:raise AssertionError(args)
            return ''
        def clone(old,value):
            self.containers['new-id']={**old,'Id':'new-id','Name':'/lijizhanshe-app','State':{'Running':False},
                'Config':{**old['Config'],'Labels':{'org.leiguoguo.snapshot-release':value['manifest_sha256']}}}
        for name,func in [('inspect',inspect),('optional_container',optional),('owned_runtime',lambda *a:None),('verify_mount_sources',lambda *a:None)]:
            self.stack.enter_context(patch.object(release.code,name,side_effect=func))
        for name,func in [('preflight',lambda:None),('credential_check',lambda:None),('check_runtime_target',lambda *a:None),
                          ('runtime_target',lambda:{'network':'host'}),('configure',lambda *a:None)]:
            self.stack.enter_context(patch.object(release.vps,name,side_effect=func))
        self.stack.enter_context(patch.object(release,'checked_bundle',return_value={}))
        self.stack.enter_context(patch.object(release,'database',side_effect=lambda path:Path(path).read_text()))
        self.stack.enter_context(patch.object(release,'run',side_effect=execute))
        self.stack.enter_context(patch.object(release,'probe'))
        return clone

    def test_explicit_replacement_switches_full_state_and_retains_old_data(self):
        clone=self.setup_cutover()
        with patch.object(release,'clone_runtime',side_effect=clone):
            release.apply(argparse.Namespace(release=self.path,replace_experience_data=True))
        self.assertEqual((self.target/'.runtime/review.sqlite3').read_text(),'new-business-data')
        self.assertEqual((self.path/'previous-instance/.runtime/review.sqlite3').read_text(),'old-vps-comments')
        self.assertEqual(json.loads((self.control/'usage/attempts.json').read_text())['total_attempts'],6)
        self.assertEqual(json.loads((self.control/'state.json').read_text())['publication_id'],self.publication)
        self.assertEqual(release.receipt(self.path)['phase'],'open')

    def test_missing_explicit_replace_flag_rejects_without_touching_target(self):
        with self.assertRaisesRegex(ValueError,'explicit'):
            release.apply(argparse.Namespace(release=self.path,replace_experience_data=False))
        self.assertFalse(self.path.exists())

    def test_create_failure_after_directory_switch_restores_original_comments_and_runtime(self):
        self.setup_cutover()
        with patch.object(release,'clone_runtime',side_effect=RuntimeError('injected create failure')):
            with self.assertRaisesRegex(RuntimeError,'injected'):
                release.apply(argparse.Namespace(release=self.path,replace_experience_data=True))
        self.assertEqual((self.target/'.runtime/review.sqlite3').read_text(),'old-vps-comments')
        self.assertEqual((self.path/'failed-instance/.runtime/review.sqlite3').read_text(),'new-business-data')
        self.assertEqual(self.containers['old-id']['Name'],'/lijizhanshe-app')
        self.assertTrue(self.containers['old-id']['State']['Running'])
        self.assertEqual(release.receipt(self.path)['phase'],'rolled-back')

    def test_opening_uncertainty_never_rolls_back_and_resume_keeps_new_writes(self):
        clone=self.setup_cutover()
        def configure(maintenance):
            if not maintenance:
                (self.target/'.runtime/review.sqlite3').write_text('new-public-comment')
                raise RuntimeError('proxy reload result unknown')
        with patch.object(release,'clone_runtime',side_effect=clone),patch.object(release.vps,'configure',side_effect=configure):
            with self.assertRaisesRegex(RuntimeError,'unknown'):
                release.apply(argparse.Namespace(release=self.path,replace_experience_data=True))
        self.assertEqual(release.receipt(self.path)['phase'],'opening')
        with self.assertRaisesRegex(ValueError,'may accept writes'):
            release.rollback(self.path,release.receipt(self.path))
        release.resume(argparse.Namespace(release=self.path))
        self.assertEqual((self.target/'.runtime/review.sqlite3').read_text(),'new-public-comment')
        self.assertEqual(release.receipt(self.path)['phase'],'open')

    def test_live_write_lock_conflict_keeps_old_data_and_original_runtime(self):
        self.setup_cutover()
        import fcntl
        with (self.target/'.runtime/http-write.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                release.apply(argparse.Namespace(release=self.path,replace_experience_data=True))
        self.assertEqual((self.target/'.runtime/review.sqlite3').read_text(),'old-vps-comments')
        self.assertTrue(self.containers['old-id']['State']['Running'])

    def test_existing_readonly_lock_can_be_locked_without_changing_permissions(self):
        import fcntl
        path=self.root/'http-write.lock';path.write_text('');path.chmod(0o444)
        with release.write_window(path) as first:
            self.assertFalse(first.writable())
            fcntl.flock(first,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with release.write_window(path) as second:
                with self.assertRaises(BlockingIOError):fcntl.flock(second,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.assertEqual(path.stat().st_mode&0o777,0o444)

    def test_retry_preserves_first_failure_and_reuses_the_same_frozen_candidate(self):
        clone=self.setup_cutover()
        import fcntl
        with (self.target/'.runtime/http-write.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                release.apply(argparse.Namespace(release=self.path,replace_experience_data=True))
        with patch.object(release,'clone_runtime',side_effect=clone):
            release.retry(argparse.Namespace(release=self.path,replace_experience_data=True,controller_commit='a'*40))
        self.assertEqual(release.receipt(self.path)['phase'],'open')
        self.assertEqual(json.loads((self.path/'attempt-1.json').read_text())['phase'],'rolled-back')
        self.assertEqual(release.receipt(self.path)['controller']['commit'],'a'*40)
        self.assertEqual((self.target/'.runtime/review.sqlite3').read_text(),'new-business-data')


if __name__=='__main__':unittest.main()
