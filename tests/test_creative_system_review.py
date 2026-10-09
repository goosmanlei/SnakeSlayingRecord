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
        expected = [re.sub(r'^#{1,2} ', '', line) for line in raw.decode().splitlines() if line.strip()]
        self.assertEqual(actual, expected)
        self.assertEqual(tab['source']['sha256'], hashlib.sha256(raw).hexdigest())
        release.check_vision_change(before, updated, raw)
        changed = copy.deepcopy(updated)
        changed['tabs'][1]['lead'] += ' unrelated edit'
        with self.assertRaisesRegex(ValueError, 'old approach content'):
            release.check_vision_change(before, changed, raw)


class ReviewMethodDeliveryTest(unittest.TestCase):
    def test_full_source_projection_prepare_restore_and_frozen_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
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
            self.assertEqual(len(resources), 3)
            for resource, spec in zip(resources, seed['sources'][0]['sections'].values()):
                self.assertEqual(resource['content'], (ROOT / spec['path']).read_text())
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
            for index, resource in enumerate(resources):
                self.assertEqual((folder / 'shared' / (str(index) + '.md')).read_text(), resource['content'])
            methods.restore_registry(restored, json.loads((folder / 'registry.json').read_text()))
            self.assertEqual(methods.prepare(restored, request), execution)
            self.assertEqual(methods.resolve(restored, 'creative-system-review'),
                             methods.resolve(store, 'creative-system-review'))


if __name__ == '__main__':
    unittest.main()
