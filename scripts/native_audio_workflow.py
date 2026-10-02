#!/usr/bin/env python3
"""Migrate this story to Seedance native audiovisual shots; no model calls.

plan creates a reviewable, guarded import. apply physically removes only unused
REQUIREMENT histories and imports revised descriptions through the same service.
Original media, actual calls, screenplay and all user comments remain intact.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from migrate_complete_states import digest

ROOT=Path(__file__).resolve().parents[1]
MELODIES={'need-form-boat-song-short-overall','need-form-blue-awning-song-complete-overall',
          'need-form-snake-welcome-song-chorus-overall','need-form-blessing-stage-song-distant-overall'}
KEEP_OVERALL=MELODIES|{'need-form-offscreen-caller-base-overall'}
DESCRIPTION_FORMS={'form-stage-drum-audible','form-blue-awning-song-missing','form-blue-awning-song-practice',
                   'form-blue-awning-song-soft','form-blue-awning-song-teaching'}
AUDIO_MODE='seedance-native-audio-v1'


def ref(row):return {'object_id':row['object_id'],'revision_id':row['id']}


def obsolete(row):
    return (row['kind']=='REQUIREMENT' and row['payload']['media_type']=='audio' and
            row['payload']['slot']!='voice' and row['object_id'] not in KEEP_OVERALL)


def plan(store,p):
    from review_desk.store import Store
    from review_desk.production_states import scope_coverage
    original=p.current_records(store);by={r['object_id']:r for r in original}
    targets=[r for r in original if obsolete(r)]
    deleted_ids={r['object_id'] for r in targets}
    revisions=[r for r in store.revisions() if r['object_id'] in deleted_ids]
    clone=Store(':memory:');store.db.backup(clone.db);clone.db_path=store.db_path
    changes=[];resolved={}
    def put(row,payload):
        if row['payload']==payload:return row
        item={'object_id':row['object_id'],'kind':row['kind'],'expected_version':row['version'],'payload':payload}
        p.import_records(clone,{'format':'production-import-v1','records':[item]});changes.append(item)
        resolved[row['object_id']]=p.record(clone,row['object_id']);return resolved[row['object_id']]
    def update_refs(payload):
        for _,r in p.references(payload):
            if r['object_id'] in resolved and r['revision_id']==by[r['object_id']]['id']:
                r['revision_id']=resolved[r['object_id']]['id']
        return payload
    try:
        removals=[ref(r) for r in targets]
        if removals:p.import_records(clone,{'format':'production-import-v1','records':[], 'remove_unreferenced_requirements':removals})
        for oid in sorted(DESCRIPTION_FORMS):
            row=by[oid];payload=deepcopy(row['payload']);payload['reference_mode']='description'
            if not payload.get('production_description'):payload['production_description']='\n'.join(b['text'] for b in payload['blocks'])
            payload['sound_delivery']='按本状态的歌词范围、表演与时空描述，随镜头生成声音；不要求此状态独立录音。'
            put(row,payload)
        needs={r['object_id']:r for r in original if r['kind']=='REQUIREMENT' and r['object_id'] not in deleted_ids}
        ordered=[];pending=dict(needs)
        while pending:
            available=[r for r in pending.values() if not any(i['reference']['object_id'] in pending for i in r['payload'].get('generation',{}).get('inputs',[]))]
            if not available:raise ValueError('cyclic generation requirements')
            for r in available:ordered.append(r);del pending[r['object_id']]
        for kind in ('PREPARATION','SHOT_DESIGN','REQUIREMENT'):
            for row in ordered if kind=='REQUIREMENT' else original:
                if row['kind']!=kind or row['object_id'] in deleted_ids:continue
                payload=update_refs(deepcopy(row['payload']))
                if kind=='SHOT_DESIGN':
                    payload['audio_delivery']=AUDIO_MODE
                    for event in payload['sound']:
                        event['delivery']='native_audio';event['timing_status']='镜内预计窗口，随画面生成后实际观看与听辨复核'
                    payload['animatic_method']='Seedance 2.0 有声视听预演；不是正式镜头交付'
                if kind=='REQUIREMENT' and payload['media_type']=='audio':
                    payload['usage']='generation_input'
                    payload['audio_role']='melody_reference' if row['object_id'] in MELODIES else 'voice_reference'
                    payload['specification']['reference_intent']='参考音色或旋律，镜内歌词与台词另由定稿文本约束；不是后配成品轨'
                    generation=payload.get('generation')
                    if generation:
                        generation['prompt']=generation['prompt'].replace('实际镜内对白仍单独录制','实际镜内对白随画面生成').replace('环境与音乐另轨','不生成环境或伴奏；该音频仅作音色／旋律参考')
                        generation['output']['description']=generation['output']['description'].replace('实际镜内对白仍单独录制','实际镜内对白随画面生成')
                put(row,payload)
        # New candidate associations follow the revised intent; old asset/CALL
        # revisions and all physical files stay exact and recoverable.
        for row in original:
            if row['kind']!='ASSET':continue
            payload=deepcopy(row['payload']);update_refs(payload.get('candidate_requirements',[]))
            put(row,payload)
        heads=p.current_records(clone)
        coverage=scope_coverage(clone,[r for r in heads if r['kind'] in ('PREPARATION','SHOT_DESIGN')],heads)
        if coverage['issues']:raise ValueError(coverage['issues'][:8])
        from review_desk import generation as g
        from generation_design import ENTITIES
        for key in ENTITIES:
            prep=g.preparation(clone,g.current_scope(clone,'entity-'+key,heads))
            if not prep['complete']:raise ValueError(prep['issues'])
        document={'format':'production-import-v1','expected_heads':{r['object_id']:r['id'] for r in original},
                  'remove_unreferenced_requirements':removals,'records':changes}
        return {'format':'native-audio-migration-v1','source_sha256':hashlib.sha256((ROOT/'imports/screenplay-04.json').read_bytes()).hexdigest(),
                'document':document,'document_sha256':digest(document),
                'removed':[{'object_id':r['object_id'],'title':r['payload']['title'],'slot':r['payload']['slot']} for r in targets],
                'summary':{'removed_requirements':len(targets),'removed_revisions':len(revisions),'removed_files':0,
                           'changed':dict(Counter(r['kind'] for r in changes)),
                           'remaining_audio_requirements':sum(r['kind']=='REQUIREMENT' and r['payload']['media_type']=='audio' for r in heads),
                           'checked_uses':coverage['checked_count'],'coverage_issues':coverage['issues']}}
    finally:clone.close()


def apply(store,p,value):
    if value['document_sha256']!=digest(value['document']):raise ValueError('migration checksum differs')
    if value['source_sha256']!=hashlib.sha256((ROOT/'imports/screenplay-04.json').read_bytes()).hexdigest():raise ValueError('screenplay changed')
    return p.import_records(store,value['document']) if value['document']['records'] or value['document']['remove_unreferenced_requirements'] else {'already_current':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['plan','apply']);parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True);parser.add_argument('--file',type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p
    store=Store(args.instance.resolve()/'.runtime/review.sqlite3')
    try:
        if args.command=='plan':
            value=plan(store,p);args.file.parent.mkdir(parents=True,exist_ok=True);args.file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps(value['summary'],ensure_ascii=False))
        else:
            value=json.loads(args.file.read_text());result=apply(store,p,value);print(json.dumps({'removed':len(result.get('removed',[])),'updated':len(result.get('records',[]))}))
    finally:store.close()

if __name__=='__main__':main()
