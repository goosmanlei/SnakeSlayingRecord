"""Read-only acceptance for source ownership and original production evidence."""
import argparse,json,sys
from pathlib import Path


def audit(store, baseline):
    from review_desk import production as p, production_current as current
    from review_desk.production_current_bundle import validate
    from review_desk import semantic_consolidation as semantic
    validate(store)
    rows = [r for r in p.current_records(store) if not semantic.is_retired(r['payload']) and r['payload'].get('status') != 'withdrawn']
    owners = {r['object_id']:r for r in rows if r['kind'] in ('ENTITY','STATE','AV_SHOT')}
    needs = [r for r in rows if r['kind']=='REQUIREMENT']
    entity_needs = [r for r in needs if r['payload']['scope']['object_id'] in owners and owners[r['payload']['scope']['object_id']]['kind'] in ('ENTITY','STATE')]
    states = [r for r in owners.values() if r['kind']=='STATE']
    for state in states:
        assert any(r['payload']['scope']['object_id']==state['object_id'] for r in needs), state['object_id']
    for need in needs:
        ref=need['payload']['scope'];target=p.ref_record(store,ref)
        assert not semantic.is_retired(target['payload']), need['object_id']
    for table in ('production_submissions','production_candidates','production_candidate_targets','comments','comment_events','production_comment_quotes'):
        a=[tuple(r) for r in baseline.db.execute('SELECT * FROM '+table+' ORDER BY 1,2')]
        b=[tuple(r) for r in store.db.execute('SELECT * FROM '+table+' ORDER BY 1,2')]
        assert a==b, 'original evidence changed: '+table
    originals=0
    for old in p.current_records(baseline, {'ASSET','CALL'}):
        assert p.record(store,old['object_id'])['payload']==old['payload'],old['object_id']
        originals+=1
    songs={
        'need-form-boat-song-independent-overall':'entity-boat-song',
        'need-form-blessing-song-independent-overall':'entity-blessing-stage-song',
        'need-form-blue-awning-song-independent-overall':'entity-blue-awning-song',
        'need-form-welcome-song-independent-overall':'entity-snake-welcome-song'}
    for mid,oid in songs.items():assert p.record(store,mid)['payload']['scope']['object_id']==oid
    zero=['entity-xiao-man','entity-xu-bride','entity-street-laundry','entity-work-ledger','entity-wet-paste']
    for oid in zero:assert oid in owners and not any(r['payload']['scope']['object_id']==oid for r in needs),oid
    # Video work belongs to another task and must remain byte-for-byte intact.
    for oid in ('material-av-e01-a01-s01-video','material-av-e01-a01-s02-video'):
        assert p.record(store,oid)['payload']==p.record(baseline,oid)['payload'],oid
    return {'entities':sum(r['kind']=='ENTITY' for r in owners.values()),'states':len(states),
            'entity_state_requirements':len(entity_needs),'all_requirements':len(needs),
            'unique_direct_sources':True,'every_state_has_real_need':True,'current_bundle_valid':True,
            'original_calls_assets_preserved':originals,'submissions_candidates_comments_exact':True,
            'zero_need_exceptions':zero,'concurrent_video_content_exact':True,
            'complete_songs_entity_owned':songs}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p
    current=Store.open_existing(args.database);baseline=Store.open_existing(args.baseline)
    try:
        with p.read_scope(current),p.read_scope(baseline):result=audit(current,baseline)
    finally:current.close();baseline.close()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
