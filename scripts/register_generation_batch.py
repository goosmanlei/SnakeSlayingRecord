#!/usr/bin/env python3
"""Register selected real calls and inspected originals in an isolated instance."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def ref(row):
    return {'object_id': row['object_id'], 'revision_id': row['id']}


def validate_reference_authorization(resolve, request, references, states, entity, media):
    image_sources = []
    if media == 'image':
        parents = [{k: r[k] for k in ('object_id', 'revision_id')} for r in references]
        image_sources = [resolve(r, {'ASSET'})['payload'] for r in parents]
        lineage = request.get('lineage', {'i2i_depth': 0, 'references': []})
        expected_depth = max((a['lineage']['i2i_depth'] for a in image_sources), default=-1) + 1
        assert lineage['references'] == parents, 'lineage must name every submitted reference'
        assert lineage['i2i_depth'] == expected_depth <= 2, 'image lineage exceeds or resets the two-generation limit'
    if not references:
        return
    approval = request.get('master_approval')
    approvals = request.get('master_approvals')
    if approvals is not None:
        assert not approval and isinstance(approvals, list) and len(approvals) == len(references), 'one ordered approval per reference required'
        for selected, judgment in zip(references, approvals):
            decision = resolve(judgment, {'JUDGMENT'})['payload']
            assert decision['actor'] == 'user' and decision['verdict'] == 'accepted', 'user acceptance required'
            assert decision['target'] == {k: selected[k] for k in ('object_id', 'revision_id')}, 'approval does not match ordered reference'
        return
    if approval:
        decision = resolve(approval, {'JUDGMENT'})['payload']
        assert decision['actor'] == 'user' and decision['verdict'] == 'accepted'
        assert all(decision['target'] == {k: r[k] for k in ('object_id', 'revision_id')} for r in references)
        return
    # Repairing an unaccepted candidate of the SAME complete state is allowed.
    # It never authorizes another state or identity to derive from that candidate.
    repair = request.get('same_state_repair') or {}
    assert media == 'image' and len(references) == 1 and repair.get('reason'), 'approved master required'
    source_ref = {k: references[0][k] for k in ('object_id', 'revision_id')}
    assert repair.get('source') == source_ref
    source = image_sources[0]
    assert source['media_type'] == 'image' and source['states'] == states and source['subjects'] == [entity], 'repair cannot change identity/state'
    feedback = repair.get('feedback')
    if feedback:
        decision = resolve(feedback, {'JUDGMENT'})['payload']
        assert decision.get('actor') == 'user' and decision.get('verdict') == 'changes_requested', 'exact user repair feedback required'
        assert decision.get('target') == source_ref, 'repair feedback targets another candidate'
    else:
        assert source.get('verification', {}).get('self_review_status') == 'changes_requested'
    lineage = request['lineage']
    assert lineage['references'] == [source_ref]
    assert lineage['i2i_depth'] == source['lineage']['i2i_depth'] + 1 <= 2


def validate_builtin_plan(plan, request):
    actual = request['request']
    assert set(actual) <= {'prompt', 'transparent_background', 'referenced_image_paths'}, 'unsupported built-in parameter'
    assert len(actual.get('referenced_image_paths', [])) <= 5, 'built-in tool accepts at most 5 reference images'
    assert plan['method'] == 'generate' and not plan.get('blockers'), 'prepared plan is not executable'
    assert request['model'] == plan['model'] == 'GPT Image', 'built-in model must match the exposed tool surface'
    assert actual['prompt'] == plan['prompt'], 'submitted prompt differs from its immutable prepared plan'
    assert {k: v for k, v in actual.items() if k != 'prompt'} == plan['parameters'], 'submitted parameters differ from prepared plan'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--ids', nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); instance = args.instance.resolve()
    if ROOT / '.runtime' not in instance.parents:
        parser.error('use an isolated instance within this task worktree .runtime')
    if args.output.exists():
        parser.error('this exact batch already exists; inspect before recovery')
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk import production as p
    from review_desk.production_media import ingest
    from review_desk.store import Store
    qa = {r['id']: r for r in read(ROOT / 'production/full-generation/representative-review.json')['items']}
    recipes = read(ROOT / 'production/full-generation/recipes.json')
    voices = {r['id']: r for r in recipes['voices']}
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        heads = {r['object_id']: r['id'] for r in p.current_records(store)}
        records, outputs = [], []
        for label in args.ids:
            item = qa[label]; request_path = ROOT / 'production/requests' / (label + '.json')
            request = read(request_path); media = item['media_type']; actual_references = []
            if 'call-' + label in heads or 'asset-' + label in heads:
                raise ValueError('already registered call: ' + label)
            if media == 'image' and request.get('tool') == 'image_gen.imagegen':
                receipt_path = ROOT / 'production/receipts' / (label + '-builtin-complete.json')
                receipt = read(receipt_path)
                assert receipt['status'] == 'COMPLETED' and receipt['tool'] == 'image_gen.imagegen'
                assert receipt['request_file_sha256'] == hashlib.sha256(request_path.read_bytes()).hexdigest()
                assert receipt['sha256'] == item['sha256'] and receipt['file'] == item['file']
                assert receipt['underlying_model_id'] is None, 'do not invent a hidden built-in model ID'
                assert request['model'] == 'GPT Image'
                prompt = request['request']['prompt']; model = request['model']
                params = {k: v for k, v in request['request'].items() if k != 'prompt'}
                assert set(params) <= {'transparent_background', 'referenced_image_paths', 'num_last_images_to_include'}
                needs = [request['requirement']]; states = [request['state']]; entity = request['entity']
                lineage = request['lineage']
                for selection in request.get('references', []):
                    actual_references.append({**selection['reference'], 'component_id': selection['component_id'],
                        **{k: selection[k] for k in ('crop', 'range') if k in selection}})
                # Local original inputs must exactly match the files actually submitted.
                expected_paths = []
                for selection in request.get('references', []):
                    selected = p.ref_record(store, selection['reference'], {'ASSET'})['payload']
                    component = next(c for c in selected['components'] if c['id'] == selection['component_id'])
                    assert component['sha256'] == selection['sha256']
                    expected_paths.append(str((ROOT / 'export/assets' / component['file']).resolve()))
                assert params.get('referenced_image_paths', []) == expected_paths
                assert not params.get('num_last_images_to_include'), 'managed calls must use exact local originals'
                usage = item['usage']
            elif media == 'image':
                receipt_path = ROOT / 'production/receipts' / (label + '-connector-complete.json')
                receipt = read(receipt_path)
                assert receipt['status'] == 'COMPLETED'
                assert receipt['prompt'] == request['request']['params']['prompt']
                prompt = request['request']['params']['prompt']; model = request['request']['model']
                params = {**request['request']['params'], 'mode': request['request']['mode'], 'projectId': request['request']['projectId']}
                needs = [request['requirement']]; states = [request['state']]; entity = request['entity']
                lineage = request.get('lineage', {'i2i_depth': 0, 'references': []})
                for selection in request.get('references', []):
                    actual_references.append({**selection['reference'], 'component_id': selection['component_id'],
                        **{k: selection[k] for k in ('crop', 'range') if k in selection}})
                usage = item['usage']
            else:
                receipt_path = ROOT / 'production/receipts' / ('seed-' + label + '.json')
                receipt = read(receipt_path)
                assert receipt['status'] == 'completed' and receipt['input']['text_prompt'] == request['text_prompt']
                prompt = request['text_prompt']; model = receipt['input']['model']
                params = {k: v for k, v in receipt['input'].items() if k not in ('model', 'text_prompt', 'references')}
                recipe = voices[request['recipe_id']]; states = recipe['coverage']; entity = recipe['entity']; lineage = {}
                needs = [r['reference'] for r in recipe['state_requirements']]
                assert len(needs) == len(states), 'voice identity/state requirement mapping incomplete'
                for selection in request.get('references', []):
                    actual_references.append({**selection['asset'], 'component_id': selection['component_id'], 'range': selection['range']})
                usage = {'original_duration_seconds': receipt['original_duration'], 'quota_id': receipt['quota_id'],
                         'billing': 'provider output duration; live remaining balance is recorded separately'}
            for need in needs:
                assert p.record(store, need['object_id'])['id'] == need['revision_id'], 'prepared plan changed'
            if media == 'image' and request.get('tool') == 'image_gen.imagegen':
                validate_builtin_plan(p.ref_record(store, needs[0], {'REQUIREMENT'})['payload']['generation'], request)
            approval = request.get('master_approval')
            validate_reference_authorization(lambda reference, kinds: p.ref_record(store, reference, kinds),
                request, actual_references, states, entity, media)
            components = []
            for cid, path, role in [('original', ROOT / item['file'], 'original'), ('receipt', receipt_path, 'metadata'), ('request', request_path, 'metadata')]:
                with path.open('rb') as stream: component = ingest(instance, stream, path.name)
                with path.open('rb') as stream: assert ingest(ROOT, stream, path.name)['sha256'] == component['sha256']
                components.append({**component, 'id': cid, 'role': role})
            assert components[0]['sha256'] == item['sha256']
            call_id, asset_id = 'call-' + label, 'asset-' + label
            call_payload = {'format': 'production-call-v1', 'title': item['title'] + ' · 实际输入',
                'blocks': [{'id': 'description', 'text': '按任务授权执行；派生引用认可母版，同状态返工引用明确记录的待修候选，独立文字生成无媒体参考。真实输入、请求及回执保存，不推定新结果已被用户接受。'}],
                'method': 'generation', 'tool': request.get('tool', 'OpenArt connector') if media == 'image' else 'Doubao Speech HTTP',
                'status': 'submitted', 'model': model, 'prompt': prompt, 'parameters': params,
                'inputs': [entity, *states, *actual_references], 'outputs': [], 'prepared_plan': needs[0],
                'master_approval': approval, 'request_file_sha256': hashlib.sha256(request_path.read_bytes()).hexdigest(),
                'receipt': receipt, 'usage': usage, 'lineage': lineage,
                'same_state_repair': request.get('same_state_repair'),
                'authorization': '用户任务执行指令；对应状态派生须获准确母版认可，未认可候选仅用于其自身明确问题的返工。'}
            if 'master_approvals' in request:
                call_payload['master_approvals'] = deepcopy(request['master_approvals'])
            asset_payload = {'format': 'production-asset-v1', 'title': item['title'],
                'blocks': [{'id': 'description', 'text': item['review']}], 'media_type': media,
                'subjects': [entity], 'states': states, 'components': components,
                'production': {'object_id': call_id, 'revision_id': '@' + call_id}, 'lineage': lineage,
                'placeholder': False, 'verification': {'file_inspected': True, 'visually_inspected': media == 'image',
                    'listened': False, 'user_accepted': False, 'self_review_status': item['self_review_status'],
                    'reviewer': 'Codex（图像目视、文件及字幕核对；未独立听辨）'},
                'state_coverage': [{'state': s, 'role': 'overall' if media == 'image' else 'detail',
                    'component_id': 'original', 'detail': item['title'], 'text': item['review']} for s in states],
                'candidate_requirements': needs, 'task': 'task-20261002-0003'}
            call = {'object_id': call_id, 'kind': 'CALL', 'expected_version': 0, 'payload': call_payload}
            records += [call, {'object_id': asset_id, 'kind': 'ASSET', 'expected_version': 0, 'payload': asset_payload}]
            outputs.append((call, asset_id))
        batch = {'format': 'production-import-v1', 'expected_heads': heads, 'records': records}
        p.import_records(store, batch, validate_only=True); p.import_records(store, batch)
        done = []
        for call, asset_id in outputs:
            row = deepcopy(call); row['expected_version'] = 1
            row['payload'].update(status='completed', outputs=[ref(p.record(store, asset_id))]); done.append(row)
        completed = {'format': 'production-import-v1', 'records': done}
        p.import_records(store, completed, validate_only=True); p.import_records(store, completed)
        document = {'format': 'full-generation-registration-v1', 'batches': [batch, completed],
            'summary': {'new_assets': len(outputs), 'new_calls': len(outputs), 'new_user_acceptances': 0},
            'asset_refs': [ref(p.record(store, asset_id)) for _, asset_id in outputs]}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(document['summary']))
    finally:
        store.close()


if __name__ == '__main__': main()
