"""Story clients against the real desk contract, including lost confirmations."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import creative_method as creative, method_runtime as runtime, media_method as media
try:
    from review_desk import methods, production_current as current
    from review_desk.store import Store
except ImportError:
    methods = None


class LedgerClient:
    def __init__(self, store):
        self.store = store

    def prepare(self, request):
        return methods.prepare(self.store, request)

    def read(self, ref):
        return methods.read(self.store, **ref)

    def artifact(self, execution, request, stage, output):
        return methods.artifact(self.store, {**request, 'execution': runtime.reference(execution),
                                             'stage': stage, 'output': output})

    def stage(self, execution, stage):
        return methods.stage_record(self.store, execution, stage)

    def call(self, path, value):
        from review_desk import method_media
        if path == '/api/methods/media-prepare':
            return method_media.prepare(self.store, value)
        raise ValueError('Unexpected test endpoint: ' + path)


@unittest.skipIf(methods is None, 'run with the managed desk on PYTHONPATH')
class StageRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.store = Store(self.root / 'service/.runtime/review.sqlite3')
        self.addCleanup(self.store.close)
        self.assertEqual(self.store.db.execute(
            'SELECT contract FROM production_current_policy WHERE id=1').fetchone()[0], current.CONTRACT)
        self.client = LedgerClient(self.store)
        self.folder = self.root / 'step'
        self.request = {'work_type': 'audiovisual-design', 'target': 'shot', 'run_id': 'recovery',
                        'step_id': 'one', 'inputs': {'context': {'text': '原输入🧵'}}, 'private': True}
        self.seed('audiovisual-design', ['understanding', 'principles', 'design', 'handoff', 'review'])

    def seed(self, work, steps):
        method = methods.save(self.store, {'category': 'skill', 'name': work, 'expected_version': 0,
            'payload': {'title': work, 'purpose': 'Exact original', 'applies': 'Local work', 'inputs': 'context',
                'outputs': 'Original value', 'checks': 'Read the original', 'work_types': [work],
                'required_inputs': ['context'], 'steps': steps,
                'files': {'SKILL.md': '---\nname: recovery\ndescription: Preserve original values\n---\nRead the exact source.'}, 'resources': []}})
        methods.save(self.store, {'category': 'binding', 'name': work, 'expected_version': 0,
            'payload': {'work_type': work, 'rules': [{**runtime.reference(method), 'when': {}}]}})

    def begin(self):
        return creative.begin(self.client, self.folder, self.request)

    def test_original_unicode_json_types_and_real_cross_stage_revision(self):
        self.begin()
        outputs = ['第一行\r\n第二行🧵\n', {'flag': True, 'number': 1, 'none': None, 'array': [False, '一']},
                   {'design': '草稿'}, {'design': '真实修订'}, {'assessment': '检查了实际差异'}]
        for stage, output in zip(['understanding', 'principles', 'design', 'handoff', 'review'], outputs):
            artifact = creative.record(self.client, self.folder, stage, output)
            self.assertEqual(runtime.checksum(creative.read_stage(self.client, self.folder, stage)), runtime.checksum(output))
            self.assertEqual(artifact['payload']['output']['sha256'], runtime.checksum(output))
            self.assertNotEqual(artifact['payload']['output_sha256'], runtime.checksum(output))
        with self.assertRaisesRegex(ValueError, '同阶段'):
            creative.record(self.client, self.folder, 'understanding', 'changed')
        path = self.root / 'crlf.md'; path.write_bytes('原行\r\n第二行🧵\n'.encode('utf-8'))
        self.assertEqual(runtime.read_text_value(path), '原行\r\n第二行🧵\n')
        runtime.save_text(self.root / 'crlf-delivered.md', runtime.read_text_value(path))
        runtime.save_text(self.root / 'crlf-delivered.md', runtime.read_text_value(path))
        self.assertEqual((self.root / 'crlf-delivered.md').read_bytes(), path.read_bytes())

    def test_response_lost_then_client_restarts_retrieves_one_existing_artifact(self):
        self.begin()
        original = self.client.artifact
        def accepted_then_disconnected(*args):
            original(*args)
            raise OSError('response lost after commit')
        with patch.object(self.client, 'artifact', accepted_then_disconnected), self.assertRaises(OSError):
            creative.record(self.client, self.folder, 'understanding', '原正文\n')
        self.assertTrue((self.folder / 'stage-understanding-value.json').exists())
        self.assertFalse((self.folder / 'stage-understanding.json').exists())
        self.assertEqual(creative.read_stage(LedgerClient(self.store), self.folder, 'understanding'), '原正文\n')
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM objects WHERE id LIKE 'method.artifact.%'").fetchone()[0], 1)

    def test_atomic_product_and_confirmation_interruptions_never_publish_partial_file(self):
        self.begin()
        real_link = runtime.os.link
        def interrupted(source, target):
            if str(target).endswith('stage-understanding-value.json'):
                raise OSError('interrupted value publication')
            return real_link(source, target)
        with patch.object(runtime.os, 'link', interrupted), self.assertRaises(OSError):
            creative.record(self.client, self.folder, 'understanding', 'exact')
        self.assertFalse((self.folder / 'stage-understanding-value.json').exists())
        self.assertIsNone(self.client.stage(runtime.reference(self.begin()['execution']), 'understanding')['artifact'])
        def interrupted_receipt(source, target):
            if str(target).endswith('stage-understanding.json'):
                raise OSError('interrupted confirmation publication')
            return real_link(source, target)
        with patch.object(runtime.os, 'link', interrupted_receipt), self.assertRaises(OSError):
            creative.record(self.client, self.folder, 'understanding', 'exact')
        self.assertEqual(creative.recover(LedgerClient(self.store), self.folder, 'understanding'), 'exact')

    def test_missing_fulltext_adoption_and_tamper_preserve_original_files(self):
        self.begin(); creative.record(self.client, self.folder, 'understanding', 'original')
        raw = self.folder / 'stage-understanding-value.json'; raw.unlink()
        with self.assertRaisesRegex(ValueError, '全文缺失'):
            creative.read_stage(self.client, self.folder, 'understanding')
        with self.assertRaisesRegex(ValueError, '摘要不符'):
            creative.recover(self.client, self.folder, 'understanding', 'wrong')
        self.assertFalse(raw.exists())
        self.assertEqual(creative.recover(self.client, self.folder, 'understanding', 'original'), 'original')
        value = json.loads(raw.read_text()); value['output'] = 'tampered'; raw.write_text(json.dumps(value))
        before = raw.read_bytes()
        with self.assertRaisesRegex(ValueError, '摘要或'):
            creative.read_stage(self.client, self.folder, 'understanding')
        self.assertEqual(raw.read_bytes(), before)

    def test_unconfirmed_is_not_finished_and_prior_stage_is_enforced(self):
        self.begin()
        with self.assertRaises(ValueError):
            creative.record(self.client, self.folder, 'design', 'pending')
        with self.assertRaisesRegex(ValueError, '尚未获服务确认'):
            creative.read_stage(self.client, self.folder, 'design')
        with self.assertRaisesRegex(ValueError, '归属'):
            value = json.loads((self.folder / 'stage-design-value.json').read_text())
            value['stage'] = 'understanding'
            (self.folder / 'stage-design-value.json').write_text(json.dumps(value))
            creative.recover(self.client, self.folder, 'design')

    def test_method_binding_changes_keep_original_and_input_condition_drift_fails(self):
        delivery = self.begin()
        method = methods.read(self.store, delivery['execution']['payload']['package']['method']['object_id'])
        payload = copy.deepcopy(method['payload']); payload['files']['SKILL.md'] += '\nnew rule'
        updated = methods.save(self.store, {'category': 'skill', 'name': 'audiovisual-design', 'expected_version': 1, 'payload': payload})
        methods.save(self.store, {'category': 'binding', 'name': 'audiovisual-design', 'expected_version': 1,
            'payload': {'work_type': 'audiovisual-design', 'rules': [{**runtime.reference(updated), 'when': {}}]}})
        self.assertEqual(self.begin(), delivery)
        for key, changed in [('inputs', {'context': 'changed'}), ('conditions', {'new': True}), ('target', 'other')]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, '恢复请求'):
                creative.begin(self.client, self.folder, {**self.request, key: changed})

    def test_legacy_full_service_output_and_assessment_without_local_value(self):
        self.seed('novel-writing', ['result'])
        request = {**self.request, 'work_type': 'novel-writing'}
        folder = self.root / 'legacy'
        delivery = creative.begin(self.client, folder, request)
        artifact = self.client.artifact(delivery['execution'], delivery['request'], 'result', '旧完整正文')
        runtime.save_json(folder / 'stage-result.json', artifact)
        self.assertEqual(creative.read_stage(self.client, folder, 'result'), '旧完整正文')
        self.begin(); creative.record(self.client, self.folder, 'understanding', {'assessment': '真实原评价'})
        (self.folder / 'stage-understanding-value.json').unlink()
        self.assertEqual(creative.read_stage(self.client, self.folder, 'understanding'), {'assessment': '真实原评价'})

    def test_begin_response_loss_and_partial_method_delivery_resume_original(self):
        original = self.client.prepare
        def lost(request):
            original(request)
            raise OSError('lost begin response')
        with patch.object(self.client, 'prepare', lost), self.assertRaises(OSError):
            self.begin()
        self.assertTrue((self.folder / 'begin-request.json').exists())
        self.assertFalse((self.folder / 'delivery.json').exists())
        delivery = self.begin()
        (self.folder / 'SKILL.md').unlink()
        self.assertEqual(self.begin(), delivery)
        self.assertTrue((self.folder / 'SKILL.md').exists())

    def test_path_symlink_escape_and_output_collision_are_rejected(self):
        self.begin(); outside = self.root / 'outside'; outside.mkdir()
        (self.folder / 'stage-understanding-value.json').symlink_to(outside / 'file')
        with self.assertRaisesRegex(ValueError, '符号链接'):
            creative.record(self.client, self.folder, 'understanding', 'wrong')
        self.assertFalse((outside / 'file').exists())
        with self.assertRaisesRegex(ValueError, '越界'):
            media.export_result(self.folder, self.folder / '..' / 'escaped.json', {})

    def test_text_layer_full_body_survives_client_stages_and_lost_confirmation(self):
        self.seed('media-plan', ['draft', 'review', 'result'])
        base = methods.read(self.store, 'method.skill.media-plan')
        skill = methods.save(self.store, {'category': 'skill', 'name': 'text-layer',
            'expected_version': 0, 'payload': base['payload']})
        methods.save(self.store, {'category': 'binding', 'name': 'media-plan',
            'expected_version': 1, 'payload': {'work_type': 'media-plan',
                'rules': [{**runtime.reference(skill), 'when': {'material_category': 'text-layer'}}]}})
        record = {'object_id': 'text', 'kind': 'REQUIREMENT', 'expected_version': 0,
            'payload': {'media_type': 'project', 'material_category': 'text-layer',
                'purpose': '同页两笔工钱', 'blocks': [{'id': 'title', 'text': '一日两升'}],
                'specification': {'delivery': 'SVG', 'tracking': 'same page'}}}
        delivery = media.begin(self.client, self.folder, record, 'recovery', 'text')
        original = self.client.artifact
        def lost(*args):
            original(*args)
            raise OSError('response lost after text draft commit')
        with patch.object(self.client, 'artifact', lost), self.assertRaises(OSError):
            media.stage(self.client, self.folder, 'draft', record=record)
        draft = media.read_stage(self.client, self.folder, 'draft')
        self.assertEqual(draft['record'], record)
        media.stage(self.client, self.folder, 'review', review='保留约定标题，两笔工钱不是三笔。')
        final = copy.deepcopy(record)
        final['payload']['blocks'].append({'id': 'wages', 'text': '两升；两升'})
        media.stage(self.client, self.folder, 'result', record=final)
        result = media.read_stage(self.client, self.folder, 'result')
        self.assertEqual(result['record']['payload']['blocks'], final['payload']['blocks'])
        self.assertNotIn('generation', result['record']['payload'])
        artifact = self.client.stage(runtime.reference(delivery['execution']), 'result')['artifact']
        self.assertEqual(artifact['payload']['output']['text_layer_sha256'],
                         runtime.checksum(result['output']['text_layer']))


if __name__ == '__main__':
    unittest.main()
