import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from approach_foundation import project_document,reading_routes
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


if __name__=='__main__':unittest.main()
