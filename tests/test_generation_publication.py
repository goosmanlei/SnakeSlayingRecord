import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from review_desk.store import Store

from generation_fixtures import make_worktree, git, PublicationFixture
from scripts import generation_publication as publication
from scripts import publish_generation as runner
from scripts.generation_review import initialize, export_review


class GenerationPublicationTest(unittest.TestCase):
    def test_exact_method_execution_publishes_after_binding_update(self):
        from review_desk import methods
        from scripts.managed_methods import install
        seed = json.loads((Path(__file__).resolve().parents[1] / 'content/managed-methods.json').read_text())
        install(self.fixture.store, seed)
        formal = Store(self.formal)
        self.addCleanup(formal.close)
        methods.restore_registry(formal, methods.export_registry(self.fixture.store))
        baseline = Path(self.temp.name) / 'method-baseline.sqlite3'
        publication.backup(self.fixture.store.db_path, baseline)
        request = {'work_type': 'novel-writing', 'run_id': 'writer', 'step_id': 'one', 'target': 'entity-boat-song',
                   'inputs': {'context': {'source': 'exact original', 'spec': 'reflect'}}}
        execution = methods.prepare(self.fixture.store, request)
        for stage in ('draft', 'review', 'result'):
            methods.artifact(self.fixture.store, {**request, 'execution': methods.reference(execution), 'stage': stage, 'output': stage})
        delta = publication.build_plan(baseline, self.fixture.store.db_path)
        binding = methods.read(formal, 'method.binding.novel-writing')
        methods.save(formal, {'category': 'binding', 'name': 'novel-writing', 'expected_version': binding['version'], 'payload': binding['payload']})
        publication.apply_plan(formal.db, delta)
        self.assertEqual(methods.prepare(formal, request), execution)
        self.assertEqual(methods.read(formal, binding['object_id'])['version'], 2)
        self.assertTrue(publication.apply_plan(formal.db, delta)['already_published'])

    def test_retired_version_baseline_cannot_replay_even_with_unchanged_target_rows(self):
        db=self.db()
        with db:db.execute("INSERT INTO consolidation_runs VALUES ('new-baseline','checksum','{}')")
        before='\n'.join(db.iterdump())
        with self.assertRaisesRegex(ValueError,'retired version baseline'):publication.apply_plan(db,self.delta)
        self.assertEqual('\n'.join(db.iterdump()),before)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.main, self.task = make_worktree(self.temp.name)
        self.fixture = PublicationFixture()
        self.addCleanup(self.fixture.close)
        (self.main / '.runtime').mkdir()
        (self.main / 'export/assets').mkdir(parents=True)
        self.formal = self.main / '.runtime/review.sqlite3'
        publication.backup(self.fixture.store.db_path, self.formal)
        self.baseline = Path(self.temp.name) / 'baseline.sqlite3'
        publication.backup(self.formal, self.baseline)
        self.fixture.advance()
        self.delta = publication.build_plan(self.baseline, self.fixture.store.db_path)

    def db(self):
        db = publication.connect(self.formal, readonly=False)
        self.addCleanup(db.close)
        return db

    def test_preserves_concurrent_unrelated_rows_and_retries_without_duplicates(self):
        db = self.db()
        with db:
            db.execute("UPDATE comments SET body='new formal feedback' WHERE id='history'")
        result = publication.apply_plan(db, self.delta)
        self.assertFalse(result['already_published'])
        self.assertEqual(db.execute("SELECT body FROM comments WHERE id='history'").fetchone()[0], 'new formal feedback')
        self.assertEqual(db.execute('SELECT COUNT(*) FROM comment_events').fetchone()[0], 2)
        before = '\n'.join(db.iterdump())
        self.assertTrue(publication.apply_plan(db, self.delta)['already_published'])
        self.assertEqual('\n'.join(db.iterdump()), before)

    def test_concurrent_same_object_is_rejected_without_journal_or_mutation(self):
        db = self.db()
        with db:
            db.execute("UPDATE objects SET updated_at='concurrent' WHERE id='entity-boat-song'")
        before = '\n'.join(db.iterdump())
        with self.assertRaisesRegex(ValueError, 'object changed'):
            publication.apply_plan(db, self.delta)
        self.assertEqual('\n'.join(db.iterdump()), before)

    def test_concurrent_unrelated_revisions_and_guidance_are_preserved(self):
        store = Store(self.formal)
        try:
            store.put_object('entity-unrelated','ENTITY',{'title':'concurrent revision'},expected_version=1)
            store.put_object('guidance-unrelated','GUIDANCE',{'note':'unrelated concurrent guidance','actor':'fixture'},expected_version=0)
        finally:
            store.close()
        before = publication.tables(self.formal)
        publication.apply_plan(self.db(),self.delta)
        after = publication.tables(self.formal)
        ids = {'entity-unrelated','guidance-unrelated'}
        for table, column in (('objects','id'),('revisions','object_id')):
            self.assertEqual([r for r in after[table] if r[column] in ids],
                             [r for r in before[table] if r[column] in ids])

    def test_current_input_drift_is_rejected_even_when_old_revision_still_exists(self):
        new_id = self.delta['changes']['revisions'][0]['after']['id']
        with self.fixture.db:
            self.fixture.db.execute('INSERT INTO dependencies VALUES (?,?,?)',(new_id,'other','input'))
        plan = publication.build_plan(self.baseline,self.fixture.store.db_path)
        store = Store(self.formal)
        try:
            store.put_object('entity-unrelated','ENTITY',{'title':'new input'},expected_version=1)
        finally:
            store.close()
        before = publication.tables(self.formal)
        with self.assertRaisesRegex(ValueError,'input changed'):
            publication.apply_plan(self.db(),plan)
        self.assertEqual(publication.tables(self.formal),before)

    def test_missing_reference_rolls_back_the_entire_increment(self):
        db = self.db()
        plan = copy.deepcopy(self.delta)
        plan['changes']['dependencies'][0]['after']['to_revision'] = 'missing'
        before = '\n'.join(db.iterdump())
        with self.assertRaises((sqlite3.IntegrityError, ValueError)):
            publication.apply_plan(db, plan)
        self.assertEqual('\n'.join(db.iterdump()), before)

    def test_preserves_comment_edit_history_and_detects_concurrent_edit(self):
        # A review may edit a pre-existing comment. Its exact previous row is a guard.
        db = self.fixture.db
        with db:
            db.execute("UPDATE comments SET body='task edit',version=2 WHERE id='history'")
            db.execute("INSERT INTO comment_events(comment_id,action,body,at) VALUES ('history','EDIT','task edit','after')")
        delta = publication.build_plan(self.baseline, self.fixture.store.db_path)
        formal = self.db()
        with formal:
            formal.execute("UPDATE comments SET body='formal edit' WHERE id='history'")
        before = '\n'.join(formal.iterdump())
        with self.assertRaisesRegex(ValueError, 'row changed: comments'):
            publication.apply_plan(formal, delta)
        self.assertEqual('\n'.join(formal.iterdump()), before)
        with formal:
            formal.execute("UPDATE comments SET body='actual feedback' WHERE id='history'")
        publication.apply_plan(formal, delta)
        self.assertEqual(formal.execute("SELECT body FROM comments WHERE id='history'").fetchone()[0], 'task edit')
        self.assertEqual(formal.execute("SELECT COUNT(*) FROM comment_events WHERE comment_id='history'").fetchone()[0], 2)

    def test_deleted_history_and_nonproduction_data_cannot_be_frozen(self):
        db = self.fixture.db
        with db:
            db.execute("UPDATE comment_events SET body='rewrite' WHERE id=1")
        with self.assertRaisesRegex(ValueError, 'events changed'):
            publication.build_plan(self.baseline, self.fixture.store.db_path)
        with db:
            db.execute("UPDATE comment_events SET body='old opinion' WHERE id=1")
            db.execute("UPDATE objects SET kind='SOURCE' WHERE id='entity-boat-song'")
        with self.assertRaisesRegex(ValueError, 'story or system'):
            publication.build_plan(self.baseline, self.fixture.store.db_path)

    def commit_package(self):
        path = self.task / 'release.json'
        path.write_text(json.dumps(self.delta))
        git(self.task, 'add', 'release.json')
        git(self.task, 'commit', '-qm', 'reviewed increment')
        return path, git(self.task, 'rev-parse', 'HEAD')

    def test_preflight_is_readonly_and_main_apply_requires_integrated_commit(self):
        path, commit = self.commit_package()
        before = publication.tables(self.formal)
        result = runner.run_publication(self.task, self.main, path, 'preflight')
        self.assertFalse(result['applied'])
        self.assertEqual(publication.tables(self.formal), before)
        with self.assertRaisesRegex(ValueError, 'not been integrated'):
            runner.run_publication(self.task, self.main, path, 'early', apply=True, source_commit=commit)
        self.assertEqual(publication.tables(self.formal), before)
        git(self.main, 'merge', '--ff-only', commit)
        self.assertTrue(runner.run_publication(self.task, self.main, path, 'published', apply=True, source_commit=commit)['applied'])

    def test_committed_transaction_survives_missing_external_receipt(self):
        path, commit = self.commit_package()
        git(self.main, 'merge', '--ff-only', commit)
        real_write = runner.write_json
        def fail_receipt(root, target, value):
            if Path(target).name == 'transaction.json':
                raise OSError('simulated disk failure after commit')
            return real_write(root, target, value)
        with patch.object(runner, 'write_json', side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, 'disk failure'):
                runner.run_publication(self.task, self.main, path, 'interrupted', apply=True, source_commit=commit)
        before = publication.tables(self.formal)
        result = runner.run_publication(self.task, self.main, path, 'recovered', apply=True, source_commit=commit)
        self.assertTrue(result['already_published'])
        self.assertEqual(publication.tables(self.formal), before)
        self.assertTrue((self.task / '.runtime/generation/publications/recovered/applied.json').is_file())

    def test_duplicate_plan_rows_cannot_overwrite_data(self):
        plan = copy.deepcopy(self.delta)
        plan['changes']['comments'].append(plan['changes']['comments'][0])
        db = self.db()
        before = '\n'.join(db.iterdump())
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            publication.apply_plan(db, plan)
        self.assertEqual('\n'.join(db.iterdump()), before)

    def test_media_manifest_cannot_omit_a_published_component(self):
        plan = copy.deepcopy(self.delta)
        row = plan['changes']['revisions'][0]['after']
        payload = json.loads(row['payload'])
        payload['components'] = [{'file':'0'*64+'.wav','sha256':'0'*64,'bytes':1}]
        row['payload'] = json.dumps(payload)
        db = self.db()
        before = '\n'.join(db.iterdump())
        with self.assertRaisesRegex(ValueError,'media manifest differs'):
            publication.apply_plan(db,plan)
        self.assertEqual('\n'.join(db.iterdump()),before)

    def test_json_key_order_does_not_change_foreign_key_application_order(self):
        plan = json.loads(json.dumps(self.delta, sort_keys=True))
        self.assertFalse(publication.apply_plan(self.db(), plan)['already_published'])

    def test_missing_review_cannot_create_an_empty_export_or_database(self):
        with self.assertRaisesRegex(ValueError, 'database missing'):
            export_review(self.task, '.runtime/missing')
        self.assertFalse((self.task / '.runtime/missing').exists())

    def test_initialization_preserves_main_and_refuses_to_reset_review(self):
        (self.task / 'config').mkdir()
        (self.task / 'content').mkdir()
        (self.task / 'config/instance.json').write_text(json.dumps({'id': 'test', 'title': 'Review'}))
        before = publication.tables(self.formal)
        instance = initialize(self.task, '.runtime/review')
        self.assertEqual(publication.tables(instance / '.runtime/review.sqlite3'), before)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            initialize(self.task, '.runtime/review')
        self.assertEqual(publication.tables(self.formal), before)


