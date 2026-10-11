"""Recover only proven historical originals and small identity receipts.

The original revision hash and the existing deletion receipt must agree. This
does not recreate former requirements, states, candidates or submitted facts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def recover(store, root, source_commit, replace_draft_id=None):
    from review_desk import production as p, production_current as current, material_reference as identity
    from review_desk.store import canonical
    from review_desk.version_consolidation import row_hash
    commit=subprocess.check_output(['git','rev-parse',source_commit],cwd=root,text=True).strip()
    old=json.loads(subprocess.check_output(['git','show',commit+':export/objects.json'],cwd=root))
    rows={r['id']:{**r,'payload':json.loads(r['payload'])} for r in old['revisions']}
    active={r[0] for r in store.db.execute('SELECT operation_id FROM production_candidates')}
    references={}
    for raw in store.db.execute('SELECT operation_id,snapshot FROM production_submissions'):
        if raw[0] not in active:continue
        for item in json.loads(raw[1])['input_contents']:
            ref=item['reference'].get('reference',item['reference'])
            if not ref.get('component_id',item['reference'].get('component_id')):continue
            current_row=p.ref_record(store,ref)
            if current_row['kind']=='ASSET' and (current_row.get('unavailable') or current_row['payload'].get('status')=='withdrawn'):
                references[ref['object_id'],ref['revision_id']]=(ref,current_row)
    evidence=[];files={}
    for key,(ref,actual) in sorted(references.items()):
        previous=rows.get(ref['revision_id'])
        if not previous and actual.get('unavailable'):
            raise ValueError('exact managed historical revision not found: '+str(key))
        body=previous['payload'] if previous else actual['payload']
        if previous and (previous['object_id']!=ref['object_id'] or row_hash(previous['object_id'],previous['version'],body)!=previous['id']):
            raise ValueError('historical revision identity mismatch')
        sha=current.checksum(body)
        item={'object_id':ref['object_id'],'revision_id':ref['revision_id'],
              'title':body['title'],'media_type':body['media_type'],
              'source_proof':({'commit':commit,'original_version':previous['version'],'original_content_sha256':sha} if previous else
                              {'retirement_operation':body['operation_id'],'retained_revision':actual['id']}),
              'historical_requirements':[],'subjects':[]}
        for subject in body.get('subjects',[]):
            row=rows.get(subject['revision_id'])
            if row:item['subjects'].append({'reference':subject,'title':row['payload']['title'],'code':identity.code(store,subject['object_id'])})
        op=body.get('production',{}).get('revision_id');call=rows.get(op,{}).get('payload',{})
        if not call:
            saved=current.submission(store,body['production']['object_id'])['snapshot'];call=saved['request']
            for value in saved['input_contents']:
                if value.get('kind')=='ENTITY':
                    subject=value['reference'];row=p.ref_record(store,subject)
                    item['subjects'].append({'reference':subject,'title':row['payload']['title'],'code':identity.code(store,subject['object_id'])})
        # These three edited song fragments have no recorded old demand. The
        # archived edit receipts and frozen source inputs identify the work and
        # exact cut; do not map them onto today's complete-song requirement.
        boat_fragments={'asset-songs-ref-boat-home':(95.12,106.28),
                        'asset-songs-ref-boat-opening':(1.48,10.6),
                        'asset-songs-boat-diction-reference-v1':(0,11)}
        if ref['object_id'] in boat_fragments:
            start,end=boat_fragments[ref['object_id']]
            source=next(v for v in call['inputs'] if v.get('object_id',v.get('reference',{}).get('object_id'))=='asset-songs-boat-full')
            if source['range']!={'start_seconds':start,'end_seconds':end}:
                raise ValueError('song fragment range differs from frozen edit')
            work=p.record(store,'entity-boat-song')
            item['subjects']=[{'reference':{'object_id':work['object_id'],'revision_id':work['id']},'title':work['payload']['title'],'code':identity.code(store,work['object_id'])}]
            item['source_range']=source['range']
            item['source_proof']['frozen_source_input']=source
        need=call.get('generation_requirement') or call.get('prepared_plan')
        if need and need['revision_id'] in rows:
            payload=rows[need['revision_id']]['payload'];scope=payload['scope'];owner=rows[scope['revision_id']]
            item['historical_requirements'].append({**need,'title':payload['title'],'code':identity.code(store,need['object_id']),
                'scope':{**scope,'title':owner['payload']['title'],'code':identity.code(store,scope['object_id'])}})
        if actual.get('unavailable'):
            deleted=store.db.execute('SELECT before_sha256 FROM consolidation_revisions WHERE revision_id=? AND object_id=? AND new_number IS NULL',(ref['revision_id'],ref['object_id'])).fetchone()
            if not deleted or deleted[0]!=sha:raise ValueError('historical payload differs from deletion receipt')
            component=next(c for c in body['components'] if c['id']==ref.get('component_id','original'))
            data=subprocess.check_output(['git','show',commit+':export/assets/'+component['file']],cwd=root)
            if hashlib.sha256(data).hexdigest()!=component['sha256'] or len(data)!=component['bytes']:
                raise ValueError('historical original checksum differs')
            files[component['file']]=data;item['component']=component
            item['reason']='原件曾随旧版本清理；已从受管历史核对准确修订、删除前内容及文件哈希后恢复。冻结提交中的原缺口记录保持不变。'
        else:
            item['reason']=actual['payload']['reason']
            if not item['historical_requirements']:
                item['reason']='当时未保存准确素材需求；仅能核对作品与原片段，不能归入当前需求。'+item['reason']
        evidence.append(item)
    receipt={'format':identity.EVIDENCE,'references':evidence}
    receipt['id']=current.checksum(receipt)
    old_receipt=store.db.execute('SELECT result FROM production_current_operations WHERE id=?',(receipt['id'],)).fetchone()
    if old_receipt and json.loads(old_receipt[0])!=receipt:raise ValueError('reference evidence identity conflict')
    assets=p.root_of(store)/'export/assets';added=0
    for name,data in files.items():
        target=assets/name
        if target.exists():
            if target.is_symlink() or target.read_bytes()!=data:raise ValueError('original file collision')
        else:target.write_bytes(data);added+=1
    if not old_receipt:
        with store.db:
            if replace_draft_id:
                # Only this task's unpublished local draft may be corrected.
                # The formal publisher receives the final receipt as an add.
                db=Path(store.db.execute('PRAGMA database_list').fetchone()[2]).resolve()
                if not db.is_relative_to((root/'.runtime/generation').resolve()):
                    raise ValueError('draft replacement is restricted to the isolated generation instance')
                previous=store.db.execute('SELECT result FROM production_current_operations WHERE id=?',(replace_draft_id,)).fetchone()
                if not previous:raise ValueError('exact unpublished draft receipt missing')
                previous=json.loads(previous[0])
                def originals(r):return {(v['object_id'],v['revision_id']):v.get('component') for v in r['references']}
                if previous['format']!=identity.EVIDENCE or originals(previous)!=originals(receipt):
                    raise ValueError('draft identity correction cannot change originals')
                base=db.parent/'generation-base.sqlite3'
                import sqlite3
                with sqlite3.connect('file:'+str(base)+'?mode=ro',uri=True) as baseline:
                    if baseline.execute('SELECT 1 FROM production_current_operations WHERE id=?',(replace_draft_id,)).fetchone():
                        raise ValueError('already published evidence cannot be replaced')
                store.db.execute('DELETE FROM production_current_operations WHERE id=?',(replace_draft_id,))
            store.db.execute('INSERT INTO production_current_operations VALUES (?,?,?)',(receipt['id'],current.checksum(receipt),canonical(receipt)))
            identity.validate_evidence(store)
    return {'receipt':receipt,'restored_originals':len(files),'added_files':added,'already_applied':bool(old_receipt)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--source-commit',required=True);parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--replace-draft-id')
    args=parser.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    store=Store(args.database)
    try:result=recover(store,Path.cwd(),args.source_commit,args.replace_draft_id)
    finally:store.close()
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='receipt'}))


if __name__=='__main__':main()
