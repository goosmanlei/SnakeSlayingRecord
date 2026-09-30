import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import seed_audio


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

    def test_reference_cannot_read_outside_managed_media(self):
        for path in ('/tmp/private.wav','../../private.wav','export/assets/../private.wav'):
            with self.subTest(path=path),self.assertRaises(ValueError):
                seed_audio.payload_for({'text_prompt':'参考@音频1','references':[{'file':path,'sha256':'0'*64}]})

    def test_original_is_preserved_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as root,patch.object(seed_audio,'ROOT',Path(root)):
            raw=b'provider-original-bytes'
            original,sha=seed_audio.save_original(raw)
            self.assertEqual(original.read_bytes(),raw)
            self.assertEqual(sha,hashlib.sha256(raw).hexdigest())
            self.assertEqual(seed_audio.save_original(raw),(original,sha))
            original.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):seed_audio.save_original(raw)
            self.assertEqual(original.read_bytes(),b'corrupt')


if __name__=='__main__':unittest.main()
