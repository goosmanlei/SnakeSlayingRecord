import json
import tempfile
import unittest
from pathlib import Path
from scripts.method_runtime import deliver_files
from scripts import creative_method


class MethodDeliveryTest(unittest.TestCase):
    def test_companion_paths_and_actual_supporting_documents_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            package={'files':{'SKILL.md':'method'},'resources':[{'title':'Knowledge','reference':{'object_id':'resource','revision_id':'v1','section':'main'},
                     'file':'book/main.md','content':'![diagram](diagram.svg)', 'files':{'book/diagram.svg':'<svg/>'}}]}
            inputs={'supporting_records':[{'reference':{'object_id':'original','revision_id':'v1'},'kind':'ASSET','content_json':'{"title":"Actual"}'}]}
            deliver_files(root,package,inputs)
            self.assertEqual((root/'shared/0/book/diagram.svg').read_text(),'<svg/>')
            self.assertIn('shared/0/book/main.md',(root/'RESOURCES.md').read_text())
            self.assertEqual(json.loads((root/'materials/0.json').read_text())['payload']['title'],'Actual')
            deliver_files(root,package,inputs)
            (root/'SKILL.md').write_text('changed')
            with self.assertRaisesRegex(ValueError,'发生变化'):deliver_files(root,package,inputs)

    def test_flat_resources_use_standard_export_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            package = {'files': {'SKILL.md': '[Full](shared/0.md)'}, 'resources': [
                {'title': 'Full', 'reference': {'object_id': 'resource', 'revision_id': 'v1', 'section': 'skill'},
                 'file': 'references/skill.md', 'content': 'Frozen original prose'}]}
            deliver_files(root, package, {})
            self.assertEqual((root / 'shared/0.md').read_text(), 'Frozen original prose')
            self.assertIn('(shared/0.md)', (root / 'RESOURCES.md').read_text())

    def test_delivery_rejects_symlink_and_outside_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'outside').mkdir();(root/'link').symlink_to(root/'outside')
            with self.assertRaisesRegex(ValueError,'符号链接'):
                creative_method.begin(None,root/'link'/'new',{})
            self.assertFalse((root/'outside/new').exists())
            with self.assertRaisesRegex(ValueError,'越界'):
                deliver_files(root,{'files':{'../escape':'bad'},'resources':[]},{})
            with self.assertRaisesRegex(ValueError,'阶段名'):
                creative_method.read_stage(None,root,'../escape')


if __name__=='__main__':unittest.main()
