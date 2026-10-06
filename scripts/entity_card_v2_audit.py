#!/usr/bin/env python3
"""Audit cleanup identities and every indexed/embedded historical reference."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def audit(system,db,output):
    sys.path.insert(0,str(system.resolve()))
    from review_desk import production as p,state_cleanup as cleanup
    from review_desk.store import Store,digest,canonical
    s=Store(db)
    try:
        plan=cleanup.plan(s);ids={r['object_id'] for r in plan['states']};rids={r['revision_id'] for r in plan['revisions']}
        by={r['id']:r for r in s.objects()};revs={r['id']:r for r in s.revisions()};refs={rid:[] for rid in rids}
        with p.read_scope(s):
            for rev in revs.values():
                for role,ref in p.references(json.loads(rev['payload'])):
                    if ref['revision_id'] in refs:refs[ref['revision_id']].append({'object_id':rev['object_id'],'revision_id':rev['id'],'kind':by[rev['object_id']]['kind'],'current':by[rev['object_id']]['current_revision']==rev['id'],'path':role,'reference':ref})
        deps=[{**d,'from_object_id':revs[d['from_revision']]['object_id'],'from_kind':by[revs[d['from_revision']]['object_id']]['kind'],'current':by[revs[d['from_revision']]['object_id']]['current_revision']==d['from_revision']} for d in s.dependencies() if d['to_revision'] in rids]
        states=[]
        for target in plan['states']:
            versions=[r for r in plan['revisions'] if r['object_id']==target['object_id']];incoming=[v for r in versions for v in refs[r['revision_id']]]
            related_ids={v['object_id'] for v in incoming};media=[r for r in s.revisions() if r['object_id'] in related_ids and by[r['object_id']]['kind']=='ASSET']
            components=[{'asset':r['object_id'],'revision_id':r['id'],'file':v['file'],'sha256':v['sha256'],'bytes':v['bytes']} for r in media for v in json.loads(r['payload']).get('components',[])]
            title=json.loads(revs[target['current_revision']]['payload'])['title']
            states.append({**target,'title':title,'revisions':versions,'references':incoming,'materials_and_calls':sorted(related_ids),'components':components,'comments':[c for c in s.comments() if c['target_object_id'] in related_ids|{target['object_id']}],
                'disposition':'删除独立STATE及全部正文；修订索引改为无正文删除凭据，原引用逐条保持，准确目标显示已清理；不建立等价映射。',
                'export_and_recovery':'仅净化后的Schema 7及相容读取器可恢复；旧重放定义移除或禁用，已提交Git历史不改写。'})
        value={'format':'entity-card-v2-cleanup-audit-v1','states':states,'dependencies':deps,'counts':{'states':len(states),'revisions':len(rids),'dependencies':len(deps),'embedded_references':sum(map(len,refs.values())),'state_comments':len(plan['comments'])},'current_inbound_kinds':dict(Counter(d['from_kind'] for d in deps if d['current'])),'unresolved':[], 'plan_sha256':digest(canonical(plan).encode())}
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        return value['counts']
    finally:s.close()

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--system',type=Path,required=True);a.add_argument('--db',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args();print(json.dumps(audit(args.system,args.db,args.output)))
