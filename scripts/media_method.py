"""Deliver methods before authoring one exact media plan; no generation calls."""
import argparse
import json
from pathlib import Path, PurePosixPath

try:
    from .method_runtime import MethodClient, reference
except ImportError:
    from method_runtime import MethodClient, reference


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def plan_output(record):
    payload = record['payload']
    return {'requirement': {k: v for k, v in payload.items() if k not in
            ('generation', 'method_basis', 'status', 'withdrawal_reason', 'required', 'blocks')},
            'generation': payload['generation']}


def begin(client, directory, record, run_id, step_id):
    directory = Path(directory)
    if directory.exists():
        saved = read(directory / 'delivery.json')
        if read(directory / 'record.json') != record or saved['request']['run_id'] != run_id or saved['request']['step_id'] != step_id:
            raise ValueError('恢复目录属于其他步骤或输入；请沿原步骤恢复')
        if client.prepare(saved['request']) != saved['execution']:
            raise ValueError('恢复服务的准确方法与本步骤不同')
        return saved
    value = {'object_id': record['object_id'], 'payload': record['payload'], 'expected_version': record['expected_version'], 'run_id': run_id, 'step_id': step_id}
    prepared = client.call('/api/methods/media-prepare', value)
    directory.mkdir(parents=True)
    package = prepared['execution']['payload']['package']
    for name, body in package['files'].items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('方法包路径越界')
        target = directory / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    (directory / 'shared').mkdir(exist_ok=True)
    for index, resource in enumerate(package['resources']):
        (directory / 'shared' / (str(index) + '.md')).write_text(resource['content'])
    write(directory / 'request.json', prepared['request']['inputs'])
    write(directory / 'delivery.json', prepared)
    write(directory / 'record.json', record)
    return prepared


def stage(client, directory, name, record=None, review=None):
    directory = Path(directory); saved = read(directory / 'delivery.json')
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
    draft = subs.add_parser('draft'); draft.add_argument('--record', type=Path, required=True)
    review = subs.add_parser('review'); review.add_argument('--assessment', type=Path, required=True)
    finish = subs.add_parser('finish'); finish.add_argument('--record', type=Path, required=True); finish.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); client = MethodClient(args.method_url)
    if args.action == 'begin':
        result = begin(client, args.directory, read(args.record), args.run_id, args.step_id)
    elif args.action == 'review':
        result = stage(client, args.directory, 'review', review=args.assessment.read_text())
    else:
        result = stage(client, args.directory, 'result' if args.action == 'finish' else 'draft', record=read(args.record))
        if args.action == 'finish':
            write(args.output, {'format': 'production-import-v1', 'records': [result]})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
