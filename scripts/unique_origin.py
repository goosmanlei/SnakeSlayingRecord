"""Prepare reviewed state handoffs and small irreversible retirement receipts.

This story adapter does not decide which states are necessary. Decisions must
name every affected state, the reason, and the actual destination of conditions.
The desk owns the atomic transaction and immutable history safeguards.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

FROZEN = {'method_basis', 'method_adjustment', '_method_binding', 'initial_plan_source'}
LISTS = {'states','continuity_context','sources','contexts','previous_states'}


def build(store, decisions):
    from review_desk import production as p, production_current as current, semantic_consolidation as semantic
    rows={r['object_id']:r for r in p.current_records(store) if r['kind'] in current.RECORD_KINDS}
    for oid in decisions['states']:
        if oid not in rows:
            retired=p.record(store,oid)
            semantic.validate_retirement(store,oid,'STATE',retired['payload'])
    reviewed={oid:d for oid,d in decisions['states'].items() if oid in rows}
    removed={oid:choice for oid,choice in reviewed.items() if choice['action']=='remove'}
    replacements={oid:d['replace_with'] for oid,d in removed.items() if d.get('replace_with')}
    for oid,target in replacements.items():
        if (target not in rows or rows[target]['kind']!='STATE' or target in removed or
                rows[target]['payload'].get('status')=='withdrawn' or
                rows[target]['payload']['entity']!=rows[oid]['payload']['entity']):
            raise ValueError('state reuse requires a retained form of the same exact entity: '+oid)
    handoff_needs={v['object_id']:v for d in removed.values() for v in d.get('requirement_handoffs',[])}
    for item in handoff_needs.values():
        if rows[item['object_id']]['kind']!='REQUIREMENT' or rows[item['scope']]['kind'] not in ('ENTITY','AV_SHOT'):
            raise ValueError('a reviewed requirement handoff needs an existing entity or shot')
    for oid,choice in reviewed.items():
        row=rows.get(oid)
        if not row or row['kind']!='STATE' or row['payload'].get('status')=='withdrawn':
            raise ValueError('review target is not an active state: '+oid)
        if choice['action'] not in ('retain','remove') or not choice['reason']:
            raise ValueError('explicit semantic decision required: '+oid)
        if oid in removed and (choice.get('destination') not in ('entity','shot') or not choice.get('condition')):
            raise ValueError('condition destination required: '+oid)
    def refs(value):
        return [(path,ref) for path,ref in p.references(value) if not any('.'+key in path for key in FROZEN)]
    def add_block(payload, name, text):
        old=next((b for b in payload.get('blocks',[]) if b['id']==name),None)
        if old:
            if text not in old['text']:old['text']+='\n'+text
        else:payload.setdefault('blocks',[]).append({'id':name,'text':text})
    consumers={oid:[] for oid in reviewed}
    for oid,row in rows.items():
        if row['payload'].get('status')=='withdrawn':continue
        for path,ref in refs(row['payload']):
            if ref['object_id'] in consumers:consumers[ref['object_id']].append({'object_id':oid,'kind':row['kind'],'path':path})
    def rewrite(value, key=None):
        if key in FROZEN:return copy.deepcopy(value)
        if isinstance(value,list):
            if key in LISTS:
                result=[]
                for v in value:
                    if v.get('object_id') in removed and v.get('object_id') not in replacements:continue
                    item=rewrite(v)
                    if not result or item!=result[-1]:result.append(item)
                return result
            if key=='state_transitions':
                result=[]
                for v in value:
                    if any(ref['object_id'] in removed and ref['object_id'] not in replacements for _,ref in refs(v)):continue
                    item=rewrite(v)
                    if item['from']!=item['to']:result.append(item)
                return result
            return [rewrite(v) for v in value]
        if not isinstance(value,dict):return value
        if value.get('object_id') in replacements and 'revision_id' in value:
            target=rows[replacements[value['object_id']]]
            return {**copy.deepcopy(value),'object_id':target['object_id'],'revision_id':target['id']}
        return {k:rewrite(v,k) for k,v in value.items()}
    patches={}
    for oid,row in rows.items():
        body=row['payload']
        if row['kind'] not in current.CURRENT_KINDS or oid in removed or body.get('status')=='withdrawn':continue
        value=rewrite(body)
        if oid in handoff_needs:
            handoff=handoff_needs[oid]
            value['scope']={'object_id':handoff['scope'],'revision_id':rows[handoff['scope']]['id']}
            value['title']=handoff['title']
            if value.get('generation'):value['generation']['output']['name']=handoff['title']
            value['specification'].pop('reference_role',None)
            if rows[handoff['scope']]['kind']=='ENTITY':
                value['entities']=[{'object_id':handoff['scope'],'revision_id':rows[handoff['scope']]['id']}]
        for sid,d in removed.items():
            target=d.get('replace_entity')
            if (not target or row['kind'] not in ('REQUIREMENT','AV_SHOT') or
                    not any(ref['object_id']==sid for _,ref in refs(body))):continue
            if target not in rows or rows[target]['kind']!='ENTITY':raise ValueError('identity destination is not an entity')
            original_owner=rows[sid]['payload']['entity']['object_id']
            entities=value.setdefault('entities',[])
            if d.get('replace_consumer_entity'):
                entities[:]=[ref for ref in entities if ref['object_id']!=original_owner]
            if not any(ref['object_id']==target for ref in entities):
                entities.append({'object_id':target,'revision_id':rows[target]['id']})
        if row['kind']=='ENTITY':
            additions=[d['condition'] for sid,d in removed.items() if d['destination']=='entity' and d.get('condition_entity', rows[sid]['payload']['entity']['object_id'])==oid]
            if additions:value['production_description']='\n'.join([body.get('production_description',''),*additions]).strip()
            # The prose block and editable description are the same content;
            # keep the existing block identity (and opinions), avoid two copies.
            if additions:
                if len(value.get('blocks',[])) == 1 and value['blocks'][0]['id']=='description':
                    value['blocks'][0]['text']=value['production_description']
                else:
                    add_block(value,'production-conditions','\n'.join(additions))
        if row['kind']=='AV_SHOT':
            used={ref['object_id'] for ref in body.get('states',[])+body.get('continuity_context',[])}
            additions=[d['condition'] for sid,d in removed.items() if sid in used and d['destination']=='shot']
            if additions:
                add_block(value,'state-handoff',
                    '只核对本镜实际起止与已经发生的阶段，后续变化不能提前。\n'+'\n'.join(additions))
        handoffs=[]
        if row['kind']=='REQUIREMENT' and body['scope']['object_id'] in rows and rows[body['scope']['object_id']]['kind']=='AV_SHOT':
            shot=rows[body['scope']['object_id']]['payload']
            used={ref['object_id'] for ref in body.get('states',[])}
            # A first frame only uses its declared start states. A video also
            # consumes the shot's ordered changes and continuity context.
            if body['media_type']=='video':used.update(ref['object_id'] for ref in shot.get('states',[])+shot.get('continuity_context',[]))
            for sid,d in removed.items():
                if sid not in used or d['destination']!='shot':continue
                condition=d.get('audio_condition') if body['media_type']=='audio' else d['condition']
                if condition:handoffs.append(condition)
            if handoffs:
                # Cross-shot conditions belong to the preparation/review body,
                # not to a model Prompt that would execute later actions now.
                lead=('只检查本镜起点与已发生阶段，后续动作不得提前画入首帧。'
                      if body['media_type']=='image' else
                      '对照本镜原有起点、动作与落点，只执行本镜阶段；跨镜顺序作为核对依据。')
                add_block(value,'continuity-conditions',lead+'\n'+'\n'.join(handoffs))
        unresolved=[(path,ref['object_id']) for path,ref in refs(value) if ref['object_id'] in removed]
        if unresolved:raise ValueError('current consumer needs an explicit handoff: '+oid+' '+str(unresolved))
        if value!=body:patches[oid]=value
    audit=[]
    for oid,choice in reviewed.items():
        row=rows[oid]
        direct=[r['object_id'] for r in rows.values() if r['kind']=='REQUIREMENT' and r['payload'].get('status')!='withdrawn' and r['payload']['scope']['object_id']==oid]
        if oid in removed and any(mid not in handoff_needs for mid in direct):
            raise ValueError('state still owns requirements without reviewed handoff: '+oid+' '+str(direct))
        audit.append({'object_id':oid,'title':row['payload']['title'],'content_sha256':current.checksum(row['payload']),
            **choice,'direct_requirements':direct,'consumers':consumers[oid],
            'updated_consumers':sorted({c['object_id'] for c in consumers[oid] if c['object_id'] in patches})})
    choices={'retire':[{'source':oid,'reason':d['reason']} for oid,d in removed.items()],
             'updates':[{'object_id':oid,'payload':body,'reason':'已审状态条件承接到实际身份或镜头方案，移除失效状态引用。'} for oid,body in patches.items()]}
    return semantic.prepare(store,choices),audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    sub=parser.add_subparsers(dest='command',required=True)
    prepare=sub.add_parser('prepare');prepare.add_argument('--decisions',type=Path,required=True);prepare.add_argument('--output',type=Path,required=True);prepare.add_argument('--audit',type=Path,required=True)
    apply=sub.add_parser('apply');apply.add_argument('--plan',type=Path,required=True);apply.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p, semantic_consolidation as semantic
    store=Store(args.database)
    try:
        if args.command=='prepare':
            with p.read_scope(store):plan,audit=build(store,json.loads(args.decisions.read_text()))
            for path,value in ((args.output,plan),(args.audit,audit)):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({'plan':plan['id'],'retire':len(plan['reasons']),'updates':len(plan['patches']),'reviewed':len(audit)}))
        else:
            receipt=semantic.apply(store,json.loads(args.plan.read_text()))
            args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({'retired':len(receipt['retired']),'changed':len(receipt['changed_objects']),'already_applied':receipt['already_applied']}))
    finally:store.close()


if __name__=='__main__':main()
