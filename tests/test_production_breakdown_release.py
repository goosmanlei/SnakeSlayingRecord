"""Approval boundary and serial release order; no formal resources are touched."""
import argparse
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import production_breakdown_release as r


class BreakdownReleaseTest(unittest.TestCase):
    def test_both_apply_and_explicit_phase_exception_are_required(self):
        for apply,exception in ((False,False),(True,False),(False,True)):
            with patch.object(r,'load') as load:
                with self.assertRaisesRegex(ValueError,'actual user confirmation'):
                    r.apply(argparse.Namespace(apply=apply,allow_internal_task_api=exception))
                load.assert_not_called()

    def test_changed_confirmed_manifest_stops_before_integration(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'manifest.json').write_text('{}')
            a=argparse.Namespace(apply=True,allow_internal_task_api=True,bundle=root,manifest_sha256='wrong')
            with patch.object(r,'load',return_value=(root,{},{})),patch.object(r,'integrate_story') as integrate:
                with self.assertRaisesRegex(ValueError,'digest changed'):r.apply(a)
                integrate.assert_not_called()

    def test_code_integrates_before_delta_and_service_then_waits_for_browser(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'service').mkdir()
            for f in ('manifest.json','service/image.json'):(root/f).write_text('{}')
            digest=r.base.sha(b'{}');calls=[]
            m={'service_manifest_sha256':'service-digest'}
            s={'story_candidate':'a'*40,'system_candidate':'b'*40}
            a=argparse.Namespace(apply=True,allow_internal_task_api=True,bundle=root,
                manifest_sha256=digest,image_receipt_sha256=digest,note='fixture approval boundary only')
            with patch.object(r,'load',return_value=(root,m,s)), \
                 patch.object(r.service,'checks',side_effect=lambda *a,**kw:calls.append('checks')), \
                 patch.object(r,'runtime_preflight',side_effect=lambda *a:calls.append('runtime')), \
                 patch.object(r,'originals',side_effect=lambda *a:calls.append('originals')), \
                 patch.object(r,'integrate_story',side_effect=lambda *a:calls.append('story')), \
                 patch.object(r.base,'run',side_effect=lambda *a,**kw:calls.append('system')), \
                 patch.object(r,'rehearse',side_effect=lambda *a,**kw:(calls.append('delta' if kw.get('apply') else 'rehearsal') or {'publication_id':'fixture'})), \
                 patch.object(r.service,'apply',side_effect=lambda *a:calls.append('service')), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                r.apply(a)
            self.assertEqual(calls,['checks','runtime','originals','rehearsal','story','system','delta','service'])
            self.assertIn('formal_browser_pending',output.getvalue())
            self.assertIn('"complete_invoked": false',output.getvalue())

    def test_foreign_runtime_is_rejected_before_integration(self):
        with patch.object(r.service,'inspect',return_value={'Image':'foreign','Mounts':[]}), \
             patch.object(r.base,'safe_container',return_value={'image':'foreign'}), \
             patch.object(r.base,'compose_definition',return_value={'services':{'app':{'volumes':[]}}}):
            with self.assertRaisesRegex(ValueError,'another formal runtime'):
                r.runtime_preflight(Path('/fixture'),{'previous_app':{'image':'old'},
                    'story_main':'/fixture/main','release_name':'candidate'}, {'image':'approved'})


if __name__=='__main__':unittest.main()
