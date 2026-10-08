import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_filmcraft', ROOT / 'scripts/sync_filmcraft.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FilmcraftDerivationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        base = self.root / module.BASE; (base / 'diagrams').mkdir(parents=True)
        (self.root / 'content').mkdir()
        self.path = self.root / 'content/production-approach.json'
        self.original = {'schema_version': 2, 'tabs': [
            {'id': id, 'label': id, 'title': id, 'lead': '', 'sections': []}
            for id in ('story', 'materials', 'video-handbook')]}
        self.path.write_text(json.dumps(self.original))
        for i, group in enumerate(('space', 'light', 'post')):
            (base / f'sources-{group}.json').write_text(json.dumps([{
                'id': f'SP0{i+1}', 'author': 'Author', 'title': 'Read material',
                'url': f'https://example.org/source-{i}', 'published': '2020', 'accessed': '2026-10-08',
                'locator': 'Section 1', 'domains': ['01'], 'supports': ['Bounded claim'],
                'read_scope': 'Section 1 only', 'kind': 'primary',
            }]))
        self.doc = base / 'README.md'
        self.doc.write_text('# 知识\n\n中文完整段落。\n\n## 判断条件\n\n[证据](sources.md#sp01)\n\n![空间示意](diagrams/space.svg)\n\n```text\n原样\n  下一行\n```\n')
        self.diagram = base / 'diagrams/space.svg'
        self.diagram.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600"><text>示意</text></svg>')
        self.files = patch.object(module, 'FILES', ['README.md', 'sources.md'])
        self.files.start(); self.addCleanup(self.files.stop)

    def sync(self, check=False):
        with contextlib.redirect_stdout(io.StringIO()): module.synchronize(self.root, check)

    def test_full_text_internal_evidence_and_original_diagram_survive_derivation(self):
        self.sync(); self.sync(True)
        value = json.loads(self.path.read_text())
        self.assertEqual(value['tabs'][:3], self.original['tabs'])
        blocks = value['tabs'][3]['sections'][0]['blocks']
        self.assertEqual(blocks[0]['text'], '中文完整段落。')
        self.assertIn('#approach-filmcraft-sources-sp01', blocks[2]['text'])
        self.assertEqual(blocks[-1]['text'], '原样\n  下一行')
        image = self.root / 'content/production-approach-assets/filmcraft-space.svg'
        self.assertEqual(image.read_bytes(), self.diagram.read_bytes())
        self.sync()
        self.assertEqual(json.loads(self.path.read_text()), value)

    def test_missing_changed_or_corrupt_inputs_cannot_pass_a_stale_page(self):
        self.sync()
        self.doc.write_text(self.doc.read_text().replace('中文完整段落。', '修订后的段落。'))
        with self.assertRaisesRegex(ValueError, 'stale'): self.sync(True)
        self.sync(); self.diagram.unlink()
        with self.assertRaisesRegex(ValueError, 'missing diagram'): self.sync(True)

    def test_unrecognized_markup_and_broken_links_fail_instead_of_disappearing(self):
        for body in ('<iframe>content</iframe>', '#### hidden heading', '  nested unsupported',
                     '[missing](sources.md#sp99)', '![remote](https://example.org/x.png)',
                     '```text\ntruncated', '| A | B |\n| --- | --- |\n| one |'):
            self.doc.write_text('# 知识\n\n' + body + '\n')
            with self.subTest(body=body), self.assertRaises(ValueError): module.derive(self.root)

    def test_source_url_parentheses_cannot_truncate_a_clickable_reference(self):
        path = self.root / module.BASE / 'sources-space.json'
        sources = json.loads(path.read_text())
        sources[0]['url'] = 'https://example.org/Directors_(2025)_.pdf'
        path.write_text(json.dumps(sources))
        self.sync()
        page = json.loads(self.path.read_text())['tabs'][3]
        text = '\n'.join(block.get('text', '') for section in page['sections'] for block in section['blocks'])
        self.assertIn('https://example.org/Directors_%282025%29_.pdf)', text)


if __name__ == '__main__':
    unittest.main()
