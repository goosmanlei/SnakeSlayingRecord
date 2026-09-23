import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.novel_writing import Conflict, WritingStore, canonical, checksum


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "novel_writing.py"


SOURCE = {
    "id": "refinement-test", "title": "故事精修一", "version_type": "原创",
    "origin": "test", "source_url": "https://example.org/source", "collected_at": "2026-09-23",
    "notes": "原梗概", "assets": [], "blocks": [{"id": "old", "text": "原有梗概"}],
    "group": "story-refinements", "order": 1,
}


class WritingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / "working" / "work.sqlite3"
        self.work = WritingStore(self.path)
        self.seed = {"source": SOURCE, "source_revision": checksum(SOURCE), "constraints": ["逐片段写作"],
                     "book_title": "测试小说", "notes": {"outlook": "初步构想", "facts": {}, "issues": {}}}
        self.work.init(self.seed)
        self.formal_path = self.root / ".runtime" / "review.sqlite3"
        self.formal_path.parent.mkdir()
        # Minimal read-contract fixture, not a dependency on review-desk code.
        self.formal = sqlite3.connect(self.formal_path)
        self.formal.executescript("""
            CREATE TABLE sources(id TEXT PRIMARY KEY, document TEXT, revision TEXT);
            CREATE TABLE comments(id TEXT PRIMARY KEY, body TEXT);
            CREATE TABLE comment_events(id INTEGER PRIMARY KEY, body TEXT);
            INSERT INTO comments VALUES ('existing', '既有评论');
            INSERT INTO comment_events VALUES (1, '既有事件');
        """)
        self.formal.execute("INSERT INTO sources VALUES (?,?,?)", (SOURCE["id"], canonical(SOURCE), checksum(SOURCE)))
        self.formal.commit()

    def tearDown(self):
        self.work.close()
        self.formal.close()
        self.tmp.cleanup()

    def begin(self, step="s1", action="WRITE", targets=None):
        context = self.work.context()
        spec = {"step_id": step, "base_revision": context["revision"], "action": action,
                "targets": targets if targets is not None else [step], "purpose": "test",
                "chapter_id": "c01", "chapter_title": "第一章 灯"}
        self.work.begin(spec)
        return spec

    def write(self, step="s1", text="她把灯放在门边。"):
        self.begin(step)
        self.work.save_candidate(step, {"fragments": [{"id": step, "text": text}]})
        self.work.read_candidate(step)
        return self.work.accept(step, {"observations": "动作成立", "updates": {"next": "继续"}})

    def ready(self):
        self.write()
        for phase in ("FULL_DRAFT", "REVISING", "READY_TO_PUBLISH"):
            head = self.work.context(full=True)["revision"]
            self.work.stage({"phase": phase, "base_revision": head, "review": "全稿检查通过",
                             "checked_fragment_ids": ["s1"],
                             "checks": {k: True for k in ("complete", "causality", "continuity", "language", "clean_copy")}})
        return self.work.bundle()

    def test_serial_scope_and_reread_are_required(self):
        spec = self.begin()
        with self.assertRaises(Conflict):
            self.work.begin({**spec, "step_id": "s2", "targets": ["s2"]})
        with self.assertRaises(ValueError):
            self.work.save_candidate("s1", {"fragments": [{"id": "s1", "text": "甲"}, {"id": "s2", "text": "乙"}]})
        with self.assertRaises(ValueError):
            self.work.save_candidate("s1", {"fragments": [{"id": "s1", "text": "字" * 2201}]})
        self.work.save_candidate("s1", {"fragments": [{"id": "s1", "text": "甲"}]})
        with self.assertRaises(Conflict):
            self.work.accept("s1", {"observations": "未重读", "updates": {}})
        self.assertEqual(self.work.status()["fragments"], 0)

    def test_candidate_resume_and_acceptance_idempotency(self):
        self.begin()
        candidate = {"fragments": [{"id": "s1", "text": "甲"}]}
        saved = self.work.save_candidate("s1", candidate)
        self.work.close()
        self.work = WritingStore(self.path)
        self.assertEqual(saved, self.work.save_candidate("s1", candidate))
        with self.assertRaises(Conflict):
            self.work.save_candidate("s1", {"fragments": [{"id": "s1", "text": "乙"}]})
        self.work.read_candidate("s1")
        review = {"observations": "读过保存结果", "updates": {}}
        result = self.work.accept("s1", review)
        self.work.close()
        self.work = WritingStore(self.path)
        self.assertEqual(result, self.work.accept("s1", review))
        self.assertEqual(self.work.status()["fragments"], 1)
        self.assertEqual(self.work.context()["fragments"][0]["text"], "甲")

    def test_old_context_and_bad_notes_cannot_overwrite(self):
        old = self.work.context()["revision"]
        self.write()
        with self.assertRaises(Conflict):
            self.work.begin({"step_id": "s2", "base_revision": old, "action": "WRITE", "targets": ["s2"], "purpose": "stale"})
        self.begin("s2")
        self.work.save_candidate("s2", {"fragments": [{"id": "s2", "text": "乙"}]})
        self.work.read_candidate("s2")
        current = self.work.current()
        with self.assertRaises(ValueError):
            self.work.accept("s2", {"observations": "无效引用", "updates": {"facts": {"bad": {"text": "不存在", "fragment_ids": ["missing"]}}}})
        self.assertEqual(current, self.work.current())
        self.assertEqual(self.work.status()["active"][0]["status"], "CANDIDATE_SAVED")

    def test_real_revision_updates_prose_and_fact_together(self):
        self.write(text="她没有见过祭册。")
        self.begin("r1", "REVISE", ["s1"])
        self.work.save_candidate("r1", {"fragments": [{"id": "s1", "text": "她见过祭册上的名字。"}]})
        self.work.read_candidate("r1")
        review = {"observations": "更改知情范围", "updates": {"facts": {"knowledge": {"text": "已见祭册", "fragment_ids": ["s1"]}}},
                  "rechecked_fragment_ids": ["s1"], "dependency_review": "尚无后文；下一步须据此续写"}
        self.work.accept("r1", review)
        context = self.work.context()
        self.assertIn("见过祭册", context["fragments"][0]["text"])
        self.assertEqual(context["notes"]["facts"]["knowledge"]["text"], "已见祭册")
        self.assertEqual(json.loads(self.formal.execute("SELECT document FROM sources").fetchone()[0]), SOURCE)

    def test_blocker_prevents_forward_writing_not_reflection(self):
        self.begin("think", "REFLECT", [])
        self.work.save_candidate("think", {"reflection": "动机冲突，应先修"})
        self.work.read_candidate("think")
        self.work.accept("think", {"observations": "阻止照提纲强推", "updates": {"issues": {"causality": {"status": "OPEN", "blocking": True}}}})
        with self.assertRaises(Conflict):
            self.begin()
        self.begin("think2", "REFLECT", [])
        self.work.reject("think2", "保留后重新判断")
        self.assertFalse(self.work.status()["active"])

    def test_no_bundle_before_complete_checks_and_publish_recovery(self):
        with self.assertRaises(Conflict):
            self.work.bundle()
        package = self.ready()
        self.assertEqual(json.loads(self.formal.execute("SELECT document FROM sources").fetchone()[0]), SOURCE)
        self.work.close()
        self.work = WritingStore(self.path)
        self.assertEqual(package, self.work.bundle())
        with self.assertRaises(Conflict):
            self.work.published(self.formal_path)
        # Simulate an independent publisher; this tool only verifies the result.
        with self.formal:
            self.formal.execute("UPDATE sources SET document=?,revision=? WHERE id=?", (canonical(package["document"]), package["document_sha256"], SOURCE["id"]))
        # Publication succeeded, author checkpoint did not yet record it.
        self.work.close()
        self.work = WritingStore(self.path)
        formal_before = self.formal_path.read_bytes()
        self.assertEqual(self.work.published(self.formal_path)["phase"], "PUBLISHED")
        self.assertEqual(self.work.published(self.formal_path)["phase"], "PUBLISHED")
        self.assertEqual(self.formal_path.read_bytes(), formal_before)

    def test_bundle_uses_seed_title_without_story_specific_metadata(self):
        package = self.ready()
        self.assertEqual(package["document"]["text_heading"], "测试小说 · 小说全文")
        self.assertEqual(package["document"]["edition"], "小说完本稿")
        self.assertTrue(package["markdown"].startswith("# 测试小说\n"))
        self.assertNotIn("把灯带回家", str(package))

    def cli(self, *args):
        # Isolated Python mode excludes repo/PYTHONPATH imports. No review desk
        # checkout or installed package is needed to run this script.
        return subprocess.run([sys.executable, "-I", str(SCRIPT), "--instance", str(self.root),
                               "--run", "local-test", *args], cwd=self.root,
                              capture_output=True, text=True)

    def test_standalone_cli_reads_formal_snapshot_without_writes(self):
        seed_path = self.root / "seed.json"
        seed_path.write_text(json.dumps({"source_id": SOURCE["id"], "book_title": "测试",
                                         "constraints": ["串行"], "notes": {}}, ensure_ascii=False))
        formal_before = self.formal_path.read_bytes()
        result = self.cli("init", str(seed_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["phase"], "DRAFTING")
        result = self.cli("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        db_path = self.root / ".runtime/novel-writing/local-test/work.sqlite3"
        reopened = WritingStore(db_path)
        try:
            seed = reopened._get("seed")
            self.assertEqual(seed["source"], SOURCE)
            self.assertEqual(seed["formal_baseline"]["comments"], [{"id": "existing", "body": "既有评论"}])
            self.assertEqual(seed["formal_baseline"]["events"], [{"id": 1, "body": "既有事件"}])
        finally:
            reopened.close()
        self.assertEqual(self.formal_path.read_bytes(), formal_before)

    def test_missing_run_does_not_create_an_empty_work_database(self):
        result = self.cli("status")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("writing run does not exist", result.stderr)
        self.assertFalse((self.root / ".runtime/novel-writing").exists())

    def test_status_preserves_existing_checkpoint_bytes(self):
        self.write()
        self.work.close()
        before = self.path.read_bytes()
        self.work = WritingStore(self.path)
        self.assertEqual(self.work.status()["fragments"], 1)
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
