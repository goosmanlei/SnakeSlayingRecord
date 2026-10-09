#!/usr/bin/env python3
"""Register local authored ZIP projects in an isolated review, without adoption."""
import argparse
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

from audiovisual_design import ROOT, reference
from exact_text_handoffs import load, records, package, bind_current
from generation_workspace import generation_root, isolated_instance
from revise_audiovisual import reconcile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--only', action='append')
    args = parser.parse_args()
    instance = isolated_instance(generation_root(ROOT), args.instance)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk import production as p
    from review_desk.production_media import ingest
    data = load()
    if args.only:
        if set(args.only) - {i['id'] for i in data['handoffs']}:
            raise ValueError('unknown handoff')
        data['handoffs'] = [i for i in data['handoffs'] if i['id'] in args.only]
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        rows = p.current_records(store)
        definitions = records(data, rows, {r['object_id']: r for r in rows if r['kind']=='ENTITY'},
                              {r['object_id']: r for r in rows if r['kind']=='STATE'})
        batch, _ = reconcile(store, p, bind_current(definitions, store, p))
        if batch['records']:
            p.import_records(store, batch)
        receipt = []
        def exists(oid):
            return bool(store.db.execute('SELECT 1 FROM objects WHERE id=?', (oid,)).fetchone())
        def write(oid, kind, payload, version=0):
            p.import_records(store, {'format': 'production-import-v1', 'records': [
                {'object_id': oid, 'kind': kind, 'expected_version': version, 'payload': payload}]})
            return p.record(store, oid)
        for item in data['handoffs']:
            need = p.record(store, 'material-text-' + item['id'])
            raw = package(item)
            digest = hashlib.sha256(raw).hexdigest()
            key = hashlib.sha256((digest + need['id']).encode()).hexdigest()[:20]
            call_id, asset_id = 'call-text-' + key, 'asset-text-' + key
            component = ingest(instance, BytesIO(raw), item['id'] + '.zip')
            call_payload = {'format': 'production-call-v1', 'title': item['title'] + ' · 本地排版交付',
                'blocks': [{'id':'record', 'text':'按已核定原词确定性打包 SVG 与交接文档。无模型调用、无费用；不代表成片合成或采纳。'}],
                'method':'external-edit', 'tool':'Python zipfile / authored SVG text',
                'status':'submitted', 'inputs':[], 'outputs':[], 'prepared_plan':reference(need),
                'parameters':{'archive_sha256':digest}, 'prompt':'保留可编辑 text 元素与 UTF-8 原词；实际文件为 ZIP 工程。'}
            call = p.record(store, call_id) if exists(call_id) else write(call_id, 'CALL', call_payload)
            if exists(asset_id):
                asset = p.record(store, asset_id)
                if asset['payload']['components'] != [component] or asset['payload']['candidate_requirements'] != [reference(need)]:
                    raise ValueError('existing text project identity differs')
            else:
                asset = write(asset_id, 'ASSET', {'format':'production-asset-v1', 'title':item['title'] + ' · 可编辑文件',
                    'blocks':[{'id':'check','text':'已核 ZIP 原件哈希、UTF-8 原词与可编辑 SVG text 元素。排版和交接见本版本素材要求；尚无实际镜头合成，不代表视频可读性通过。'}],
                    'media_type':'project', 'subjects':[need['payload']['scope'], *need['payload']['entities']],
                    'states':need['payload']['states'], 'components':[component], 'production':reference(call),
                    'candidate_requirements':[reference(need)], 'lineage':{}})
            if call['payload']['status'] == 'submitted':
                completed = deepcopy(call['payload']); completed.update(status='completed', outputs=[reference(asset)])
                call = write(call_id, 'CALL', completed, call['version'])
            if call['payload']['status'] != 'completed' or call['payload']['outputs'] != [reference(asset)]:
                raise ValueError('text project call has an unresolved lifecycle')
            receipt.append({'handoff':item['id'], 'requirement':reference(need), 'asset':reference(asset),
                            'call':reference(call), 'file':component})
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    finally:
        store.close()


if __name__ == '__main__':
    main()
