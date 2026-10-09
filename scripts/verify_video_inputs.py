#!/usr/bin/env python3
"""Read-only verification of the story's reviewed video input responsibilities."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from video_input_design import load_audit, EXECUTION


def verify(store, p, ic, g):
    shots=sorted(p.current_records(store,{'AV_SHOT'}),key=lambda r:r['object_id']); audit=load_audit(shots)
    counts=Counter(); samples=[]
    with p.read_scope(store):
        for shot in shots:
            sid=shot['object_id']; rule=audit[sid]; need=p.record(store,'material-'+sid+'-video'); plan=need['payload']['generation']
            assert plan['execution']==EXECUTION,sid
            assert '已选首帧' not in plan['prompt'],sid
            declarations=[{'media_type':p.ref_record(store,i['reference'])['payload']['media_type'],'role':i.get('role')} for i in plan['inputs']]
            checked=ic.planned_contract(plan,declarations)
            assert checked['verified'],(sid,checked)
            expected=[v['state'] for v in rule.get('supplements',[])]
            supplement_ids=[i['relation']['object_id'] for i in plan['inputs'] if i.get('relation',{}).get('object_id','').startswith('mr-video-input-')]
            assert supplement_ids==['mr-video-input-'+sid+'-'+s for s in expected],sid
            for state in expected:
                assert 'material-'+state+'-overall' in {p.ref_record(store,i['relation'])['payload']['upstream']['object_id'] for i in plan['inputs']},sid
            ready=g.readiness(store,need['object_id'])
            if any(i.get('selection_state')=='unselected' for i in plan['inputs']):
                assert not ready['ready'],sid
            counts[rule['decision']]+=1;counts[plan['model']]+=1
            if rule['label'] in ('ASH001','ASH004','ASH012','ASH152','ASH218','ASH333'):
                samples.append({'shot':rule['label'],'material':need.get('business_code'),'revision':need['id'],
                    'execution':plan['execution'],'roles':[i['role'] for i in plan['inputs']],
                    'ready':ready['ready'],'input_contract':checked['verified'],'issues':ready['issues']})
    return {'format':'video-input-verification-v1','scenes':len({s['object_id'].rsplit('-s',1)[0] for s in shots}),
            'shots':len(shots),'counts':dict(counts),'samples':samples,
            'scope':'方案职责、模式和准备闸门；没有真实生成与媒体效果验收'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--db',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk import production as p,input_contracts as ic,generation as g
    store=Store.open_readonly(args.db)
    try:result=verify(store,p,ic,g)
    finally:store.close()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},ensure_ascii=False))

if __name__=='__main__':main()
