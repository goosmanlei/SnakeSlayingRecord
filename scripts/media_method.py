"""Deliver methods before authoring one exact media plan; no generation calls."""
import argparse
import copy
import json
from pathlib import Path

try:
    from .method_runtime import (MethodClient, deliver_files, delivery_directory, reference,
                                 load_json, save_json, delivery_lock, read_stage_value, checksum, stage_paths, read_text_value)
except ImportError:
    from method_runtime import (MethodClient, deliver_files, delivery_directory, reference,
                                load_json, save_json, delivery_lock, read_stage_value, checksum, stage_paths, read_text_value)


def read(path):
    return load_json(path)


def write(path, value):
    save_json(path, value)


def plan_output(record):
    payload = record['payload']
    excluded = ('generation', 'method_basis', 'status', 'withdrawal_reason', 'required', 'blocks', 'method_adjustment', 'shot_reference_operation')
    if payload.get('material_category') == 'text-layer':
        excluded += ('specification',)
    result = {'requirement': {k: v for k, v in payload.items() if k not in excluded},
              'generation': payload.get('generation')}
    if payload.get('material_category') == 'text-layer':
        result['text_layer'] = {key: copy.deepcopy(payload.get(key)) for key in ('blocks', 'specification')}
    return result


def selection_conditions(payload, supplied):
    # Match the server's explicit old audio-hint input conversion. Classification
    # itself always comes from the requirement and is validated by the server.
    result = {**(supplied or {}), 'media_type': payload['media_type']}
    if payload.get('material_category'):
        if 'audio_type' in result and result['audio_type'] != payload['material_category']:
            raise ValueError('调用条件不能改变素材分类')
        result.pop('audio_type', None)
        if result.get('material_category', payload['material_category']) != payload['material_category']:
            raise ValueError('调用条件不能改变素材分类')
        result['material_category'] = payload['material_category']
    return result


def _begin(client, directory, record, run_id, step_id, conditions=None, supporting=None):
    directory = delivery_directory(directory)
    if (directory / 'delivery.json').exists():
        saved = read(directory / 'delivery.json')
        original = saved['record'] if 'record' in saved else read(directory / 'record.json')
        if checksum(original) != checksum(record) or saved['request']['run_id'] != run_id or saved['request']['step_id'] != step_id:
            raise ValueError('恢复目录属于其他步骤或输入；请沿原步骤恢复')
        if conditions is not None and checksum(saved['request']['conditions']) != checksum(selection_conditions(record['payload'], conditions)):
            raise ValueError('恢复条件改变；请新建步骤并复核受影响的工作')
        if supporting is not None and checksum(saved['request']['inputs'].get('supporting_references')) != checksum(supporting):
            raise ValueError('恢复材料改变；请新建步骤')
        if checksum(client.read(reference(saved['execution']))) != checksum(saved['execution']) or checksum(client.prepare(saved['request'])) != checksum(saved['execution']):
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
    write(directory / 'begin-request.json', {'request': value, 'record': record})
    prepared = {**client.call('/api/methods/media-prepare', value), 'record': record}
    package = prepared['execution']['payload']['package']
    write(directory / 'delivery.json', prepared)
    write(directory / 'record.json', record)
    deliver_files(directory, package, prepared['request']['inputs'])
    return prepared


def begin(client, directory, record, run_id, step_id, conditions=None, supporting=None):
    with delivery_lock(directory):
        return _begin(client, directory, record, run_id, step_id, conditions, supporting)


def validate_record(saved, record):
    original = saved.get('record')
    if original is None:
        raise ValueError('旧步骤缺少完整媒体记录；请先沿原 begin 请求恢复')
    def baseline(value):
        result = copy.deepcopy(value)
        keys = ('generation', 'method_basis', 'method_adjustment', 'shot_reference_operation')
        if value['payload'].get('material_category') == 'text-layer': keys += ('blocks', 'specification')
        for key in keys:
            result['payload'].pop(key, None)
        return result
    if (record['object_id'] != saved['execution']['payload']['target']
            or checksum(plan_output(record)['requirement']) != checksum(saved['request']['inputs']['context'])
            or checksum(baseline(record)) != checksum(baseline(original))):
        raise ValueError('制作对象、准确需求或并发基线变化；需要新的方法步骤')


