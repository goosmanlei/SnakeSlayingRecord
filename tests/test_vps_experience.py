import argparse
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import tarfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import vps_experience_remote as remote


class VPSPackageBoundaryTest(unittest.TestCase):
    def test_unusable_credentials_are_rejected_without_disclosing_values(self):
        with tempfile.TemporaryDirectory() as folder:
            control=Path(folder).resolve();credentials=control/'credentials.env';credentials.touch(mode=0o600)
            with patch.object(remote,'CONTROL',control):
                for content in ['OPENAI_API_KEY=\nREVIEW_POLISH_MAX_ATTEMPTS=5\n',
                                'OPENAI_API_KEY=test-only-secret\nREVIEW_POLISH_MAX_ATTEMPTS=0\n',
                                'OPENAI_API_KEY=test-only-secret\nOPENAI_API_KEY=duplicate\nREVIEW_POLISH_MAX_ATTEMPTS=5\n']:
                    credentials.write_text(content)
                    with self.assertRaises(ValueError) as error:remote.credential_check()
                    self.assertNotIn('test-only-secret',str(error.exception))
                credentials.write_text('OPENAI_API_KEY=test-only-secret\nREVIEW_POLISH_MAX_ATTEMPTS=5\n')
                remote.credential_check()
                (control/'usage').mkdir();(control/'usage/attempts.json').write_text('{"attempts":5}')
                with self.assertRaisesRegex(ValueError,'exhausted'):remote.credential_check()

    def test_changed_shared_nginx_mount_is_rejected_before_any_write(self):
        nginx={'State':{'Running':True},'Mounts':[],'NetworkSettings':{'Networks':{remote.NETWORK:{}}},'Id':'shared-nginx'}
        def execute(*args):
            if args[:2]==('docker','info'):return '2\n'
            if args[:2]==('docker','inspect'):return json.dumps([nginx])
            self.fail('no shared-service mutation is allowed before mount validation')
        with patch.object(remote.os,'uname') as uname,patch.object(Path,'read_text',return_value='MemAvailable: 2097152 kB\nSwapFree: 2097152 kB\n'),patch.object(remote,'run',side_effect=execute):
            uname.return_value.machine='x86_64'
            with self.assertRaisesRegex(ValueError,'mount boundary'):remote.preflight()

    def test_incomplete_upload_is_rejected_before_old_instance_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();control=root/'control';target=root/'www/lijizhanshe'
            package=control/'incoming/round1/bundle.tar';package.parent.mkdir(parents=True)
            package.write_bytes(b'incomplete upload');target.mkdir(parents=True);old=target/'old-experience';old.write_text('keep until new package is valid')
            with patch.object(remote,'CONTROL',control),patch.object(remote,'TARGET',target),patch.object(remote,'run') as run:
                with self.assertRaisesRegex(ValueError,'checksum differs'):
                    remote.stage(argparse.Namespace(publication='round1',sha256='0'*64))
                self.assertEqual(old.read_text(),'keep until new package is valid');run.assert_not_called()

    def test_unsafe_archive_cannot_escape_staging_or_touch_old_instance(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();control=root/'control';target=root/'www/lijizhanshe';target.mkdir(parents=True)
            package=control/'incoming/round1/bundle.tar';package.parent.mkdir(parents=True)
            with tarfile.open(package,'w') as archive:
                entry=tarfile.TarInfo('../escaped');entry.size=4;archive.addfile(entry,io.BytesIO(b'evil'))
            with patch.object(remote,'CONTROL',control),patch.object(remote,'TARGET',target),patch.object(remote,'run') as run:
                with self.assertRaisesRegex(ValueError,'unsafe package'):
                    remote.stage(argparse.Namespace(publication='round1',sha256=remote.sha(package)))
                self.assertFalse((package.parent/'escaped').exists());self.assertTrue(target.is_dir());run.assert_not_called()

    def test_symlink_target_is_not_a_deletion_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();real=root/'other-site';real.mkdir();link=root/'lijizhanshe';link.symlink_to(real)
            with self.assertRaisesRegex(ValueError,'symlink boundary'):remote.safe(link)
            self.assertTrue(real.is_dir())
