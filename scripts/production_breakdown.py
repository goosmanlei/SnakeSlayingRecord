#!/usr/bin/env python3
"""Compile authored V4 shot designs and exact, nonexecuting material plans.

Only the isolated instance is writable. Source text, existing original files,
user judgments and real calls are never changed by this compiler.
"""
import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from episode01_shots import complete_states_for_blocks, numbers
from production_data import refresh_drafts

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility

ROOT = Path(__file__).resolve().parents[1]
STYLE = '二维人物与轻手绘背景；轮廓清楚、平涂大色块、正常身体比例，背景薄而干净。不加纸纹、噪点、摄影皮肤和密集织物纹理。'
AUDIBLE = '唱|哼|声|响|咳|叫|答|喊|念|说|问|提醒|开口|嘀咕'


def ref(row):
    return {'object_id': row['object_id'], 'revision_id': row['id']}


def draft_ref(oid):
    return {'object_id': oid, 'revision_id': '@'+oid}


def record(oid, kind, title, **value):
    return {'object_id': oid, 'kind': kind, 'payload': {'format': {'SHOT_DESIGN':'production-shot-design-v1','REQUIREMENT':'production-requirement-v1','RELATION':'production-relation-v1'}[kind],
        'title': title, 'blocks': [{'id':'description','text': value.get('purpose', value.get('reason', title))}], **value}}


def recipe(model, params, prompt, inputs, name, blockers):
    return {'format':'generation-plan-v1','method':'generate','model':model,'parameters':params,
        'randomization':{'mode':'random'},'prompt':prompt,'inputs':inputs,'blockers':blockers,
        'output':{'name':name,'description':'待生成并审阅的'+name,'review_criteria':['人物身份、完整状态、空间方位与本镜依据一致','交接与动作起止完整，前后镜承接可还原','台词歌词逐字核对，画面可读文字由后期准确排版','保存直接返回的原件和真实调用，不把方案记为产物']}}


def need(oid, title, scope, slot, media, purpose, generation, entities=(), states=()):
    return record(oid,'REQUIREMENT',title,scope=scope,slot=slot,media_type=media,purpose=purpose,
        required=True,usage='generation_input',entities=list(entities),states=list(states),specification={},generation=generation)


def sound_units(blocks, source):
    result=[]
    for b in blocks:
        m=re.match(r'^([^：]{1,14})：(.*)$',b['text'])
        if m and m[1]!='字幕':
            speaker=m[1];result.append({'type':'singing' if '（唱）' in speaker else 'dialogue','speaker':speaker.replace('（唱）',''),
                'text':m[2],'source':{**source,'block_ids':[b['id']]}})
        else:
            # Keep exact prose for inline speech, wordless hums, calls and action
            # sounds instead of guessing a speaker or inventing missing lyrics.
            audible=bool(re.search(AUDIBLE,b['text']))
            result.append({'type':'source_sound' if audible else 'source_action','description':b['text'],'source':{**source,'block_ids':[b['id']]}})
    return result


