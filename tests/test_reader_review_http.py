"""Optional integration test against the sibling desk, using an isolated instance."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from scripts.reader_review import HTTPDesk, ReaderRun
from test_reader_review import Model, issue, result, source


ROOT = Path(__file__).resolve().parents[1]
SYSTEM = next((p for p in ((Path(os.environ["REVIEW_DESK_SYSTEM_PATH"]).resolve(),) if os.environ.get("REVIEW_DESK_SYSTEM_PATH")
                          else (ROOT.parent / "story-review-desk-python", ROOT.parent / "story-review-desk"))
               if (p / "review_desk/__main__.py").is_file()), None)


@unittest.skipIf(SYSTEM is None, "sibling review desk is needed for the HTTP integration test")
class HTTPIntegrationTest(unittest.TestCase):
    def test_comments_edit_and_export_restore_on_real_http(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "instance"
            (root / "config").mkdir(parents=True)
            config = {"id": "reader-test", "title": "Reader test"}
            (root / "config/instance.json").write_text(json.dumps(config))
            doc = {**source(), "version_type": "original", "origin": "test", "source_url": "https://example.org",
                   "collected_at": "2026-09-27", "assets": []}
            document = Path(temporary) / "source.json"
            document.write_text(json.dumps([doc], ensure_ascii=False))
            env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
            env["PYTHONPATH"] = str(SYSTEM)

            def cli(instance, *args):
                completed = subprocess.run([sys.executable, "-m", "review_desk", "--instance", str(instance), *args],
                                           env=env, capture_output=True, text=True, timeout=20)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                return json.loads(completed.stdout)

            cli(root, "import-sources", str(document))
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            with (Path(temporary) / "server.log").open("w") as log:
                process = subprocess.Popen([sys.executable, "-m", "review_desk", "--instance", str(root), "serve", "--port", str(port)],
                                           env=env, stdout=log, stderr=log)
                work = None
                try:
                    desk = HTTPDesk(root, "http://127.0.0.1:" + str(port))
                    for attempt in range(100):
                        try:
                            desk.http("GET", "/api/instance")
                            break
                        except OSError:
                            time.sleep(.05)
                    else:
                        self.fail("isolated HTTP server did not start")
                    work = ReaderRun.initialize(Path(temporary) / "reader", desk, "fixture", "灯")
                    model = Model([result([issue("COMMENT", note="初读问题。")]),
                                   result([issue("EXPLAINED", issue_id="q0001-01", note="后文已经解释。")]),
                                   result(), result(final=True)])
                    for _ in range(4):
                        work.step(desk, model, sleeper=lambda n: None)
                    verification = work.verify(desk)
                    self.assertTrue(verification["full_reading_complete"])
                    self.assertEqual(verification["formal_comments_verified"], 1)
                    self.assertEqual(verification["baseline_changes"], [])
                    exported = cli(root, "export")
                    self.assertEqual(exported["events"], 2)
                    restored = Path(temporary) / "restored"
                    (restored / "config").mkdir(parents=True)
                    (restored / "config/instance.json").write_text(json.dumps(config))
                    import shutil
                    shutil.copytree(root / "export", restored / "export")
                    cli(restored, "restore")
                    cli(restored, "export")
                    for name in ["manifest.json", *exported["files"]]:
                        self.assertEqual((root / "export" / name).read_bytes(), (restored / "export" / name).read_bytes())
                finally:
                    if work:
                        work.close()
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
