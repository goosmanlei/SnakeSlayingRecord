"""External creator checkpoints over the existing exact method HTTP contract.

No model calls or production imports. All stages stay in the chosen run folder
and in the method service, private by default. The caller supplies real inputs.
"""
import argparse
import json
from pathlib import Path

try:
    from .method_runtime import (MethodClient, deliver_files, delivery_directory, reference,
                                 load_json, save_json, delivery_lock, read_stage_value, checksum, read_text_value)
except ImportError:
    from method_runtime import (MethodClient, deliver_files, delivery_directory, reference,
                                load_json, save_json, delivery_lock, read_stage_value, checksum, read_text_value)


def load(path):
    return load_json(path)


def save(path, value):
    save_json(path, value)


def begin(client, directory, request):
    request = {**request, 'private': request.get('private', True)}
    with delivery_lock(directory) as directory:
        path = directory / 'delivery.json'
        if path.exists():
            delivery = load(path)
            if checksum(request) != checksum(delivery['request']):
                raise ValueError('恢复请求与原步骤不同；换输入或方法须新建步骤')
            if checksum(client.read(reference(delivery['execution']))) != checksum(delivery['execution']) or checksum(client.prepare(request)) != checksum(delivery['execution']):
                raise ValueError('准确方法快照不一致；先恢复原包')
        else:
            save(directory / 'begin-request.json', request)
            execution = client.prepare(request)
            delivery = {'request': request, 'execution': execution}
            save(path, delivery)
        deliver_files(directory, delivery['execution']['payload']['package'], request['inputs'])
        return delivery


def record(client, directory, stage, output):
    with delivery_lock(directory):
        return read_stage_value(client, directory, stage, source=output, resume=True)[1]


def read_stage(client, directory, stage):
    with delivery_lock(directory):
        return read_stage_value(client, directory, stage)[0]


def recover(client, directory, stage, output=None):
    with delivery_lock(directory):
        return read_stage_value(client, directory, stage, source=output, resume=True)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method-url', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    subs = parser.add_subparsers(dest='action', required=True)
    start = subs.add_parser('begin'); start.add_argument('--request', type=Path, required=True)
    item = subs.add_parser('record'); item.add_argument('--stage', required=True); item.add_argument('--file', type=Path, required=True)
    read = subs.add_parser('read'); read.add_argument('--stage', required=True)
    recovery = subs.add_parser('recover'); recovery.add_argument('--stage', required=True)
    recovery.add_argument('--file', type=Path, help='旧摘要步骤仍有准确原文时，经摘要核验接入；已有原值无需此参数')
    args = parser.parse_args(); client = MethodClient(args.method_url)
    if args.action == 'begin':
        result = begin(client, args.directory, load(args.request))
        result = {'execution': reference(result['execution']), 'steps': result['execution']['payload']['package']['steps'], 'directory': str(args.directory)}
    elif args.action == 'record':
        body = load(args.file) if args.file.suffix == '.json' else read_text_value(args.file)
        result = reference(record(client, args.directory, args.stage, body))
    elif args.action == 'recover':
        body = (load(args.file) if args.file.suffix == '.json' else read_text_value(args.file)) if args.file else None
        result = recover(client, args.directory, args.stage, body)
    else:
        result = read_stage(client, args.directory, args.stage)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None
