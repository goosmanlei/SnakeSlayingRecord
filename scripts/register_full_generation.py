#!/usr/bin/env python3
"""Prepare incremental full-story plans and register real representative outputs.

Writes only a new/recovered isolated instance. Publication uses the resulting
exact batches through the shared importer, never replaces a live database.
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def reference(row):
    return {'object_id': row['object_id'], 'revision_id': row['id']}


def image_spec(old):
    result = deepcopy(old)
    for key in ('minimum_long_edge', 'minimum_width', 'minimum_height'):
        result.pop(key, None)
    result.update(native_4k=False, native_resolution_policy='highest_provider_native',
                  reference_role='overall', task='task-20261002-0003')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    args = parser.parse_args()
    instance = args.instance.resolve()
    if ROOT not in instance.parents or '.runtime' not in instance.relative_to(ROOT).parts:
        parser.error('registration preparation requires an isolated instance under this worktree .runtime')
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk import production as p
    from review_desk.production_media import ingest
    from review_desk.store import Store
    recipes = read(ROOT / 'production/full-generation/recipes.json')
    source_lock = read(ROOT / 'production/full-generation/source-lock.json')
    qa = read(ROOT / 'production/full-generation/representative-review.json')
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        rows = p.current_records(store); by = {r['object_id']: r for r in rows}
        guards = {r['object_id']: r['revision_id'] for r in source_lock['formal_heads']}
        for oid, rid in guards.items():
            if p.record(store, oid)['id'] != rid:
                raise ValueError('input changed; reread and review delta: ' + oid)
        records = []
        def append(oid, payload):
            old = by.get(oid)
            records.append({'object_id': oid, 'kind': 'REQUIREMENT',
                            'expected_version': old['version'] if old else 0, 'payload': payload})
            return {'object_id': oid, 'revision_id': '@' + oid}
        image_needs = {}
        for recipe in sorted(recipes['images'], key=lambda i: (not i['is_baseline'], i['id'])):
            oid = recipe['requirement']['object_id']; old = by[oid]['payload']; payload = deepcopy(old)
            plan = deepcopy(recipe['generation'])
            if not recipe['is_baseline']:
                plan['inputs'][0]['reference'] = image_needs[recipe['baseline_state']['object_id']]
            payload['generation'] = plan
            payload['specification'] = image_spec(old['specification'])
            payload['preparation_task'] = 'task-20261002-0003'
            payload['plan_source_sha256'] = recipes['source_lock_sha256']
            image_needs[recipe['id']] = append(oid, payload)
        voice_needs = {}
        roots = {}
        for recipe in recipes['voices']:
            coverage = recipe['coverage']
            # Existing first-episode slots retain their object identity.
            preferred = {'a-heng':'form-a-heng-blue','li-ji':'form-li-ji-paste','li-dan':'form-li-dan-work'}
            root_state = next((s for s in coverage if s['object_id'] == preferred.get(recipe['identity'])), coverage[0])
            ordered = [root_state] + [s for s in coverage if s != root_state]
            for index, state in enumerate(ordered):
                if recipe['identity'].startswith('temple-crowd-'):
                    slot = 'voice-' + recipe['identity'].removeprefix('temple-crowd-')
                else:
                    slot = 'overall' if recipe['identity'] == 'offscreen-caller' else 'voice'
                oid = 'need-' + state['object_id'] + '-' + slot
                old = by.get(oid)
                plan = {'format':'generation-plan-v1','method':'generate','model':'seed-audio-1.0',
                    'parameters':deepcopy(recipe['generation']['parameters']),
                    'prompt':recipe['generation']['prompt'],'inputs':[],
                    'output':{'name':recipe['title'], 'description':recipe['direction'],
                        'review_criteria':['实际听辨定稿原句和声音身份，字幕仅为辅助','干净单人录音，无音乐或他人声','48 kHz WAV，登记实际声道、编码、时长','准确母版获用户认可后才供派生；不把试读当剧情新增对白']},
                    'blockers':[]}
                if index:
                    plan.update(method='reuse',prompt='复用同一说话身份的准确音色原件，不发起新调用。'+recipe.get('reuse_reason',recipe.get('reason','')),
                                inputs=[{'reference':roots[recipe['id']], 'use':'取得用户认可后绑定此声音母版或状态补充的完整原件；不自动采用最新候选。'}],
                                blockers=['待准确母版获认可并绑定原件组成、SHA-256与片段。'])
                elif recipe['kind'] == 'supplement':
                    plan['inputs'] = [{'reference':roots['voice-a-heng-base'], 'use':'@音频1，用户认可的阿蘅基础母版完整原件，不超过30秒；固定同一说话身份。'}]
                    plan['blockers'] = ['等待阿蘅准确基础母版获认可并绑定。']
                payload = deepcopy(old['payload']) if old else {'format':'production-requirement-v1'}
                payload.update(title=by[state['object_id']]['payload']['title']+' · '+recipe['title'],
                    blocks=[{'id':'purpose','text':recipe['sample_policy']+'\n'+recipe.get('reuse_reason',recipe.get('reason',''))}],
                    scope=state, slot=slot, required=True, purpose=recipe['title'], media_type='audio', usage='generation_input',
                    entities=[recipe['entity']],states=[state],generation=plan,
                    specification={'minimum_sample_rate':48000,'reference_role':'overall' if slot=='overall' else 'detail','audio_role':'voice_reference'},
                    sources=list({json.dumps(s['source'],sort_keys=True):s['source'] for s in recipe['samples']}.values()),
                    voice_identity=recipe['identity'], preparation_task='task-20261002-0003',
                    sample_policy=recipe['sample_policy'], samples=recipe['samples'], plan_source_sha256=recipes['source_lock_sha256'])
                saved = append(oid,payload)
                voice_needs.setdefault(recipe['id'],[]).append(saved)
                if index == 0: roots[recipe['id']] = saved
        document = {'format':'production-import-v1','expected_heads':guards,'records':records}
        p.import_records(store,document,validate_only=True)
        p.import_records(store,document)
        batches=[document]
        media_records=[]
        def actual_ref(oid): return reference(p.record(store,oid))
        def media_component(path,cid,role):
            with path.open('rb') as f: component=ingest(instance,f,path.name)
            component.update(id=cid,role=role)
            with path.open('rb') as f: assert ingest(ROOT,f,path.name)['sha256']==component['sha256']
            return component
        def record(oid,kind,payload,version=0):
            return {'object_id':oid,'kind':kind,'expected_version':version,'payload':{'format':'production-'+p.KINDS[kind]+'-v1',**payload}}
        outputs=[]
        for item in qa['items']:
            label=item['id']; media=item['media_type']; req=read(ROOT / ('production/requests/'+label+'.json'))
            if media=='image':
                receipt_path=ROOT / ('production/receipts/'+label+'-connector-complete.json');receipt=read(receipt_path)
                assert receipt['status']=='COMPLETED' and receipt['prompt']==req['request']['params']['prompt']
                prompt=req['request']['params']['prompt']; model=req['request']['model']; params={**req['request']['params'],'projectId':req['request']['projectId'],'mode':req['request']['mode']}
                needs=[actual_ref(req['requirement']['object_id'])];states=[req['state']];entity=req['entity'];lineage={'i2i_depth':0,'references':[]}
                usage={'quoted_credits':item['quoted_credits'],'actual_batch_credit_delta':1065,'allocation':'per-call quoted cost; provider receipt has no per-call billed field','batch_before':9979,'batch_after':8914}
                original=ROOT/item['file']
            else:
                receipt_path=ROOT / ('production/receipts/seed-'+label+'.json');receipt=read(receipt_path)
                assert receipt['status']=='completed' and receipt['input']['text_prompt']==req['text_prompt']
                prompt=receipt['input']['text_prompt']; model=receipt['input']['model'];params={k:v for k,v in receipt['input'].items() if k not in ('text_prompt','references','model')}
                recipe=next(v for v in recipes['voices'] if v['id']==req['recipe_id'])
                needs=[actual_ref(n['object_id']) for n in voice_needs[recipe['id']]]
                states=recipe['coverage'];entity=recipe['entity'];lineage={};original=ROOT/receipt['file']
                usage={'original_duration_seconds':receipt['original_duration'],'quota_id':receipt['quota_id'],'billing':'recorded output duration; final provider balance may lag'}
            call_id='call-'+label;asset_id='asset-'+label
            call=record(call_id,'CALL',{'title':item['title']+' · 实际输入','blocks':[{'id':'description','text':'依据用户本任务授权生成代表候选。尚未获得用户母版认可；本次登记不创建采纳或镜头采用。'}],
                'method':'generation','tool':'OpenArt connector' if media=='image' else 'Doubao Speech HTTP', 'status':'submitted',
                'model':model,'prompt':prompt,'parameters':params,'inputs':[entity,*states], 'outputs':[],
                'prepared_plan':needs[0],'request_file_sha256':hashlib.sha256((ROOT/('production/requests/'+label+'.json')).read_bytes()).hexdigest(),
                'receipt':receipt,'usage':usage,'lineage':lineage,'authorization':'用户 task-20261002-0003 执行指令；不是页面采纳记录。'})
            components=[media_component(original,'original','original'), media_component(receipt_path,'receipt','metadata'),
                        media_component(ROOT/('production/requests/'+label+'.json'),'request','metadata')]
            coverage=[{'state':s,'role':'overall' if media=='image' else 'detail','component_id':'original',
                       'detail':item['title'],'text':item['review']} for s in states]
            asset=record(asset_id,'ASSET',{'title':item['title'],'blocks':[{'id':'description','text':item['review']}],
                'media_type':media,'subjects':[entity],'states':states,'components':components,
                'production':{'object_id':call_id,'revision_id':'@'+call_id}, 'lineage':lineage,'placeholder':False,
                'verification':{'file_inspected':True,'visually_inspected':media=='image','listened':False,'user_accepted':False,
                    'self_review_status':item['self_review_status'],'reviewer':'Codex (图像目视/文件和字幕核对；未听辨)'},
                'state_coverage':coverage,'candidate_requirements':needs,'task':'task-20261002-0003'})
            media_records += [call,asset];outputs.append((call,asset_id))
        media_document={'format':'production-import-v1','records':media_records}
        p.import_records(store,media_document,validate_only=True);p.import_records(store,media_document);batches.append(media_document)
        completed=[]
        for call,asset_id in outputs:
            saved=deepcopy(call);saved['expected_version']=1
            saved['payload'].update(status='completed',outputs=[actual_ref(asset_id)])
            completed.append(saved)
        done={'format':'production-import-v1','records':completed}
        p.import_records(store,done,validate_only=True);p.import_records(store,done);batches.append(done)
        write(ROOT/'production/full-generation/registration.json',{'format':'full-generation-registration-v1','batches':batches,
            'summary':{'image_plans':255,'voice_state_plans':sum(len(v) for v in voice_needs.values()),'new_assets':6,'new_calls':6,'user_acceptances':0},
            'asset_refs':[actual_ref(oid) for _,oid in outputs]})
        print(json.dumps({'image_plans':255,'voice_state_plans':sum(len(v) for v in voice_needs.values()),'new_assets':6,'new_calls':6,'user_acceptances':0}))
    finally: store.close()


if __name__=='__main__':main()
