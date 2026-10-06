#!/usr/bin/env python3
"""Sanitize authorized state bodies in managed replay archives and content nodes."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]

def sanitize(store,plan):
    from review_desk import material_archives as a,material_storage as storage
    from review_desk.store import canonical,digest
    from review_desk.state_cleanup import receipt_payload
    ids={r['object_id'] for r in plan['states']};revisions={r['revision_id']:r for r in plan['revisions']}
    receipts={r['revision_id']:dict(r) for r in store.db.execute('SELECT * FROM state_cleanup_receipts')}
    changed=[];candidates=set();pending_files=[]
    def clean(value):
        n=0
        if isinstance(value,dict):
            oid=value.get('object_id');payload=value.get('payload');parsed=json.loads(payload) if isinstance(payload,str) and payload.startswith('{') else payload
            if oid in ids and isinstance(parsed,dict) and parsed.get('format')=='production-state-v1':
                version=value.get('version',value.get('expected_version',0)+1)
                rid=value.get('id') or value.get('revision_id') or digest(canonical({'object_id':oid,'version':version,'payload':parsed}).encode())
                # A source definition can predate a later head; its exact identity
                # must still appear among the audited revisions before deletion.
                replacement=receipt_payload(receipts[rid]) if rid in receipts else {'format':'state-cleanup-source-receipt-v1','object_id':oid,'removed_source_sha256':digest(canonical(parsed).encode()),'reason':'此对象的历史来源定义已清理；源批次占位引用不冒充准确修订。'}
                value={**value,'payload':canonical(replacement) if isinstance(payload,str) else replacement}
                if 'kind' in value:value['kind']='DELETED_STATE'
                if rid in receipts:value['cleaned_revision_id']=rid
                return value,1
            result={}
            for k,v in value.items():result[k],m=clean(v);n+=m
            return result,n
        if isinstance(value,list):
            result=[]
            for v in value:v,m=clean(v);result.append(v);n+=m
            return result,n
        return value,0
    nodes={r['id']:json.loads(r['body']) for r in store.db.execute('SELECT * FROM material_content')}
    def children(value):
        if isinstance(value,dict):
            for v in value.values():yield from children(v)
        elif isinstance(value,list):
            for v in value:yield from children(v)
        elif isinstance(value,str) and value in nodes:yield value
    def closure(roots):
        seen=set();todo=list(roots)
        while todo:
            key=todo.pop()
            if key in seen:continue
            seen.add(key);value=nodes[key]
            if 'archive_recipe_zlib' in value:value=json.loads(zlib.decompress(base64.b64decode(value['archive_recipe_zlib'])))
            todo.extend(children(value))
        return seen
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    catalog={r['path']:json.loads(r['container']) for r in store.db.execute('SELECT * FROM material_archive_files')}
    with a.read_scope(store):
        for name in paths:
            if not name.endswith('.json') or name.startswith(('export/','production/entity-card-v2/')):continue
            path=ROOT/name;before=path.read_bytes();container=catalog.get(name)
            raw=a.decode(container,lambda key:storage.expand(store,key)) if container else a.read_bytes(path)
            if b'production-state-v1' not in raw or not any(i.encode() in raw for i in ids):continue
            data,count=clean(json.loads(raw))
            if not count:continue
            if isinstance(data,dict):data['state_cleanup_policy']='历史保留状态已物理清理；本包保留准确引用和删除凭据，不可作为旧状态重放源。'
            after=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
            if container:
                candidates|=closure(children(container));new=a.encode(store,after);store.db.execute('UPDATE material_archive_files SET container=? WHERE path=?',(canonical(new),name));disk=(json.dumps(new,ensure_ascii=False,indent=2)+'\n').encode()
            else:disk=after
            pending_files.append((path,disk))
            changed.append({'path':name,'before_sha256':digest(before),'after_sha256':digest(disk),'removed_state_bodies':count})
    nodes={r['id']:json.loads(r['body']) for r in store.db.execute('SELECT * FROM material_content')}
    roots=set(r[0] for r in store.db.execute('SELECT id FROM material_definitions'))
    for r in storage.physical_revisions(store):roots.update(children(json.loads(r['payload'])))
    for r in store.db.execute('SELECT * FROM material_archive_files'):roots.update(children(json.loads(r['container'])))
    keep=closure(roots);removed=candidates-keep
    for key in removed:store.db.execute('DELETE FROM material_content WHERE id=?',(key,))
    store.db.commit()
    for path,disk in pending_files:path.write_bytes(disk)
    return {'archives':changed,'removed_unreferenced_content_nodes':len(removed),'removed_state_bodies':sum(r['removed_state_bodies'] for r in changed)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--system',type=Path,required=True);p.add_argument('--instance',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from generation_workspace import isolated_instance
    from review_desk.store import Store
    s=Store(isolated_instance(ROOT,args.instance)/'.runtime/review.sqlite3')
    try:result=sanitize(s,json.loads((ROOT/'production/entity-card-v2/cleanup-plan.json').read_text()));args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='archives'},ensure_ascii=False))
    finally:s.close()
