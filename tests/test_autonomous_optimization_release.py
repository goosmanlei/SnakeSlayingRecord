"""Offline author checks for the release draft; no Docker or formal API calls."""
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('release_draft', HERE.parent / 'scripts/autonomous_optimization_release.py')
r = importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class DraftChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(HERE.parent / 'production/autonomous-optimization-release/project-context', self.root / 'project-update')
        self.request, self.before, self.after = r.update_package(self.root / 'project-update')

    def current(self, version=15, body=None):
        return {**self.before, 'schema_version': 4, 'version': version, 'body': self.after if body is None else body, 'updated_at': 'technical timestamp'}

    def test_package_only_two_fields_and_old_full_record(self):
        path = self.root / 'project-update/request.json'
        value = json.loads(path.read_text());value['updates']['current_stage'] = 'anything'
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'only the two'): r.update_package(path.parent)

    def test_old_record_timestamp_drift_stops_before_patch(self):
        calls = []
        with patch.object(r, 'project', return_value={**self.before, 'updated_at': 'changed'}), patch.object(r, 'http', side_effect=lambda *args: calls.append(args)):
            with self.assertRaisesRegex(ValueError, 'original PROJECT'): r.update_project(self.root)
        self.assertEqual(calls, [])

    def test_truncated_json_after_commit_reads_once_without_second_patch(self):
        calls = []
        def write(*args):
            calls.append(args);raise json.JSONDecodeError('truncated', '', 0)
        with patch.object(r, 'project', side_effect=[self.before, self.current()]), patch.object(r, 'http', side_effect=write):
            result = r.update_project(self.root)
        self.assertEqual(len(calls), 1);self.assertTrue(result['response_lost_or_rejected'])
        self.assertEqual(calls[0][1], self.request)

    def test_unknown_write_readback_does_not_retry(self):
        with patch.object(r, 'project', side_effect=[self.before, self.before]), patch.object(r, 'http', side_effect=OSError('connection reset')) as write:
            with self.assertRaisesRegex(ValueError, 'not exactly confirmed'): r.update_project(self.root)
        self.assertEqual(write.call_count, 1)

    def test_already_exact_applied_skips_patch_but_higher_revision_refuses(self):
        with patch.object(r, 'project', return_value=self.current()), patch.object(r, 'http') as write:
            self.assertTrue(r.update_project(self.root)['already_applied']);write.assert_not_called()
        with patch.object(r, 'project', return_value=self.current(16)), patch.object(r, 'http') as write:
            with self.assertRaisesRegex(ValueError, 'original PROJECT'): r.update_project(self.root)
            write.assert_not_called()

    def test_compensation_changes_only_two_fields_with_exact_next_version(self):
        with patch.object(r, 'project', side_effect=[self.current(), self.current(16, self.before['body'])]), patch.object(r, 'http', return_value={}) as write:
            r.update_project(self.root, compensate=True)
        self.assertEqual(write.call_args.args[1], {'expected_version': 15, 'updates': {k: self.before['body'][k] for k in r.FIELDS}})
        altered = self.current();altered['body'] = {**altered['body'], 'current_stage': 'different'}
        with patch.object(r, 'project', return_value=altered), patch.object(r, 'http') as write:
            with self.assertRaisesRegex(ValueError, 'compensation refused'): r.update_project(self.root, compensate=True)
            write.assert_not_called()

    def database(self, file):
        with sqlite3.connect(file) as db:
            db.executescript('CREATE TABLE configurations(scope TEXT,schema_version INTEGER,version INTEGER,body TEXT,updated_at TEXT); CREATE TABLE configuration_events(id INTEGER PRIMARY KEY,scope TEXT,version INTEGER,body TEXT,at TEXT); CREATE TABLE comments(id TEXT,body TEXT); CREATE TABLE revisions(id TEXT,payload TEXT);')
            db.execute('INSERT INTO configurations VALUES(?,?,?,?,?)', ('PROJECT', 3, 14, json.dumps(self.before['body']), 'old'))
            db.execute('INSERT INTO configurations VALUES(?,?,?,?,?)', ('SYSTEM', 4, 1, '{}', 'old'))
            db.execute('INSERT INTO configuration_events VALUES(?,?,?,?,?)', (1, 'PROJECT', 14, json.dumps(self.before['body']), 'old'))
            db.execute('INSERT INTO comments VALUES(?,?)', ('comment-original', 'preserve exactly'))
            db.execute('INSERT INTO revisions VALUES(?,?)', ('revision-original', 'preserve history'))

    def test_consistent_snapshot_and_all_old_rows_subset(self):
        before, after = self.root/'before.sqlite3', self.root/'after.sqlite3'
        self.database(before);r.snapshot(before, after)
        with sqlite3.connect(after) as db:
            db.execute('UPDATE configurations SET schema_version=4,version=15,body=? WHERE scope="PROJECT"', (json.dumps(self.after),))
            db.execute('INSERT INTO configuration_events VALUES(?,?,?,?,?)', (2, 'PROJECT', 15, json.dumps(self.after), 'new'))
            db.execute('INSERT INTO comments VALUES(?,?)', ('new-coordinated-comment', 'allowed new row'))
        result = r.verify_history(before, after, self.after, 15, 1)
        self.assertEqual(result['comments'], {'before': 1, 'after': 2, 'old_rows_preserved': True})
        with sqlite3.connect(after) as db: db.execute('UPDATE revisions SET payload="changed"')
        with self.assertRaisesRegex(ValueError, 'revisions'): r.verify_history(before, after, self.after, 15, 1)

    def test_extra_configuration_event_rejected_even_with_correct_head(self):
        before, after = self.root/'before.sqlite3', self.root/'after.sqlite3';self.database(before);r.snapshot(before, after)
        with sqlite3.connect(after) as db:
            db.execute('UPDATE configurations SET schema_version=4,version=15,body=? WHERE scope="PROJECT"', (json.dumps(self.after),))
            for key, scope in [(2, 'PROJECT'), (3, 'SYSTEM')]:
                db.execute('INSERT INTO configuration_events VALUES(?,?,?,?,?)', (key, scope, 15, json.dumps(self.after), 'new'))
        with self.assertRaisesRegex(ValueError, 'event delta'): r.verify_history(before, after, self.after, 15, 1)

    def test_permanent_compose_uses_placeholders_exact_files_ca_and_two_ports(self):
        m = {'story_main': '/technical/main', 'previous_app': {'environment_names': ['OPENAI_API_KEY', 'SSL_CERT_FILE'], 'mounts': [{'Destination': '/run/local-ca/cacert.pem', 'Source': '/technical/ca.pem'}]}, 'previous_nginx': {'image': 'sha256:nginx'}}
        value = r.compose_definition(m, {'image': 'sha256:candidate'}, Path('/technical/release'))
        app = value['services']['app'];self.assertEqual(app['environment']['OPENAI_API_KEY'], '${AO_RELEASE_ENV_0?required}')
        self.assertEqual([x['target'] for x in app['volumes']], ['/instance', '/run/local-ca/cacert.pem', '/instance/config/instance.json', '/instance/content/production-approach.json'])
        self.assertEqual([x['read_only'] for x in app['volumes']], [False, True, True, True])
        self.assertEqual(value['services']['nginx']['ports'], ['127.0.0.1:3000:3000','127.0.0.1:64401:3000'])

    def test_immutable_file_refuses_overwrite_and_symlink(self):
        target = self.root/'fixed';r.write_once(target,b'a');r.write_once(target,b'a')
        with self.assertRaisesRegex(ValueError,'immutable'): r.write_once(target,b'b')
        link = self.root/'link';link.symlink_to(target)
        with self.assertRaisesRegex(ValueError,'immutable'): r.write_once(link,b'a')

    def test_failed_subprocess_does_not_expose_secret_output(self):
        class Result: returncode=1;stdout=b'technical-secret';stderr=b'technical-secret'
        with patch.object(r.subprocess,'run',return_value=Result()):
            with self.assertRaises(RuntimeError) as found:r.run(['docker','inspect','technical'])
        self.assertNotIn('technical-secret',str(found.exception))

    def test_exact_compensated_state_can_finish_without_another_patch(self):
        with patch.object(r, 'project', return_value=self.current(16, self.before['body'])), patch.object(r, 'http') as write:
            result = r.update_project(self.root, compensate=True)
            self.assertTrue(result['already_applied']);write.assert_not_called()

    def test_compensation_requires_exact_v15_and_v16_event_bodies(self):
        before, after = self.root/'before.sqlite3', self.root/'after.sqlite3';self.database(before);r.snapshot(before, after)
        with sqlite3.connect(after) as db:
            db.execute('UPDATE configurations SET schema_version=4,version=16 WHERE scope="PROJECT"')
            db.execute('INSERT INTO configuration_events VALUES(?,?,?,?,?)', (2, 'PROJECT', 15, '{}', 'new'))
            db.execute('INSERT INTO configuration_events VALUES(?,?,?,?,?)', (3, 'PROJECT', 16, json.dumps(self.before['body']), 'newer'))
        with self.assertRaisesRegex(ValueError, 'body chain'):
            r.verify_history(before, after, self.before['body'], 16, 2, {15: self.after, 16: self.before['body']})

    def recovery_fixture(self):
        oldfile=self.root/'old-compose.json';oldfile.write_text(json.dumps({'services': {'app': {'image':'mutable-tag'}, 'nginx': {'build':'.'}}}))
        previous_app={'image':'sha256:old-app', 'environment_names':['TECHNICAL_ONLY'], 'config_files':str(oldfile),
                      'mounts':[{'Type':'bind','Source':'/technical/ca','Destination':'/run/local-ca/cacert.pem','RW':False}]}
        previous_nginx={'image':'sha256:old-nginx','config_files':str(oldfile)}
        m={'story_main':str(self.root), 'release_name':'exact-candidate', 'previous_app':previous_app,
           'previous_nginx':previous_nginx,'previous_compose_hashes':{str(oldfile):r.sha(oldfile.read_bytes())}}
        image={'image':'sha256:candidate'};release=self.root/'.runtime/service-releases/exact-candidate'
        candidate={**previous_app,'image':image['image'],'config_files':str(release/'compose.release.json'),
            'mounts':sorted([{'Type':'bind','Source':str(v['source']),'Destination':v['target'],'RW':not v['read_only']}
                            for v in r.compose_definition(m,image,release)['services']['app']['volumes']],key=lambda v:v['Destination'])}
        args=type('Args',(),{'action':'service','manifest_sha256':'technical-manifest','image_receipt_sha256':'technical-image'})()
        r.save(self.root/'run/identity.json',{'manifest':args.manifest_sha256,'image_receipt':args.image_receipt_sha256})
        r.write_once(self.root/'run/before.sqlite3',b'opaque backup placeholder for service-only test')
        r.save(self.root/'run/before.json',{'sha256':r.sha((self.root/'run/before.sqlite3').read_bytes())})
        return m,image,release,candidate,args

    def test_foreign_service_is_refused_before_any_recovery_mutation(self):
        import contextlib
        m,image,release,current,args=self.recovery_fixture();current={**current,'image':'sha256:another-publisher'}
        def inspect(name,image=False):return {'safe':current if name==r.APP else m['previous_nginx'],'Config':{'Env':['TECHNICAL_ONLY=no-secret']}}
        with patch.object(r,'authorized_bundle',return_value=(self.root,m)),patch.object(r,'publication_locks',return_value=contextlib.nullcontext()),patch.object(r,'common_checks',return_value=image),patch.object(r,'inspect',side_effect=inspect),patch.object(r,'safe_container',side_effect=lambda c:c['safe']),patch.object(r,'compose_up') as mutate:
            with self.assertRaisesRegex(ValueError,'foreign or unknown app'):r.recover(args)
            mutate.assert_not_called()
        self.assertFalse((release/'compose.previous.json').exists())

    def test_service_recovery_pins_both_previous_images_before_compose(self):
        import contextlib,io
        m,image,release,current,args=self.recovery_fixture();active={'app':current,'nginx':m['previous_nginx']};mutations=[]
        rollback_files=','.join([*m['previous_compose_hashes'],str(release/'compose.previous.json')])
        def inspect(name,image=False):
            if image:return {'Id':name}
            return {'safe':active['app' if name==r.APP else 'nginx'],'Config':{'Env':['TECHNICAL_ONLY=no-secret']}}
        def up(manifest,files,env,*,release=False):
            override=json.loads(Path(files[-1]).read_text());mutations.append(override)
            self.assertTrue(release);self.assertEqual(override['services']['app']['image'],'sha256:old-app');self.assertEqual(override['services']['nginx']['image'],'sha256:old-nginx')
            self.assertNotIn('no-secret',json.dumps(override))
            active['app']={**m['previous_app'],'config_files':rollback_files};active['nginx']={**m['previous_nginx'],'config_files':rollback_files}
        with patch.object(r,'authorized_bundle',return_value=(self.root,m)),patch.object(r,'publication_locks',return_value=contextlib.nullcontext()),patch.object(r,'common_checks',return_value=image),patch.object(r,'inspect',side_effect=inspect),patch.object(r,'safe_container',side_effect=lambda c:c['safe']),patch.object(r,'compose_up',side_effect=up),patch.object(r,'wait_healthy'),contextlib.redirect_stdout(io.StringIO()):
            r.recover(args);r.recover(args)
        self.assertEqual(len(mutations),1)

    def test_base_tag_is_task_scoped_and_reuses_only_the_fixed_image(self):
        image='sha256:'+'a'*64;tag=r.base_image_tag(image)
        self.assertEqual(tag,'ao-'+r.TASK+'-base:'+'a'*64)
        with patch.object(r,'inspect',return_value={'Id':image}),patch.object(r,'run',return_value=(image+'\n').encode()) as command:
            r.pin_base_image(image,tag)
        self.assertEqual(command.call_count,1);self.assertIn('ls',command.call_args.args[0])

    def test_missing_base_tag_is_created_from_exact_local_id(self):
        image='sha256:'+'b'*64;tag=r.base_image_tag(image)
        with patch.object(r,'inspect',return_value={'Id':image}),patch.object(r,'run',side_effect=[b'',b'']) as command:
            r.pin_base_image(image,tag)
        self.assertEqual(command.call_args.args[0],[r.DOCKER,'tag',image,tag])

    def test_foreign_base_tag_is_not_replaced(self):
        image='sha256:'+'c'*64;tag=r.base_image_tag(image)
        with patch.object(r,'inspect',return_value={'Id':image}),patch.object(r,'run',return_value=('sha256:'+'d'*64+'\n').encode()) as command:
            with self.assertRaisesRegex(ValueError,'do not replace'):r.pin_base_image(image,tag)
        self.assertEqual(command.call_count,1)

    def test_failed_base_listing_does_not_guess_absence_or_create_tag(self):
        image='sha256:'+'e'*64;tag=r.base_image_tag(image)
        with patch.object(r,'inspect',return_value={'Id':image}),patch.object(r,'run',side_effect=RuntimeError('docker unavailable')) as command:
            with self.assertRaisesRegex(RuntimeError,'docker unavailable'):r.pin_base_image(image,tag)
        self.assertEqual(command.call_count,1)

    def test_build_rechecks_base_tag_after_build_before_receipt(self):
        image='sha256:'+'a'*64;tag=r.base_image_tag(image);m={'previous_app':{'image':image},'base_image_tag':tag,'system_candidate':'b'*40,'story_candidate':'c'*40}
        args=type('Args',(),{'bundle':self.root})()
        with patch.object(r,'load_bundle',return_value=(self.root,m)),patch.object(r,'inspect',side_effect=[{'Id':image},{'Id':image},{'Id':'sha256:'+'d'*64}]),patch.object(r,'run',side_effect=[(image+'\n').encode(),b'']) as command,patch.object(r,'source_check') as check:
            with self.assertRaisesRegex(ValueError,'during build'):r.build(args)
        self.assertIn('--network=none',command.call_args.args[0]);check.assert_not_called();self.assertFalse((self.root/'image.json').exists())


if __name__ == '__main__': unittest.main()
