#!/usr/bin/env python3
"""Verify an append-only generation registration against read-only snapshots."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
try:
    from .verify_production_review import read_tables
except ImportError:
    from verify_production_review import read_tables

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility


def scope_changes(before, registration):
    """Allow only an explicitly confirmed consolidation, retaining old payloads."""
    change=registration.get('scope_amendment')
    if not change:return set()
    evidence=change.get('approval',{})
    if evidence.get('actor')!='user' or not evidence.get('reply') or not evidence.get('question_item_id'):
        raise ValueError('scope consolidation requires exact user evidence')
    old_objects={r[0]:r for r in before['objects']}
    old_revisions={r[0]:r for r in before['revisions']}
    withdrawals=set(change['withdrawn_objects']);preparations=set(change['changed_preparations']);allowed=withdrawals|preparations
    records={r['object_id']:r for b in registration['batches'] for r in b['records']}
    if set(records)!=allowed:raise ValueError('scope consolidation changes unexpected objects')
    for oid,spec in records.items():
        prior=json.loads(old_revisions[old_objects[oid][2]][3]);payload=spec['payload'];kind=spec['kind']
        if oid in preparations:
            expected={**prior,'occurrences':[o for o in prior['occurrences'] if o['entity']['object_id']!=change['withdrawn_entity']]}
            if kind!='PREPARATION' or expected==prior or payload!=expected:
                raise ValueError('consolidation must only remove the duplicate occurrence')
        else:
            if kind not in ('ENTITY','STATE','REQUIREMENT','RELATION','REPRESENTATION'):
                raise ValueError('consolidation cannot change actual media, calls or decisions')
            expected={**prior,'status':'withdrawn','withdrawal_reason':change['reason'],'merged_into':change['replacements'][oid]}
            if kind=='REQUIREMENT':
                expected['required']=False;expected.pop('generation',None)
            if payload!=expected:raise ValueError('withdrawal changed unrelated content: '+oid)
    return allowed


def verify(before, after, registration):
    old,new=read_tables(before),read_tables(after)
    if old.keys()!=new.keys(): raise ValueError('unexpected schema change')
    records=[r for b in registration['batches'] for r in b['records']]
    allowed={r['object_id'] for r in records}
    decisions=set(registration.get('user_master_decisions',[]))
    consolidated=scope_changes(old,registration)
    for record in records:
        if record['object_id'] in consolidated:continue
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
    model_tables={'material_content','material_definitions','material_aliases','material_definition_versions','material_archive_files'}
    plan_tables={'material_plan_versions','material_plan_members','material_candidate_members'}
    code_tables={'business_codes','business_candidates'} & old.keys()
    for table in old.keys()-{'objects','revisions','dependencies','material_rounds','material_members'}-plan_tables-model_tables-code_tables:
        if Counter(old[table])!=Counter(new[table]): raise ValueError('protected table changed: '+table)
        protected[table]=len(old[table])
    for table in ('revisions','dependencies','material_members','material_content','material_definitions',*code_tables):
        if Counter(old.get(table,[]))-Counter(new.get(table,[])): raise ValueError('old history changed: '+table)
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
    if plan_tables<=old.keys():
        # Rebuild only the derived indices from their previous state plus this
        # exact registration. Unrelated version/candidate changes are rejected.
        from review_desk import material_plans as mp, production as production, business_codes as codes
        from types import SimpleNamespace
        source_db=sqlite3.connect(Path(after).resolve().as_uri()+'?mode=ro',uri=True)
        replay=sqlite3.connect(':memory:');source_db.backup(replay);source_db.close();replay.row_factory=sqlite3.Row;sqlite_compatibility(replay,hydrate=True)
        try:
            for table in code_tables:
                replay.execute('DELETE FROM '+table)
                columns=len(replay.execute('PRAGMA table_info('+table+')').fetchall())
                replay.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in range(columns))+')',old[table])
            for table in ('material_definition_versions','material_aliases','material_archive_files','material_candidate_members','material_plan_members','material_plan_versions'):
                replay.execute('DELETE FROM '+table)
            for table in ('material_plan_versions','material_plan_members','material_candidate_members','material_definition_versions','material_aliases','material_archive_files'):
                columns=len(replay.execute('PRAGMA table_info('+table+')').fetchall())
                replay.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in range(columns))+')',old[table])
            proxy=SimpleNamespace(db=replay)
            for spec in records:
                row=production.record(proxy,revision_id=revisions[spec['object_id'],spec['expected_version']+1][0])
                from review_desk.material_model import refresh_identity
                if row['kind']=='REQUIREMENT':refresh_identity(proxy,row)
                mp.register(proxy,row)
                if code_tables:
                    codes.allocate(proxy,row['object_id'],row['kind'],row['payload'])
                    codes.allocate_candidates(proxy,row['id'])
            for table in plan_tables|{'material_aliases','material_definition_versions','material_archive_files'}|code_tables:
                if Counter(tuple(row) for row in replay.execute('SELECT * FROM '+table))!=Counter(new[table]):
                    raise ValueError('material plan index differs from exact registration: '+table)
        finally:replay.close()
    return {'old_objects_preserved':len(old_objects),'new_objects':len(new_objects)-len(old_objects),
        'old_revisions_preserved':len(old['revisions']),'added_revisions':len(added),
        'old_dependencies_preserved':len(old['dependencies']),'old_material_members_preserved':len(old['material_members']),
        'old_rounds_preserved':len(before_rounds),'new_rounds':len(after_rounds)-len(before_rounds),
        'protected_tables_unchanged':protected,'changed_objects':sorted(changed)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','registration','report'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();r=verify(args.before,args.after,material_read_json(args.registration))
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='changed_objects'},ensure_ascii=False))
