#!/usr/bin/env python3
"""Bind the four originals explicitly approved in this task's conversation.

This records an existing user decision; it never infers one or clicks adoption.
Run once against a fresh isolated copy of the current formal database.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def ref(row):
    return {'object_id': row['object_id'], 'revision_id': row['id']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    args = parser.parse_args()
    instance = args.instance.resolve()
    if ROOT / '.runtime' not in instance.parents:
        parser.error('use an isolated instance under this task worktree .runtime')
    folder = ROOT / 'production/full-generation'
    output = folder / 'binding-registration.json'
    if output.exists():
        parser.error('binding already prepared; inspect its exact revisions before continuing')
    decision = read(folder / 'master-approvals.json')
    assert decision['user_reply'] == '1. 认可\n2. 不补'
    assert decision['voice_scope']['new_generation_count'] == 42
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk import production as p
    from review_desk.store import Store
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        rows = p.current_records(store)
        by = {row['object_id']: row for row in rows}
        heads = {oid: row['id'] for oid, row in by.items()}
        recipes = read(folder / 'recipes.json')
        bindings, judgments, records = {}, [], []
        for item in decision['masters']:
            asset = p.ref_record(store, item['asset'], {'ASSET'})
            original = next(c for c in asset['payload']['components'] if c['id'] == 'original')
            assert original['sha256'] == item['sha256']
            assert hashlib.sha256((ROOT / item['file']).read_bytes()).hexdigest() == item['sha256']
            selected = {'reference': item['asset'], 'component_id': 'original', 'sha256': item['sha256']}
            if item['media_type'] == 'audio':
                selected['range'] = {'start_seconds': 0, 'end_seconds': original['duration_seconds']}
            else:
                assert asset['payload']['lineage']['i2i_depth'] == 0
                selected['crop'] = {'x': 0, 'y': 0, 'width': 1, 'height': 1}
            selected['use'] = '用户已认可的准确母版完整原件；保持身份，不从候选排序推定采用。'
            bindings[item['key']] = selected
            judgments.append({'object_id': item['judgment_id'], 'kind': 'JUDGMENT', 'expected_version': 0,
                'payload': {'format': 'production-judgment-v1', 'title': item['title'] + ' · 用户母版认可',
                    'blocks': [{'id': 'decision', 'text': '用户在审阅入口及准确原件清单后回复“1. 认可”。本结论只针对该原件作为母版；不代表其他身份、派生候选、镜头采用或任务完成。'}],
                    'target': item['asset'], 'verdict': 'accepted', 'actor': 'user',
                    'reason': '本任务会话明确认可代表母版：1. 认可；2. 不补。',
                    'review_type': 'generation_master', 'task': decision['task'],
                    'evidence': {'source': 'user_conversation', 'reply': decision['user_reply'],
                        'recorded_at': decision['recorded_at'], 'file_sha256': item['sha256'],
                        'audio_review': '用户针对听审请求回复认可；Codex未独立听辨' if item['media_type'] == 'audio' else None}}})

        def bind_need(oid, selection, prompt=None, params=None):
            row = by[oid]; payload = deepcopy(row['payload'])
            payload['generation']['inputs'] = [deepcopy(selection)]
            payload['generation']['blockers'] = []
            if prompt is not None:
                payload['generation']['prompt'] = prompt
            if params is not None:
                payload['generation']['parameters'] = params
            records.append({'object_id': oid, 'kind': 'REQUIREMENT', 'expected_version': row['version'], 'payload': payload})

        suffixes = {'form-a-heng-hoarse': 'aheng-hoarse', 'form-a-heng-later': 'aheng-later',
                    'form-a-heng-tears': 'aheng-tears', 'form-a-heng-wet': 'aheng-wet',
                    'form-a-heng-wet-shoes': 'aheng-wet-shoes', 'form-old-lantern-lit': 'lantern-lit'}
        requests = []
        for recipe in recipes['images']:
            if recipe['id'] not in suffixes:
                continue
            key = 'aheng_image' if recipe['entity']['object_id'] == 'entity-a-heng' else 'lantern_image'
            selection = deepcopy(bindings[key]); selection['use'] = '参考图1：用户认可的干净根母版完整原图；固定身份、轮廓、配色、笔触与构图，仅改变本状态明确部位。'
            master = next(m for m in decision['masters'] if m['key'] == key)
            receipt = read(ROOT / ('production/receipts/' + master['call_label'] + '-connector-complete.json'))
            resource = receipt['resources'][0]
            visual = {'type': 'image', 'id': resource['id'], 'url': resource['url'], 'label': '参考图1'}
            prompt = recipe['generation']['prompt']
            prompt = prompt.replace('无纸张颗粒、脏噪点、浮雕肌理、过锐边缘、密集纹理或摄影皮肤；高质量用于干净边缘与稳定比例。',
                '以参考图1已获用户认可的轻水彩质感为准；不加重纸纹、颗粒、锐化或衣料细纹，高质量用于稳定身份与比例。')
            if recipe['id'] == 'form-a-heng-tears':
                prompt += '\n只画阿蘅的完整身体，以轻微侧倾表现准备靠向身旁李绡肩的姿态；李绡在画外，不绘制未绑定身份的第二个人。取消母版中的书和米袋，让手自然放松，保留衣着、发式与全身比例。泪痕清楚但克制。'
            elif recipe['id'] in ('form-a-heng-hoarse', 'form-a-heng-later', 'form-a-heng-wet-shoes'):
                prompt += '\n这是同一人物独立完整状态参考。取消母版中的书和米袋，不添加其他物件；嗓音本身不能画成伤口，用轻微姿态表达，衣服所有干湿部位严格遵守本张完整形态。'
            elif recipe['id'] == 'form-a-heng-wet':
                prompt += '\n保留怀中同一本捞起的书；取消米袋。把两袖放至手腕使湿深色范围可辨，肘以下、膝下及下摆湿深，脸和发型保持基准，不画整身落水、发烧或新伤。'
            params = deepcopy(recipe['generation']['parameters'])
            recipe['generation'].update(prompt=prompt, inputs=[selection], blockers=[])
            recipe['execution'].update(binding_status='bound_approved_master', reference_bindings=[{**selection, 'provider_input': visual}],
                master_approval={'object_id': master['judgment_id'], 'revision_id': '@' + master['judgment_id']})
            bind_need(recipe['requirement']['object_id'], selection, prompt, params)
            label = 'fg3-' + suffixes[recipe['id']] + '-image-01'
            requests.append({'id': label, 'recipe_id': recipe['id'], 'entity': recipe['entity'], 'state': recipe['state'],
                'requirement': recipe['requirement'], 'source_lock_sha256': recipes['source_lock_sha256'],
                'master_approval': deepcopy(recipe['execution']['master_approval']), 'references': [selection],
                'lineage': {'i2i_depth': 1, 'references': [master['asset']]},
                'request': {'projectId': recipe['execution']['project_id'], 'model': recipe['generation']['model'],
                    'mode': 'image2image', 'params': {**params, 'prompt': prompt, 'visualReferences': [visual]}}})
        for recipe in recipes['voices']:
            if recipe['identity'] not in ('a-heng', 'zhou'):
                continue
            key = 'aheng_voice' if recipe['identity'] == 'a-heng' else 'zhou_voice'
            master = next(m for m in decision['masters'] if m['key'] == key)
            selection = deepcopy(bindings[key])
            for state in recipe['coverage']:
                oid = 'need-' + state['object_id'] + '-voice'
                if by[oid]['payload']['generation']['method'] == 'reuse' and recipe['kind'] == 'base':
                    bind_need(oid, selection)
                elif recipe['kind'] == 'supplement' and by[oid]['payload']['generation']['method'] == 'generate':
                    bind_need(oid, {**selection, 'use': '@音频1：用户认可的阿蘅基础母版完整14.50秒；保留同一声音身份，只改变本项声音状态。'})
            if recipe['kind'] == 'supplement':
                reference = {'number': 1, 'file': master['file'], 'sha256': master['sha256'],
                    'asset': master['asset'], 'component_id': 'original', 'range': selection['range'],
                    'use': '@音频1：已认可的阿蘅基础声音完整原件'}
                recipe['generation']['references'] = [reference]
                recipe['execution']['binding_status'] = 'bound_approved_master'
                requests.append({'id': 'fg3-' + recipe['id'].removeprefix('voice-') + '-voice-01', 'recipe_id': recipe['id'],
                    'text_prompt': recipe['generation']['prompt'], 'references': [reference],
                    'source_lock_sha256': recipes['source_lock_sha256'],
                    'master_approval': {'object_id': master['judgment_id'], 'revision_id': '@' + master['judgment_id']}})
            else:
                recipe['execution']['approved_master'] = {**selection, 'file': master['file']}

        batch = {'format': 'production-import-v1', 'expected_heads': heads, 'records': judgments + records}
        p.import_records(store, batch, validate_only=True)
        p.import_records(store, batch)
        def resolve(value):
            if isinstance(value, dict):
                if str(value.get('revision_id', '')).startswith('@'):
                    value['revision_id'] = p.record(store, value['object_id'])['id']
                for child in value.values(): resolve(child)
            elif isinstance(value, list):
                for child in value: resolve(child)
        for request in requests:
            if 'requirement' in request: request['requirement'] = ref(p.record(store, request['requirement']['object_id']))
            resolve(request)
            path = ROOT / 'production/requests' / (request['id'] + '.json')
            assert not path.exists(), 'never overwrite an execution request'
            write(path, request)
        resolve(recipes)
        for item in recipes['images']:
            if item['id'] in suffixes: item['requirement'] = ref(p.record(store, item['requirement']['object_id']))
        recipes.update(stage='approved_masters_bound', user_master_acceptances=decision['masters'],
            voice_scope_status='已按用户“不补”锁定40基础音色加2声音变化；76状态关联、34复用。两处已识别发声作为用户明确排除项保留，不补实体、状态或调用。',
            voice_scope_decision=decision['voice_scope'], excluded_voice_scope=recipes['pending_voice_scope'], pending_voice_scope=[])
        write(folder / 'recipes.json', recipes)
        write(output, {'format': 'full-generation-registration-v1', 'batches': [batch],
            'user_master_decisions': [r['object_id'] for r in judgments],
            'summary': {'new_assets': 0, 'new_calls': 0, 'user_master_acceptances': 4, 'bound_plans': len(records)}})
        print(json.dumps({'approved_masters': 4, 'bound_plans': len(records), 'prepared_requests': len(requests)}, ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    main()
