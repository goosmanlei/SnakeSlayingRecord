#!/usr/bin/env python3
"""Register this story's real first-round files in an isolated review instance.

No model calls occur here. Each receipt becomes a submitted CALL, a real ASSET,
then a completed CALL revision. Re-running refuses an existing asset rather than
silently replacing it. Batch files can be replayed after inventory.json.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

try:
    from .generation_workspace import generation_root, contained, isolated_instance
except ImportError:
    from generation_workspace import generation_root, contained, isolated_instance

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility

ROOT = Path(__file__).resolve().parents[1]


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = generation_root(args.workspace)
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk import production as p
    from review_desk.production_media import ingest
    from review_desk.store import Store
    instance = isolated_instance(ROOT, args.instance)
    if instance == ROOT or instance == ROOT.parents[2]:
        parser.error('use an isolated instance, not either story checkout')
    store = Store(instance / '.runtime/review.sqlite3')
    out = contained(ROOT, 'production/baseline-records')
    out.mkdir(parents=True, exist_ok=True)
    sequence = 0

    def read(path):
        return material_read_json(ROOT / path)

    def ref(oid):
        value = p.record(store, oid)
        return {'object_id': oid, 'revision_id': value['id']}

    def rec(oid, kind, title, body, version=0, **values):
        return {'object_id': oid, 'kind': kind, 'expected_version': version, 'payload': {
            'format': 'production-' + p.KINDS[kind] + '-v1', 'title': title,
            'blocks': [{'id': 'description', 'text': body}], **values}}

    def publish(records):
        nonlocal sequence
        document = {'format': 'production-import-v1', 'records': records}
        result = p.import_records(store, document)
        sequence += 1
        contained(ROOT, out / f'{sequence:03d}.json').write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')
        return result

    def component(path, role='original', cid='original'):
        with (ROOT / path).open('rb') as stream:
            value = ingest(instance, stream, Path(path).name)
        value.update(role=role, id=cid)
        # Keep original and metadata files in the story's managed media store too.
        destination = ROOT / 'export/assets' / value['file']
        if not destination.exists():
            destination.write_bytes((instance / 'export/assets' / value['file']).read_bytes())
        return value

    def submit_candidate(label, asset_id, title, media, prompt, model, parameters,
                         original, receipt_path, subjects, states, inputs, usage, lineage, version=0):
        receipt = read(receipt_path)
        call_id = 'call-' + label
        submission = rec(call_id, 'CALL', title + ' · 实际制作输入',
            '实际已提交的第一轮候选制作，输入保持不可变。未获用户对具体母版的接受。',
            method='generation', tool='OpenArt connector' if media=='image' else 'Doubao Voice HTTP',
            status='submitted', model=model, prompt=prompt, parameters=parameters, inputs=inputs,
            outputs=[], receipt=receipt, usage=usage, lineage=lineage)
        publish([submission])
        original_meta = component(original)
        if media=='image' and original_meta['width'] != 2016:
            raise ValueError('unexpected image dimensions; inspect the receipt before registering')
        metadata = component(receipt_path, 'metadata', 'receipt')
        body = ('文字生成候选，实际 2016×2688；请求 high/4K，但未达到原生 4K 要求。未经用户选为母版。'
                if media=='image' else '第一轮声线或演唱候选，真实 48 kHz WAV 原件；已核文件和返回字幕，尚未完成实际听审或用户接受。')
        publish([rec(asset_id, 'ASSET', title, body, version=version, media_type=media,
                     subjects=subjects, states=states, components=[original_meta, metadata],
                     production=ref(call_id), lineage=lineage, placeholder=False,
                     verification={'file_inspected':True, 'visually_inspected':media=='image',
                                   'listened':False, 'native_4k_passed':False if media=='image' else None,
                                   'user_accepted':False})])
        completed = copy.deepcopy(submission)
        completed['expected_version'] = 1
        completed['payload'].update(status='completed',outputs=[ref(asset_id)])
        completed['payload']['title'] = title + ' · 实际制作完成'
        publish([completed])
        reason = ('两次显式 4K 请求均输出 2016×2688，规格待处理；人物轮廓和用色可供首轮比较，尚未认可为母版。'
                  if media=='image' else '原件格式和返回字幕已核查；本会话不支持直接听辨，不能以字幕一致代替音色、咬字和演唱审阅。')
        publish([rec('review-'+label,'JUDGMENT',title+' · 待审说明',reason,
                     target=ref(asset_id),verdict='changes_requested' if media=='image' else 'pending',
                     actor='Codex',reason=reason)])

    try:
        if any(r['kind']=='ASSET' for r in p.current_records(store)):
            raise ValueError('candidate assets already exist; explicit revision import is required')
        for i in (1,2):
            label = f'liji-baseline-{i:02d}'
            request = read(f'production/requests/{label}.json')
            receipt_path = f'production/receipts/{label}-complete.json'
            receipt = read(receipt_path)
            submit_candidate(label,'asset-liji-image','李寄造型候选', 'image',request['params']['prompt'],
                request['model'],{**request['params'],'projectId':request['projectId']},
                'export/assets/'+receipt['component']['file'],receipt_path,
                [ref('entity-li-ji')],[ref('state-liji-paste'),ref('state-liji-water-mark')],
                [ref('production-input-screenplay04'),ref('entity-li-ji')],
                {'credits':250,'platform':'OpenArt','account_after':receipt['account_after']},
                {'i2i_depth':0,'references':[]},version=i-1)
        for label, entity, title in [
            ('aheng-voice-01','a-heng','阿蘅对白声线候选'),
            ('liji-voice-01','li-ji','李寄对白声线候选'),
            ('zhou-voice-01','zhou','周掌柜对白声线候选'),
            ('zhao-voice-01','zhao','赵执事对白声线候选'),
            ('aheng-song-01','boat-song','阿蘅舟行曲演唱候选')]:
            receipt_path = f'production/receipts/seed-{label}.json'
            receipt = read(receipt_path)
            if receipt['status']!='completed':
                raise ValueError('incomplete audio cannot be registered as a real candidate')
            inputs=[ref('production-input-screenplay04'),ref('entity-'+entity)]
            subjects=[ref('entity-'+entity)]
            if label=='aheng-song-01':
                inputs.append({**ref('asset-aheng-voice-01'),'component_id':'original'})
                subjects.append(ref('entity-a-heng'))
            submit_candidate(label,'asset-'+label,title,'audio',receipt['input']['text_prompt'],
                receipt['input']['model'],receipt['input']['audio_config'],receipt['file'],receipt_path,
                subjects,[],inputs,{'billed_seconds':receipt['original_duration'],
                                   'quota_id':receipt['quota_id']},{})
        print(json.dumps({'batches':sequence,'asset_objects':6,'asset_versions':7,'adoptions':0,'instance':str(instance)},ensure_ascii=False))
    finally:
        store.close()


if __name__=='__main__':
    main()
