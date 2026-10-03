import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import seed_audio
from generation_fixtures import make_worktree, git


class SeedAudioSafetyTest(unittest.TestCase):
    def setUp(self):
        self.quota={'id':'observed','model':'seed-audio-1.0','service_status':'已开通','remaining_seconds':300}

    def test_unknown_and_submitted_calls_keep_full_reservations(self):
        receipts=[{'quota_id':'observed','status':'unknown'},
                  {'quota_id':'observed','status':'submitted'},
                  {'quota_id':'observed','status':'completed','original_duration':17},
                  {'quota_id':'observed','status':'rejected'},
                  {'quota_id':'another-snapshot','status':'completed','original_duration':80}]
        self.assertEqual(seed_audio.remaining_allowance(self.quota,receipts),43)
        self.assertLess(seed_audio.remaining_allowance(self.quota,receipts),120)

    def test_corrupt_billing_cannot_expand_available_credit(self):
        for bad in (-1,0,float('nan'),float('inf'),'12',None):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                seed_audio.remaining_allowance(self.quota,[{'quota_id':'observed','status':'completed','original_duration':bad}])

    def test_quota_counts_other_worktrees_and_deduplicates_committed_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            main, task = make_worktree(directory)
            other = main.parent / 'other'
            git(main, 'worktree', 'add', '-qb', 'other', str(other))
            completed = {'request_id':'one','quota_id':'observed','status':'completed','original_duration':20}
            pending = {'request_id':'two','quota_id':'observed','status':'submitted'}
            for root, data in ((main, completed), (task, completed), (other, pending)):
                folder = root / 'production/receipts'
                folder.mkdir(parents=True)
                (folder/'seed-test.json').write_text(json.dumps(data))
            self.assertEqual(seed_audio.remaining_allowance(self.quota,seed_audio.quota_receipts(task)),160)
            # Stale submitted copies cannot release a reservation early.
            completed['status'] = 'submitted'
            (task/'production/receipts/seed-test.json').write_text(json.dumps(completed))
            self.assertEqual(seed_audio.remaining_allowance(self.quota,seed_audio.quota_receipts(task)),60)

    def test_reference_cannot_read_outside_managed_media(self):
        for path in ('/tmp/private.wav','../../private.wav','export/assets/../private.wav'):
            with self.subTest(path=path),self.assertRaises(ValueError):
                seed_audio.payload_for({'text_prompt':'参考@音频1','references':[{'file':path,'sha256':'0'*64}]})

    def test_original_is_preserved_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            _, root = make_worktree(directory)
            with patch.object(seed_audio, 'ROOT', root):
                raw=b'provider-original-bytes'
                original,sha=seed_audio.save_original(raw)
                self.assertEqual(original.read_bytes(),raw)
                self.assertEqual(sha,hashlib.sha256(raw).hexdigest())
                self.assertEqual(seed_audio.save_original(raw),(original,sha))
                original.write_bytes(b'corrupt')
                with self.assertRaises(ValueError):seed_audio.save_original(raw)
                self.assertEqual(original.read_bytes(),b'corrupt')


if __name__=='__main__':unittest.main()
