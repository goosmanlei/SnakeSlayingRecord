#!/usr/bin/env python3
"""Plan and resume this instance's one-time version/file consolidation.

Plans are hashes and identities. Retained real request/receipt bytes remain
immutable; prior import and migration packages are retired, never replayed.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
FORMAT='content-version-consolidation-files-v1'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.writing')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    os.replace(temporary,path)


def safe(root,name):
    relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe managed path')
    path=root/relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):raise ValueError('symlink escapes managed instance')
    return path


def identities(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if isinstance(item,str) and (key.lower() in ('id','sha256','request_id','requestid','historyid','history_id','job_id','provider_call_id','input_sha256','request_file_sha256','receipt_sha256','call_id','quota_id')):
                if 8<=len(item)<=128:yield item
            yield from identities(item)
    elif isinstance(value,list):
        for item in value:yield from identities(item)


def business_copy(value):
    """Recognize old full revision/delta packages, including nested JSON rows."""
    if isinstance(value,dict):
        if value.get('format') in ('production-entity-v1','production-state-v1','production-requirement-v1','production-shot-v1','production-shot-design-v1','production-call-v1','production-asset-v1','production-relation-v1','production-representation-v1','production-judgment-v1','material-definition-v1','full-generation-recipes-v1','seedance-episode-plan-v1','shot-reference-state-additions-v1','production-export-index-v1'):
            return True
        if isinstance(value.get('material_content'),list) and any(isinstance(r,dict) and 'body' in r for r in value['material_content']):return True
        if isinstance(value.get('prompt'),str) and 'model' in value and 'parameters' in value:return True
        return any(business_copy(v) for v in value.values())
    if isinstance(value,list):return any(business_copy(v) for v in value)
    if isinstance(value,str) and value.lstrip().startswith(('{','[')):
        try:return business_copy(json.loads(value))
        except ValueError:return False
    return False


def file_plan(store,database_plan,workspace):
    from review_desk import material_archives as archives, material_storage as storage, production as p
    from review_desk import version_consolidation as vc
    lost={r['revision_id'] for r in database_plan['delete_revisions']}
    roots=defaultdict(set);owners=defaultdict(set);keep_ids=set();lost_ids=set();call_hashes=set();lost_hashes=set()
    requests=defaultdict(lambda: {'retained':set(),'discarded':set()})
    from review_desk.store import canonical,digest
    for meta in store.db.execute('SELECT r.id,r.object_id,o.kind,r.payload FROM revisions r JOIN objects o ON o.id=r.object_id'):
        payload=json.loads(meta['payload']);kept=meta['id'] not in lost
        for name in vc.file_references(payload):
            owners[name].add(meta['id'])
            if kept:roots[name].add(meta['id'])
        if meta['kind']=='CALL':
            target=keep_ids if kept else lost_ids
            target.add(meta['object_id']);target.update(identities(payload))
            key=digest(canonical({'model':payload.get('model'),'parameters':payload.get('parameters')}).encode())
            requests[key]['retained' if kept else 'discarded'].add(meta['id'])
        if meta['kind']=='ASSET':
            (call_hashes if kept else lost_hashes).update(c['sha256'] for c in payload.get('components',[]) if c.get('role')=='metadata')
    for source in store.sources():
        for name in vc.file_references(source):roots[name].add('source:'+source['id'])
    for scope in ('SYSTEM','WORKSPACE'):
        try:
            icon=store.configuration(scope)['body'].get('site_favicon')
            if icon:roots[icon].add('configuration:'+scope)
        except (KeyError,ValueError):pass
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=workspace).decode().split('\0')
    catalog={r['path']:json.loads(r['container']) for r in store.db.execute('SELECT * FROM material_archive_files')}
    operations=[];retained=[];anomalies=[];remove_catalog=set();audit=[]
    def operation(name,action,reason):
        path=safe(workspace,name);before=sha(path);size=path.stat().st_size
        row={'path':name,'action':action,'before_sha256':before,'before_bytes':size,'reason':reason}
        if action=='retire':
            receipt={'format':'retired-production-package-v1','path':name,'source_sha256':before,
                     'source_bytes':size,'reason':reason,'effective_recovery':'export/manifest.json'}
            data=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
            row.update(after_sha256=hashlib.sha256(data).hexdigest(),after_bytes=len(data),receipt=receipt)
        operations.append(row);remove_catalog.add(name)
    with archives.read_scope(store,workspace):
        for name in tracked:
            if not name or name.startswith('production/version-consolidation/'):continue
            path=safe(workspace,name)
            if not path.is_file():raise ValueError('tracked file missing: '+name)
            if name.startswith('export/assets/'):
                file=path.name
                if file in roots:
                    retained.append({'path':name,'sha256':sha(path),'bytes':path.stat().st_size,'references':sorted(roots[file])})
                elif file in owners:
                    operation(name,'delete','all exact revision owners are discarded')
                else:
                    retained.append({'path':name,'sha256':sha(path),'bytes':path.stat().st_size,'references':['outside discarded production ownership']})
                continue
            if not name.startswith('production/') or not name.endswith(('.json','.json.gz','.jsonl.gz','.zip')):continue
            if name.endswith('.zip'):
                # The old song publication zip is a duplicate replay package;
                # its real audio is independently retained by exact file roots.
                import zipfile
                with zipfile.ZipFile(path) as z:
                    members=z.infolist()
                    if sum(i.file_size for i in members)>256*1024*1024:raise ValueError('archive expansion needs a separate bounded plan')
                    affected=any(i.filename.endswith('.json') and business_copy(json.loads(z.read(i))) for i in members)
                if affected:operation(name,'delete','obsolete replay zip; current exact content and original audio remain in the complete export')
                continue
            if name.endswith('.gz'):
                # Existing audit files are bounded by their known 150 MB limit.
                with gzip.open(path,'rb') as f:raw=f.read(150*1024*1024+1)
                if len(raw)>150*1024*1024:raise ValueError('compressed audit exceeds approved scan limit')
                values=[json.loads(line) for line in raw.splitlines()] if name.endswith('.jsonl.gz') else [json.loads(raw)]
                if any(business_copy(v) for v in values):operation(name,'delete','old full database/restore audit; identities and hashes remain in the new migration evidence')
                continue
            # Read the actual managed path, not a stale catalog entry for it.
            raw=archives.read_bytes(path);value=json.loads(raw);logical=hashlib.sha256(raw).hexdigest()
            if name.startswith(('production/requests/','production/receipts/')):
                keys=set(identities(value));kept=keys & keep_ids;removed=keys & lost_ids
                wire=value.get('request',value)
                if isinstance(wire,dict) and isinstance(wire.get('params'),dict):
                    normalized={'model':wire.get('model'),'parameters':{**wire['params'],**({'projectId':wire['projectId']} if wire.get('projectId') else {})}}
                    match=requests.get(digest(canonical(normalized).encode()),{})
                    kept.update(match.get('retained',()));removed.update(match.get('discarded',()))
                quota=isinstance(value,dict) and 'remaining_seconds' in value and 'service_status' in value and not business_copy(value)
                if quota:kept.add('account quota evidence; independent of version membership')
                if logical in call_hashes or kept:
                    retained.append({'path':name,'sha256':sha(path),'logical_sha256':logical,'bytes':path.stat().st_size,'references':sorted(kept) or ['exact retained candidate metadata checksum']})
                elif logical in lost_hashes or removed:
                    operation(name,'delete','request/receipt exact identities belong only to discarded calls or candidates')
                else:anomalies.append({'path':name,'reason':'request/receipt has no proven exact call or candidate owner','logical_sha256':logical,'identity_keys':sorted(keys)[:12]})
                continue
            full=business_copy(value)
            if full:
                operation(name,'retire','previous creation/import/migration package retired; complete current recovery is export/manifest.json')
            else:
                retained.append({'path':name,'sha256':sha(path),'logical_sha256':logical,'bytes':path.stat().st_size,'references':['historical metadata without full business bodies; not a current recovery source']})
            audit.append({'path':name,'full_business_package':full})
    for name in catalog:
        if name in remove_catalog:continue
        if name.startswith('export/assets/') and not safe(workspace,name).exists():remove_catalog.add(name)
    for name,refs in roots.items():
        path=safe(workspace,'export/assets/'+name)
        if not path.is_file():anomalies.append({'path':'export/assets/'+name,'reason':'retained real-call or content file missing','references':sorted(refs)})
    return {'format':FORMAT,'operations':operations,'retained':retained,'archive_deletions':sorted(remove_catalog & catalog.keys()),
            'anomalies':anomalies,'scan':audit,'counts':{'delete_files':sum(r['action']=='delete' for r in operations),
             'retire_packages':sum(r['action']=='retire' for r in operations),'before_bytes':sum(r['before_bytes'] for r in operations),
             'after_bytes':sum(r.get('after_bytes',0) for r in operations),'shared_original_files':sum(len(v)>1 for v in roots.values())}}


def prepare(store,workspace):
    from review_desk import version_consolidation as vc
    from review_desk.store import canonical,digest
    result=vc.plan(store);files=file_plan(store,result,workspace)
    if files['anomalies']:return {'database':result,'files':files,'blocked':True}
    result['files']=files;result['archive_deletions']=files['archive_deletions']
    result['id']=digest(canonical({k:v for k,v in result.items() if k!='id'}).encode())
    return result


def check_files(root,plan,allow_applied=False):
    for item in plan['files']['operations']:
        path=safe(root,item['path']);actual=sha(path) if path.is_file() else None
        allowed={item['before_sha256']}
        if allow_applied:allowed.add(item.get('after_sha256'))
        if actual not in allowed:raise ValueError('managed file drift: '+item['path'])
    for item in plan['files']['retained']:
        path=safe(root,item['path'])
        if not path.is_file() or sha(path)!=item['sha256']:raise ValueError('retained original drift: '+item['path'])


def apply_files(root,plan,journal,*,fault_after=None):
    """DB commits first. Each file is then either old or its exact new state."""
    from review_desk import version_consolidation as vc
    from review_desk.store import Store,canonical,digest
    check_files(root,plan,allow_applied=True)
    pending=any((sha(safe(root,r['path'])) if safe(root,r['path']).is_file() else None)!=r.get('after_sha256') for r in plan['files']['operations'])
    s=Store.open_readonly(root/'.runtime/review.sqlite3')
    try:
        row=s.db.execute('SELECT receipt FROM consolidation_runs WHERE id=?',(plan['id'],)).fetchone()
        if not row:raise ValueError('database transaction has not committed')
        if pending:
            current=digest(canonical({k:v for k,v in vc.fingerprint(s).items() if k!='consolidation_runs'}).encode())
            if current!=json.loads(row[0]).get('database_head_sha256'):raise ValueError('database drift after migration; file publication refused')
    finally:s.close()
    changed=0
    for row in plan['files']['operations']:
        path=safe(root,row['path']);actual=sha(path) if path.exists() else None
        if actual==row.get('after_sha256'):continue
        if actual!=row['before_sha256']:raise ValueError('managed file drift during publication: '+row['path'])
        if row['action']=='delete':path.unlink()
        else:save(path,row['receipt'])
        changed+=1
        if fault_after is not None and changed>=fault_after:raise RuntimeError('injected interruption during file publication')
    check_files(root,plan,allow_applied=True)
    for row in plan['files']['operations']:
        path=safe(root,row['path']);actual=sha(path) if path.exists() else None
        if actual!=row.get('after_sha256'):raise ValueError('file publication incomplete')
    receipt={'plan_id':plan['id'],'additional_changed_files':changed,'counts':plan['files']['counts'],'verified':True}
    save(journal,receipt);return receipt


def restore_publication_receipts(store,root):
    """Story-owned idempotency receipts stay outside the generic review model."""
    policy=json.loads((root/'config/instance.json').read_text()).get('version_consolidation_policy',{})
    expected=policy.get('publication_receipts_sha256')
    if not expected:raise ValueError('consolidated recovery is missing publication receipt policy')
    path=root/'production/version-consolidation/recovery.json'
    if sha(path)!=expected:raise ValueError('publication recovery receipt changed')
    document=json.loads(path.read_text())
    if document.get('format')!='version-consolidation-recovery-v1' or document.get('plan_id')!=policy['plan_id']:raise ValueError('publication recovery baseline differs')
    with store.db:
        store.db.execute('CREATE TABLE IF NOT EXISTS generation_publications (id TEXT PRIMARY KEY,receipt TEXT NOT NULL)')
        for row in document['generation_publications']:
            old=store.db.execute('SELECT receipt FROM generation_publications WHERE id=?',(row['id'],)).fetchone()
            if old and old[0]!=row['receipt']:raise ValueError('publication receipt collision')
            store.db.execute('INSERT OR IGNORE INTO generation_publications VALUES (?,?)',(row['id'],row['receipt']))
    return len(document['generation_publications'])


def export_publication_receipts(store,root):
    from review_desk import version_consolidation as vc
    if not vc.available(store):return
    runs=[r[0] for r in store.db.execute('SELECT id FROM consolidation_runs')]
    if not runs:return
    if len(runs)!=1:raise ValueError('ambiguous consolidated baseline')
    exists=store.db.execute("SELECT 1 FROM sqlite_master WHERE name='generation_publications'").fetchone()
    rows=[dict(r) for r in store.db.execute('SELECT * FROM generation_publications ORDER BY id')] if exists else []
    path=root/'production/version-consolidation/recovery.json'
    save(path,{'format':'version-consolidation-recovery-v1','plan_id':runs[0],'generation_publications':rows})
    config_path=root/'config/instance.json';config=json.loads(config_path.read_text())
    config['version_consolidation_policy']={'format':'version-consolidation-policy-v1','plan_id':runs[0],
        'ledger_sha256':vc.ledger_hash(vc.dump(store)),'publication_receipts_sha256':sha(path)}
    save(config_path,config)


def verify(store,plan,baseline=None):
    """Check every retained revision/candidate, not a page sample."""
    from review_desk import version_consolidation as vc,material_model
    from review_desk.store import canonical,digest
    report=material_model.verify(store)
    lost={r['revision_id'] for r in plan['delete_revisions']}
    selection={r['object_id']:r['old_number'] for r in plan['objects'] if r['kind']=='MATERIAL'}
    core={r['object_id'] for r in plan['objects'] if r['kind'] in vc.CORE_KINDS}
    for rid in lost:
        if store.db.execute('SELECT 1 FROM revisions WHERE id=?',(rid,)).fetchone():raise ValueError('deleted revision remains')
        if not vc.deleted(store,rid):raise ValueError('missing deletion identity')
    for mid in selection:
        numbers=[r[0] for r in store.db.execute('SELECT number FROM material_plan_versions WHERE material_id=?',(mid,))]
        if numbers!=[1]:raise ValueError('material is not exactly V1: '+mid)
    candidates=defaultdict(set)
    for r in store.db.execute('SELECT m.material_id,c.candidate_id FROM material_candidate_members c JOIN material_plan_members m ON m.revision_id=c.revision_id'):
        candidates[r[0]].add(r[1])
    for item in plan['objects']:
        if item['kind']=='MATERIAL':
            expected=set(next(v['candidates'] for v in item['versions'] if v['number']==item['old_number']))
            if candidates[item['object_id']]!=expected:raise ValueError('retained exact candidates differ: '+item['object_id'])
        else:
            rows=list(store.db.execute('SELECT id,version FROM revisions WHERE object_id=?',(item['object_id'],)))
            if len(rows)!=1 or rows[0]['id']!=item['keep_revision'] or rows[0]['version']!=1:raise ValueError('core baseline differs')
    checked=calls=0
    if baseline is not None:
        for row in baseline.db.execute('SELECT r.*,o.kind FROM revisions r JOIN objects o ON o.id=r.object_id ORDER BY r.id'):
            if row['id'] in lost:continue
            old=json.loads(row['payload']);expected=old if row['kind']=='CALL' else vc.clear_references(old,lost,selection)
            current=store.db.execute('SELECT * FROM revisions WHERE id=?',(row['id'],)).fetchone()
            if not current or json.loads(current['payload'])!=expected:raise ValueError('retained body differs: '+row['id'])
            if current['version']!=(1 if row['object_id'] in core else row['version']):raise ValueError('unexpected revision numbering')
            if row['kind']=='CALL':
                if current['payload']!=row['payload']:raise ValueError('real call input bytes changed')
                calls+=1
            checked+=1
        removed=set(plan['delete_comments'])
        for table,key in (('comments','id'),('comment_events','comment_id')):
            expected=[dict(r) for r in baseline.db.execute('SELECT * FROM '+table+' ORDER BY 1') if r[key] not in removed]
            actual=[dict(r) for r in store.db.execute('SELECT * FROM '+table+' ORDER BY 1')]
            if expected!=actual:raise ValueError('retained comments/events changed')
    root=store.db_path.parent.parent
    check_files(root,plan,allow_applied=True)
    for row in plan['files']['operations']:
        path=safe(root,row['path'])
        if (sha(path) if path.exists() else None)!=row.get('after_sha256'):raise ValueError('old package or file remains')
    if store.db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or store.db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('database integrity failure')
    return {'model':report,'objects':len(plan['objects']),'retained_revisions_compared':checked,
            'immutable_real_call_revisions':calls,'deleted_revisions_absent':len(lost),
            'candidate_memberships':sum(len(v) for v in candidates.values()),'files':plan['files']['counts'],
            'database_head_sha256':digest(canonical({k:v for k,v in vc.fingerprint(store).items() if k!='consolidation_runs'}).encode())}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--system',type=Path,required=True);p.add_argument('--instance',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('plan');q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('apply');q.add_argument('--plan',type=Path,required=True);q.add_argument('--journal',type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.system.resolve()))
    from generation_workspace import isolated_instance
    from review_desk.store import Store
    from review_desk import version_consolidation as vc
    instance=isolated_instance(ROOT,a.instance)
    if a.command=='plan':
        s=Store.open_readonly(instance/'.runtime/review.sqlite3')
        try:result=prepare(s,ROOT);save(a.output,result)
        finally:s.close()
        print(json.dumps({'blocked':result.get('blocked',False),'files':result['files']['counts'],'anomalies':result['files']['anomalies']}));return
    plan=json.loads(a.plan.read_text());check_files(instance,plan,allow_applied=True)
    s=Store(instance/'.runtime/review.sqlite3')
    try:result=vc.apply_database(s,plan)
    finally:s.close()
    print(json.dumps({'database':result,'files':apply_files(instance,plan,a.journal)},ensure_ascii=False))

if __name__=='__main__':main()
