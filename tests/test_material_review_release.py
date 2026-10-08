"""Release guards and preservation checks; no formal Docker/DB writes."""
import argparse
import contextlib
import importlib.util
import io
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import material_review_release as r
import task_repository_delivery as delivery

class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.before=self.root/'before.sqlite3';self.after=self.root/'after.sqlite3'
        with sqlite3.connect(self.before) as db:
            db.executescript("CREATE TABLE revisions(id TEXT PRIMARY KEY,payload TEXT);CREATE TABLE comments(id TEXT PRIMARY KEY,body TEXT);CREATE TABLE comment_events(id INTEGER PRIMARY KEY,body TEXT);INSERT INTO revisions VALUES ('one','unchanged');INSERT INTO comments VALUES ('c','original');INSERT INTO comment_events VALUES (1,'CREATE');")
        shutil.copyfile(self.before,self.after)

    def test_concurrent_user_comment_edit_keeps_history_and_is_not_restored(self):
        with sqlite3.connect(self.after) as db:
            db.execute("UPDATE comments SET body='user edit'");db.execute("INSERT INTO comment_events VALUES (2,'EDIT')");db.execute('CREATE INDEX revision_lookup ON revisions(payload)')
        result=r.preserved(self.before,self.after);self.assertEqual(result['revisions']['before'],1);self.assertEqual(result['comment_events']['after'],2)
        self.assertEqual(sqlite3.connect(self.after).execute('SELECT body FROM comments').fetchone()[0],'user edit')

    def test_lost_revision_event_or_comment_identity_is_rejected(self):
        for table in ('revisions','comment_events','comments'):
            shutil.copyfile(self.before,self.after)
            with sqlite3.connect(self.after) as db:db.execute('DELETE FROM '+table)
            with self.assertRaisesRegex(ValueError,'lost'):r.preserved(self.before,self.after)

    def install_read_generation_fixture(self):
        with sqlite3.connect(self.after) as db:
            names=[row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            db.execute('CREATE TABLE read_generations (name TEXT PRIMARY KEY, token TEXT NOT NULL)')
            for name in names:
                db.execute('INSERT INTO read_generations VALUES (?,?)',(name,'a'*32))
                for operation in ('INSERT','UPDATE','DELETE'):
                    trigger='read_generation_'+hashlib.sha256((name+operation).encode()).hexdigest()[:24]
                    db.execute(f'CREATE TRIGGER "{trigger}" AFTER {operation} ON "{name}" BEGIN UPDATE read_generations SET token=lower(hex(randomblob(16))) WHERE name=\'{name}\'; END')

    def test_only_reviewed_cache_migration_is_allowed_and_history_remains_required(self):
        self.install_read_generation_fixture()
        with self.assertRaisesRegex(ValueError,'table set changed'):
            r.preserved(self.before,self.after)
        self.assertEqual(r.preserved(self.before,self.after,allow_read_generations=True)['revisions']['after'],1)
        with sqlite3.connect(self.after) as db:db.execute('DELETE FROM revisions')
        with self.assertRaisesRegex(ValueError,'immutable history lost'):
            r.preserved(self.before,self.after,allow_read_generations=True)

    def test_cache_migration_rejects_missing_trigger_or_invalid_token(self):
        self.install_read_generation_fixture()
        with sqlite3.connect(self.after) as db:
            db.execute("UPDATE read_generations SET token='invalid' WHERE name='revisions'")
        with self.assertRaisesRegex(ValueError,'invalid read generation token'):
            r.preserved(self.before,self.after,allow_read_generations=True)
        with sqlite3.connect(self.after) as db:
            db.execute("UPDATE read_generations SET token=?",('a'*32,))
            name=db.execute("SELECT name FROM sqlite_master WHERE type='trigger' LIMIT 1").fetchone()[0]
            db.execute('DROP TRIGGER "'+name+'"')
        with self.assertRaisesRegex(ValueError,'triggers differ'):
            r.preserved(self.before,self.after,allow_read_generations=True)

    def test_unconfirmed_flag_or_changed_digests_stop_before_action(self):
        args=argparse.Namespace(apply=False,bundle=self.root,manifest_sha256='wrong',image_receipt_sha256='wrong')
        with patch.object(r,'load_bundle') as load:
            with self.assertRaisesRegex(ValueError,'confirmation'):r.authorized(args)
            load.assert_not_called()
        (self.root/'manifest.json').write_text('{}');(self.root/'image.json').write_text('{}');args.apply=True
        with patch.object(r,'load_bundle',return_value=(self.root,{})):
            with self.assertRaisesRegex(ValueError,'digest'):r.authorized(args)

    def test_foreign_bundle_cannot_use_restart(self):
        r.save(self.root/'manifest.json',{'format':'another-task'});r.save(self.root/'image.json',{})
        with patch.object(r,'inspect') as inspect:
            with self.assertRaisesRegex(ValueError,'not this release'):r.restart(argparse.Namespace(apply=True,release=self.root))
            inspect.assert_not_called()

    def test_release_names_keep_task_identity_and_old_default(self):
        self.assertEqual(r.release_name(r.TASK,'a'*40,'b'*40), 'materials-20261004-0004-'+'a'*12+'-'+'b'*12)
        self.assertEqual(r.release_name('task-20261004-0005','a'*40,'b'*40), 'asset-cleanup-20261004-0005-'+'a'*12+'-'+'b'*12)
        self.assertEqual(r.release_name('task-20261004-0008','a'*40,'b'*40), 'ui-unification-20261004-0008-'+'a'*12+'-'+'b'*12)
        self.assertEqual(r.release_name('task-20261005-0001','a'*40,'b'*40), 'autonomous-20261005-0001-'+'a'*12+'-'+'b'*12)
        self.assertEqual(r.release_name('task-20261006-0002','a'*40,'b'*40), 'entity-cards-20261006-0002-'+'a'*12+'-'+'b'*12)
        with self.assertRaisesRegex(ValueError,'unsupported release task'):
            r.release_name('../foreign','a'*40,'b'*40)

    def test_code_only_release_rejects_story_already_integrated_before_any_service_check(self):
        story, main = self.root / 'story', self.root / 'story-main'
        candidate, target = 'a' * 40, 'd' * 40
        manifest = {'story_worktree': story,
                    'story_main': main, 'story_candidate': candidate, 'story_target': target}
        def git(repo, *args):
            if args == ('rev-parse', 'HEAD'):
                return candidate  # The story target has already advanced.
            if args == ('branch', '--show-current'):
                return 'main'
            self.fail('unexpected Git read after the story target guard: ' + repr(args))
        for task in ('task-20261004-0008', 'task-20261005-0001'):
            with self.subTest(task=task), \
                 patch.object(r.base, 'primary', return_value=main.resolve()), \
                 patch.object(r.base, 'git', side_effect=git), \
                 patch.object(r.base, 'run') as run, patch.object(r, 'inspect') as inspect:
                with self.assertRaisesRegex(ValueError, 'target changed or story already completed'):
                    r.checks(self.root, {**manifest, 'task': task})
                run.assert_not_called()
                inspect.assert_not_called()

    def test_changed_task_in_bundle_stops_before_hash_or_docker(self):
        for task in ('task-20261004-0005', 'task-20261005-0001'):
            root=self.root/task
            r.save(root/'manifest.json',{'format':'material-review-release-v1','task':task,'push':False,'story_candidate':'a'*40,'system_candidate':'b'*40,'release_name':'materials-20261004-0004-'+'a'*12+'-'+'b'*12})
            with self.subTest(task=task), patch.object(r,'inspect') as inspect:
                with self.assertRaisesRegex(ValueError,'task or name differs'):
                    r.load_bundle(root)
                inspect.assert_not_called()

    def test_prepare_bundle_keeps_task_name_and_loads_for_old_and_new_tasks(self):
        root = self.root.resolve()
        story, system = root / 'story', root / 'system'
        story_main, system_main = root / 'story-main', root / 'system-main'
        for root in (story, system, story_main, system_main):
            root.mkdir()
        for root in (story, story_main):
            (root / 'config').mkdir(); (root / 'content').mkdir()
            (root / 'config/instance.json').write_text(json.dumps({'review_desk_commit': 'b' * 40}))
            (root / 'content/production-approach.json').write_text('{}')
        (story / 'scripts').mkdir()
        for name in ('material_review_release.py', 'autonomous_optimization_release.py',
                     'integrate_generation_review_system.py'):
            shutil.copyfile(Path(r.__file__).parent / name, story / 'scripts' / name)
        (system / 'review_desk').mkdir()
        (system / 'review_desk/z.py').write_text('# last source filename must not become release name\n')
        compose, ca = self.root / 'compose.json', self.root / 'test-ca.pem'
        compose.write_text('{}'); ca.write_text('offline fixture')
        config = {'Cmd': ['fixture'], 'Entrypoint': None, 'WorkingDir': '/app', 'User': '',
                  'Env': [], 'Labels': {'com.docker.compose.project.config_files': str(compose),
                  'com.docker.compose.project.working_dir': str(story_main)}}
        app = {'Image': 'sha256:' + 'c' * 64, 'Config': config,
               'State': {'Running': True, 'Health': {'Status': 'healthy'}},
               'HostConfig': {'RestartPolicy': {'Name': 'unless-stopped', 'MaximumRetryCount': 0},
                              'PortBindings': {}}, 'Mounts': [
                   {'Type': 'bind', 'Source': str(story_main), 'Destination': '/instance', 'RW': True},
                   *({'Type': 'bind', 'Source': str(story_main / name),
                      'Destination': '/instance/' + name, 'RW': False} for name in r.base.INSTANCE_FILES),
                   {'Type': 'bind', 'Source': str(ca), 'Destination': '/run/local-ca/cacert.pem', 'RW': False}]}
        nginx = {**app, 'Mounts': [], 'HostConfig': {**app['HostConfig'], 'PortBindings': r.base.PORTS}}
        def inspect(name, image=False):
            return {'Config': config} if image else app if name == r.base.APP else nginx
        def primary(path):
            return story_main if path == story else system_main
        with patch.object(r, 'inspect', side_effect=inspect), \
             patch.object(r.base, 'stable_image_policy', return_value={'image_policy': r.base.IMAGE_POLICY,
                 'base_image_tag': r.base.IMAGE_BASE, 'build_base_image': 'sha256:' + 'c' * 64}), \
             patch.object(delivery, 'uses_native_backend', return_value=False), \
             patch.object(r.base, 'primary', side_effect=primary), \
             patch.object(r.base, 'repo_check'), \
             patch.object(r.base, 'git_file', side_effect=lambda repo, commit, name: (repo / name).read_bytes()), \
             patch.object(r, 'git', return_value='100644 blob fixture\treview_desk/z.py'), \
             contextlib.redirect_stdout(io.StringIO()):
            for task in (r.TASK, 'task-20261004-0005', 'entity-acceptance-20261004',
                         'task-20261004-0007', 'task-20261004-0008', 'task-20261005-0001',
                         'task-20261005-0007', 'task-20261006-0006', 'task-20261008-0002'):
                if task in {'task-20261005-0007', 'task-20261006-0006', 'task-20261008-0002'}:
                    (story / 'content/production-approach.json').write_text('{"new_method": true}')
                if task == 'task-20261008-0002':
                    media = story / r.METHOD_MEDIA_DIRECTORY / 'demo.mp4'
                    media.parent.mkdir(); media.write_bytes(b'original method fixture')
                    document = {'tabs': [{'sections': [{'blocks': [{'type': 'media', 'kind': 'video',
                        'file': media.name, 'caption': 'example', 'sha256': r.sha(media.read_bytes()), 'width': 1280, 'height': 720}]}]}]}
                    (story / 'content/production-approach.json').write_text(json.dumps(document))
                args = argparse.Namespace(story_worktree=story, system_worktree=system,
                    story_candidate='a' * 40, system_candidate='b' * 40,
                    story_target='d' * 40, system_target='e' * 40,
                    bundle=story / '.runtime' / task)
                if task != r.TASK:
                    args.task = task
                r.prepare(args)
                _, manifest = r.load_bundle(args.bundle)
                self.assertEqual(manifest['task'], task)
                self.assertEqual(manifest['release_name'], r.release_name(task, 'a' * 40, 'b' * 40))
                self.assertEqual(r.read(args.bundle / 'system-delivery.json')['task'], task)
                if task == 'task-20261008-0002':
                    relative = r.METHOD_MEDIA_DIRECTORY + '/demo.mp4'
                    self.assertEqual(manifest['method_media'], {relative: r.sha(media.read_bytes())})
                    self.assertEqual((args.bundle / 'instance' / relative).read_bytes(), media.read_bytes())
                    volumes = r.base.compose_definition(manifest, {'image': 'test'}, args.bundle)['services']['app']['volumes']
                    mount = next(v for v in volumes if v['target'] == '/instance/' + r.METHOD_MEDIA_DIRECTORY)
                    self.assertTrue(mount['read_only'])
                    media.write_bytes(b'changed after declaration')
                    args.bundle = story / '.runtime' / 'wrong-media-version'
                    with self.assertRaisesRegex(ValueError, 'method media differs from declared version'):
                        r.prepare(args)
                    media.write_bytes(b'original method fixture')
            # Only the method rewrite tasks may change the instance-owned text.
            args.task = 'task-20261005-0006'
            args.bundle = story / '.runtime' / 'forbidden-content-change'
            with self.assertRaisesRegex(ValueError, 'approach content change'):
                r.prepare(args)

    def test_replacing_round_member_at_same_row_count_is_rejected(self):
        for path in (self.before,self.after):
            with sqlite3.connect(path) as db:
                db.executescript("CREATE TABLE material_members(material_id TEXT,number INTEGER,revision_id TEXT);INSERT INTO material_members VALUES ('need',1,'original');")
        with sqlite3.connect(self.after) as db:db.execute("UPDATE material_members SET revision_id='unrelated'")
        with self.assertRaisesRegex(ValueError,'identities lost: material_members'):r.preserved(self.before,self.after)

    def test_duplicate_immutable_rows_cannot_hide_deletion(self):
        for path in (self.before,self.after):
            with sqlite3.connect(path) as db:
                db.executescript("CREATE TABLE history(body TEXT);INSERT INTO history VALUES ('same'),('same');")
        with sqlite3.connect(self.after) as db:db.execute('DELETE FROM history WHERE rowid=1')
        with self.assertRaisesRegex(ValueError,'immutable history lost: history'):r.preserved(self.before,self.after)

    def test_history_schema_change_and_blobs_are_rejected(self):
        with sqlite3.connect(self.after) as db:db.execute('ALTER TABLE revisions ADD COLUMN another TEXT')
        with self.assertRaisesRegex(ValueError,'schema changed'):r.preserved(self.before,self.after)
        shutil.copyfile(self.before,self.after)
        with sqlite3.connect(self.after) as db:db.execute('INSERT INTO revisions VALUES (?,?)',('blob',b'unknown'))
        with self.assertRaisesRegex(ValueError,'BLOB history'):r.preserved(self.before,self.after)

    def test_large_history_comparison_and_file_hash_do_not_load_entire_databases(self):
        with sqlite3.connect(self.before) as db:
            db.executemany('INSERT INTO revisions VALUES (?,?)',((str(i),'x'*65536) for i in range(256)))
        shutil.copyfile(self.before,self.after)
        expected=r.sha(self.before.read_bytes())
        tracemalloc.start()
        try:
            with patch.object(r.base,'rows',side_effect=AssertionError('whole database loaded')), \
                 patch.object(Path,'read_bytes',side_effect=AssertionError('whole file loaded')):
                result=r.preserved(self.before,self.after)
                self.assertEqual(r.file_sha256(self.before),expected)
            peak=tracemalloc.get_traced_memory()[1]
        finally:tracemalloc.stop()
        self.assertEqual(result['revisions']['before'],257)
        self.assertLess(peak,4*1024*1024)

if __name__=='__main__':unittest.main()