def _stage(client, directory, name, record=None, review=None):
    directory = delivery_directory(directory); saved = read(directory / 'delivery.json')
    if name == 'review':
        output = {'assessment': review}
        if not review or not review.strip():
            raise ValueError('请记录实际回读发现与修订判断')
    else:
        validate_record(saved, record)
        output = plan_output(record)
    _, artifact = read_stage_value(client, directory, name, source=output, resume=True, record=record)
    if name == 'result':
        return import_record(saved, record, artifact)
    return artifact


def stage(client, directory, name, record=None, review=None):
    with delivery_lock(directory):
        return _stage(client, directory, name, record, review)


def import_record(saved, record, artifact):
    record = copy.deepcopy(record)
    record['payload'].pop('method_adjustment', None)
    record['payload'].pop('shot_reference_operation', None)
    record['payload']['method_basis'] = {'execution': reference(saved['execution']), 'artifact': reference(artifact),
                                         'run_id': saved['request']['run_id'], 'step_id': saved['request']['step_id']}
    return record


def read_stage(client, directory, name, *, resume=False, record=None, review=None):
    with delivery_lock(directory) as directory:
        saved = read(directory / 'delivery.json')
        source = None
        if record is not None:
            validate_record(saved, record)
            source = plan_output(record)
        elif review is not None:
            source = {'assessment': review}
        output, artifact = read_stage_value(client, directory, name, source=source, resume=resume, record=record)
        if name == 'review':
            return output
        raw = read(stage_paths(directory, name)[0])
        original = raw.get('record')
        if original is None:
            # Legacy full outputs may use the frozen original envelope, never today's plan.
            original = copy.deepcopy(saved.get('record') or read(directory / 'record.json'))
            if output.get('generation') is not None:
                original['payload']['generation'] = copy.deepcopy(output['generation'])
            if output.get('text_layer'):
                original['payload'].update(copy.deepcopy(output['text_layer']))
        validate_record(saved, original)
        if checksum(plan_output(original)) != checksum(output):
            raise ValueError('完整媒体记录与阶段原值不一致：' + name)
        result = {'output': output, 'record': original}
        if name == 'result':
            result['record'] = import_record(saved, original, artifact)
            result['import_package'] = {'format': 'production-import-v1', 'records': [result['record']]}
            write(directory / 'result-import.json', result['import_package'])
        return result


def result_path(directory, path):
    directory = delivery_directory(directory)
    path = delivery_directory(path)
    if not path.is_relative_to(directory):
        raise ValueError('待导入包须保存在原步骤目录内；输出路径越界')
    return path


def export_result(directory, path, package):
    write(result_path(directory, path), package)


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
    for action in ('read', 'recover'):
        item = subs.add_parser(action); item.add_argument('--stage', choices=['draft', 'review', 'result'], required=True)
        item.add_argument('--output', type=Path, help='result 的待导入包，须位于步骤目录内')
        if action == 'recover':
            item.add_argument('--record', type=Path, help='旧 draft/result 尚有准确原记录时核验接入')
            item.add_argument('--assessment', type=Path, help='旧 review 的准确原正文')
    args = parser.parse_args(); client = MethodClient(args.method_url)
    if getattr(args, 'output', None):
        result_path(args.directory, args.output)
    if args.action == 'begin':
        result = begin(client, args.directory, read(args.record), args.run_id, args.step_id,
                       read(args.conditions) if args.conditions else None, read(args.supporting) if args.supporting else None)
    elif args.action == 'review':
        result = stage(client, args.directory, 'review', review=read_text_value(args.assessment))
    elif args.action in ('read', 'recover'):
        result = read_stage(client, args.directory, args.stage, resume=args.action == 'recover',
                            record=read(args.record) if getattr(args, 'record', None) else None,
                            review=read_text_value(args.assessment) if getattr(args, 'assessment', None) else None)
        if args.output:
            if args.stage != 'result':
                raise ValueError('只有 result 阶段提供待导入包')
            export_result(args.directory, args.output, result['import_package'])
    else:
        result = stage(client, args.directory, 'result' if args.action == 'finish' else 'draft', record=read(args.record))
        if args.action == 'finish':
            package = read_stage(client, args.directory, 'result')['import_package']
            export_result(args.directory, args.output, package)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None
