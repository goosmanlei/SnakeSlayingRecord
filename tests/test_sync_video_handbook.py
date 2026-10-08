import importlib.util
from pathlib import Path
import unittest
import tempfile
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync_video_handbook", ROOT / "scripts/sync_video_handbook.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HandbookDerivationTest(unittest.TestCase):
    def test_only_explicit_local_method_media_is_embedded_with_exact_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/'content/production-approach-assets';folder.mkdir(parents=True)
            (folder/'demo.png').write_bytes(b'original fixture')
            (folder/'demo.mp4').write_bytes(b'original video fixture')
            manifest = root/module.MEDIA_MANIFEST; manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({
                'images': [{'file': 'content/production-approach-assets/demo.png', 'sha256': hashlib.sha256(b'original fixture').hexdigest(), 'width': 1672, 'height': 941}],
                'videos': [{'file': 'content/production-approach-assets/demo.mp4', 'sha256': hashlib.sha256(b'original video fixture').hexdigest(), 'output': {'width': 1280, 'height': 720}}]}))
            prefix='# Method\n\nLead\n\n<!-- section:demo -->\n## Demo\n\n'
            tab=module.derive((prefix+'![Original image](../content/production-approach-assets/demo.png)\n\n[Original video](../content/production-approach-assets/demo.mp4)\n').encode(),root)
            blocks=tab['sections'][0]['blocks']
            self.assertEqual([b['kind'] for b in blocks],['image','video'])
            self.assertEqual(blocks[0]['sha256'],hashlib.sha256(b'original fixture').hexdigest())
            self.assertEqual([(b['width'], b['height']) for b in blocks], [(1672, 941), (1280, 720)])
            for link in ['![Private](https://private.invalid/p.png)','![Missing](../content/production-approach-assets/missing.png)','![Wrong kind](../content/production-approach-assets/demo.mp4)']:
                with self.assertRaises(ValueError):module.derive((prefix+link).encode(),root)
            (folder/'demo.png').write_bytes(b'changed image')
            with self.assertRaisesRegex(ValueError, 'metadata differs'):
                module.derive((prefix+'![Original image](../content/production-approach-assets/demo.png)').encode(),root)

    def test_full_source_and_prompt_bytes_are_retained(self):
        raw = ("# 方法\n\n独立导语\n\n<!-- section:one -->\n## 一\n\n说明。\n\n"
               "```text\n0—2 秒：动作\n  <speaker>\n```\n\n"
               "| 条件 | 选择 |\n| --- | --- |\n| A | B |\n\n"
               "1. 第一步\n2. 第二步\n").encode()
        tab = module.derive(raw)
        self.assertEqual(tab["lead"], "独立导语")
        self.assertEqual(tab["sections"][0]["blocks"][1]["text"], "0—2 秒：动作\n  <speaker>")
        self.assertEqual(tab["sections"][0]["blocks"][2]["rows"], [["A", "B"]])
        self.assertEqual(tab["sections"][0]["blocks"][3]["items"], ["第一步", "第二步"])

    def test_unsupported_or_truncated_content_fails_instead_of_disappearing(self):
        prefix = "# 方法\n\n导语\n\n<!-- section:one -->\n## 一\n\n"
        for body in ["![原件](private.png)", "<iframe>private</iframe>", "```text\n未闭合", "| A | B |\n| --- | --- |\n| 缺列 |", "## 没有准确锚点", "  不支持的缩进", "正文\n\n<!-- section:one -->\n## 重复\n\n正文"]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                module.derive((prefix + body).encode())


if __name__ == "__main__":
    unittest.main()
