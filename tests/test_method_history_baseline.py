"""Real ledger recovery after pruning old method definitions; no formal writes.

Run with the pinned review-desk source on PYTHONPATH.
"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from scripts import method_migration as migration


@unittest.skipUnless(importlib.util.find_spec('review_desk'), 'requires pinned review-desk source')
class MethodHistoryBaselineTest(unittest.TestCase):
    def setUp(self):
        from review_desk import methods
        from review_desk.store import Store
        self.methods, self.Store = methods, Store
        self.tmp = tempfile.TemporaryDirectory(prefix='method-history-baseline-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.store('source')
        resource = methods.save(self.source, {'category': 'resource', 'name': 'example', 'expected_version': 0,
            'payload': {'title': 'Example', 'files': {'reference.md': 'Use accurate input.'},
                        'sections': {'main': 'reference.md'}}})
        payload = {'title': 'Example', 'purpose': 'Read an input', 'applies': 'Supplied text',
                   'inputs': 'Text', 'outputs': 'Result', 'checks': 'Matches input',
                   'work_types': ['example'], 'required_inputs': ['context'], 'steps': ['result'],
                   'files': {'SKILL.md': '---\nname: example\ndescription: Read text.\n---\nOriginal body.\n'},
                   'resources': [{**methods.reference(resource), 'section': 'main'}]}
        for version in (1, 2):
            if version == 2:
                payload['files']['SKILL.md'] = payload['files']['SKILL.md'].replace('Original', 'Latest')
            self.latest = methods.save(self.source, {'category': 'skill', 'name': 'example',
                                                     'expected_version': version - 1, 'payload': payload})
            methods.save(self.source, {'category': 'binding', 'name': 'example', 'expected_version': version - 1,
                'payload': {'work_type': 'example', 'rules': [{**methods.reference(self.latest), 'when': {}}]}})
        archive = methods.export_registry(self.source)
        archive['records'] = [row for row in archive['records']
                              if row['object_id'] == resource['object_id'] or row['version'] == 2]
        archive[migration.BASELINES] = {row['object_id']: {'version': row['version'], 'revision_id': row['revision_id']}
                                       for row in archive['records'] if row['version'] == 2}
        self.archive = self.sign(archive)

    def store(self, name):
        store = self.Store(self.root / name / '.runtime/review.sqlite3')
        self.addCleanup(store.close)
        return store

    def sign(self, archive):
        archive.pop('sha256', None)
        archive['sha256'] = self.methods.checksum(archive)
        return archive

    def test_empty_restore_preserves_revision_then_accepts_new_work_and_next_version(self):
        from review_desk import method_files
        target = self.store('target')
        migration.restore_configuration(target, self.archive)
        actual = self.methods.read(target, self.latest['object_id'])
        self.assertEqual(actual, self.latest)
        self.assertEqual(target.db.execute('SELECT count(*) FROM revisions WHERE object_id=?',
                                          (self.latest['object_id'],)).fetchone()[0], 1)
        method_files.validate(target)
        execution = self.methods.prepare(target, {'work_type': 'example', 'run_id': 'new', 'step_id': 'one',
            'target': 'sample', 'conditions': {}, 'inputs': {'context': 'Supplied input'}, 'private': True})
        self.assertEqual(execution['payload']['package']['method'], self.methods.reference(self.latest))
        self.methods.artifact(target, {**{key: execution['payload'][key] for key in ('work_type', 'run_id', 'step_id', 'target')},
            'execution': self.methods.reference(execution), 'inputs': execution['payload']['inputs'],
            'stage': 'result', 'output': 'Actual new result'})
        payload = copy.deepcopy(actual['payload'])
        payload['files']['SKILL.md'] += 'Next deliberate change.\n'
        next_version = self.methods.save(target, {'category': 'skill', 'name': 'example',
                                                 'expected_version': 2, 'payload': payload})
        self.assertEqual(next_version['version'], 3)
        exported = migration.export_configuration(target.db_path)
        self.assertEqual(exported[migration.BASELINES][actual['object_id']]['revision_id'], actual['revision_id'])
        recovered = self.store('recovered')
        migration.restore_configuration(recovered, exported)
        self.assertEqual(self.methods.read(recovered, actual['object_id']), next_version)
        # Standard private execution archives can be restored after their
        # exact configuration baseline, without fabricating versions 1..N.
        private_archive = self.methods.export_registry(target, executions=[execution['object_id']])
        self.methods.restore_registry(recovered, private_archive)
        self.assertEqual(self.methods.read(recovered, execution['object_id']), execution)
        with self.assertRaisesRegex(ValueError, '目标已更新'):
            migration.restore_configuration(target, self.archive)
        self.assertEqual(self.methods.read(target, actual['object_id']), next_version)

    def test_replay_does_not_prune_existing_target_history(self):
        before = self.source.db.execute('SELECT count(*) FROM revisions').fetchone()[0]
        result = migration.restore_configuration(self.source, self.archive)
        self.assertEqual(result['inserted'], 0)
        self.assertEqual(self.source.db.execute('SELECT count(*) FROM revisions').fetchone()[0], before)

    def test_bootstrap_staging_accepts_retained_history_baseline(self):
        from scripts.managed_methods import install
        target = self.store('bootstrap-target')
        migration.restore_configuration(target, self.archive)
        result = install(target, {'records': [], 'bindings': []})
        self.assertEqual(result['restored']['inserted'], 0)
        self.assertEqual(self.methods.read(target, self.latest['object_id']), self.latest)

    def test_bad_baseline_or_semantic_dependency_rolls_back_every_row(self):
        target = self.store('invalid')
        for mutation in ('baseline', 'section'):
            archive = copy.deepcopy(self.archive)
            if mutation == 'baseline':
                archive[migration.BASELINES][self.latest['object_id']]['version'] = 3
            else:
                skill = next(row for row in archive['records'] if row['object_id'] == self.latest['object_id'])
                previous = skill['revision_id']
                skill['payload']['resources'][0]['section'] = 'missing'
                skill['revision_id'] = self.methods.checksum({key: skill[key] for key in ('object_id', 'version', 'payload')})
                archive[migration.BASELINES][skill['object_id']]['revision_id'] = skill['revision_id']
                binding = next(row for row in archive['records'] if row['payload']['format'] == self.methods.FORMATS['binding'])
                binding['payload']['rules'][0]['revision_id'] = skill['revision_id']
                binding['dependencies'][0]['revision_id'] = skill['revision_id']
                binding['revision_id'] = self.methods.checksum({key: binding[key] for key in ('object_id', 'version', 'payload')})
                archive[migration.BASELINES][binding['object_id']]['revision_id'] = binding['revision_id']
                self.assertNotEqual(previous, skill['revision_id'])
            self.sign(archive)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                migration.restore_configuration(target, archive)
            self.assertEqual(target.db.execute('SELECT count(*) FROM objects').fetchone()[0], 0)
            self.assertFalse(target.db.in_transaction)


if __name__ == '__main__':
    unittest.main()