if __name__ == '__main__':
    unittest.main()

class NumberPublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source.sqlite3';self.formal=self.root/'formal.sqlite3'
        self.store=Store(self.source);self.addCleanup(self.store.close)
        self.store.put_object('episode','EPISODE',{'title':'锁定正文','number':1,'blocks':[],'scenes':[{'id':'scene-one','block_ids':[]}]})
        with self.store.db:
            self.store.db.execute("DELETE FROM business_codes WHERE prefix IN ('E','S','SH')")
        publication.backup(self.source,self.formal)
        # Current E/S are derived from an exact screenplay edition. These
        # tests cover publication of the pre-existing legacy allocation ledger.
        with self.store.db:
            self.store.db.executemany('INSERT INTO business_codes VALUES (?,?,?)',
                                     [('episode','E',1),('scene:episode:scene-one','S',1)])
        self.plan=publication.build_plan(self.formal,self.source)

    def test_existing_story_gets_codes_without_story_revisions_and_repeated_apply_is_safe(self):
        self.assertEqual(self.plan['scope'],[])
        self.assertFalse(self.plan['changes']['objects']);self.assertFalse(self.plan['changes']['revisions'])
        before=publication.tables(self.formal)
        db=publication.connect(self.formal,readonly=False);self.addCleanup(db.close)
        publication.apply_plan(db,self.plan)
        self.assertTrue(publication.apply_plan(db,self.plan)['already_published'])
        after=publication.tables(self.formal)
        self.assertEqual(before['objects'],after['objects']);self.assertEqual(before['revisions'],after['revisions'])
        self.assertEqual(after['business_codes'],publication.tables(self.source)['business_codes'])

    def test_matching_startup_migration_is_reused_but_number_collision_is_rejected(self):
        target=Store(self.formal)
        with target.db:target.db.executemany('INSERT INTO business_codes VALUES (?,?,?)',[('episode','E',1),('scene:episode:scene-one','S',1)])
        target.close()
        db=publication.connect(self.formal,readonly=False);self.addCleanup(db.close)
        publication.apply_plan(db,self.plan)
        self.assertEqual(db.execute('SELECT count(*) FROM business_codes').fetchone()[0],2)
        # A separate exact target with a concurrent allocation must not be renumbered.
        other=self.root/'other.sqlite3';publication.backup(self.source,other)
        clash=publication.connect(other,readonly=False);self.addCleanup(clash.close)
        with clash:
            clash.execute('DELETE FROM business_codes')
            clash.execute("INSERT INTO business_codes VALUES ('concurrent-object','E',1)")
        before='\n'.join(clash.iterdump())
        with self.assertRaises((ValueError,sqlite3.IntegrityError)):
            publication.apply_plan(clash,self.plan)
        self.assertEqual('\n'.join(clash.iterdump()),before)

    def test_wrong_prefix_missing_scene_or_unguarded_identity_rolls_back(self):
        db=publication.connect(self.formal,readonly=False);self.addCleanup(db.close)
        for mutate in ('prefix','scene','guard'):
            bad=copy.deepcopy(self.plan)
            if mutate=='prefix':bad['changes']['business_codes'][0]['after']['prefix']='D'
            elif mutate=='scene':
                next(c for c in bad['changes']['business_codes'] if c['after']['prefix']=='S')['after']['object_id']='scene:episode:absent'
            else:bad['expected_numbered_objects']={}
            before='\n'.join(db.iterdump())
            with self.assertRaises(ValueError):publication.apply_plan(db,bad)
            self.assertEqual('\n'.join(db.iterdump()),before)
