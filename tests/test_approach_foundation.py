import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from approach_foundation import project_document,reading_routes,sync_handbook_resource
from material_review_release import registry_media_files
from sync_filmcraft import FILES


class FoundationProjectionTest(unittest.TestCase):
    def test_retiring_pages_preserves_vision_and_the_overview_relations(self):
        original=json.loads((ROOT/'content/production-approach.json').read_text())
        original['tabs']+=[{'id':'filmcraft'},{'id':'video-handbook'}]
        previous=copy.deepcopy(original)
        result=project_document(original,ROOT)
        self.assertEqual(original,previous)
        self.assertEqual(result['tabs'][0],previous['tabs'][0])
        self.assertEqual([x['id'] for x in result['tabs']],['vision','model','foundation','story','materials'])
        for name in ('story','materials'):
            before=next(x for x in previous['tabs'] if x['id']==name)['sections'][0]['diagram']
            after=next(x for x in result['tabs'] if x['id']==name)['sections'][0]['diagram']
            self.assertEqual(after['connections'],before['connections'])
            self.assertEqual(after['groups'],before['groups'])
            self.assertEqual(after['feedback']['targets'],before['feedback']['targets'])

    def test_all_professional_files_and_six_cases_have_real_reading_targets(self):
        routes=reading_routes(ROOT)
        covered={x['file'] for x in routes['filmcraft']['anchors'].values()}
        self.assertEqual(covered,{'production/filmcraft/'+name for name in FILES})
        cases=[entry for entry in routes['filmcraft']['anchors'].values()
               if entry['file'].endswith('applications.md') and entry['section']]
        self.assertEqual(len(cases),6)
        self.assertEqual(len({x['section'] for x in cases}),6)
        for entry in cases:
            self.assertTrue((ROOT/entry['file']).is_file())
        self.assertIn('approach-video-handbook-case-song',routes['video-handbook']['anchors'])

    def test_original_media_survives_page_retirement_and_conflicting_history_is_rejected(self):
        row={'payload':{'media':{'references/handbook.md':{'../demo.mp4':{
            'path':'content/production-approach-assets/demo.mp4','sha256':'a'*64}}}}}
        archive={'records':[row,copy.deepcopy(row)]}
        self.assertEqual(registry_media_files(archive),{'content/production-approach-assets/demo.mp4':'a'*64})
        archive['records'][1]['payload']['media']['references/handbook.md']['../demo.mp4']['sha256']='b'*64
        with self.assertRaises(ValueError):registry_media_files(archive)
        row['payload']['media']['references/handbook.md']['../demo.mp4']['path']='../private.mp4'
        with self.assertRaises(ValueError):registry_media_files({'records':[row]})


@unittest.skipUnless(importlib.util.find_spec('review_desk'), 'requires pinned review-desk source')
class HandbookResourceAnchorTest(unittest.TestCase):
    def test_tree_anchor_resolves_and_repeated_sync_does_not_add_versions(self):
        from review_desk import methods
        from review_desk.method_document import project
        from review_desk.store import Store
        with tempfile.TemporaryDirectory(prefix='handbook-anchor-test-') as directory:
            root = Path(directory)
            path = root / 'book.md'
            body = '# Handbook\n\nLead.\n\n<!-- section:prompt -->\n## Write a timeline\n\n0-8 seconds: one action.\n'
            path.write_text(body)
            source = {'name': 'video-handbook', 'title': 'Handbook', 'expected_version': 0,
                      'preserve_paths': False, 'sections': {'handbook': {'path': 'book.md'},
                      'prompt': {'path': 'book.md', 'section': 'prompt'}}}
            store = Store(root / 'review.sqlite3')
            try:
                first = sync_handbook_resource(store, root, source)
                payload = first['payload']
                self.assertEqual(payload['files']['references/handbook.md'], body)
                spec = payload['source']['files']['references/prompt.md']
                headings = [b for b in project(payload, 'references/prompt.md') if b['type'] == 'heading']
                self.assertEqual(headings[0]['section'], spec['section'])
                self.assertEqual(spec['sha256'], hashlib.sha256(body.encode()).hexdigest())
                self.assertEqual(spec['content_sha256'], hashlib.sha256(payload['files']['references/prompt.md'].encode()).hexdigest())
                self.assertEqual(path.read_text(), body)
                self.assertEqual(sync_handbook_resource(store, root, {**source, 'expected_version': 1}), first)
                self.assertEqual(store.db.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 1)
                path.write_text(body.replace('one action', 'one clear action'))
                second = sync_handbook_resource(store, root, {**source, 'expected_version': 1})
                self.assertEqual(second['version'], 2)
                self.assertEqual(store.db.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 2)
                with self.assertRaises(ValueError):
                    sync_handbook_resource(store, root, {**source, 'expected_version': 2,
                        'sections': {'missing': {'path': 'book.md', 'section': 'absent'}}})
                self.assertEqual(methods.read(store, first['object_id']), second)
                with self.assertRaises(ValueError):
                    methods.save(store, {'category': 'resource', 'name': 'video-handbook',
                                        'expected_version': 2, 'payload': second['payload']})
            finally:
                store.close()


if __name__=='__main__':unittest.main()
