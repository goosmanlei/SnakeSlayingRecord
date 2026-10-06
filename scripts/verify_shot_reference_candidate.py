#!/usr/bin/env python3
"""Verify the complete reviewed increment and emit exact per-shot evidence.

This checks compiled output against authored semantic decisions. It does not
claim browser acceptance or turn unselected material into accepted media.
"""
import argparse
import copy
from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'production/breakdown-shot-v2'


def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def ref(row):return {'object_id':row['object_id'],'revision_id':row['id']}
def require(value,message):
    if not value:raise ValueError(message)


def preservation_tables(path):
    from generation_publication import connect
    names=('revisions','comments','comment_events','business_codes','business_comments',
           'business_candidates','material_candidate_members','material_plan_comments','objects','material_plan_versions')
    db=connect(path)
    try:return {name:[dict(row) for row in db.execute('SELECT * FROM '+name)] for name in names}
    finally:db.close()


def file_digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()


def verify(store,instance,output):
    from review_desk import production as p, material_plans as mp, reference_paths as rp, shot_references as sr
    from review_desk.input_contracts import check_declared,check_parameters
    from review_desk.production_states import validate_state
    from generation_publication import canonical
    base=preservation_tables(instance/'.runtime/generation-base.sqlite3')
    candidate=preservation_tables(instance/'.runtime/review.sqlite3')
    preservation={}
    for table,key in [('revisions','id'),('comments','id'),('comment_events','id'),
                      ('business_codes','object_id'),('business_comments','comment_id')]:
        current={r[key]:r for r in candidate[table]}
        require(all(current.get(r[key])==r for r in base[table]),'old row altered: '+table)
        preservation[table]=len(base[table])
    for table in ['business_candidates','material_candidate_members','material_plan_comments']:
        before={canonical(r) for r in base[table]};after={canonical(r) for r in candidate[table]}
        require(before==after,'candidate or comment membership changed: '+table)
        preservation[table]=len(before)
    current_objects={r['id']:r for r in candidate['objects']}
    baseline_heads={r['id']:r['current_revision'] for r in base['objects']}
    for old in base['objects']:
        if old['kind'] in ('SOURCE','STORY','EPISODE','CALL','ASSET','JUDGMENT','INPUT_LOCK'):
            require(current_objects[old['id']]==old,'protected current object changed: '+old['id'])
    current_versions={(r['material_id'],r['number']):r for r in candidate['material_plan_versions']}
    frozen=[r for r in base['material_plan_versions'] if r['frozen']]
    require(all(current_versions[(r['material_id'],r['number'])]==r for r in frozen),'frozen version changed')
    preservation['frozen_material_versions']=len(frozen)
    baseline=read(DATA/'baseline.json');issues=read(DATA/'semantic-issues.json')
    require(file_digest(instance/'.runtime/generation-base.sqlite3')==baseline['baseline_database_sha256'],'frozen baseline bytes changed')
    require(hashlib.sha256((ROOT/baseline['screenplay']['source_file']).read_bytes()).hexdigest()==baseline['screenplay']['file_sha256'],'locked screenplay bytes changed')
    reviews={}
    for path in sorted(DATA.glob('review-e*.json')):
        value=read(path)
        for item in value.get('shots',value.get('items',[])):reviews[item['shot']['object_id']]=item
    expected={v['shot']['object_id'] for v in baseline['plans']}
    require(set(reviews)==expected,'review denominator changed')
    readback=read(DATA/'output-semantic-review.json')
    final_reviews={v['shot']:v for v in readback['items']}
    require(len(readback['items'])==readback['reviewed']==readback['baseline_total']==len(expected) and set(final_reviews)==expected,'final Prompt readback denominator differs')
    rows=p.current_records(store);heads={r['object_id']:r for r in rows}
    require({r['object_id'] for r in rows if r['kind']=='SHOT_DESIGN'}==expected,'current shot set changed')
    for row in rows:
        for _,target in p.references(row['payload']):p.ref_record(store,target)
    all_ref_count=0;shots=[];lineage=defaultdict(list);voice_lineage=defaultdict(list)
    selection_reviews=[];seen_input_owners=set()
    for locked in baseline['plans']:
        oid=locked['shot']['object_id'];review=reviews[oid];shot=heads[oid];s=shot['payload']
        original=p.ref_record(store,locked['shot']);old=original['payload'];approved=copy.deepcopy(old)
        for change in issues['issues']:
            if change['shot']!=oid:continue
            if change['field']=='review_note':
                require(change['proposed'] in review['review_note'] and change['current'] not in review['review_note'],'authored review erratum differs: '+oid)
                continue
            field=change['field'];owner=approved;parts=field.split('.')
            for part in parts[:-1]:owner=owner[int(part)] if isinstance(owner,list) else owner[part]
            key=int(parts[-1]) if isinstance(owner,list) else parts[-1]
            owner[key]=owner[key].replace(change['current'],change['proposed'])
            if field=='framing':approved['spatial']=approved['spatial'].replace(change['current'],change['proposed'])
        for change in issues['sound_classification_corrections']:
            if change['shot']==oid:
                unit=approved['sound'][change['index']];unit['type']=change['to']
                unit['description']=unit.pop('speaker')+'：'+unit.pop('text')
        changed={'states','entities','state_transitions','occurrences','reference_review'}
        require({k:v for k,v in s.items() if k not in changed}=={k:v for k,v in approved.items() if k not in changed},'unapproved design/script edit: '+oid)
        require(s['source']==review['source'] and s['reference_review']['note']==review['review_note'],'review source drift: '+oid)
        expected_images=[r['object_id'] for r in old['states'] if r['object_id'] not in review['image_remove']]
        expected_images=[v for v in expected_images+review['image_add'] if heads[v]['payload']['reference_media']=='image']
        if review.get('image_order'):
            require(sorted(expected_images)==sorted(review['image_order']),'authored state order changes membership: '+oid)
            expected_images=review['image_order']
        require([r['object_id'] for r in s['reference_review']['image_states']]==expected_images,'compiled visual states differ from authored review: '+oid)
        require([r['object_id'] for r in s['reference_review']['voice_states']]==list(dict.fromkeys(review['voice_states'])),'compiled voices differ from authored review: '+oid)
        video=heads[locked['video']['object_id']];plan=video['payload']['generation']
        require(video['payload']['scope']==ref(shot),'video scope mismatch: '+oid)
        require(review['review_note'] in plan['prompt'],'authored semantic constraint missing: '+oid)
        final=final_reviews[oid]
        require(final['result']=='checked' and final['source']==s['source'] and final['prompt_sha256']==hashlib.sha256(plan['prompt'].encode()).hexdigest(),'final readback does not cover accurate compiled Prompt: '+oid)
        for field in ('framing','spatial','purpose','motion','action_start','action_end','continuity'):
            require(not s.get(field) or s[field] in plan['prompt'],'protected prompt field omitted: '+oid+'/'+field)
        for unit in s['sound']:
            if unit['type'] in ('dialogue','singing'):require(unit['text'] in plan['prompt'],'literal speech omitted: '+oid)
        media=[p.ref_record(store,v['reference'])['payload']['media_type'] for v in plan['inputs']]
        check_parameters(plan['model'],plan['parameters'])
        require(not check_declared(plan['model'],plan['prompt'],media),'model shape invalid: '+oid)
        slots=rp.validate(store,video);projected=rp.project(store,video)
        require(all(not r.get('invalid') for r in projected),'broken reference path: '+oid)
        state_links=defaultdict(list)
        for link in plan['reference_links']:state_links[link['state']['object_id']].append(link)
        actual_states={r['object_id'] for r in s['states']}
        require(set(state_links)==actual_states,'missing or excess state link: '+oid)
        require(set(r['reference_key'] for r in plan['prompt_links'])==set(slots),'unmarked or phantom review reference: '+oid)
        for link in plan['reference_links']:
            if len(link['path'])==1 and link['key'].startswith('image-'):
                require('@图片'+str(link['path'][0]+1)+'：'+link['label'] in plan['prompt'],'direct image number differs from exact identity: '+oid)
        old_ids={r['object_id'] for r in old['states']};old_refs={r['object_id']:r for r in old['states']}
        references=[];all_ref_count+=len(projected)
        for link,resolved in zip(plan['reference_links'],projected):
            state=p.ref_record(store,link['state']);validate_state(store,state['payload'])
            entity=p.ref_record(store,state['payload']['entity']);state_id=state['object_id']
            valid_pending={'尚未选定素材版本','尚未选定候选'}
            require(set(resolved['issues'])<=valid_pending,'invalid selected reference: '+oid+'/'+state_id+str(resolved['issues']))
            action='added' if state_id not in old_ids else 'corrected' if old_refs[state_id]!=link['state'] else 'retained'
            references.append({'state':link['state'],'state_title':state['payload']['title'],'dimensions':state['payload']['dimensions'],
                               'entity':link['entity'],'entity_title':entity['payload']['title'],'media_type':resolved['record']['payload']['media_type'],
                               'action':action,'old_state':old_refs.get(state_id),'basis':s['source'],'reason':review['review_note'],
                               'material':ref(resolved['record']),'material_id':resolved['material_id'],'path':link['path'],
                               'selection_owner':resolved['selection_owner'],'selection_owner_title':resolved['selection_owner_title'],
                               'version':resolved['number'],'candidate_number':resolved['candidate_number'],
                               'direct':resolved['direct'],'model_input_index':link['path'][0],
                               'use':link['purpose'],'prompt_key':link['key'],'selection_issues':resolved['issues']})
        # Preserve every old direct input which still names the same accurate material.
        old_video=p.ref_record(store,locked['video']);old_inputs=old_video['payload']['generation']['inputs']
        current_slots=sr.slots(store,plan['inputs']);retained_selections=[]
        for entry in old_inputs:
            before=sr.slot(store,entry,0)
            matches=[v for v in current_slots if v['material_id']==before['material_id']]
            require(len(matches)==1,'baseline direct input silently lost: '+oid)
            after=matches[0]
            require((before['number'],before['candidate_number'])==(after['number'],after['candidate_number']),'baseline selection changed: '+oid)
            retained_selections.append({'material_id':before['material_id'],'version':before['number'],'candidate_number':before['candidate_number']})
        for owner in locked['reference_chain']:
            owner_key=(owner['object_id'],owner['revision_id'])
            if owner_key in seen_input_owners:continue
            seen_input_owners.add(owner_key)
            changed_owner=baseline_heads[owner['object_id']]!=heads[owner['object_id']]['id']
            # A historical chain may intentionally name a non-current upstream
            # revision. An untouched owner is compared at that exact revision,
            # never against an unrelated newer head from before this task.
            current_owner=heads[owner['object_id']] if changed_owner else p.ref_record(store,owner)
            current_inputs=current_owner['payload'].get('generation',{}).get('inputs',[])
            for index,entry in enumerate(owner['inputs']):
                before=sr.slot(store,entry,index)
                matches=[(i,v) for i,v in enumerate(current_inputs) if v['reference']['object_id']==entry['reference']['object_id']]
                summary={'owner':{'object_id':owner['object_id'],'revision_id':owner['revision_id']},
                    'compared_owner':ref(current_owner),'comparison':'revised current owner' if changed_owner else 'unchanged exact upstream history',
                    'old_index':index,'old_input':entry,
                    'old_version':before['number'],'old_candidate':before['candidate_number']}
                if matches:
                    require(len(matches)==1,'ambiguous retained input: '+str(owner_key))
                    new_index,new_entry=matches[0];after=sr.slot(store,new_entry,new_index)
                    require(all(before[k]==after[k] for k in ('number','candidate_number','material_id','candidate')),'retained upstream selection changed: '+str(owner_key))
                    require(all(entry.get(k)==new_entry.get(k) for k in ('component_id','range','crop','sha256')),'retained original selection changed: '+str(owner_key))
                    summary.update(result='retained',new_index=new_index,new_input=new_entry,
                        new_version=after['number'],new_candidate=after['candidate_number'])
                else:
                    require(owner['object_id'] in ('need-'+oid+'-composition','need-'+oid+'-sound-reference'),'unreviewed upstream removal: '+str(owner_key))
                    summary.update(result='removed_from_current_shot',source=s['source'],basis=review['review_note'],
                        rule='镜头关键画面只引用准确起点状态；声音选段只引用实际发声者；整场调度不作为本镜全体输入。旧准确方案及选择保留在历史。')
                selection_reviews.append(summary)
            for index,entry in enumerate(current_inputs):
                if not any(v['reference']['object_id']==entry['reference']['object_id'] for v in owner['inputs']):
                    require(entry.get('selection_state')=='unselected' and not entry.get('material_selection'),'new input auto-selected: '+str(owner_key)+'/'+str(index))
        old_voice=set()
        old_sound=next(r for r in locked['reference_chain'] if r['object_id']=='need-'+oid+'-sound-reference')
        for entry in old_sound['inputs']:old_voice.add(entry['reference']['object_id'])
        sound=heads['need-'+oid+'-sound-reference'];new_voice={v['reference']['object_id'] for v in sound['payload']['generation']['inputs']}
        by_entity=defaultdict(list)
        for state_ref in s['reference_review']['image_states']:
            state=p.ref_record(store,state_ref);by_entity[state['payload']['entity']['object_id']].append(state_ref)
        for entity,forms in by_entity.items():lineage[entity].append({'shot':ref(shot),'scene':s['source']['scene_id'],'start':forms[0],'end':forms[-1],'source':s['source'],'action_start':s['action_start'],'action_end':s['action_end'],'continuity':s['continuity'],'review_note':review['review_note']})
        for state_ref in s['reference_review']['voice_states']:
            state=p.ref_record(store,state_ref)
            voice_lineage[state['payload']['entity']['object_id']].append({'shot':ref(shot),'scene':s['source']['scene_id'],
                'start':state_ref,'end':state_ref,'source':s['source'],'review_note':review['review_note'],
                'sound':s['sound'],'voice':state['payload']['dimensions'].get('voice')})
        shots.append({'shot':ref(shot),'baseline_shot':locked['shot'],'source':s['source'],'script_facts':s['facts'],
                      'video':ref(video),'baseline_video':locked['video'],'references':references,'retained_direct_selections':retained_selections,
                      'removed_states':[{'state':r,'reason':review['review_note']} for r in old['states'] if r['object_id'] not in actual_states],
                      'removed_voice_materials':sorted(old_voice-new_voice),'voice_change_basis':review['review_note'],
                      'prompt':plan['prompt'],'prompt_links':plan['prompt_links'],'model':plan['model'],
                      'prompt_sha256':hashlib.sha256(plan['prompt'].encode()).hexdigest(),
                      'contract':{'image_count':media.count('image'),'audio_count':media.count('audio'),'prompt_length':len(plan['prompt']),'duration':plan['parameters']['duration']},
                      'review_note':review['review_note'],'authored_input_review':review['status'],
                      'output_comparison':'passed: exact authored constraints, protected fields, states, paths and Prompt marks',
                      'browser_review':'not_verified'})
    continuity=read(DATA/'continuity-review.json');transitions=[];voice_transitions=[]
    for mode,sequences,authored,target in [('image',lineage,continuity['items'],transitions),
                                          ('voice',voice_lineage,continuity['voice_items'],voice_transitions)]:
        keyed={(r['entity'],r['from_shot'],r['to_shot']):r for r in authored};used=set()
        require(len(keyed)==len(authored),'duplicate continuity decision: '+mode)
        for entity,occurrences in sequences.items():
            for previous,current in zip(occurrences,occurrences[1:]):
                key=(entity,previous['shot']['object_id'],current['shot']['object_id'])
                note=keyed.get(key);changed=previous['end']!=current['start']
                if note:
                    require((previous['end']['object_id'],current['start']['object_id'])==(note['expected_from'],note['expected_to']),'continuity states differ from authored review: '+str(key))
                    require(previous['source']==note['from_source'] and current['source']==note['to_source'],'continuity source moved: '+str(key))
                    used.add(key)
                require(not changed or note,'unexplained complete-state transition: '+str(key))
                target.append({'entity':entity,'from':previous,'to':current,'state_changed':changed,
                    'cross_scene':previous['scene']!=current['scene'],'review_status':'reviewed',
                    'basis':note['basis'] if note else '同一准确完整状态延续；两端动作、空间与声音约束已逐镜审定并原样进入当前 Prompt。',
                    'verification':'authored transition and exact endpoints' if note else 'exact state plus protected authored shot actions'})
        require(used==set(keyed),'unused continuity decisions: '+mode+' '+str(set(keyed)-used))
    result={'format':'shot-reference-verified-output-v1','counts':{'shots':len(shots),'video_prompts':len(shots),'reference_paths':all_ref_count},
            'history_preservation':preservation,'models':dict(Counter(r['model'] for r in shots)),
            'browser_acceptance':'not performed by this tool; see browser acceptance evidence','semantic_output_acceptance':'all exact compiled Prompts covered by per-shot readback',
            'shots':shots}
    write(output/'coverage.json',result);write(output/'continuity.json',{'format':'shot-reference-continuity-v1',
        'counts':{'image_pairs':len(transitions),'image_state_changes':sum(v['state_changed'] for v in transitions),
                  'image_cross_scene':sum(v['cross_scene'] for v in transitions),'voice_pairs':len(voice_transitions),
                  'voice_state_changes':sum(v['state_changed'] for v in voice_transitions),'voice_cross_scene':sum(v['cross_scene'] for v in voice_transitions)},
        'transitions':transitions,'voice_transitions':voice_transitions})
    write(output/'selection-preservation.json',{'format':'shot-reference-selection-preservation-v1',
        'owners':len(seen_input_owners),'counts':dict(Counter(v['result'] for v in selection_reviews)),
        'new_inputs':'all new slots explicitly unselected','items':selection_reviews})
    return {k:v for k,v in result.items() if k!='shots'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from generation_workspace import generation_root,contained
    from review_desk.store import Store
    root=generation_root(ROOT);instance=contained(root,args.instance);output=contained(root,args.output)
    require(instance.is_relative_to(root/'.runtime'),'Use the isolated task instance')
    store=Store(instance/'.runtime/review.sqlite3')
    try:print(json.dumps(verify(store,instance,output),ensure_ascii=False))
    finally:store.close()


if __name__=='__main__':main()
