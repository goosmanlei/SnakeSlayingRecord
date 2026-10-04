#!/usr/bin/env python3
"""Compare an isolated applied migration with its exact logical/physical baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('system','instance','baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store,canonical
    from review_desk import material_model as model,material_storage as storage,material_archives as archives,production,material_plans
    root=args.instance.resolve();base=args.baseline.resolve()
    if Path(__file__).resolve().parents[1]/'.runtime' not in root.parents:raise ValueError('physical evidence requires this worktree isolated instance')
    store=Store(root/'.runtime/review.sqlite3')
    original=sqlite3.connect((base/'.runtime/generation-base.sqlite3').as_uri()+'?mode=ro',uri=True);original.row_factory=sqlite3.Row
    try:
        doc=model.load_migration(root/'migration.json');result=model.verify(store)
        logical=store.revisions();before=[dict(r) for r in original.execute('SELECT * FROM revisions ORDER BY object_id,version')]
        if before!=logical:raise ValueError('logical historical revisions differ')
        protected={}
        changed={'revisions','material_plan_versions',*storage.TABLES}
        tables=[r[0] for r in original.execute("SELECT name FROM sqlite_master WHERE type='table'") if r[0] not in changed]
        for table in sorted(tables):
            old=sorted([tuple(r) for r in original.execute('SELECT * FROM '+table)],key=repr)
            new=sorted([tuple(r) for r in store.db.execute('SELECT * FROM '+table)],key=repr)
            if old!=new:raise ValueError('business identity/history changed: '+table)
            protected[table]=len(old)
        archive_list=[]
        for row in doc['archives']:
            name=row.get('path','export/assets/'+row['file']);path=root/name
            actual=hashlib.sha256(archives.read_bytes(path)).hexdigest()
            if actual!=row['before_sha256']:raise ValueError('archive original differs: '+name)
            archive_list.append({'path':name,'original_sha256':actual,'physical_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        media={}
        for row in before:
            for component in json.loads(row['payload']).get('components',[]):
                if component.get('mime','').split('/')[0] in ('image','audio','video'):
                    name=component['file'];old=(base/'export/assets'/name).read_bytes();new=(root/'export/assets'/name).read_bytes()
                    if old!=new or hashlib.sha256(new).hexdigest()!=component['sha256']:raise ValueError('media bytes changed: '+name)
                    media[name]=component['sha256']
        mid='need-form-li-ji-paste-voice';aid='asset-fg3-li-ji-base-voice-01'
        identity=storage.identity(store,mid);versions=material_plans.snapshot(store,mid);v2=next(v for v in versions if v['number']==2)
        if len(identity['associations'])!=13 or not any(r['object_id']==aid for r in v2['members']):raise ValueError('LiJi version/state invariant failed')
        prompt=production.record(store,'call-fg3-li-ji-base-voice-01')['payload']['prompt'];node=canonical({'value':prompt});node_key=hashlib.sha256(node.encode()).hexdigest()
        if store.db.execute('SELECT count(*) FROM material_content WHERE body=?',(node,)).fetchone()[0]!=1:raise ValueError('prompt leaf is not unique')
        store.db.execute('PRAGMA secure_delete=ON');checkpoint=tuple(store.db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())
        if checkpoint[0]:raise ValueError('WAL checkpoint remains busy')
        physical={'wal_checkpoint':list(checkpoint),'sqlite_complete_leaf_occurrences':store.db_path.read_bytes().count(node.encode()),
                  'export_graph_complete_leaf_occurrences':(root/'export/material-content.json').read_bytes().count(json.dumps(node,ensure_ascii=False).encode()),
                  'export_objects_prompt_occurrences':(root/'export/objects.json').read_bytes().count(prompt.encode()),
                  'managed_archive_prompt_occurrences':sum((root/r['path']).read_bytes().count(prompt.encode()) for r in archive_list),
                  'sqlite_bytes':store.db_path.stat().st_size,'content_graph_bytes':(root/'export/material-content.json').stat().st_size,'prompt_leaf_id':node_key}
        if physical['sqlite_complete_leaf_occurrences']!=1 or physical['export_graph_complete_leaf_occurrences']!=1 or physical['export_objects_prompt_occurrences'] or physical['managed_archive_prompt_occurrences']:raise ValueError('physical definition deduplication failed')
        result.update(format='material-model-data-evidence-v1',migration_id=doc['id'],system_head=doc['system_head'],counts=doc['counts'],
            original_revision_json_equal=True,protected_tables=protected,real_media_files=len(media),real_media_bytes_unchanged=True,
            physical=physical,archives=archive_list,li_ji={'material_id':mid,'associations':identity['associations'],
                'version_2_definition_id':v2['definition_id'],'version_2_provenance':v2['definition_provenance'],'version_2_gaps':v2['definition_gaps']})
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('archives','li_ji')},ensure_ascii=False,indent=2))
    finally:store.close();original.close()


if __name__=='__main__':main()
