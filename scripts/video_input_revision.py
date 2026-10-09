#!/usr/bin/env python3
"""Prepare or apply the reviewed video-input revision in an isolated instance."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import sys

from generation_review import existing_instance
from generation_workspace import generation_root
from audiovisual_design import future, reference
from video_input_design import load_audit, frame_plan, video_plan, FRAME_USE

ROOT = Path(__file__).resolve().parents[1]


def build(store, p):
    shots = sorted(p.current_records(store, {'AV_SHOT'}), key=lambda r:r['object_id'])
    audit = load_audit(shots)
    rows, pending, guards = [], {}, {r['object_id']:r['id'] for r in shots}

    def get(oid):
        row = p.record(store, oid); guards[oid] = row['id']; return row

    def add(oid, kind, payload):
        try:old=get(oid)
        except KeyError:old=None
        if old and payload == old['payload']:
            return reference(old)
        if oid in pending:
            raise ValueError('duplicate input revision: ' + oid)
        row={'object_id':oid,'kind':kind,'expected_version':old['version'] if old else 0,'payload':payload}
        rows.append(row); pending[oid]=row
        return future(oid)

    def kind(item):
        oid=item['reference']['object_id']
        return (pending[oid] if oid in pending else get(oid))['payload']['media_type']

    for shot in shots:
        sid=shot['object_id']; decision=audit[sid]
        frame=get('material-'+sid+'-first-frame')
        frame_payload=copy.deepcopy(frame['payload'])
        frame_payload['generation']=frame_plan(frame_payload['generation'], decision)
        frame_ref=add(frame['object_id'], 'REQUIREMENT', frame_payload)
        video=get('material-'+sid+'-video'); payload=copy.deepcopy(video['payload']); old_plan=payload['generation']
        first=old_plan['inputs'][0]
        relation=get(first['relation']['object_id']); rp=copy.deepcopy(relation['payload'])
        rp.update(title=FRAME_USE, purpose=FRAME_USE, preserve=shot['payload']['action_start']+'；已可见主体与空间',
                  type_label='起始图到镜头视频', check='普通参考不保证固定首帧；'+shot['payload']['action_end']+'；'+shot['payload']['continuity'])
        rp['upstream']=frame_ref
        first['relation']=add(relation['object_id'],'MATERIAL_RELATION',rp)
        if first['reference']['object_id']==frame['object_id']:
            first['reference']=frame_ref
        previous={i.get('relation',{}).get('object_id'):i for i in old_plan['inputs']}

        def supplement(value):
            state=get(value['state']); upstream=get('material-'+value['state']+'-overall')
            if upstream['payload']['scope'] != reference(state):
                raise ValueError('supplement must use current complete state: '+value['state'])
            oid='mr-video-input-'+sid+'-'+value['state']
            rp={'format':'production-material-relation-v1','title':value['use'],'purpose':value['use'],
                'blocks':[{'id':'purpose','text':value['use']}], 'upstream':reference(upstream), 'downstream_id':video['object_id'],
                'context':reference(shot),'type_id':'state-video','type_label':'镜内后续内容到视频','type_version':1,
                'type_definition':{'endpoints':['REQUIREMENT','REQUIREMENT'],'direction':'directed','attributes':{}},
                'attributes':{},'semantics':'reference','necessity':'required','basis':'production_choice','sources':shot['payload']['sources'],
                'preserve':state['payload']['title']+'的身份与完整状态；只取本镜需要显露的部分',
                'change':'按本镜时间顺序入画，不提前露脸、改站位或提前展示状态变化结果',
                'check':value['use']+'；只选本直接参考的准确候选，不自动附带祖先'}
            relation_ref=add(oid,'MATERIAL_RELATION',rp)
            prior=previous.get(oid)
            result=copy.deepcopy(prior) if prior else {'reference':reference(upstream),'selection_state':'unselected'}
            result.update(relation=relation_ref,use=value['use'])
            return result

        payload['generation']=video_plan(old_plan, decision, supplement, kind)
        add(video['object_id'],'REQUIREMENT',payload)
    return {'format':'production-import-v1','expected_heads':guards,'records':rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','apply'])
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); root=generation_root(ROOT); instance=existing_instance(root,args.instance)
    sys.path.insert(0,str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk import production as p
    store=Store(instance/'.runtime/review.sqlite3')
    try:
        document=build(store,p)
        if document['records']:
            result=p.import_records(store,document,validate_only=args.command=='plan')
        else:result={'records':[],'validated_only':args.command=='plan'}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({'format':'video-input-revision-receipt-v1','command':args.command,
            'counts':dict(Counter(r['kind'] for r in document['records'])),'result':result},ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'command':args.command,'counts':dict(Counter(r['kind'] for r in document['records'])),
                          'receipt':str(args.output)},ensure_ascii=False))
    finally:store.close()

if __name__=='__main__':main()
