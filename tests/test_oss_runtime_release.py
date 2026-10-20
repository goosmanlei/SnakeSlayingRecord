import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "oss_runtime_release", Path(__file__).parents[1] / "scripts/oss_runtime_release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class RuntimeReleaseSafetyTests(unittest.TestCase):
    def test_missing_container_is_case_insensitive(self):
        for error in ("Error: No such object: app", "error: no such object: app",
                      "Error response from daemon: No such container: app"):
            with self.subTest(error=error), patch.object(
                release.subprocess, "run",
                return_value=subprocess.CompletedProcess([], 1, "", error),
            ):
                self.assertIsNone(release.optional_container("app"))

    def test_unknown_inspection_failure_retains_recovery_window(self):
        with patch.object(release.subprocess, "run", return_value=
                          subprocess.CompletedProcess([], 1, "", "Cannot connect to daemon")):
            with self.assertRaisesRegex(RuntimeError, "retain recovery window"):
                release.optional_container("app")

    def test_live_mount_requires_existing_matching_host_type(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ca.pem"
            target = "/run/local-ca/cacert.pem"
            container = {"Id": "live", "Mounts": [{"Source": str(source), "Destination": target}]}
            with patch.object(release, "run", return_value=json.dumps({target: stat.S_IFREG})):
                with self.assertRaisesRegex(ValueError, "missing or changed type"):
                    release.verify_mount_sources(container)
                source.mkdir()
                with self.assertRaisesRegex(ValueError, "missing or changed type"):
                    release.verify_mount_sources(container)
                source.rmdir()
                source.write_text("public test certificate")
                release.verify_mount_sources(container)

    def test_mount_inspection_failure_does_not_assume_safe(self):
        with patch.object(release, "run", side_effect=RuntimeError("runtime unavailable")):
            with self.assertRaisesRegex(RuntimeError, "runtime unavailable"):
                release.verify_mount_sources({"Id": "live", "Mounts": []})


if __name__ == "__main__":
    unittest.main()
