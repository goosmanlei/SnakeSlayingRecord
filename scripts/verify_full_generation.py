#!/usr/bin/env python3
"""Verify an append-only generation registration against read-only snapshots."""
import argparse
from collections import Counter
import json
from pathlib import Path
from verify_production_review import read_tables


def verify(before, after, registration):
    old,new=read_tables(before),read_tables(after)
    if old.keys()!=new.keys(): raise ValueError('unexpected schema change')
    records=[r for b in registration['batches'] for r in b['records']]
    allowed={r['object_id'] for r in records}
    decisions=set(registration.get('user_master_decisions',[]))
    for record in records:
        if record['kind'] in ('REQUIREMENT','CALL','ASSET'): continue
        payload=record['payload']
        if (record['kind']!='JUDGMENT' or record['object_id'] not in decisions
                or record['expected_version']!=0 or payload.get('actor')!='user'
                or payload.get('review_type')!='generation_master' or payload.get('verdict')!='accepted'
                or payload.get('evidence',{}).get('source')!='user_conversation'):
            raise ValueError('unexpected record kind or ungrounded master decision')
    old_objects={r[0]:r for r in old['objects']};new_objects={r[0]:r for r in new['objects']}
    if old_objects.keys()-new_objects.keys(): raise ValueError('existing identity disappeared')
    changed={oid for oid in new_objects if new_objects[oid]!=old_objects.get(oid)}
    if changed!=allowed: raise ValueError('changed heads differ from registration')
    protected={}
    for table in old.keys()-{'objects','revisions','dependencies','material_rounds','material_members'}:
        if Counter(old[table])!=Counter(new[table]): raise ValueError('protected table changed: '+table)
        protected[table]=len(old[table])
    for table in ('revisions','dependencies','material_members'):
        if Counter(old[table])-Counter(new[table]): raise ValueError('old history changed: '+table)
    added=list((Counter(new['revisions'])-Counter(old['revisions'])).elements())
    if len(added)!=len(records) or {r[1] for r in added}!=allowed: raise ValueError('unexpected revisions')
    revisions={(r[1],r[2]):r for r in new['revisions']}
    for spec in records:
        payload=json.loads(json.dumps(spec['payload']))
        def resolve(value):
            if isinstance(value,dict):
                if isinstance(value.get('revision_id'),str) and value['revision_id'].startswith('@'):
                    target=value['object_id'];versions=[s['expected_version']+1 for s in records if s['object_id']==target]
                    value['revision_id']=revisions[target,min(versions)][0]
                for v in value.values():resolve(v)
            elif isinstance(value,list):
                for v in value:resolve(v)
        resolve(payload)
        actual=revisions[spec['object_id'],spec['expected_version']+1]
        if json.loads(actual[3])!=payload: raise ValueError('payload mismatch: '+spec['object_id'])
    before_rounds={(r[0],r[1]):r for r in old['material_rounds']};after_rounds={(r[0],r[1]):r for r in new['material_rounds']}
    produced_requirements={n['object_id'] for spec in records if spec['kind']=='ASSET'
                           for n in spec['payload'].get('candidate_requirements',[])}
    for key,row in before_rounds.items():
        other=after_rounds.get(key)
        expected_production=(other and row[0] in produced_requirements and row[2]=='preparing'
                             and other[2]=='produced' and row[:2]==other[:2] and row[3:]==other[3:])
        if not other or row[3]!=other[3] or (row!=other and row[0] not in allowed and not expected_production):
            raise ValueError('old material round changed unexpectedly')
    # First-round generation cannot fabricate revision feedback or another round.
    if any(r[1]!=1 for k,r in after_rounds.items() if k not in before_rounds):raise ValueError('unexpected new material round')
    return {'old_objects_preserved':len(old_objects),'new_objects':len(new_objects)-len(old_objects),
        'old_revisions_preserved':len(old['revisions']),'added_revisions':len(added),
        'old_dependencies_preserved':len(old['dependencies']),'old_material_members_preserved':len(old['material_members']),
        'old_rounds_preserved':len(before_rounds),'new_rounds':len(after_rounds)-len(before_rounds),
        'protected_tables_unchanged':protected,'changed_objects':sorted(changed)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','registration','report'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();r=verify(args.before,args.after,json.loads(args.registration.read_text()))
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='changed_objects'},ensure_ascii=False))
