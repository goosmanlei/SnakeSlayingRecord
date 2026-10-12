"""Author one episode's video plans through real media-method stages.

The author supplies every Prompt and assessment. This tool gathers exact inputs,
persists and reads full stages, and imports reviewed results; it never rewrites
event strings or decides camera, performance, words, or reference selection.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

try:
    from . import media_method
    from .method_runtime import MethodClient, checksum
    from .generation_workspace import generation_root, isolated_instance, contained
except ImportError:
    import media_method
    from method_runtime import MethodClient, checksum
    from generation_workspace import generation_root, isolated_instance, contained

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def inventory(store, episode):
    from review_desk import production as p
    lock = load(ROOT / 'production/source-lock.json')
    source_path = ROOT / lock['screenplay']['source_file']
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != lock['screenplay']['file_sha256']:
        raise ValueError('锁定剧本字节已改变')
    rows = p.current_records(store)
    shots = sorted((r for r in rows if r['kind'] == 'AV_SHOT' and
                    r['object_id'].startswith(f'av-e{episode:02d}-')), key=lambda r: r['object_id'])
    needs = []
    for shot in shots:
        products = [p.ref_record(store, item['requirement'], {'REQUIREMENT'})
                    for item in shot['payload']['products']]
        videos = [r for r in products if r['payload']['media_type'] == 'video']
        if len(videos) != 1:
            raise ValueError('每镜必须有唯一当前视频需求：' + shot['object_id'])
        needs.append(videos[0])
    return {'episode': episode, 'source': load(source_path)['episodes'][episode - 1],
            'source_reference': lock['episodes'][episode - 1], 'shots': shots, 'needs': needs}


def envelope(row):
    return {'object_id': row['object_id'], 'kind': row['kind'],
            'expected_version': row['version'], 'payload': copy.deepcopy(row['payload'])}


def inspect(store, episode, offset, count, include_source, compact=False):
    from review_desk import production as p
    from review_desk.material_relations import active_inputs
    value = inventory(store, episode)
    if include_source:
        source = value['source']
        print(source['title'])
        for scene in source['scenes']:
            print('\n' + scene['id'] + ' ' + scene['heading'])
            for block in source['blocks']:
                if block['id'] in scene['block_ids']:
                    print(block['id'].rsplit('-', 1)[-1], block['text'])
    for shot, need in list(zip(value['shots'], value['needs']))[offset:offset + count]:
        print('\nSHOT', shot['object_id'], shot['payload']['title'], need.get('code', ''))
        print('目标', shot['payload']['purpose'])
        print('起点', [v['description'] for v in shot['payload'].get('key_states', [])])
        print('状态', [r['object_id'] for r in shot['payload'].get('states', [])])
        plan = need['payload']['generation']
        print('参数', plan['model'], plan['parameters'], plan.get('execution'))
        counts = {}
        from review_desk.input_contracts import LABELS
        for index, item in active_inputs(store, plan, need['object_id'])[0]:
            row = p.ref_record(store, item['reference'])
            kind = row['payload']['media_type']; counts[kind] = counts.get(kind, 0) + 1
            shown = ({k: item[k] for k in ('role', 'use', 'selection_state', 'range', 'component_id') if k in item}
                     if compact else item)
            print('输入', '@' + LABELS[kind] + str(counts[kind]), row['payload']['title'],
                  json.dumps(shown, ensure_ascii=False))
        print('缺项', plan.get('blockers', []))
        prompt = plan['prompt']
        if compact and '意图与表演：' in prompt:
            prompt = '[已单列上方的共同风格、参数与输入职责省略，仅用于阅读]\n意图与表演：' + prompt.split('意图与表演：', 1)[1]
        print('当前正文\n' + prompt)


def begin(store, client, directory, episode, shot_ids, run_id, conditions):
    from review_desk import production as p
    value = inventory(store, episode)
    for index, (shot, need) in enumerate(zip(value['shots'], value['needs'])):
        if shot_ids and shot['object_id'] not in shot_ids:
            continue
        folder = directory / shot['object_id']
        record_path = folder / 'record.json'
        record = load(record_path) if record_path.exists() else envelope(need)
        supporting = [value['source_reference'] | {'object_id': value['source_reference']['object_id'],
                                                  'revision_id': value['source_reference']['revision_id']}]
        supporting[0] = {k: supporting[0][k] for k in ('object_id', 'revision_id')}
        supporting += [{'object_id': r['object_id'], 'revision_id': r['id']}
                       for r in value['shots'][max(0, index - 1):index + 2]]
        chosen = (conditions.get('by_shot', {}).get(shot['object_id'], conditions['default'])
                  if 'default' in conditions else conditions)
        prepared = media_method.begin(client, folder, record, run_id, shot['object_id'], chosen, supporting)
        print(shot['object_id'], prepared['execution']['revision_id'],
              prepared['execution']['payload']['package']['method'])


def draft(client, directory, author):
    for oid, decision in author.items():
        folder = directory / oid
        record = load(folder / 'record.json')
        if not isinstance(decision.get('prompt'), str) or not decision['prompt'].strip():
            raise ValueError('缺少实际作者稿：' + oid)
        record['payload']['generation']['prompt'] = decision['prompt']
        if 'generation_changes' in decision:
            record['payload']['generation'].update(copy.deepcopy(decision['generation_changes']))
        path = folder / 'draft-record.json'
        if path.exists() and load(path) != record:
            raise ValueError('已保存草稿不能覆盖；修订交给 result：' + oid)
        save(path, record)
        receipt = media_method.stage(client, folder, 'draft', record=record)
        print(oid, 'draft', receipt['revision_id'])


def read(client, directory, shots, stage):
    for oid in shots:
        result = media_method.read_stage(client, directory / oid, stage)
        print('\n' + oid + ' ' + stage)
        if stage == 'review':
            print(result['assessment'])
        else:
            print(result['output']['generation']['prompt'])
            print('BLOCKERS', result['output']['generation'].get('blockers', []))


def finish(store, client, directory, author):
    from review_desk import production as p
    from review_desk.production_current import marker
    ready, expected = [], {}
    for oid, decision in author.items():
        folder = directory / oid
        assessment = decision.get('assessment')
        if not isinstance(assessment, str) or not assessment.strip():
            raise ValueError('缺少本镜实际回读判断：' + oid)
        media_method.stage(client, folder, 'review', review=assessment)
        reviewed = media_method.read_stage(client, folder, 'review')
        print(oid, 'review\n' + reviewed['assessment'], flush=True)
        final = load(folder / 'draft-record.json')
        if 'prompt' in decision:
            final['payload']['generation']['prompt'] = decision['prompt']
        if 'generation_changes' in decision:
            final['payload']['generation'].update(copy.deepcopy(decision['generation_changes']))
        save(folder / 'final-record.json', final)
        media_method.stage(client, folder, 'result', record=final)
        result = media_method.read_stage(client, folder, 'result')
        current = p.record(store, final['object_id'])
        intended = result['record']['payload']
        if current['payload'] != intended:
            original = load(folder / 'delivery.json')['request']['inputs']['baseline_marker']
            expected[current['object_id']] = original
            ready.append(result['record'])
    if ready:
        # The complete model is checked once after the episode's atomic import;
        # each record still goes through normal method and reference validation.
        p.import_records(store, {'format': 'production-import-v1', 'records': ready,
                                'expected_heads': {r['object_id']: p.record(store, r['object_id'])['id'] for r in ready},
                                'expected_content': expected})
    for oid in author:
        folder = directory / oid
        intended = media_method.read_stage(client, folder, 'result')['record']['payload']
        current = p.record(store, load(folder / 'record.json')['object_id'])
        if current['payload'] != intended:
            raise ValueError('定稿实际保存正文不同：' + oid)
        save(folder / 'applied.json', {'object_id': current['object_id'], 'revision_id': current['id'],
                                    'marker': marker(current), 'method_basis': current['payload']['method_basis'],
                                    'prompt_sha256': hashlib.sha256(current['payload']['generation']['prompt'].encode()).hexdigest()})
        print(oid, 'result saved', current['id'], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--directory', type=Path, default=Path('.runtime/video-prompts/steps'))
    parser.add_argument('--method-url', required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    context = sub.add_parser('context'); context.add_argument('--episode', type=int, required=True)
    context.add_argument('--offset', type=int, default=0); context.add_argument('--count', type=int, default=30)
    context.add_argument('--source', action='store_true')
    context.add_argument('--compact', action='store_true', help='omit repeated display metadata; exact stages retain full inputs')
    start = sub.add_parser('begin'); start.add_argument('--episode', type=int, required=True)
    start.add_argument('--shots', nargs='+'); start.add_argument('--run-id', required=True)
    start.add_argument('--conditions', type=Path, required=True)
    for name in ('draft', 'finish'):
        item = sub.add_parser(name); item.add_argument('--file', type=Path, required=True)
    item = sub.add_parser('read'); item.add_argument('--shots', nargs='+', required=True)
    item.add_argument('--stage', choices=('draft', 'review', 'result'), required=True)
    args = parser.parse_args()
    root = generation_root(ROOT); instance = isolated_instance(root, args.instance)
    directory = contained(root, args.directory)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        client = MethodClient(args.method_url)
        if args.action == 'context':
            inspect(store, args.episode, args.offset, args.count, args.source, args.compact)
        elif args.action == 'begin':
            begin(store, client, directory, args.episode, args.shots, args.run_id, load(args.conditions))
        elif args.action == 'read':
            read(client, directory, args.shots, args.stage)
        else:
            (draft if args.action == 'draft' else finish)(*((client, directory, load(args.file))
                if args.action == 'draft' else (store, client, directory, load(args.file))))
    finally:
        store.close()


if __name__ == '__main__':
    main()
