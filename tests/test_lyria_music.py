import base64
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave

from scripts import lyria_music as lyria
from scripts import generation_operation
from generation_fixtures import make_worktree


class LyriaMusicTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.primary, self.root = make_worktree(self.temp.name)
        self.spec = self.root / "spec.json"
        (self.root / "lyrics.txt").write_text("[Verse]\n船靠岸，灯来迎", encoding="utf-8")
        (self.root / "directions.txt").write_text("中文女声，2/4拍，76 BPM。", encoding="utf-8")
        self.spec.write_text(json.dumps({"id": "boat-v1-a01", "song_entity_id": "entity-boat-song",
                                        "lyrics_file": "lyrics.txt", "directions_file": "directions.txt",
                                        "output_format": "wav",
                                        "production":{"url":"http://127.0.0.1:53101","requirement_id":"music","operation_id":"submit-music","call_id":"music-call"}}))
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as out:
            out.setnchannels(2)
            out.setsampwidth(2)
            out.setframerate(44100)
            out.writeframes(b"\0" * 44100 * 4)
        self.audio = buffer.getvalue()
        self.response = {"id": "interaction-01", "status": "completed", "model": lyria.MODEL,
                         "steps": [{"type": "model_output", "content": [
                             {"type": "text", "text": "provider lyrics"},
                             {"type": "audio", "mime_type": "audio/wav",
                              "data": base64.b64encode(self.audio).decode()}]}]}

    def mocked_submit(self, error=None):
        payload, metadata = lyria.prepare(self.spec)
        response = (json.dumps(self.response).encode(), self.response)
        package={'model':payload['model'],'prompt':payload['input'],
                 'parameters':{k:v for k,v in payload.items() if k not in ('model','input')},
                 'inputs':[],'current_marker':{'edit_token':1,'content_sha256':'a'*64}}
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "secret-test-key"}), \
             patch.object(lyria, "shared_root", return_value=self.root), \
             patch.object(generation_operation,'MethodClient') as client, \
             patch.object(lyria, "request_json") as request:
            client.return_value.call.side_effect=[package,{'already_applied':False,'call_id':'music-call','submission_sha256':'b'*64}]
            def dispatch(*_args,**_kwargs):
                self.assertEqual(client.return_value.call.call_args.args[0],'/api/production/submit')
                self.assertEqual(client.return_value.call.call_count,2)
                if error:raise error
                return response
            request.side_effect=dispatch
            result = lyria.submit(payload, metadata, self.root, "0.08", 60)
        return result, request

    def test_preview_does_not_call_api_or_create_runtime(self):
        with patch.object(lyria, "request_json") as request, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lyria.main([str(self.spec)]), 0)
        request.assert_not_called()
        self.assertFalse((self.root / ".runtime").exists())

    def test_selected_lyrics_hash_and_spec_fields_are_enforced(self):
        spec = json.loads(self.spec.read_text())
        spec["lyrics_sha256"] = "0" * 64
        self.spec.write_text(json.dumps(spec))
        with self.assertRaisesRegex(ValueError, "checksum"):
            lyria.prepare(self.spec)
        spec.pop("lyrics_sha256")
        spec["references"] = [{"audio": "private.wav"}]
        self.spec.write_text(json.dumps(spec))
        with self.assertRaisesRegex(ValueError, "unknown"):
            lyria.prepare(self.spec)

    def test_mp3_default_omits_generic_audio_response_format(self):
        spec = json.loads(self.spec.read_text())
        spec.pop("output_format")
        self.spec.write_text(json.dumps(spec))
        payload, metadata = lyria.prepare(self.spec)
        self.assertNotIn("response_format", payload)
        self.assertEqual(metadata["requested_format"], "mp3")

    def test_native_wav_saved_byte_exactly_and_no_acceptance_inferred(self):
        (run, receipt, matches), request = self.mocked_submit()
        request.assert_called_once()
        self.assertTrue(matches)
        self.assertEqual((run / receipt["files"][0]["file"]).read_bytes(), self.audio)
        self.assertEqual(receipt["files"][0]["sample_rate"], "44100")
        self.assertFalse(receipt["audio_accepted"])
        self.assertEqual(receipt["listening_review"], "pending")
        self.assertEqual(json.loads((run / "request.json").read_text())["response_format"],
                         {"type": "audio"})
        for path in run.iterdir():
            self.assertNotIn(b"secret-test-key", path.read_bytes())
        with self.assertRaises(FileExistsError):
            self.mocked_submit()

    def test_timeout_has_one_post_unknown_receipt_and_no_resubmission(self):
        with self.assertRaisesRegex(RuntimeError, "do not automatically resubmit"):
            self.mocked_submit(TimeoutError("do not expose secret-test-key"))
        run = self.root / ".runtime/lyria/boat-v1-a01"
        receipt = json.loads((run / "receipt.json").read_text())
        self.assertEqual(receipt["status"], "unknown")
        self.assertNotIn("secret-test-key", (run / "receipt.json").read_text())
        with self.assertRaises(FileExistsError):
            self.mocked_submit()

    def test_missing_key_or_budget_does_not_submit(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}), \
             patch.object(lyria, "request_json") as request, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(lyria.main([str(self.spec), "--submit", "--max-cost-usd", "0.08"]), 1)
        request.assert_not_called()
        with patch.object(lyria, "request_json") as request, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(lyria.main([str(self.spec), "--submit"]), 1)
        request.assert_not_called()

    def test_mp3_response_is_preserved_and_not_disguised_as_wav(self):
        # A mocked probe models a provider returning MP3 despite the WAV request.
        actual = {"container": "mp3", "codec": "mp3", "sample_rate": "44100", "channels": 2,
                  "duration_seconds": 1, "native_pcm_wav": False, "extension": "mp3"}
        with patch.object(lyria, "probe", return_value=actual):
            (run, receipt, matches), _ = self.mocked_submit()
        self.assertFalse(matches)
        self.assertEqual(receipt["status"], "completed_format_mismatch")
        self.assertEqual(receipt["files"][0]["file"], "audio-01.mp3")
        self.assertEqual((run / "audio-01.mp3").read_bytes(), self.audio)
        self.assertFalse((run / "audio-01.wav").exists())

    def test_recovery_uses_saved_response_without_network_or_key(self):
        with patch.object(lyria, "probe", side_effect=ValueError("local decode error")):
            with self.assertRaises(RuntimeError):
                self.mocked_submit()
        run = self.root / ".runtime/lyria/boat-v1-a01"
        self.assertTrue((run / "response.json").exists())
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}), \
             patch.object(lyria, "request_json") as request, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lyria.main(["--workspace", str(self.root), "--recover", str(run)]), 0)
        request.assert_not_called()
        self.assertEqual(json.loads((run / "receipt.json").read_text())["status"], "completed")

    def test_runtime_symlink_and_original_overwrite_are_refused(self):
        (self.root / ".runtime").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            lyria.private_runtime(self.root)
        path = self.root / "original.wav"
        lyria.save_original(path, self.audio)
        with self.assertRaises(ValueError):
            lyria.save_original(path, b"different")

    def test_task_worktree_and_main_share_repository_lock_root(self):
        self.assertEqual(lyria.shared_root(self.primary), lyria.shared_root(self.root))

    def test_explicit_clash_proxy_and_credential_redaction(self):
        self.assertEqual(lyria.validate_proxy("http://127.0.0.1:7897"), "http://127.0.0.1:7897")
        for bad in ("socks5://127.0.0.1:7897", "http://user:pass@127.0.0.1:7897"):
            with self.assertRaises(ValueError):
                lyria.validate_proxy(bad)
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "secret-test-key"}), \
             patch.object(lyria, "request_json", return_value=(b"{}", {})) as request, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lyria.main(["--check-api", "--proxy", "http://127.0.0.1:7897"]), 0)
        self.assertEqual(request.call_args.kwargs["proxy"], "http://127.0.0.1:7897")

    def test_authenticated_remote_proxy_uses_environment_without_exposing_credentials(self):
        proxy = "http://example.com:44445"
        self.assertEqual(lyria.validate_proxy(proxy), proxy)
        output = io.StringIO()
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key", "LYRIA_PROXY_USER": "test-user:test-password"}), \
             patch.object(lyria, "request_json", return_value=(b"{}", {})) as request, \
             contextlib.redirect_stdout(output):
            self.assertEqual(lyria.main(["--check-api", "--proxy", proxy,
                                        "--proxy-user-env", "LYRIA_PROXY_USER"]), 0)
        self.assertEqual(request.call_args.kwargs["proxy_user"], "test-user:test-password")
        self.assertNotIn("test-user", output.getvalue())
        self.assertNotIn("test-password", output.getvalue())
        encoded = base64.b64encode(b"test-user:test-password")
        self.assertEqual(lyria.redact(b"test-key test-user:test-password " + encoded,
                                    "test-key", "test-user:test-password"),
                         b"[REDACTED] [REDACTED] [REDACTED]")


if __name__ == "__main__":
    unittest.main()
