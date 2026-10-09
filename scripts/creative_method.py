"""External creator checkpoints over the existing exact method HTTP contract.

No model calls or production imports. All stages stay in the chosen run folder
and in the method service, private by default. The caller supplies real inputs.
"""
import argparse
import json
import re
from pathlib import Path

try:
    from .method_runtime import MethodClient, deliver_files, delivery_directory, reference
except ImportError:
    from method_runtime import MethodClient, deliver_files, delivery_directory, reference


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    if path.exists():
        if load(path) != value:
            raise ValueError('本地产物已存在且内容不同；保留原步骤并新建修订步骤')
        return
    with path.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def begin(client, directory, request):
    directory = delivery_directory(directory)
    request = {**request, 'private': request.get('private', True)}
    if directory.exists():
        delivery = load(directory / 'delivery.json')
        if request != delivery['request']:
            raise ValueError('恢复请求与原步骤不同；换输入或方法须新建步骤')
        if client.prepare(request) != delivery['execution']:
            raise ValueError('准确方法快照不一致；先恢复原包')
        deliver_files(directory, delivery['execution']['payload']['package'], request['inputs'])
        return delivery
    execution = client.prepare(request)
    directory.mkdir(parents=True)
    delivery = {'request': request, 'execution': execution}
    # Persist the identity first, so a partial file export can be recovered.
    save(directory / 'delivery.json', delivery)
    deliver_files(directory, execution['payload']['package'], request['inputs'])
    return delivery


def record(client, directory, stage, output):
    directory = delivery_directory(directory)
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', stage):
        raise ValueError('无效阶段名')
    delivery = load(directory / 'delivery.json')
    execution = client.prepare(delivery['request'])
    if execution != delivery['execution']:
        raise ValueError('准确方法快照不一致；先恢复原包')
    artifact = client.artifact(execution, delivery['request'], stage, output)
    save(directory / ('stage-' + stage + '.json'), artifact)
    return artifact


def read_stage(client, directory, stage):
    directory = delivery_directory(directory)
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', stage):
        raise ValueError('无效阶段名')
    delivery = load(Path(directory) / 'delivery.json')
    local = load(Path(directory) / ('stage-' + stage + '.json'))
    remote = client.read(reference(local))
    if remote != local or remote['payload']['execution'] != reference(delivery['execution']):
        raise ValueError('阶段产物或方法归属不一致')
    return remote['payload']['output']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method-url', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    subs = parser.add_subparsers(dest='action', required=True)
    start = subs.add_parser('begin'); start.add_argument('--request', type=Path, required=True)
    item = subs.add_parser('record'); item.add_argument('--stage', required=True); item.add_argument('--file', type=Path, required=True)
    read = subs.add_parser('read'); read.add_argument('--stage', required=True)
    args = parser.parse_args(); client = MethodClient(args.method_url)
    if args.action == 'begin':
        result = begin(client, args.directory, load(args.request))
        result = {'execution': reference(result['execution']), 'steps': result['execution']['payload']['package']['steps'], 'directory': str(args.directory)}
    elif args.action == 'record':
        body = load(args.file) if args.file.suffix == '.json' else args.file.read_text()
        result = reference(record(client, args.directory, args.stage, body))
    else:
        result = read_stage(client, args.directory, args.stage)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
