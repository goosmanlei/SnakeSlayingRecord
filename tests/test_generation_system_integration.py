import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import integrate_generation_review_system as delivery


class SystemIntegrationGuardTest(unittest.TestCase):
    def setUp(self):
        self.original_root = delivery.ROOT
        runtime = self.original_root / ".runtime"
        runtime.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=runtime, prefix="system-delivery-test-")
        self.root = Path(self.temp.name)
        self.main = self.root / "system"
        self.worktree = self.root / "candidate"
        subprocess.run(["git", "init", "-b", "main", str(self.main)], check=True, capture_output=True)
        for key, value in (("user.name", "Delivery Test"), ("user.email", "delivery-test@example.invalid")):
            self.g("config", key, value)
        (self.main / "ui.txt").write_text("before\n")
        self.g("add", "ui.txt")
        self.g("commit", "-m", "base")
        self.target = self.g("rev-parse", "HEAD")
        self.g("worktree", "add", "-b", "candidate", str(self.worktree))
        (self.worktree / "ui.txt").write_text("reviewed candidate\n")
        delivery.git(self.worktree, "add", "ui.txt")
        delivery.git(self.worktree, "commit", "-m", "candidate")
        self.candidate = delivery.git(self.worktree, "rev-parse", "HEAD")
        delivery.ROOT = self.root
        self.receipt = self.root / ".runtime/receipt.json"

    def tearDown(self):
        delivery.ROOT = self.original_root
        self.temp.cleanup()

    def g(self, *args):
        return delivery.git(self.main, *args)

    def run_delivery(self, apply=False):
        return delivery.integrate(self.main, self.worktree, self.target, self.candidate,
                                  self.receipt if apply else None)

    def test_preflight_then_exact_fast_forward_and_idempotent_receipt(self):
        result = self.run_delivery()
        self.assertTrue(result["preflight_only"])
        self.assertEqual(self.g("rev-parse", "HEAD"), self.target)
        self.assertFalse(self.receipt.exists())
        self.run_delivery(True)
        self.assertEqual(self.g("rev-parse", "HEAD"), self.candidate)
        receipt = self.receipt.read_bytes()
        self.run_delivery(True)
        self.assertEqual(self.receipt.read_bytes(), receipt)
        self.assertFalse(json.loads(receipt)["push"])
        self.assertFalse(json.loads(receipt)["database_write"])

    def test_dirty_target_is_preserved(self):
        (self.main / "ui.txt").write_text("another writer's work\n")
        with self.assertRaisesRegex(ValueError, "tracked system files"):
            self.run_delivery(True)
        self.assertEqual((self.main / "ui.txt").read_text(), "another writer's work\n")
        self.assertEqual(self.g("rev-parse", "HEAD"), self.target)
        self.assertFalse(self.receipt.exists())

    def test_changed_target_or_wrong_receipt_cannot_integrate(self):
        self.receipt.parent.mkdir()
        self.receipt.write_text(json.dumps({"candidate": "different", "target_after": "different"}))
        with self.assertRaisesRegex(ValueError, "different delivery"):
            self.run_delivery(True)
        self.assertEqual(self.g("rev-parse", "HEAD"), self.target)
        self.receipt.unlink()
        (self.main / "parallel.txt").write_text("concurrent change\n")
        self.g("add", "parallel.txt")
        self.g("commit", "-m", "parallel")
        advanced = self.g("rev-parse", "HEAD")
        with self.assertRaisesRegex(ValueError, "system main changed"):
            self.run_delivery(True)
        self.assertEqual(self.g("rev-parse", "HEAD"), advanced)
        self.assertFalse(self.receipt.exists())


if __name__ == "__main__":
    unittest.main()
