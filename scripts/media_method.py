"""Deliver methods before authoring one exact media plan; no generation calls."""
import argparse
import json
from pathlib import Path

try:
    from .method_runtime import MethodClient, deliver_files, delivery_directory, reference
except ImportError:
    from method_runtime import MethodClient, deliver_files, delivery_directory, reference


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def plan_output(record):
    payload = record['payload']
    return {'requirement': {k: v for k, v in payload.items() if k not in
            ('generation', 'method_basis', 'status', 'withdrawal_reason', 'required', 'blocks', 'method_adjustment', 'shot_reference_operation')},
            'generation': payload['generation']}


def begin(client, directory, record, run_id, step_id, conditions=None, supporting=None):
    directory = delivery_directory(directory)
    if directory.exists():
        saved = read(directory / 'delivery.json')
        original = saved['record'] if 'record' in saved else read(directory / 'record.json')
        if original != record or saved['request']['run_id'] != run_id or saved['request']['step_id'] != step_id:
            raise ValueError('恢复目录属于其他步骤或输入；请沿原步骤恢复')
        if conditions is not None and saved['request']['conditions'] != {**conditions, 'media_type': record['payload']['media_type']}:
            raise ValueError('恢复条件改变；请新建步骤并复核受影响的工作')
        if supporting is not None and saved['request']['inputs'].get('supporting_references') != supporting:
            raise ValueError('恢复材料改变；请新建步骤')
        if client.prepare(saved['request']) != saved['execution']:
            raise ValueError('恢复服务的准确方法与本步骤不同')
        if not (directory / 'record.json').exists():
            write(directory / 'record.json', original)
        elif read(directory / 'record.json') != original:
            raise ValueError('本地准确方案已改变')
        deliver_files(directory, saved['execution']['payload']['package'], saved['request']['inputs'])
        return saved
    value = {'object_id': record['object_id'], 'payload': record['payload'], 'expected_version': record['expected_version'], 'run_id': run_id, 'step_id': step_id}
    if conditions is not None:
        value['method_conditions'] = conditions
    if supporting is not None:
        value['supporting_references'] = supporting
    prepared = {**client.call('/api/methods/media-prepare', value), 'record': record}
    directory.mkdir(parents=True)
    package = prepared['execution']['payload']['package']
    write(directory / 'delivery.json', prepared)
    write(directory / 'record.json', record)
    deliver_files(directory, package, prepared['request']['inputs'])
    return prepared


def stage(client, directory, name, record=None, review=None):
    directory = delivery_directory(directory); saved = read(directory / 'delivery.json')
    execution = client.prepare(saved['request'])
    if execution != saved['execution']:
        raise ValueError('服务返回的冻结方法与本步骤不同；请恢复准确执行包')
    if name == 'review':
        output = {'assessment': review}
        if not review or not review.strip():
            raise ValueError('请记录实际回读发现与修订判断')
    else:
        if record['object_id'] != execution['payload']['target'] or plan_output(record)['requirement'] != saved['request']['inputs']['context']:
            raise ValueError('制作对象或准确输入变化；需要新的方法步骤')
        output = plan_output(record)
    artifact = client.artifact(execution, saved['request'], name, output)
    if name == 'result':
        record['payload'].pop('method_adjustment', None)
        record['payload'].pop('shot_reference_operation', None)
        record['payload']['method_basis'] = {'execution': reference(execution), 'artifact': reference(artifact),
                                             'run_id': saved['request']['run_id'], 'step_id': saved['request']['step_id']}
        return record
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method-url', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    subs = parser.add_subparsers(dest='action', required=True)
    start = subs.add_parser('begin')
    start.add_argument('--record', type=Path, required=True)
    start.add_argument('--run-id', required=True); start.add_argument('--step-id', required=True)
    start.add_argument('--conditions', type=Path, help='按本次制作问题选取方法与章节的 JSON 条件')
    start.add_argument('--supporting', type=Path, help='输入锁、必要相邻方案或原件的准确引用 JSON 数组')
    draft = subs.add_parser('draft'); draft.add_argument('--record', type=Path, required=True)
    review = subs.add_parser('review'); review.add_argument('--assessment', type=Path, required=True)
    finish = subs.add_parser('finish'); finish.add_argument('--record', type=Path, required=True); finish.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); client = MethodClient(args.method_url)
    if args.action == 'begin':
        result = begin(client, args.directory, read(args.record), args.run_id, args.step_id,
                       read(args.conditions) if args.conditions else None, read(args.supporting) if args.supporting else None)
    elif args.action == 'review':
        result = stage(client, args.directory, 'review', review=args.assessment.read_text())
    else:
        result = stage(client, args.directory, 'result' if args.action == 'finish' else 'draft', record=read(args.record))
        if args.action == 'finish':
            write(args.output, {'format': 'production-import-v1', 'records': [result]})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
