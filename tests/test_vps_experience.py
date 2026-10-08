import argparse
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import tarfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import vps_experience_remote as remote


class VPSPackageBoundaryTest(unittest.TestCase):
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
