"""Exact Review delivery, isolated method execution, and reversible restoration."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import managed_methods
import sync_system_vision as vision
import material_review_release as release
from scripts.method_runtime import deliver_files
from review_desk import methods
from review_desk.store import Store


class VisionDeliveryTest(unittest.TestCase):
    def test_all_prose_is_preserved_and_other_tabs_are_unchanged(self):
        raw = (ROOT / vision.SOURCE).read_bytes()
        document = json.loads((ROOT / vision.DESTINATION).read_text())
        before = {**document, 'tabs': [t for t in document['tabs'] if t['id'] != 'vision']}
        updated = vision.update(before, raw)
        self.assertEqual(updated, document)
        self.assertEqual(updated['tabs'][1:], before['tabs'])
        self.assertEqual(vision.update(updated, raw), updated)
        tab = updated['tabs'][0]
        actual = [tab['title'], tab['lead']]
        for section in tab['sections']:
            actual += [section['title']] + [block['text'] for block in section['blocks']]
        expected = [re.sub(r'^#{1,2} ', '', line) for line in raw.decode().splitlines()
                    if line.strip() and not line.startswith(('<!-- layout: ', '<!-- diagram: '))]
        self.assertEqual(actual, expected)
        diagrams = [json.loads(line[len('<!-- diagram: '):-len(' -->')])
                    for line in raw.decode().splitlines() if line.startswith('<!-- diagram: ')]
        self.assertEqual([section['diagram'] for section in tab['sections'] if 'diagram' in section], diagrams)
        self.assertEqual(tab['source']['sha256'], hashlib.sha256(raw).hexdigest())
        release.check_vision_change(before, updated, raw)
        changed = copy.deepcopy(updated)
        changed['tabs'][1]['lead'] += ' unrelated edit'
        with self.assertRaisesRegex(ValueError, 'old approach content'):
            release.check_vision_change(before, changed, raw)


class ReviewMethodDeliveryTest(unittest.TestCase):
    def test_legacy_execution_reexport_and_restore_keep_original_prose(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            store = Store(root / 'old/.runtime/review.sqlite3')
            restored = Store(root / 'restored/.runtime/review.sqlite3')
            self.addCleanup(store.close); self.addCleanup(restored.close)
            archive = json.loads((ROOT / 'content/creative-system-review-registry.json').read_text())
            legacy = {'format': archive['format'], 'records': [r for r in archive['records'] if r['version'] == 1]}
            legacy['sha256'] = methods.checksum(legacy)
            methods.restore_registry(store, legacy)
            request = {'work_type': 'creative-system-review', 'run_id': 'legacy-reading', 'step_id': 'original',
                       'target': 'frozen-prose', 'private': True,
                       'inputs': {'goal': 'compatibility', 'scope': 'legacy definition',
                                  'authorization': 'isolated test', 'evidence': 'original registry'}}
            execution = methods.prepare(store, request)
            methods.restore_registry(store, archive)
            self.assertEqual(methods.prepare(store, request), execution)
            fresh = methods.prepare(store, {**request, 'step_id': 'new-binding'})
            self.assertNotEqual(fresh['payload']['package']['binding'], execution['payload']['package']['binding'])
            self.assertEqual(len(execution['payload']['package']['resources']), 3)
            self.assertEqual(len(fresh['payload']['package']['resources']), 1)
            folder = root / 'standard'
            methods.export_execution(store, methods.reference(execution), folder)
            deliver_files(root / 'author', execution['payload']['package'], request['inputs'])
            for number, resource in enumerate(execution['payload']['package']['resources']):
                self.assertEqual((folder / f'shared/{number}.md').read_text(), resource['content'])
                self.assertEqual((root / 'author' / f'shared/{number}.md').read_text(), resource['content'])
            # Do not manufacture absent companions or rewrite historical SKILL prose.
            self.assertFalse((folder / 'shared/references/project-context.md').exists())
            methods.restore_registry(restored, json.loads((folder / 'registry.json').read_text()))
            self.assertEqual(methods.prepare(restored, request), execution)

    def test_full_source_projection_prepare_restore_and_frozen_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            store = Store(root / 'source/.runtime/review.sqlite3')
            restored = Store(root / 'restored/.runtime/review.sqlite3')
            self.addCleanup(store.close)
            self.addCleanup(restored.close)
            seed = json.loads((ROOT / 'content/creative-system-review-method.json').read_text())
            # An existing independent method remains exactly the same.
            other = copy.deepcopy(seed['records'][0])
            other['name'] = 'existing-review'
            other['payload']['resources'] = []
            prior = methods.save(store, other)
            managed_methods.install(store, seed)
            self.assertEqual(methods.read(store, prior['object_id']), prior)
            self.assertEqual(managed_methods.install(store, seed)['restored']['inserted'], 0)
            request = {'work_type': 'creative-system-review', 'run_id': 'offline-delivery',
                       'step_id': 'first', 'target': 'vision-and-review', 'private': True,
                       'inputs': {'goal': '核对愿景与协作阅读', 'scope': '准确候选页面',
                                  'authorization': '隔离实例检验', 'evidence': '源稿及真实阅读另验'}}
            execution = methods.prepare(store, request)
            resources = execution['payload']['package']['resources']
            self.assertEqual(len(resources), 1)
            self.assertEqual(resources[0]['content'], (ROOT / 'skills/creative-system-review/SKILL.md').read_text())
            for spec in seed['sources'][0]['sections'].values():
                path = spec['path']
                body = resources[0]['content'] if path == resources[0]['file'] else resources[0]['files'][path]
                self.assertEqual(body.encode(), (ROOT / path).read_bytes())
            projection = methods.read(store, 'method.resource.creative-system-review-texts')
            for filename, source in projection['payload']['source']['files'].items():
                raw = (ROOT / source['path']).read_bytes()
                self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(source['content_sha256'], hashlib.sha256(projection['payload']['files'][filename].encode()).hexdigest())
            with self.assertRaisesRegex(ValueError, '正文由项目 Markdown'):
                methods.save(store, {'category': 'resource', 'name': 'creative-system-review-texts',
                                     'expected_version': projection['version'], 'payload': projection['payload']})
            # A new method/binding must not rewrite a prepared execution.
            current = methods.read(store, 'method.skill.creative-system-review')
            revised = copy.deepcopy(current['payload']); revised['checks'] += ' 新步骤增加复核。'
            next_method = methods.save(store, {'category': 'skill', 'name': 'creative-system-review',
                                              'expected_version': current['version'], 'payload': revised})
            binding = methods.read(store, 'method.binding.creative-system-review')
            payload = copy.deepcopy(binding['payload'])
            payload['rules'][0].update(methods.reference(next_method))
            methods.save(store, {'category': 'binding', 'name': 'creative-system-review',
                                 'expected_version': binding['version'], 'payload': payload})
            self.assertEqual(methods.prepare(store, request), execution)
            next_execution = methods.prepare(store, {**request, 'step_id': 'second'})
            self.assertEqual(next_execution['payload']['package']['method'], methods.reference(next_method))
            folder = root / 'exported'
            methods.export_execution(store, methods.reference(execution), folder)
            author = root / 'author'
            deliver_files(author, execution['payload']['package'], request['inputs'])
            for delivered in (author, folder):
                entry = (delivered / 'SKILL.md').read_text()
                full = delivered / re.search(r'\[完整方法\]\(([^)]+)\)', entry)[1]
                text = full.read_text()
                adaptation = full.parent / re.search(r'\[项目适配\]\(([^)]+)\)', text)[1]
                self.assertEqual(adaptation.read_bytes(), (ROOT / 'skills/creative-system-review/references/project-context.md').read_bytes())
                for spec in seed['sources'][0]['sections'].values():
                    self.assertEqual((delivered / 'shared/0' / spec['path']).read_bytes(), (ROOT / spec['path']).read_bytes())
            methods.restore_registry(restored, json.loads((folder / 'registry.json').read_text()))
            self.assertEqual(methods.prepare(restored, request), execution)
            methods.export_execution(restored, methods.reference(execution), root / 'reexported')
            for spec in seed['sources'][0]['sections'].values():
                path = Path('shared/0') / spec['path']
                self.assertEqual((root / 'reexported' / path).read_bytes(), (folder / path).read_bytes())
            self.assertEqual(methods.resolve(restored, 'creative-system-review'),
                             methods.resolve(store, 'creative-system-review'))


if __name__ == '__main__':
    unittest.main()
