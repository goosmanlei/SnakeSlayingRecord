#!/usr/bin/env python3
"""Plan/apply the reviewed full-state migration with exact-head concurrency guards.

All planning happens in a SQLite copy. Apply is a single production import,
with existing-head guards checked inside the same write transaction. Only use
this task's isolated instance until separately authorized formal integration.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from production_data import refresh_drafts
from production_inventory import compile_inventory, readable_inventory
from episode01_shots import compile_shots, render
from scene_requirements import compile_needs

ROOT=Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def plan(store, production):
    from review_desk.store import Store
    clone=Store(':memory:');store.db.backup(clone.db);clone.db_path=store.db_path
    original=production.current_records(store)
    changes=[]
    try:
        inventory=compile_inventory()
        changes.extend(refresh_drafts(clone,production,inventory,apply=True)['records'])
        shots,cues,frames=compile_shots(clone,production)
        changes.extend(refresh_drafts(clone,production,shots,apply=True)['records'])
        needs,counts=compile_needs(clone,production)
        changes.extend(refresh_drafts(clone,production,needs,apply=True)['records'])
        active_needs={r['object_id'] for r in needs['records']}
        withdrawals=[]
        for r in original:
            if r['kind']=='REQUIREMENT' and r['object_id'].startswith('need-preparation-') and r['object_id'] not in active_needs and r['payload'].get('status')!='withdrawn':
                payload=deepcopy(r['payload']);payload.update(required=False,status='withdrawn',withdrawal_reason='逐场复核版本四后，此项仅被提及或改由准确的出场对象登记；旧需求与来源保留。')
                withdrawals.append({'object_id':r['object_id'],'kind':r['kind'],'expected_version':r['version'],'payload':payload})
        if withdrawals:
            production.import_records(clone,{'format':'production-import-v1','records':withdrawals});changes.extend(withdrawals)
        if len({r['object_id'] for r in changes})!=len(changes):raise ValueError('migration changed one object twice')
        full=[r for r in production.current_records(clone,{'STATE'}) if r['payload'].get('state_model')=='complete-v1']
        old_to_full=[]
        for old in original:
            if old['kind']!='STATE' or old['payload'].get('state_model')=='complete-v1':continue
            owner=old['payload']['entity']['object_id']
            old_scenes={s.get('scene_id') for s in old['payload']['sources']}
            matches=[r for r in full if r['payload']['entity']['object_id']==owner and old_scenes & {s.get('scene_id') for s in r['payload']['sources']}]
            old_to_full.append({'old':{'object_id':old['object_id'],'revision_id':old['id']},'entity':owner,
                                'complete_states':[{'object_id':r['object_id'],'revision_id':r['id']} for r in matches],
                                'review':'语义对应供复核；不是素材兼容或自动替换结论'})
        heads=production.current_records(clone)
        from review_desk.production_states import scope_coverage
        coverage=scope_coverage(clone,[r for r in heads if r['kind'] in ('PREPARATION','SHOT_DESIGN')],heads)
        if coverage['issues']:raise ValueError('migration still has state coverage errors: '+str(coverage['issues'][:5]))
        protected=[r for r in original if r['kind'] in ('ASSET','CALL','RELATION','JUDGMENT') or
                   (r['kind']=='STATE' and r['payload'].get('state_model')!='complete-v1')]
        for r in protected:
            if production.record(clone,r['object_id'])['id']!=r['id']:raise ValueError('migration changed protected actual/history record')
        result={'format':'complete-state-migration-v1','source_sha256':json.loads((ROOT/'production/source-lock.json').read_text())['screenplay']['file_sha256'],
                'guards':{r['object_id']:r['id'] for r in original},
                'document':{'format':'production-import-v1','records':changes},
                'summary':{'changed_records':len(changes),'changed_by_kind':dict(Counter(r['kind'] for r in changes)),
                           'entities':len([r for r in heads if r['kind']=='ENTITY']),'complete_states':len(full),
                           'legacy_states_preserved':len(old_to_full),'checked_entity_uses':coverage['checked_count'],
                           'state_coverage_issues':coverage['issues'],'withdrawn_needs':[r['object_id'] for r in withdrawals],
                           'protected_heads_digest':digest({r['object_id']:r['id'] for r in protected})},
                'correspondence':old_to_full,
                'affected': [{'object_id':r['object_id'],'kind':r['kind'],'old_revision':next((o['id'] for o in original if o['object_id']==r['object_id']),None),
                              'new_revision':production.record(clone,r['object_id'])['id']} for r in changes],
                'remaining_review':['旧图像和录音尚未声明覆盖新完整状态；需逐份核对后显式建立候选关联和采用。','完整状态的具体造型、声音及连续性选择仍待第一轮制作基准审阅。']}
        result['document_sha256']=digest(result['document'])
        artifacts={'inventory':inventory,'shots':shots,'cues':cues,'frames':frames,'needs':needs,'counts':counts,
                   'names':{r['object_id']:r['payload']['title'] for r in heads}}
        return result,artifacts
    finally:clone.close()


def apply(store,production,value):
    if value.get('format')!='complete-state-migration-v1' or digest(value['document'])!=value['document_sha256']:
        raise ValueError('migration document checksum differs')
    if hashlib.sha256((ROOT/'imports/screenplay-04.json').read_bytes()).hexdigest()!=value['source_sha256']:
        raise ValueError('approved screenplay changed; do not silently switch input')
    if not value['document']['records']:return {'records':[],'already_current':True}
    # import_records owns its transaction. Its guards are rechecked under BEGIN
    # IMMEDIATE, so another writer cannot race the precondition and batch import.
    document={**value['document'],'expected_heads':value['guards']}
    return production.import_records(store,document)


def write_artifacts(artifacts):
    for name,key in [('inventory.json','inventory'),('episode01/shots.json','shots'),('episode01/dialogue-cues.json','cues'),('scene-requirements.json','needs')]:
        (ROOT/'production'/name).write_text(json.dumps(artifacts[key],ensure_ascii=False,indent=2)+'\n')
    (ROOT/'production/inventory.md').write_text(readable_inventory(artifacts['inventory']))
    (ROOT/'production/episode01/shots.md').write_text(render(artifacts['shots'],artifacts['cues'],artifacts['frames'],artifacts['names']))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['plan','apply'])
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--file',type=Path,required=True);parser.add_argument('--write-artifacts',action='store_true');args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production
    store=Store(args.instance.resolve()/'.runtime/review.sqlite3')
    try:
        if args.command=='plan':
            value,artifacts=plan(store,production);args.file.parent.mkdir(parents=True,exist_ok=True)
            args.file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
            if args.write_artifacts:write_artifacts(artifacts)
            print(json.dumps(value['summary'],ensure_ascii=False))
        else:
            value=json.loads(args.file.read_text());result=apply(store,production,value)
            print(json.dumps({'applied_records':len(result['records'])}))
    finally:store.close()


if __name__=='__main__':main()
