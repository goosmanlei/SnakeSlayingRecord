"""Story-side client for the desk's portable method contract."""
import json
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


def instructions(package):
    return package['files']['SKILL.md'] + ''.join('\n\n## 包内文件：' + name + '\n' + body for name, body in package['files'].items() if name != 'SKILL.md') + ''.join('\n\n## 共用资料：' + r['title'] + ' / ' + r['reference']['section'] + '\n' + r['content'] for r in package['resources'])
