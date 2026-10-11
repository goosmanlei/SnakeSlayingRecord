"""Story-side client for the desk's portable method contract."""
import hashlib
import json
import os
import re
import tempfile
import fcntl
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError


class MethodClient:
    def __init__(self, base_url):
        if urlsplit(base_url).hostname not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('方法服务须使用明确的本机审阅实例')
        self.base = base_url.rstrip('/')

    def call(self, path, value=None):
        request = Request(self.base + path, data=None if value is None else json.dumps(value, ensure_ascii=False).encode(),
                          headers={'Content-Type': 'application/json'}, method='GET' if value is None else 'POST')
        try:
            with build_opener(ProxyHandler({})).open(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            try:
                detail = json.load(exc).get('error')
            except (ValueError, TypeError):
                detail = None
            raise ValueError(detail or '方法服务请求失败：HTTP ' + str(exc.code)) from None

    def resolve(self, work_type, conditions=None):
        return self.call('/api/methods/resolve?' + urlencode({'work_type': work_type, 'conditions': json.dumps(conditions or {})}))

    def prepare(self, request):
        return self.call('/api/methods/prepare', request)

    def read(self, ref):
        return self.call('/api/methods/record?' + urlencode(ref))

    def artifact(self, execution, request, stage, output):
        return self.call('/api/methods/artifact', {**request, 'execution': reference(execution), 'stage': stage, 'output': output})

    def stage(self, execution, stage):
        return self.call('/api/methods/stage?' + urlencode({
            'execution_object_id': execution['object_id'],
            'execution_revision_id': execution['revision_id'], 'stage': stage}))


def reference(record):
    return {k: record[k] for k in ('object_id', 'revision_id')}


def delivery_directory(directory):
    directory = Path(directory).absolute()
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError('方法交付路径不得经过符号链接')
    return Path(os.path.abspath(directory))


def checksum(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def read_text_value(path):
    # TextIO's universal newline handling would silently change CRLF strings.
    return Path(path).read_bytes().decode('utf-8')


def load_json(path):
    path = delivery_directory(path)
    try:
        return json.loads(read_text_value(path))
    except FileNotFoundError:
        raise ValueError('本机文件缺失：' + str(path)) from None
    except (ValueError, UnicodeError):
        raise ValueError('本机文件损坏；保留现场并核对准确原文件：' + str(path)) from None


def save_text(path, body):
    """Publish one complete file atomically, without replacing an existing value."""
    path = delivery_directory(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if read_text_value(path) != body:
            raise ValueError('已交付方法文件发生变化：' + str(path))
        return
    fd, temporary = tempfile.mkstemp(prefix='.method-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            delivery_directory(path)
            if read_text_value(path) != body:
                raise ValueError('并发写入的本机文件不同：' + str(path)) from None
        parent = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        os.unlink(temporary)


def save_json(path, value):
    path = delivery_directory(path)
    if path.exists():
        if checksum(load_json(path)) != checksum(value):
            raise ValueError('本地产物已存在且内容不同；保留原步骤及文件：' + str(path))
        return
    save_text(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


@contextmanager
def delivery_lock(directory):
    directory = delivery_directory(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = delivery_directory(directory / '.method.lock')
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield directory
    finally:
        os.close(fd)


def restore_delivery(client, directory):
    directory = delivery_directory(directory)
    delivery = load_json(directory / 'delivery.json')
    execution = delivery['execution']
    # A read must never create a replacement execution in a missing service.
    if checksum(client.read(reference(execution))) != checksum(execution) or checksum(client.prepare(delivery['request'])) != checksum(execution):
        raise ValueError('准确方法快照不一致；先恢复原包')
    deliver_files(directory, execution['payload']['package'], delivery['request']['inputs'])
    return delivery


def stage_paths(directory, stage):
    if not isinstance(stage, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', stage):
        raise ValueError('无效阶段名')
    directory = delivery_directory(directory)
    return (delivery_directory(directory / ('stage-' + stage + '-value.json')),
            delivery_directory(directory / ('stage-' + stage + '.json')))


def stage_value(delivery, stage, output, record=None):
    request = delivery['request']
    return {'format': 'method-stage-value-v1', 'execution': reference(delivery['execution']),
            **{k: request[k] for k in ('work_type', 'run_id', 'step_id', 'target')},
            'stage': stage, 'output': output, 'output_sha256': checksum(output),
            **({'record': record, 'record_sha256': checksum(record)} if record is not None else {})}


def check_value(delivery, stage, value):
    expected = stage_value(delivery, stage, value['output'], value.get('record'))
    if checksum(value) != checksum(expected):
        raise ValueError('本机阶段原值摘要或执行/目标/阶段归属不一致：' + stage)
    return value['output']


def check_artifact(delivery, stage, artifact, output):
    request = delivery['request']; payload = artifact['payload']
    execution_ref = reference(delivery['execution'])
    oid = 'method.artifact.' + checksum({'execution': execution_ref, 'stage': stage})
    if (artifact['object_id'] != oid or artifact['version'] != 1
            or payload.get('format') != 'managed-method-artifact-v1'
            or payload.get('execution') != execution_ref or payload.get('stage') != stage
            or any(payload.get(k) != request[k] for k in ('work_type', 'run_id', 'step_id', 'target'))
            or payload.get('private', False) != delivery['execution']['payload'].get('private', False)):
        raise ValueError('阶段产物或方法归属不一致：' + stage)
    saved = payload['output']
    if payload.get('output_sha256') != checksum(saved):
        raise ValueError('压缩外层输出摘要不符：' + stage)
    compact = isinstance(saved, dict) and saved.get('format') == 'production-method-output-v1'
    if compact:
        expected = {'format': 'production-method-output-v1', 'target': request['target'],
                    'stage': stage, 'sha256': checksum(output)}
        if stage in ('draft', 'result') and isinstance(output, dict) and 'requirement' in output and 'generation' in output:
            expected.update(requirement_sha256=checksum(output['requirement']), generation_sha256=checksum(output['generation']))
        elif isinstance(output, dict) and isinstance(output.get('assessment'), str):
            expected['assessment'] = output['assessment']
        if checksum(saved) != checksum(expected):
            raise ValueError('本机阶段全文与服务原值摘要不符：' + stage)
    elif checksum(saved) != checksum(output):
        raise ValueError('本机阶段全文与旧完整服务产物不符：' + stage)


def read_stage_value(client, directory, stage, *, source=None, resume=False, record=None):
    """Return the original value only after verifying service identity and hashes."""
    raw_path, receipt_path = stage_paths(directory, stage)
    delivery = restore_delivery(client, directory)
    steps = delivery['execution']['payload']['package']['steps']
    if stage not in steps:
        raise ValueError('不是该方法的必要步骤：' + stage)
    value = load_json(raw_path) if raw_path.exists() else None
    if value:
        output = check_value(delivery, stage, value)
        if source is not None and checksum(source) != checksum(output):
            raise ValueError('同阶段原值不同；保留原稿，修订须新建步骤：' + stage)
        if record is not None and checksum(value.get('record')) != checksum(record):
            raise ValueError('同阶段准确媒体记录不同：' + stage)
    else:
        output = source
    remote = client.stage(reference(delivery['execution']), stage)
    if receipt_path.exists():
        old = load_json(receipt_path)
        if checksum(remote['artifact']) != checksum(old.get('artifact', old)) or ('previous' in old and checksum(old['previous']) != checksum(remote['previous'])):
            raise ValueError('本机确认回执与服务或前置产物不一致：' + stage)
    if remote['artifact'] is not None and output is None:
        stored = remote['artifact']['payload']['output']
        if not (isinstance(stored, dict) and stored.get('format') == 'production-method-output-v1'):
            output = stored
        elif 'assessment' in stored and checksum({'assessment': stored['assessment']}) == stored['sha256']:
            output = {'assessment': stored['assessment']}
    if output is None:
        raise ValueError('本机阶段全文缺失：' + stage + '；服务只有摘要时无法补造，请提供准确原文件')
    if remote['artifact'] is not None:
        check_artifact(delivery, stage, remote['artifact'], output)
    elif resume:
        # Persist before sending; an unknown response can always resume this value.
        save_json(raw_path, stage_value(delivery, stage, output, record))
        artifact = client.artifact(delivery['execution'], delivery['request'], stage, output)
        check_artifact(delivery, stage, artifact, output)
        remote = client.stage(reference(delivery['execution']), stage)
        if checksum(remote['artifact']) != checksum(artifact):
            raise ValueError('提交响应与服务确认不一致；保留原步骤核对')
    else:
        raise ValueError('阶段尚未获服务确认；保留原值并用 recover 沿原阶段继续：' + stage)
    save_json(raw_path, stage_value(delivery, stage, output, record if record is not None else (value or {}).get('record')))
    # Legacy receipts retain their original shape and bytes.
    if not receipt_path.exists():
        save_json(receipt_path, {'format': 'method-stage-confirmation-v1', **remote})
    return output, remote['artifact']


def deliver_files(directory, package, inputs):
    """Materialize already resolved bytes, without choosing a second method."""
    directory = delivery_directory(directory)
    files = dict(package['files'])
    index = []
    for number, resource in enumerate(package['resources']):
        section = resource['reference']['section']
        if resource.get('files'):
            prefix = 'shared/' + str(number) + '/'
            files.update({prefix + n: content for n, content in resource['files'].items()})
            name = prefix + resource['file']
        else:
            name = 'shared/' + str(number) + '.md'
        files[name] = resource['content']
        index.append('- [' + resource['title'] + ' / ' + section + '](' + name + ')：'
                     + resource['reference']['object_id'] + ' @ ' + resource['reference']['revision_id'])
    files['RESOURCES.md'] = '# 本步骤取得的准确共用资料\n\n' + '\n'.join(index) + '\n'
    files['request.json'] = json.dumps(inputs, ensure_ascii=False, indent=2) + '\n'
    for number, item in enumerate(inputs.get('relation_readings', [])):
        if 'content_json' in item:
            files['materials/reference-' + str(number) + '.json'] = json.dumps(
                {'reference': {k: item[k] for k in ('object_id', 'revision_id')},
                 'kind': item['kind'], 'payload': json.loads(item['content_json'])},
                ensure_ascii=False, indent=2) + '\n'
    for number, item in enumerate(inputs.get('supporting_records', [])):
        files['materials/' + str(number) + '.json'] = json.dumps(
            {'reference': item['reference'], 'kind': item['kind'], 'payload': json.loads(item['content_json'])},
            ensure_ascii=False, indent=2) + '\n'
    for name, body in files.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('方法包路径越界')
        target = directory / name
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError('方法交付路径不得经过符号链接')
        save_text(target, body)


def instructions(package):
    return package['files']['SKILL.md'] + ''.join('\n\n## 包内文件：' + name + '\n' + body for name, body in package['files'].items() if name != 'SKILL.md') + ''.join('\n\n## 共用资料：' + r['title'] + ' / ' + r['reference']['section'] + '\n' + r['content'] for r in package['resources'])
