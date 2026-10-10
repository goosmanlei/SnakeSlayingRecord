"""Bind a real provider request to the local desk BEFORE dispatch; never retry."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
try:
    from .method_runtime import MethodClient
except ImportError:
    from method_runtime import MethodClient


def checksum(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def before_submit(context, *, model, prompt, parameters, inputs, provider_request, tool):
    if not isinstance(context,dict):
        raise ValueError('真实生成须提供 production：本机实例 URL、需求及唯一调用身份；先登记提交快照')
    client=MethodClient(context['url'])
    package=client.call('/api/production/generation-package?'+urlencode({'requirement_id':context['requirement_id']}))
    if model!=package['model'] or prompt!=package['prompt'] or parameters!=package['parameters']:
        raise ValueError('对外请求的模型、完整 Prompt 或参数与当前准备包不同；请先修正方案')
    expected=[{'sha256':item['component']['sha256'],**{k:item[k] for k in ('crop','range') if k in item}} for item in package['inputs']]
    if expected!=inputs:
        raise ValueError('对外请求的有序参考、裁切或时间段与准备包不同')
    request={'id':context['operation_id'],'call_id':context['call_id'],'requirement_id':context['requirement_id'],
             'expected_content':package['current_marker'],'package_sha256':checksum(package),'tool':tool,
             'provider_request':provider_request}
    result=client.call('/api/production/submit',request)
    if result['already_applied']:
        raise ValueError('此提交身份已登记；先查询原调用，禁止再次对外提交')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('action',choices=['submit','reuse-candidate','result'])
    args=parser.parse_args()
    print(json.dumps(MethodClient(args.url).call('/api/production/'+args.action,json.loads(args.request.read_text())),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
