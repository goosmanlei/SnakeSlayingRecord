"""Story-side client for the desk's portable method contract."""
import json
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


def reference(record):
    return {k: record[k] for k in ('object_id', 'revision_id')}


def delivery_directory(directory):
    directory = Path(directory).absolute()
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError('方法交付路径不得经过符号链接')
    return directory


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
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_text() != body:
                raise ValueError('已交付方法文件发生变化：' + name)
        else:
            target.write_text(body)


def instructions(package):
    return package['files']['SKILL.md'] + ''.join('\n\n## 包内文件：' + name + '\n' + body for name, body in package['files'].items() if name != 'SKILL.md') + ''.join('\n\n## 共用资料：' + r['title'] + ' / ' + r['reference']['section'] + '\n' + r['content'] for r in package['resources'])
