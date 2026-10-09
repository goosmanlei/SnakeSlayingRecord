import argparse
import hashlib
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
    def test_loopback_proxy_binds_only_the_actual_private_bridge(self):
        values={'REVIEW_USE_XRAY_LOOPBACK':'1','HTTPS_PROXY':'http://test-user:test-secret@127.0.0.1:9090'}
        network={'Driver':'bridge','IPAM':{'Config':[{'Subnet':'172.23.0.0/16','Gateway':'172.23.0.1'}]}}
        with patch.object(remote,'credential_values',return_value=values),patch.object(remote,'run',return_value=json.dumps([network])):
            target=remote.runtime_target()
        self.assertEqual(target['network'],'host')
        self.assertEqual(target['bind_host'],'172.23.0.1')
        self.assertEqual(target['upstream'],'http://172.23.0.1:8765')
        self.assertNotIn('test-secret',json.dumps(target))
        command=remote.runtime_command(target)
        self.assertEqual(command[command.index('--host')+1],'172.23.0.1')

    def test_proxy_credentials_and_invalid_urls_never_enter_error_messages(self):
        for proxy in ['http://test-user:test-secret@198.51.100.1:9090',
                      'http://test-user:test-secret@127.0.0.1:invalid',
                      'http://127.0.0.1:9090','https://test-user:test-secret@127.0.0.1:9090']:
            with patch.object(remote,'credential_values',return_value={'REVIEW_USE_XRAY_LOOPBACK':'1','HTTPS_PROXY':proxy}),patch.object(remote,'run') as execute:
                with self.assertRaisesRegex(ValueError,'authenticated loopback HTTP proxy') as error:remote.runtime_target()
                self.assertNotIn('test-secret',str(error.exception));execute.assert_not_called()

    def test_public_or_non_bridge_application_binding_is_rejected(self):
        values={'REVIEW_USE_XRAY_LOOPBACK':'1','HTTPS_PROXY':'http://user:pass@127.0.0.1:9090'}
        for network in [{'Driver':'host','IPAM':{'Config':[]}},
                        {'Driver':'bridge','IPAM':{'Config':[{'Subnet':'8.8.8.0/24','Gateway':'8.8.8.1'}]}},
                        {'Driver':'bridge','IPAM':{'Config':[{'Subnet':'172.23.0.0/16','Gateway':'172.24.0.1'}]}}]:
            with patch.object(remote,'credential_values',return_value=values),patch.object(remote,'run',return_value=json.dumps([network])):
                with self.assertRaises(ValueError):remote.runtime_target()

    def test_default_runtime_keeps_existing_container_network_and_local_probe(self):
        with patch.object(remote,'credential_values',return_value={}),patch.object(remote,'run') as execute:
            target=remote.runtime_target()
            self.assertEqual(target['network'],remote.NETWORK)
            self.assertEqual(target['probe_host'],'127.0.0.1')
            execute.assert_not_called()

    def test_save_config_digest_survives_different_docker_image_stores(self):
        config=json.dumps({'architecture':'amd64','config':{'Labels':{
            'org.leiguoguo.instance':'lijizhanshe','org.opencontainers.image.revision':'candidate'}}}).encode()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'image.tar.gz'
            with tarfile.open(path,'w:gz') as archive:
                for name,data in [('config.json',config),('manifest.json',json.dumps([{
                    'Config':'config.json','RepoTags':['lijizhanshe-experience:round1']}]).encode())]:
                    entry=tarfile.TarInfo(name);entry.size=len(data);archive.addfile(entry,io.BytesIO(data))
            self.assertEqual(remote.portable_image(path,'lijizhanshe-experience:round1','candidate'),
                             'sha256:'+hashlib.sha256(config).hexdigest())
            with self.assertRaisesRegex(ValueError,'revision differs'):
                remote.portable_image(path,'lijizhanshe-experience:round1','other-candidate')

    def test_unconfirmed_maintenance_cannot_clear_the_old_instance(self):
        with patch.object(remote,'clear') as clear:
            with self.assertRaisesRegex(ValueError,'maintenance must protect'):
                remote.replace({'phase':'staged','maintenance_confirmed':False})
            clear.assert_not_called()

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
                remote.credential_check()
                self.assertEqual(json.loads((control/'usage/attempts.json').read_text()),{'attempts':5})

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
