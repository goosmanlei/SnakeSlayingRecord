"""Sequential extraction author checkpoints; never decide semantics or generate.

The author reads each exact episode and supplies draft/review/result. This tool
only gathers current inputs, records the real method stages and formats names
under the author's explicit role choices. It cannot batch-author the whole play.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

try:
    from . import creative_method
    from .method_runtime import MethodClient, checksum
    from .generation_workspace import generation_root, contained, isolated_instance
except ImportError:
    import creative_method
    from method_runtime import MethodClient, checksum
    from generation_workspace import generation_root, contained, isolated_instance


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def inventory(store, root, episode):
    from review_desk import production as p, production_current as current
    source_file = root/'imports/screenplay-04.json'
    lock = load(root/'production/source-lock.json')
    if hashlib.sha256(source_file.read_bytes()).hexdigest() != lock['screenplay']['file_sha256']:
        raise ValueError('锁定剧本字节已改变')
    source = load(source_file)['episodes'][episode-1]
    locked = lock['episodes'][episode-1]
    rows = {r['object_id']: r for r in p.current_records(store)
            if r['kind'] in current.CURRENT_KINDS and r['payload'].get('status') != 'withdrawn'}
    shots = sorted((r for oid, r in rows.items() if r['kind'] == 'AV_SHOT' and
                    oid.startswith('av-e%02d-' % episode)), key=lambda r: r['object_id'])
    selected = {r['object_id'] for r in shots}
    for shot in shots:
        selected.update(r['object_id'] for key in ('entities', 'states', 'continuity_context')
                        for r in shot['payload'].get(key, []))
    needs = [r for r in rows.values() if r['kind'] == 'REQUIREMENT' and
             r['payload']['scope']['object_id'] in selected]
    selected.update(r['object_id'] for r in needs)
    objects = {oid: rows[oid] for oid in sorted(selected) if oid in rows}
    return {'episode': episode, 'source': source, 'source_reference': {
                'object_id': locked['object_id'], 'revision_id': locked['revision_id']},
            'source_sha256': lock['screenplay']['file_sha256'],
            'objects': objects, 'shots': [r['object_id'] for r in shots]}


def inspect(value, section, offset=0, limit=None, reuse_reviewed=False):
    objects = value['objects']
    if section in ('source', 'all'):
        print(value['source']['title'], value['source_reference'])
        for scene in value['source']['scenes']:
            print('\n'+scene['id']+' '+scene['heading'])
            ids = set(scene['block_ids'])
            for block in value['source']['blocks']:
                if block['id'] in ids:
                    print(block['id'].rsplit('-', 1)[-1], block['text'])
    if section in ('objects', 'all'):
        selected = [(oid, row) for oid, row in objects.items() if row['kind'] in ('ENTITY', 'STATE')]
        for oid, row in selected[offset:None if limit is None else offset+limit]:
            body = row['payload']
            if row['kind'] not in ('ENTITY', 'STATE'):
                continue
            print('\n'+row['kind'], oid, body['title'])
            previous = body.get('extraction_assessment')
            if reuse_reviewed and previous:
                report = load(Path(__file__).resolve().parents[1]/previous['result_path'])
                if report['receipt']['content_sha256'].get(oid) != row['content_sha256']:
                    raise ValueError('前集交付之后正文已变，须完整回读：'+oid)
                print('复用已读第%d集准确正文，当前内容摘要 %s' % (previous['episode'], row['content_sha256']))
            else:
                print(body.get('production_description') or json.dumps(body.get('dimensions'), ensure_ascii=False)
                      if body.get('production_description') or body.get('dimensions') else '\n'.join(b['text'] for b in body.get('blocks', [])))
            print('本集依据', [(r.get('scene_id'), [bid.rsplit('-', 1)[-1] for bid in r.get('block_ids', [])]) for r in body.get('sources', [])
                             if r['object_id'] == value['source_reference']['object_id']])
            for need in objects.values():
                n = need['payload']
                if need['kind'] == 'REQUIREMENT' and n['scope']['object_id'] == oid:
                    print('自有需求', need['object_id'], n['media_type'], n['slot'], n['title'],
                          '' if reuse_reviewed and previous else n['purpose'])
    if section in ('shots', 'all'):
        for oid in value['shots'][offset:None if limit is None else offset+limit]:
            body = objects[oid]['payload']
            print('\nSHOT', oid, body['title'], body['purpose'])
            print('STATE', [r['object_id'] for r in body.get('states', [])],
                  '连续性', [r['object_id'] for r in body.get('continuity_context', [])])
            for item in body.get('key_states', []):
                print('准备职责', item['description'])
            for need in objects.values():
                n = need['payload']
                if need['kind'] == 'REQUIREMENT' and n['scope']['object_id'] == oid:
                    print('产物', need['object_id'], n['slot'], n['media_type'], n['title'])


def format_names(value, decision):
    """Format only the roles the author has explicitly accepted for this set."""
    names = dict(decision.get('names', {}))
    rows = value['objects']
    if decision.get('format_reviewed_roles'):
        for oid, row in rows.items():
            body = row['payload']
            if row['kind'] == 'STATE':
                names.setdefault(oid, re.sub(r'\s*·\s*', ' · ', body['title']))
            elif row['kind'] == 'AV_SHOT':
                names.setdefault(oid, re.sub(r'^\d+\s*·\s*A\d+\s*·\s*\d+\s+', '', body['title']))
        for oid, row in rows.items():
            body = row['payload']
            if row['kind'] != 'REQUIREMENT':
                continue
            if oid in names:
                continue
            scope = rows.get(body['scope']['object_id'])
            if not scope:
                raise ValueError('准确出处不在已读工作集合')
            title = names.get(scope['object_id'], scope['payload']['title'])
            if scope['kind'] == 'ENTITY' and body['media_type'] == 'image':
                role = {'character': '图像身份参考', 'animal': '图像身份参考', 'group': '图像身份参考', 'space': '空间布局参考',
                        'prop': '结构参考'}.get(scope['payload']['entity_type'])
                if role is None:
                    raise ValueError('请明确这个实体的图像职责名称：'+oid)
                names.setdefault(oid, title+' · '+role)
            elif scope['kind'] == 'STATE' and body['media_type'] == 'image':
                if body['specification'].get('reference_role') != 'overall':
                    raise ValueError('请明确独立部位的细节职责名称：'+oid)
                names.setdefault(oid, title+' · 整体形态参考')
            elif scope['kind'] == 'AV_SHOT' and body['media_type'] in ('image', 'video'):
                role = {'camera-main': '主机位参考', 'first-frame': '首帧', 'video': '视频'}.get(body['slot'])
                if role is None:
                    raise ValueError('请明确这个镜头产物的职责名称：'+oid)
                names.setdefault(oid, title+' · '+role)
            elif body['media_type'] == 'audio' and body['slot'].startswith('voice-'):
                names.setdefault(oid, body['title'].split('·', 1)[0].strip()+' · 音色参考')
    return names


def apply(store, value, decision, method, directory):
    from review_desk import production as p, production_current as current, semantic_consolidation as semantic
    if decision.get('reviewed_ids') != sorted(value['objects']):
        raise ValueError('结果必须显式确认这次实际读取的完整对象集合')
    if not decision.get('assessment') or not decision.get('continuity'):
        raise ValueError('需要实际抽取判断与跨镜回读结果')
    decision_sha = checksum(decision)
    input_sha = checksum(value['objects'])
    plan_path = directory/'author-plan.json'
    handoff_receipt = None
    if plan_path.exists():
        saved = load(plan_path)
        if saved['decision_sha256'] != decision_sha or saved['input_sha256'] != input_sha:
            raise ValueError('恢复计划与原作者输入、结果不同')
        result = semantic.apply(store, saved['plan'])
        if (directory/'identity-receipt.json').exists(): result['identity_handoff'] = load(directory/'identity-receipt.json')
        return result
    identity_path = directory/'identity-plan.json'
    if not identity_path.exists():
        for oid, row in value['objects'].items(): current.guard(store, oid, current.marker(row))
        for oid, digest in decision.get('additional_objects', {}).items():
            row = p.record(store, oid)
            if row['content_sha256'] != digest:
                raise ValueError('补充回读对象已变化：'+oid)
    if decision.get('additional_objects'):
        value = {**value, 'objects': {**value['objects'], **{
            oid: p.record(store, oid) for oid in decision['additional_objects']}}}
    if decision.get('new_entities'):
        for oid, body in decision['new_entities'].items():
            if not store.db.execute('SELECT 1 FROM objects WHERE id=?',(oid,)).fetchone():
                p.import_records(store, {'format':'production-import-v1','records':[
                    {'object_id':oid,'kind':'ENTITY','expected_version':0,'payload':body}]})
            elif not identity_path.exists() and p.record(store, oid)['payload'] != body:
                raise ValueError('新实体身份已存在但正文不同，须回读：'+oid)
        value = {**value, 'objects': {**value['objects'], **{
            oid: p.record(store, oid) for oid in decision['new_entities']}}}
    if decision.get('state_handoffs'):
        if identity_path.exists(): identity_plan = load(identity_path)
        else:
            import unique_origin
            identity_plan, audit = unique_origin.build(store, {'states': decision['state_handoffs']})
            save(identity_path, identity_plan); save(directory/'identity-audit.json', audit)
        handoff_receipt = semantic.apply(store, identity_plan)
        save(directory/'identity-receipt.json', handoff_receipt)
        retired = set(handoff_receipt['retired'])
        value = {**value, 'objects': {oid: p.record(store, oid) for oid in value['objects'] if oid not in retired}}
        for oid in decision.get('new_entities', {}): value['objects'][oid] = p.record(store, oid)
    names = format_names(value, decision)
    replacements = {value['objects'][oid]['payload']['title']: name for oid, name in names.items()
                    if value['objects'][oid]['payload']['title'] != name}
    replacements.update(decision.get('text_replacements', {}))
    # Already-current names may contain an old name as a prefix. Protect the
    # complete current names before replacing stale text in other consumers.
    protected = set(replacements.values()) - set(replacements)
    pattern = re.compile('|'.join(re.escape(k) for k in sorted(set(replacements) | protected, key=len, reverse=True))) if replacements else None
    frozen = {'method_basis', 'method_adjustment', '_method_binding', 'initial_plan_source',
              'extraction_assessment', 'lyrics_stage_approval', 'song_work', 'aliases'}
    owners = decision.get('state_owners', {})
    if owners:
        for sid,target in owners.items():
            if value['objects'][sid]['kind']!='STATE' or value['objects'][target]['kind']!='ENTITY':
                raise ValueError('换归属必须是已读状态及明确实体')
        for row in p.current_records(store):
            if row['kind'] not in current.CURRENT_KINDS or row['payload'].get('status')=='withdrawn': continue
            if any(ref['object_id'] in owners for path,ref in p.references(row['payload'])
                   if not any('.'+key in path for key in frozen)) and row['object_id'] not in value['objects']:
                raise ValueError('状态换归属还需回读当前消费者：'+row['object_id'])
    def rename_text(item, key=None):
        if key in frozen: return copy.deepcopy(item)
        if isinstance(item, dict): return {k: rename_text(v, k) for k, v in item.items()}
        if isinstance(item, list): return [rename_text(v) for v in item]
        if isinstance(item, str) and pattern: return pattern.sub(lambda m: replacements.get(m.group(), m.group()), item)
        return item
    state_edits = {}
    for oid, keys in decision.get('state_dimensions', {}).items():
        original = value['objects'][oid]['payload']
        if value['objects'][oid]['kind'] != 'STATE': raise ValueError('维度判断必须属于已读STATE')
        dimensions = {key: original['dimensions'][key] for key in keys}
        state_edits[oid] = (dimensions, '\n'.join(dimensions.values()),
                           original.get('production_description') or '\n'.join(original['dimensions'].values()))
    for oid, dimensions in decision.get('state_attributes', {}).items():
        original = value['objects'][oid]['payload']
        if value['objects'][oid]['kind'] != 'STATE': raise ValueError('属性判断必须属于已读STATE')
        state_edits[oid] = (dimensions, '\n'.join(dimensions.values()),
                           original.get('production_description') or '\n'.join(original.get('dimensions',{}).values()))
    updates = {}
    for oid, row in value['objects'].items():
        current.guard(store, oid, current.marker(row))
        body = copy.deepcopy(row['payload'])
        shot_id = oid if row['kind']=='AV_SHOT' else body.get('scope',{}).get('object_id')
        released = set(decision.get('released_states',{}).get(shot_id,[]))
        if released:
            previous = [ref for ref in body.get('states',[]) if ref['object_id'] in released]
            body['states'] = [ref for ref in body.get('states',[]) if ref['object_id'] not in released]
            if row['kind']=='AV_SHOT':
                history = body.setdefault('continuity_context',[])
                history.extend(ref for ref in previous if ref not in history)
            condition = decision['release_conditions'][shot_id]
            block = next((b for b in body.get('blocks',[]) if b['id']=='state-release'),None)
            if block: block['text'] = condition
            else: body.setdefault('blocks',[]).append({'id':'state-release','text':condition})
            if body.get('generation'):
                for item in body['generation'].get('inputs',[]):
                    target = p.ref_record(store,item['reference'])
                    if target['kind']=='REQUIREMENT' and target['payload'].get('scope',{}).get('object_id') in released:
                        item['use'] = '仅借已经发生的衣层与汗迹，当前肩手已离杠，姿态按本镜起点与动作。'
                if condition not in body['generation']['prompt']:
                    body['generation']['prompt']+='\n'+condition
        if oid in owners:
            body['entity'] = {'object_id': owners[oid], 'revision_id': value['objects'][owners[oid]]['id']}
        if row['kind'] in ('AV_SHOT','REQUIREMENT'):
            used = {ref['object_id'] for path,ref in p.references(body)
                    if not any('.'+key in path for key in frozen)}
            for sid,target in owners.items():
                if sid not in used: continue
                old_owner = value['objects'][sid]['payload']['entity']['object_id']
                remaining = body.get('states',[]) + body.get('continuity_context',[])
                keep_old = any(ref['object_id'] not in owners and
                               p.ref_record(store,ref)['payload'].get('entity',{}).get('object_id')==old_owner
                               for ref in remaining)
                body['entities'] = [ref for ref in body.get('entities',[])
                                    if keep_old or ref['object_id']!=old_owner]
                ref = {'object_id':target,'revision_id':value['objects'][target]['id']}
                if ref not in body['entities']: body['entities'].append(ref)
        if oid in state_edits:
            dims, description, _ = state_edits[oid]
            body['dimensions'] = dims; body['production_description'] = description
            for block in body.get('blocks', []):
                if block['id'] == 'description': block['text'] = description
        scope = body.get('scope', {}).get('object_id')
        if scope in state_edits and body.get('generation'):
            _, description, before = state_edits[scope]
            if body['generation']['output'].get('description') == before:
                body['generation']['output']['description'] = description
            if before: body['generation']['prompt'] = body['generation']['prompt'].replace(before, description)
        body = rename_text(body)
        if oid in names:
            body['title'] = names[oid]
        if body.get('generation'):
            body['generation']['output']['name'] = body['title']
        # Explicit field edits, never automatic new states or demands.
        for path, replacement in decision.get('edits', {}).get(oid, {}).items():
            parent = body
            pieces = path.split('.')
            for key in pieces[:-1]:
                parent = parent[key]
            parent[pieces[-1]] = replacement
        for reference,use in decision.get('input_uses',{}).get(oid,{}).items():
            items = [item for item in body.get('generation',{}).get('inputs',[])
                     if item.get('reference',{}).get('object_id')==reference]
            if len(items)!=1: raise ValueError('实际输入不唯一：'+oid+' '+reference)
            items[0]['use'] = use
        for bid,content in decision.get('append_blocks',{}).get(oid,{}).items():
            block = next((b for b in body.get('blocks',[]) if b['id']==bid),None)
            if block:
                if content not in block['text']: block['text']+='\n'+content
            else: body.setdefault('blocks',[]).append({'id':bid,'text':content})
        if oid in decision.get('source_blocks', {}):
            body['sources'] = [ref for ref in body.get('sources', [])
                               if ref['object_id'] != value['source_reference']['object_id']]
            for scene, block_ids in decision['source_blocks'][oid].items():
                full_ids = [value['source_reference']['object_id'].rsplit('-e',1)[0]+'-'+scene+'-'+bid
                            for bid in block_ids]
                if not set(full_ids) <= {b['id'] for b in value['source']['blocks']}:
                    raise ValueError('作者指定依据不在本集锁定原文：'+oid)
                body['sources'].append({**value['source_reference'],'scene_id':scene,'block_ids':full_ids})
        if oid in decision.get('append_conditions', {}):
            condition = decision['append_conditions'][oid]
            body['production_description'] = '\n'.join([body.get('production_description', ''), condition]).strip()
        if body.get('production_description') != row['payload'].get('production_description'):
            for block in body.get('blocks', []):
                if block['id'] == 'description': block['text'] = body['production_description']
        if body.get('purpose') != row['payload'].get('purpose'):
            for block in body.get('blocks', []):
                if block['id'] == 'purpose': block['text'] = body['purpose']
        if row['kind'] != 'RELATION' and (oid in decision.get('annotation_ids', value['objects']) or body != row['payload']):
            body['extraction_assessment'] = {'episode': value['episode'],
                'method_sha256': method['sha256'], 'method_version': method['version'],
                'result_sha256': decision_sha,
                'result_path': decision.get('result_path', 'production/extraction/episodes/e%02d.json' % value['episode'])}
        if body != row['payload']:
            updates[oid] = body
    if not updates:
        return {'changed_objects': [], 'already_applied': False}
    plan = semantic.prepare(store, {'updates': [{'object_id': oid, 'payload': body,
                    'reason': decision['assessment']} for oid, body in updates.items()]})
    save(plan_path, {'decision_sha256': decision_sha, 'input_sha256': input_sha, 'plan': plan})
    result = semantic.apply(store, plan)
    if handoff_receipt: result['identity_handoff'] = handoff_receipt
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, default=Path('.runtime/generation/review'))
    parser.add_argument('--method-url', required=True)
    parser.add_argument('--episode', type=int, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('begin')
    show = sub.add_parser('inspect'); show.add_argument('--section', choices=('source', 'objects', 'shots', 'all'), default='all')
    show.add_argument('--offset', type=int, default=0); show.add_argument('--limit', type=int)
    show.add_argument('--reuse-reviewed', action='store_true', help='已有准确内容摘要相同的前集判断不重复全文；变化即停止')
    record = sub.add_parser('record'); record.add_argument('--stage', choices=('draft', 'review', 'result'), required=True); record.add_argument('--file', type=Path, required=True)
    record.add_argument('--read-back', action='store_true', help='保存后从方法服务读取原值，供作者实际回读')
    read = sub.add_parser('read'); read.add_argument('--stage', choices=('draft', 'review', 'result'), required=True)
    sub.add_parser('apply')
    args = parser.parse_args()
    if not 1 <= args.episode <= 17:
        parser.error('episode outside the locked story')
    root = generation_root(Path(__file__).resolve().parents[1])
    directory = contained(root, args.directory)
    if not directory.is_relative_to(root/'.runtime'):
        raise ValueError('作者工作阶段只保存到任务.runtime')
    instance = isolated_instance(root, args.instance)
    client = MethodClient(args.method_url)
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    store = Store(instance/'.runtime/review.sqlite3')
    try:
        path = directory/'inventory.json'
        if args.action == 'begin':
            if args.episode > 1:
                previous = directory.parent/('e%02d' % (args.episode-1))
                creative_method.read_stage(client, previous, 'result')
                if not (previous/'applied.json').exists():
                    raise ValueError('前集结果尚未交付回读')
            if path.exists():
                value = load(path)
            else:
                with __import__('review_desk.production', fromlist=['read_scope']).read_scope(store):
                    value = inventory(store, root, args.episode)
                save(path, value)
            request = {'work_type': 'material-assessment', 'run_id': 'task-20261012-0009',
                       'step_id': 'episode-%02d' % args.episode, 'target': value['source_reference']['object_id'],
                       'conditions': {'need_sound': True}, 'inputs': {'context': {
                           'source': value['source'], 'source_reference': value['source_reference'],
                           'source_sha256': value['source_sha256'], 'current_objects_sha256': checksum(value['objects']),
                           'scope': sorted(value['objects']), 'authorization': '全剧抽取与命名；保护故事域、原件、候选、调用和原意见；不生成或重编全剧视频正文'}}}
            delivered = creative_method.begin(client, directory, request)
            print(json.dumps({'episode': args.episode, 'method': delivered['execution']['payload']['package']['method'],
                              'objects': len(value['objects']), 'shots': len(value['shots'])}, ensure_ascii=False))
        elif args.action == 'inspect':
            inspect(load(path), args.section, args.offset, args.limit, args.reuse_reviewed)
        elif args.action == 'record':
            output = load(args.file) if args.file.suffix == '.json' else args.file.read_text()
            print(json.dumps(creative_method.record(client, directory, args.stage, output)['revision_id']))
            if args.read_back:
                original = creative_method.read_stage(client, directory, args.stage)
                if isinstance(original, dict) and 'reviewed_ids' in original:
                    original = {**{k:v for k,v in original.items() if k!='reviewed_ids'},
                                'reviewed_objects':len(original['reviewed_ids']), 'read_value_sha256':checksum(original)}
                print(json.dumps(original, ensure_ascii=False, indent=2))
        elif args.action == 'read':
            original = creative_method.read_stage(client, directory, args.stage)
            display = original
            if isinstance(original, dict) and 'reviewed_ids' in original:
                display = {k: v for k, v in original.items() if k != 'reviewed_ids'}
                display.update(reviewed_objects=len(original['reviewed_ids']), read_value_sha256=checksum(original))
            print(json.dumps(display, ensure_ascii=False, indent=2))
        else:
            value = load(path)
            decision = creative_method.read_stage(client, directory, 'result')
            delivery = creative_method.load(directory/'delivery.json')
            result = apply(store, value, decision, delivery['execution']['payload']['package'], directory)
            save(directory/'applied.json', result)
            # A small delivery index identifies the exact method and inputs,
            # not another editable copy of the private author workspace.
            save(root/'production/extraction/episodes'/('e%02d.json' % args.episode), {
                'episode': args.episode, 'source_reference': value['source_reference'],
                'source_sha256': value['source_sha256'], 'read_inventory_sha256': checksum(value['objects']),
                'method_execution': creative_method.load(directory/'delivery.json')['execution']['revision_id'],
                'decision': decision, 'receipt': result})
            print(json.dumps({'episode': args.episode, 'changed': len(result['changed_objects'])}))
    finally:
        store.close()


if __name__ == '__main__':
    main()
