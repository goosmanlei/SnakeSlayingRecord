#!/usr/bin/env python3
"""Register local authored ZIP projects in an isolated review, without adoption."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

from audiovisual_design import ROOT, reference
from exact_text_handoffs import load, package
from generation_workspace import generation_root, isolated_instance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--only', action='append')
    parser.add_argument('--operation', required=True, help='此次本地制作操作身份；恢复时使用同一身份')
    args = parser.parse_args()
    instance = isolated_instance(generation_root(ROOT), args.instance)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk import production as p
    from review_desk import production_current as current
    from review_desk.production_media import ingest
    data = load()
    if args.only:
        if set(args.only) - {i['id'] for i in data['handoffs']}:
            raise ValueError('unknown handoff')
        data['handoffs'] = [i for i in data['handoffs'] if i['id'] in args.only]
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        if not current.enabled(store):
            raise ValueError('请先迁移当前制作模型；素材需求通过既有方法流程准备，本工具不重编上游制作树')
        receipt = []
        def exists(oid):
            return bool(store.db.execute('SELECT 1 FROM objects WHERE id=?', (oid,)).fetchone())
        def write(oid, kind, payload, version=0, guard=None):
            checks={'expected_heads':{guard['object_id']:guard['id']},'expected_content':{guard['object_id']:current.marker(guard)}} if guard else {}
            p.import_records(store, {'format': 'production-import-v1', **checks, 'records': [
                {'object_id': oid, 'kind': kind, 'expected_version': version, 'payload': payload}]})
            return p.record(store, oid)
        for item in data['handoffs']:
            need = p.record(store, 'material-text-' + item['id'])
            raw = package(item)
            digest = hashlib.sha256(raw).hexdigest()
            key = hashlib.sha256((args.operation + ':' + item['id']).encode()).hexdigest()[:20]
            asset_id = 'asset-text-' + key
            if exists(asset_id):
                asset = p.record(store, asset_id)
                source = asset['payload'].get('external_source', {})
                if source.get('operation_id') != args.operation or source.get('archive_sha256') != digest:
                    raise ValueError('同一制作操作的原词或工程字节已改变；请使用新的操作身份，不覆盖原候选')
                component = asset['payload']['components'][0]
            else:
                component = ingest(instance, BytesIO(raw), item['id'] + '.zip')
                asset = write(asset_id, 'ASSET', {'format':'production-asset-v1', 'title':item['title'] + ' · 可编辑文件',
                    'blocks':[{'id':'check','text':'已核 ZIP 原件哈希、UTF-8 原词与可编辑 SVG text 元素。排版和交接见此次制作保存的素材要求；尚无实际镜头合成，不代表视频可读性通过。'}],
                    'media_type':'project', 'subjects':[need['payload']['scope'], *need['payload']['entities']],
                    'states':need['payload']['states'], 'components':[component],
                    'external_source':{'kind':'external', 'type':'authored-project', 'operation_id':args.operation,
                        'description':'本地按核定原词制作 SVG 与交接文档，打包为可编辑 ZIP；无模型调用、无费用。',
                        'tool':'Python zipfile / authored SVG text', 'archive_sha256':digest,
                        'requirement':reference(need), 'requirement_sha256':current.checksum(need['payload']),
                        'requirement_content':need['payload']},
                    'candidate_requirements':[reference(need)], 'lineage':{}}, guard=need)
            receipt.append({'handoff':item['id'], 'requirement':reference(need), 'asset':reference(asset),
                            'source':'authored-project', 'file':component})
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    finally:
        store.close()


if __name__ == '__main__':
    main()