def compile_design(store, p):
    lock=json.loads((ROOT/'production/source-lock.json').read_text())
    raw=(ROOT/'imports/screenplay-04.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=lock['screenplay']['file_sha256']:
        raise ValueError('locked screenplay bytes changed')
    source=json.loads(raw); heads={r['object_id']:r for r in p.current_records(store)}
    old=json.loads((ROOT/'production/episode01/shots.json').read_text())
    first=[r for r in old['records'] if r['kind']=='SHOT_DESIGN']
    authored=list(csv.DictReader((ROOT/'production/breakdown/design.tsv').open(),delimiter='\t'))
    occurrence_review=json.loads((ROOT/'production/breakdown/occurrence-review.json').read_text())['scenes']
    records=[]; shots=[]; coverage=[]; timings=[]; options={}
    lockrow=next(r for r in heads.values() if r['kind']=='INPUT_LOCK')
    image_params={'aspectRatio':'16:9','quality':'high','resolutionTier':'4k','outputFormat':'png','imageCount':1,'autoEnhancePrompt':False}
    style_id='need-production-style'
    records.append(need(style_id,'全剧 · 风格参考',ref(lockrow),'shared-style','image','统一线条、色块与背景笔触；不承载人物出现关系',
        recipe('gpt-image-2-5-sunburst',image_params,STYLE+'\n一张无文字风格板，表现河街日光、屋内油灯、后院冷石三种光线；不拼接剧情或造人物关系。',[], '全剧风格参考',['本任务只交付方案；待审阅风格与实际原件尺寸'])))
    # Authored additions distinguish narrative identity and performance states
    # that the earlier scene-level inventory had conflated.
    extra=material_read_json(ROOT/'production/breakdown/additional-records.json')['records']
    records.extend(extra)
    for item in extra:
        heads[item['object_id']]={**item,'id':'@'+item['object_id']}
    existing_needs=[r for r in heads.values() if r['kind']=='REQUIREMENT' and r['payload'].get('status')!='withdrawn']
    by_state={}
    for n in existing_needs:
        by_state.setdefault(n['payload']['scope']['object_id'],[]).append(n)
    assets=[r for r in heads.values() if r['kind']=='ASSET' and not r['payload'].get('placeholder')]
    for a in assets:
        for nr in a['payload'].get('candidate_requirements',[]):
            options.setdefault(nr['object_id'],[]).append({'candidate':ref(a),'candidate_id':__import__('review_desk.material_plans',fromlist=['identity']).identity(a['payload']),
                'files':[{k:c[k] for k in ('id','sha256','file','mime','role') if k in c} for c in a['payload']['components'] if c['role']=='original'],
                'status':'准确原件候选；本任务未替用户采用'})
    for ei, ep in enumerate(source['episodes']):
        er={k:lock['episodes'][ei][k] for k in ('object_id','revision_id')}
        bm={b['id']:b for b in ep['blocks']};index=0;elapsed=0
        episode_shots=[]
        for scene in ep['scenes']:
            sid=scene['id']; prep=heads['preparation-'+sid];sp=copy.deepcopy(prep['payload'])
            fixes=occurrence_review.get(sid,{})
            prep_ref=ref(prep)
            if fixes:
                current={o['entity']['object_id']:o for o in sp['occurrences']}
                for entity,fix in fixes.items():
                    if fix.get('remove'):
                        current.pop(entity,None);continue
                    if 'occurrence' in fix:
                        current[entity]=copy.deepcopy(fix['occurrence'])
                    if entity not in current:raise ValueError('reviewed occurrence missing: '+sid+'/'+entity)
                    item=current[entity]
                    if 'mode' in fix:item['mode']=fix['mode']
                    for key in ('states','transitions'):
                        if key in fix:item[key]=copy.deepcopy(fix[key])
                    bids=([f'screenplay-04-lantern-home-{sid}-b{i:03d}' for i in numbers(fix['blocks'])] if 'blocks' in fix else
                        [b for ev in item['evidence'] for b in ev['block_ids']])
                    excluded=set(numbers(fix['exclude_blocks'])) if fix.get('exclude_blocks') else set()
                    bids=[b for b in bids if int(b.rsplit('b',1)[1]) not in excluded]
                    item['evidence']=[{**er,'scene_id':sid,'block_ids':bids}]
                sp['occurrences']=list(current.values())
                sp['occurrence_review']='版本四逐块复核；依据 production/breakdown/occurrence-review.json 校正泛称和位置，旧修订保留。'
            sp['input_lock']=ref(lockrow)
            records.append({'object_id':prep['object_id'],'kind':'PREPARATION','payload':sp})
            prep_ref=draft_ref(prep['object_id'])
            source_ref={**er,'scene_id':sid,'block_ids':scene['block_ids']}
            scene_rows=[r for r in authored if r['scene']==sid]
            blocking_id='need-blocking-'+sid
            scene_choices='\n'.join(r['framing']+'；'+r['continuity'] for r in scene_rows) if ei else '\n'.join(r['payload']['spatial'] for r in first if r['payload']['scene_id']==sid)
            records.append(need(blocking_id,scene['heading']+' · 场级调度图',prep_ref,'blocking-map','image',
                '固定本场出入口、轴线、人物与关键物件位置；不推定所有实体每镜都出现',
                recipe('gpt-image-2-5-sunburst',image_params,STYLE+'\n图片1 只用于画风，不继承其中人物或布局。\n场级空间调度图，俯视布局与一个人眼高度主机位对应。\n'+scene_choices,
                    [{'reference':draft_ref(style_id),'use':'全剧画风；待具体原件采用'}],'场级调度图',['位置图尚未生成；必须按镜头空间说明审阅'])))
            specs=[copy.deepcopy(r) for r in first if r['payload']['scene_id']==sid] if ei==0 else scene_rows
            scene_covered=set()
            for spec in specs:
                index+=1;oid=f'shot-e{ei+1:02d}-{index:03d}'
                if ei==0:
                    v=spec['payload'];ids=v['source']['block_ids'];v['parent']=prep_ref
                    # Review the 33-shot draft as individual continuous shots;
                    # retain exact speech and give implied internal cuts a
                    # continuous camera movement or an off-screen sound bridge.
                    reviewed={
                        9:{'framing':'三人中景，沿倒米动作缓慢下摇到手部近景；木斗、袋口和倒米动作始终完整入框'},
                        12:{'framing':'稍宽三人景，保留掌柜回柜再过来的完整方向；他返回后缓慢推近袋口，撑袋与添米均不出框'},
                        18:{'continuity':'歌本由李寄一臂抱稳；蹲下不把书放到脏地上。只保留狗的轻呼吸，不擅加大声吠叫'},
                        20:{'framing':'赵执事中景，褐衣、腰侧钥匙与米铺檐柱同框；李寄收住话的呼吸由画外接入，路人从前景经过'},
                        28:{'framing':'阿蘅望向对街的近景，目光落点延续上一镜陶伯与空凳的位置','motion':'固定近景保持，阿蘅轻声说完；上一镜削竹停声的安静跨切延续'},
                    }
                    v.update(reviewed.get(index,{}))
                    v.pop('animatic_method',None)
                else:
                    ids=[f'screenplay-04-lantern-home-{sid}-b{i:03d}' for i in numbers(spec['blocks'])]
                    sr={**er,'scene_id':sid,'block_ids':ids};blocks=[bm[i] for i in ids]
                    sound=sound_units(blocks,sr)
                    water=sid in ('s003','s004','s011','s038','s042')
                    tense=sid in ('s029','s030','s031','s032','s033')
                    interior=sid in ('s005','s010','s014','s015','s026','s027','s034','s038','s040')
                    bed='近处呼吸与衣布轻响，石道响动按正文时点，保留安静不加鼓点' if tense else '近水轻拍岸石，脚步和纸布声近，远人声低' if water else '屋内衣布、木器与呼吸近，户外声低，不加解释性旁白' if interior else '所在院街的人群与脚步作低环境，重要发言时压低'
                    sound.append({'type':'environment_and_action','description':'制作选择：'+bed,'delivery':'native_audio'})
                    spoken=[u for u in sound if 'text' in u]
                    verbal=sum(len(re.sub(r'[^\u4e00-\u9fff0-9]','',u['text']))/(2.6 if u['type']=='singing' else 4) for u in spoken)
                    seconds=max(6, math.ceil(verbal+3),min(15,len(ids)*2))
                    if spec.get('seconds'):seconds=max(seconds,int(spec['seconds']))
                    states=[];entities=[];transitions=[];occ=[]
                    for o in sp['occurrences']:
                        # s028 b004 says an unnamed father. Li Dan belongs to
                        # the later arriving Li family and b043's named action.
                        excluded={'screenplay-04-lantern-home-s028-b004'} if sid=='s028' and o['entity']['object_id']=='entity-li-dan' else set()
                        evidence=[{**ev,'block_ids':[b for b in ev['block_ids'] if b in ids and b not in excluded]} for ev in o['evidence']]
                        evidence=[ev for ev in evidence if ev['block_ids']]
                        if not evidence:continue
                        entry={**o,'evidence':evidence};occ.append(entry)
                        mention_blocks=fixes.get(o['entity']['object_id'],{}).get('mention_blocks')
                        mentions=set(numbers(mention_blocks)) if mention_blocks else set()
                        if mentions and all(int(b.rsplit('b',1)[1]) in mentions for ev in evidence for b in ev['block_ids']):entry['mode']='mention'
                        if entry['mode']=='mention':continue
                        narrow=copy.deepcopy(o)
                        change_points={'s003':{'entity-li-ji':24},'s008':{'entity-red-rope':23},'s011':{'entity-ferry':7},
                            's014':{'entity-li-dan':35,'entity-li-home':44},'s022':{'entity-debt-note':12,'entity-debt-overlay':13},
                            's023':{'entity-feeding-channel':16},'s031':{'entity-heavy-blade':19},'s032':{'entity-li-ji':21},
                            's033':{'entity-li-xiao':12,'entity-sun-liu':12,'entity-officer-cheng':12,'entity-cave-gate':12}}
                        point=change_points.get(sid,{}).get(o['entity']['object_id'])
                        for tr in narrow.get('transitions',[]):
                            if point and len(tr['source']['block_ids'])>1:
                                bid=f'screenplay-04-lantern-home-{sid}-b{point:03d}'
                                tr['source']['block_ids']=[bid];tr['action']=bm[bid]['text']
                        full,changes=complete_states_for_blocks(narrow,ids)
                        entry['states']=full;entry['transitions']=changes
                        # Source facts establish availability; the shot's authored
                        # framing decides actual visibility, never parent scope.
                        entities.append(o['entity']);states.extend(full);transitions.extend(changes)
                    action=spec['action'];parts=re.split('[；，]',action)
                    v=record(oid,'SHOT_DESIGN',f'E{ei+1:02d}-{index:03d} '+spec['title'],
                        episode=er,parent=prep_ref,scene_id=sid,source=sr,number=index,purpose=spec['purpose'],
                        framing=spec['framing'],spatial=scene['location']+'；'+spec['framing'],
                        action_start=parts[0],action_end=parts[-1],motion=action,continuity=spec['continuity'],
                        duration_frames=seconds*24,fps=24,sound=sound,entities=entities,states=states,
                        state_model='complete-v1',state_transitions=transitions,occurrences=occ)['payload']
                if ei==0:
                    v['occurrences']=[]
                    for o in sp['occurrences']:
                        evidence=[{**ev,'block_ids':[b for b in ev['block_ids'] if b in ids]} for ev in o['evidence']]
                        evidence=[ev for ev in evidence if ev['block_ids']]
                        if not evidence:continue
                        forms=[r for r in v['states'] if heads[r['object_id']]['payload']['entity']['object_id']==o['entity']['object_id']]
                        v['occurrences'].append({**o,'evidence':evidence,'states':forms if o['mode']!='mention' else o['states'],
                            'transitions':[t for t in v.get('state_transitions',[]) if t['from'] in forms]})
                for occurrence in v.get('occurrences',[]):
                    if occurrence['mode']!='visual_voice':continue
                    entity=heads[occurrence['entity']['object_id']]['payload']
                    names=[entity['title'],*entity.get('aliases',[])]
                    cited='\n'.join(bm[b]['text'] for ev in occurrence['evidence'] for b in ev['block_ids'])
                    # A scene's voice presence is not inherited by every shot.
                    speech='(?:'+ '|'.join(re.escape(n) for n in names)+')(?:（唱）)?：|(?:'+ '|'.join(re.escape(n) for n in names)+').{0,16}(?:'+AUDIBLE+')'
                    if not re.search(speech,cited):occurrence['mode']='visual'
                v['facts']=[{'text':bm[b]['text'],'source':{**v['source'],'block_ids':[b]}} for b in ids]
                v['design_basis']='制作选择：构图、机位、动作拆分与预计时长；剧情事实见逐块原文，不增写定稿对白或歌词。'
                v['planned_start_frame']=elapsed; elapsed+=v['duration_frames']
                v['visual_status']='仅方案；没有镜头媒体产物'
                for b in ids:
                    if b not in bm or b not in scene['block_ids']:raise ValueError('source outside scene: '+b)
                scene_covered.update(ids)
                records.append({'object_id':oid,'kind':'SHOT_DESIGN','payload':v})
                shot_ref=draft_ref(oid)
                refs=[]
                for st in v['states']:
                    candidates=by_state.get(st['object_id'],[])
                    for nr in candidates:
                        if nr['payload']['slot']=='overall' and nr['payload']['media_type']=='image':
                            refs.append({'reference':ref(nr),'use':'本镜准确完整状态；候选待选，不自动使用最新图片'})
                refs=list({i['reference']['revision_id']:i for i in refs}.values())
                # Explicit applicability is independent from occurrence and calls.
                for inp in refs:
                    rid=inp['reference']['object_id']; relid='applies-'+oid+'-'+hashlib.sha256(rid.encode()).hexdigest()[:12]
                    records.append(record(relid,'RELATION',v['title']+' · 状态参考适用',relation_type='applicability',
                        subject=inp['reference'],scope=shot_ref,basis='production_choice',reason='本镜构图制作参考；不表示已实际提交或采用'))
                compid='need-'+oid+'-composition'
                frame_prompt=STYLE+'\n'+v['framing']+'\n空间：'+v['spatial']+'\n动作起点：'+v['action_start']+'\n完整动作：'+v.get('motion',v['action_end'])+'\n承接：'+v['continuity']+'\n只画本镜起始关键画面；实体状态按逐项参考，出现或提及不等于画面必须全收。文字区域留干净底，后期准确排字。'
                comp_inputs=[{'reference':draft_ref(blocking_id),'use':'本场空间调度；待原件采用'},*refs]
                if len(comp_inputs)>16:
                    grouped=[]
                    for gi in range(0,len(refs),5):
                        gid='need-'+oid+'-reference-group-'+str(gi//5+1)
                        part=refs[gi:gi+5]
                        gp=STYLE+'\n并列展示本镜所需的这组准确完整状态，各实体独立，不合成人体、不改变身份。仅作为构图参考。\n'+'\n'.join(f'图片{j+1}：'+i['use'] for j,i in enumerate(part))
                        records.append(need(gid,v['title']+' · 参考组 '+str(gi//5+1),shot_ref,'reference-group-'+str(gi//5+1),'image','将本镜大量参考分组，控制后续实际输入数量',
                            recipe('gpt-image-2-5-sunburst',image_params,gp,part,'分组参考图',['核对最深图生图谱系，超过两代须回干净母版重做'])) )
                        grouped.append({'reference':draft_ref(gid),'use':'已核对身份与完整状态的参考组'})
                    comp_inputs=[comp_inputs[0],*grouped]
                frame_prompt+='\n'+'\n'.join(f'图片{j+1}：'+i['use'] for j,i in enumerate(comp_inputs))
                comp=need(compid,v['title']+' · 构图／关键画面',shot_ref,'composition','image','固定本镜起点与人物道具接触关系',
                    recipe('gpt-image-2-5-sunburst',image_params,frame_prompt,comp_inputs,'镜头关键画面',['前置状态与调度图需锁定准确原件；核对各输入最深谱系，图生图最多两代']),v['entities'],v['states'])
                records.append(comp)
                seconds=v['duration_frames']/24
                # Each take is <=30s; planned edit duration remains separate.
                take_count=math.ceil(seconds/30);dur=math.ceil(seconds/take_count);dur=max(4,dur)
                model='seedance2.0_fast_vision' if dur<=15 else 'Seedance_2.5'
                voices=[u for u in v['sound'] if u.get('type') in ('dialogue','singing')]
                audio_id='need-'+oid+'-sound-reference'
                voice_needs=[]
                for st in v['states']:
                    for nr in by_state.get(st['object_id'],[]):
                        if nr['payload']['media_type']=='audio':voice_needs.append(ref(nr))
                audio_prompt='声音参考排练方案；不得改词。\n'+'\n'.join(u.get('speaker','')+'：'+u['text'] for u in voices)+'\n动作与环境依据：\n'+'\n'.join(bm[b]['text'] for b in ids)
                records.append(need(audio_id,v['title']+' · 声音参考选段',shot_ref,'sound-reference','audio',
                    '对白、歌词、动作声的准确参考需求；先听选音色和旋律，再形成符合视频模型时长上限的参考文件',
                    recipe('待选定声音制作渠道',{'sample_rate':48000,'reference_max_seconds':15 if model=='seedance2.0_fast_vision' else 30},audio_prompt,
                        [{'reference':r,'use':'声音身份或歌曲参考，待听审与必要选段'} for r in {r['revision_id']:r for r in voice_needs}.values()],
                        '声音参考选段',['声音渠道、演唱节奏和精确选段待审阅；本需求不是实际调用']),[],[]))
                prompt=STYLE+'\n@图片1 为已锁定起始画面；@音频1 只供声线和唱法参考，不照搬参考试读内容。\n'+v['title']+'。叙事目的：'+v['purpose']+'\n'+v['framing']+'\n空间：'+v['spatial']+'\n动作：'+v.get('motion',v['action_start']+' → '+v['action_end'])+'\n开始：'+v['action_start']+'\n结束：'+v['action_end']+'\n连续性：'+v['continuity']+'\n逐句对白／演唱：\n'+'\n'.join(u.get('speaker','')+('（唱）' if u['type']=='singing' else '')+'：'+u['text'] for u in voices)+'\n画外声与动作声仅依照所附定稿原句，不自动朗读叙述。禁新增台词、歌词、全蛇出院、额外角色或物件瞬移。可读文字后期排版。'
                auditory=[f['text'] for f in v['facts'] if re.search(AUDIBLE,f['text']) and not re.match(r'^[^：]{1,14}：',f['text'])]
                prompt+='\n原文中的原声时点（叙述不是旁白，不增补未给出的歌词）：\n'+'\n'.join(auditory)
                prompt+='\n声音设计：'+next((u['description'] for u in v['sound'] if u['type']=='environment_and_action'),'自然动作声与现场环境')
                outid='need-'+oid+'-video'
                generation=recipe(model,{'duration':dur,'resolution':'720p','aspect_ratio':'16:9'},prompt,
                    [{'reference':draft_ref(compid),'use':'准确起始构图与状态'}, {'reference':draft_ref(audio_id),'use':'准确声音参考选段；未完成前不执行'}],
                    '镜头有声视频候选',['本任务不生成；关键画面与声音参考尚未准确采用，方案待用户统一审阅'])
                generation['takes']=[{'number':i+1,'generated_seconds':dur,'edit_start_seconds':i*seconds/take_count,'edit_end_seconds':(i+1)*seconds/take_count,
                    'note':'长对白按完整换气或句末分段；选段衔接需实际视听后确定'} for i in range(take_count)]
                if len(prompt)>5000 and model=='seedance2.0_fast_vision':raise ValueError('fast prompt exceeds known limit')
                video=need(outid,v['title']+' · 镜头产物',shot_ref,'shot-video','video','本镜持续存在的视频制作需求；方案、候选与采用分别记录',generation,v['entities'],v['states'])
                video['payload']['specification']={'edit_duration_seconds':seconds,'generation_duration_seconds':dur,'planned_takes':take_count,'output_status':'not_generated'}
                records.append(video)
                shots.append({'object_id':oid,'payload':v,'composition':comp['payload'],'output':video['payload'],'sound_reference':audio_id,
                    'reference_requirements':[i['reference'] for i in refs], 'blocking_requirement':blocking_id})
                episode_shots.append(oid)
            if scene_covered!=set(scene['block_ids']):raise ValueError('uncovered scene blocks '+sid+': '+str(set(scene['block_ids'])-scene_covered))
            coverage.append({'episode':er,'scene':sid,'blocks':len(scene['block_ids']),'shots':[{'object_id':s['object_id'],'block_ids':s['payload']['source']['block_ids']} for s in shots if s['payload']['scene_id']==sid],'covered':True})
        timings.append({'episode':ei+1,'shots':len(episode_shots),'seconds':elapsed/24})
    if len(coverage)!=42 or len(timings)!=17 or sum(c['blocks'] for c in coverage)!=1114:raise ValueError('locked all-series coverage mismatch')
    return {'format':'production-import-v1','records':records},shots,{'format':'shot-coverage-v1','source':lock['screenplay'],'episodes':timings,'scenes':coverage},options


def render(shots, coverage, options, output):
    lines=['# 全剧逐镜设计首稿','',f"版本四，17 集、42 场、1114 个正文块；本稿 {len(shots)} 镜。画面、时长与拆镜是制作选择，逐镜附的正文是剧情依据。没有生成任何镜头媒体。",'',
        '阅读顺序：先看叙事、画面与动作，再对照正文、声音、连续性和生成方案。镜头参数是候选方案，关键画面与声音参考尚未采用，不能直接执行。已有实体原件按准确候选列在 reference-candidates.json；不会自动选最新候选。', '',
        '预计时长按对白每秒约四个汉字、演唱约2.6个字及动作停顿估算；第一集保留既有逐镜排练时间。它们不是实测。3秒剪辑镜生成至少4秒，实际选段必须在产物审阅后绑定。超过30秒的设计列多次生成段落，不能把整镜时长传给单次调用。', '',
        '图像模型沿用本项目已验证渠道标识，4K是请求档位；原件必须检查实际像素，不能通过放大冒充。生成视频默认Fast/720p，超过15秒采用2.5/720p；模型契约取自本次CLI只读查询。声音参考先完成听审、曲调与选段，不把文字当已生成音频。','']
    for ep in coverage['episodes']:
        lines+=['## 第%02d集 · %d镜 · 预计%.0f秒'%(ep['episode'],ep['shots'],ep['seconds']),'']
        for s in shots:
            v=s['payload']
            if int(s['object_id'].split('-')[1][1:])!=ep['episode']:continue
            g=s['output']['generation']
            lines += ['### '+v['title'],'',v['purpose'],'',f"画面与空间：{v['framing']}；{v['spatial']}",'',f"动作起止：{v['action_start']} → {v['action_end']}",'','动作过程：'+v.get('motion','见起止动作'),'','承接：'+v['continuity'],'',
                f"预计剪辑 {v['duration_frames']/24:g} 秒；{g['model']} / 720p / 16:9 / 单次 {g['parameters']['duration']} 秒 / {len(g['takes'])} 段，随机种子策略。",'',
                '正文与声音依据（'+v['scene_id']+'，准确集修订 '+v['episode']['revision_id']+'）：','']
            lines += ['- '+f['source']['block_ids'][0].rsplit('-',1)[-1]+'：'+f['text'] for f in v['facts']]
            lines+=['','素材输入：'+s['blocking_requirement']+'（场级调度）、need-'+s['object_id']+'-composition（起始画面）、'+s['sound_reference']+'（声音参考选段）；准确实体状态需求 '+', '.join(r['object_id'] for r in s['reference_requirements'])+'。','','视频提示词：','',g['prompt'],'']
    (output/'shots.md').write_text('\n'.join(lines).rstrip()+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True);parser.add_argument('--apply',action='store_true')
    a=parser.parse_args();sys.path.insert(0,str(a.system.resolve()))
    from generation_workspace import generation_root, isolated_instance
    generation_root(ROOT)
    instance=isolated_instance(ROOT,a.instance)
    from review_desk.store import Store
    from review_desk import production as p
    store=Store(instance/'.runtime/review.sqlite3')
    try:
        document,shots,coverage,options=compile_design(store,p)
        output=ROOT/'production/breakdown';output.mkdir(exist_ok=True)
        for name,data in [('drafts.json',document),('coverage.json',coverage),('reference-candidates.json',options)]:
            (output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        render(shots,coverage,options,output)
        changes=refresh_drafts(store,p,document,apply=a.apply)
        (output/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'shots':len(shots),'scenes':len(coverage['scenes']),'blocks':sum(c['blocks'] for c in coverage['scenes']),'records':len(document['records']),'changes':len(changes['records']),'applied':a.apply}))
    finally:store.close()

if __name__=='__main__': main()
