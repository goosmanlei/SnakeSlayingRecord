"""Preserve minimal publication idempotency receipts alongside the current export."""
import hashlib
import json
from pathlib import Path

RECOVERY='production/audiovisual/recovery.json'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def export_publication_receipts(store,root):
    from review_desk import version_consolidation as vc
    runs=[dict(r) for r in store.db.execute('SELECT id,receipt FROM consolidation_runs ORDER BY id')]
    if not runs:return
    exists=store.db.execute("SELECT 1 FROM sqlite_master WHERE name='generation_publications'").fetchone()
    rows=[dict(r) for r in store.db.execute('SELECT * FROM generation_publications ORDER BY id')] if exists else []
    save(root/RECOVERY,{'format':'production-publication-receipts-v1','cutovers':[r['id'] for r in runs],'generation_publications':rows})
    path=root/'config/instance.json';config=json.loads(path.read_text())
    policy=config.get('version_consolidation_policy',{})
    policy.update(ledger_sha256=vc.ledger_hash(vc.dump(store)),publication_receipts_sha256=sha(root/RECOVERY))
    config['version_consolidation_policy']=policy
    cutovers=[r['id'] for r in runs if json.loads(r['receipt']).get('format')=='production-cutover-result-v1']
    if len(cutovers)>1:raise ValueError('ambiguous audiovisual cutover')
    if cutovers:config['audiovisual_policy']={'schema_version':9,'cutover_id':cutovers[0]}
    save(path,config)

def restore_publication_receipts(store,root):
    config=json.loads((root/'config/instance.json').read_text())
    policy=config.get('version_consolidation_policy',{})
    path=root/RECOVERY
    if sha(path)!=policy.get('publication_receipts_sha256'):raise ValueError('publication recovery receipt changed')
    document=json.loads(path.read_text())
    expected={r[0] for r in store.db.execute('SELECT id FROM consolidation_runs')}
    if document.get('format')!='production-publication-receipts-v1' or set(document['cutovers'])!=expected:raise ValueError('publication recovery baseline differs')
    with store.db:
        store.db.execute('CREATE TABLE IF NOT EXISTS generation_publications (id TEXT PRIMARY KEY,receipt TEXT NOT NULL)')
        for row in document['generation_publications']:
            old=store.db.execute('SELECT receipt FROM generation_publications WHERE id=?',(row['id'],)).fetchone()
            if old and old[0]!=row['receipt']:raise ValueError('publication receipt collision')
            store.db.execute('INSERT OR IGNORE INTO generation_publications VALUES (?,?)',(row['id'],row['receipt']))
    return len(document['generation_publications'])
