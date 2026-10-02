#!/usr/bin/env python3
"""Prepare reviewed production choices and exact material recipes; never call models.

The source screenplay is fixed. Apply writes only a guarded incremental batch
on this task's isolated instance. Actual files, calls and decisions are retained.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from generation_design import ENTITIES, STATES, STYLE
from migrate_complete_states import digest

ROOT=Path(__file__).resolve().parents[1]
AUDIO={'audio_config':{'format':'wav','sample_rate':48000,'pitch_rate':0,'speech_rate':0,'loudness_rate':0,'enable_subtitle':True},'watermark':{}}
IMAGE_CHECK=['正常比例与稳定轮廓；无额外肢体或身份漂移','只呈现所述完整状态，伤势、湿痕和手持物不串场','线条干净、色块清楚，无新增纸纹、颗粒或写实皮肤','核对原件真实像素、原生尺寸回执及全部参考谱系']
AUDIO_CHECK=['逐字听辨原词，不能只依字幕判断','单一角色音色连续；无新增台词、旁白或伴奏','听清呼吸和停顿，原件无削波、突切与异常噪声','48 kHz WAV 原件及精确时长；候选通过后再明确采用']


def ref(row):return {'object_id':row['object_id'],'revision_id':row['id']}


def prepare(store,p):
    from review_desk.store import Store
    from review_desk import generation as g
    source_hash=hashlib.sha256((ROOT/'imports/screenplay-04.json').read_bytes()).hexdigest()
    if source_hash!=json.loads((ROOT/'production/source-lock.json').read_text())['screenplay']['file_sha256']:raise ValueError('approved screenplay changed')
    original=p.current_records(store);by={r['object_id']:r for r in original}
    actual=set()
    for row in original:
        if row['kind']=='PREPARATION' and row['payload']['source']['scene_id'] in ('s001','s002'):
            actual.update(o['entity']['object_id'] for o in row['payload']['occurrences'] if o['mode']!='mention')
    if actual!={'entity-'+key for key in ENTITIES}:raise ValueError('first-episode entity scope changed')
    forms=[r for r in original if r['kind']=='STATE' and r['payload'].get('state_model')=='complete-v1' and r['payload']['entity']['object_id'] in actual]
    if {'form-'+key for key in STATES}!={r['object_id'] for r in forms}:raise ValueError('complete-state scope changed')
    clone=Store(':memory:');store.db.backup(clone.db);clone.db_path=store.db_path
    changes=[];resolved={};needs=[]
    def put(oid,kind,payload):
        try:current=p.record(clone,oid)
        except KeyError:current=None
        if current and current['payload']==payload:resolved[oid]=current;return current
        item={'object_id':oid,'kind':kind,'expected_version':current['version'] if current else 0,'payload':payload}
        p.import_records(clone,{'format':'production-import-v1','records':[item]});changes.append(item);resolved[oid]=p.record(clone,oid);return resolved[oid]
    def update_refs(payload):
        for _,r in p.references(payload):
            if r['object_id'] in resolved and r['revision_id']==by.get(r['object_id'],{}).get('id'):
                r['revision_id']=resolved[r['object_id']]['id']
        return payload
    def entity(key):return resolved['entity-'+key]
    def form(key):return resolved['form-'+key]
    def image_plan(key,description,name,inputs=(),ratio=None):
        typ=entity(key)['payload']['entity_type'];ratio=ratio or ('3:4' if typ=='character' else '16:9' if typ=='space' else '4:3')
        config=json.loads((ROOT/'config/openart.json').read_text())
        prompt=f'{STYLE}\n制作对象：{entity(key)["payload"]["title"]}。{ENTITIES[key][1]}\n本张需要完整表现：{description}\n'
        prompt+=('参考图只用于锁定身份、轮廓、色块、线条与空间；局部执行本状态差异，不转绘或重绘出更重纹理。' if inputs else '从文字探索干净根母版，没有已接受图像母版，不假称已参考既有候选。')
        if '三视图' in description:composition='正面、侧面、背面三视图等高并排，脚底在同一水平线，不混入三分之四角度。'
        elif '俯视' in description:composition='纯俯视空间布局，墙线、出入口与通道清楚，不画透视全景；无文字标签。'
        elif '反向视线' in description:composition='按指定反向机位呈现空间；镜头不跨越河岸，不左右镜像既有布置。'
        elif '近景' in description:composition='以描述中指定部位的近景为主，局部边界自然，不为了全身入画缩小细节。'
        elif typ=='space':composition='画面为可理解的空间全景，水平视线、前中后景清楚，不画人物和临时镜头动作。'
        else:composition='主体完整入画，三分之四视角，平视、柔和中性光与浅暖灰纯底；清楚保留手脚、轮廓及关键细节。'
        prompt+='\n'+composition+'不加水印、装饰版框或未经指定的文字。'
        return {'format':g.PLAN,'method':'generate','model':config['preferred_model'],
                'parameters':{'project_id':config['project_id'],'quality':config['image_quality'],'resolution':config['image_resolution'],'aspect_ratio':ratio,'n':1},
                'prompt':prompt,'inputs':list(inputs),'output':{'name':name,'description':description,'review_criteria':IMAGE_CHECK},
                'blockers':['当前 GPT Image 2.5 两次请求原生 4K 均返回 2016×2688；正式调用前须解决原生尺寸及 CLI 参数支持，未达标不能计作素材齐备。']}
    def input_for(need,use):return {'reference':ref(need),'use':use}
    def audio_plan(key,text,name,description,inputs=(),reuse=False):
        prompt=(('参考'+('、'.join('@音频'+str(i+1) for i in range(len(inputs))))+'，只锁定说话人音色与自然发声方式，按下文完成新的内容；不要照搬原录音台词。\n') if inputs and not reuse else '')
        prompt+=ENTITIES[key][2]+'\n'+description+'\n'+text+'\n保留自然短停顿，开头结尾各留半秒安静；无字幕朗读、角色名、说明词、额外说话声；原件为干净独立声音，环境与音乐另轨。'
        if reuse:prompt='复用前置需求明确采用的完整原件与范围，不重新生成：'+description
        if len(prompt)>3000:raise ValueError('audio prompt too long')
        return {'format':g.PLAN,'method':'reuse' if reuse else 'generate','model':'seed-audio-1.0',
                'parameters':deepcopy(AUDIO),'prompt':prompt,'inputs':list(inputs),'output':{'name':name,'description':description,'review_criteria':AUDIO_CHECK},'blockers':[]}
    def need(state,slot,media,plan,role='detail',source=None,shots=None,original_need=None):
        oid=original_need or 'need-'+state['object_id']+'-'+slot
        old=by.get(oid)
        payload=update_refs(deepcopy(old['payload'])) if old else {'format':'production-requirement-v1'}
        output=plan['output'];payload.update(title=state['payload']['title']+' · '+output['name'],blocks=[{'id':'purpose','text':output['description']}],
           scope=ref(state),slot=slot,required=True,purpose=output['description'],media_type=media,usage='generation_input' if media=='image' else 'post_audio',
           entities=[state['payload']['entity']],states=[ref(state)],generation=plan,
           sources=source or state['payload']['sources'],planned_shots=shots or [],
           specification=({'native_4k':True} if media=='image' else {'minimum_sample_rate':48000})|{'reference_role':role})
        result=put(oid,'REQUIREMENT',payload);needs.append(result);return result
    try:
        for key,(base,description,voice) in ENTITIES.items():
            row=by['entity-'+key];payload=deepcopy(row['payload'])
            payload['production_description']=description+'\n声音方向：'+voice
            payload['blocks']=[{'id':'description','text':payload['production_description']}]
            payload['choices']=['造型、色彩、空间布置和声音方向为本次提出的制作选择，随此版本一起审阅。']
            payload['unknowns']=[u for u in payload['unknowns'] if not ('牵起墨耳' in u)]
            put(row['object_id'],'ENTITY',payload)
        for row in forms:
            key=row['payload']['entity']['object_id'].removeprefix('entity-');sid=row['object_id'].removeprefix('form-');payload=update_refs(deepcopy(row['payload']))
            description=ENTITIES[key][1]+'\n'+STATES[sid]
            payload['production_description']=description;payload['blocks']=[{'id':'description','text':description}]
            payload['choices']=['本状态的具体湿痕、伤侧、色彩和衔接安排属于制作选择，剧本事实列在下方。']
            payload['unknowns']=[]
            if key=='songbook' and sid.endswith('wet'):payload['unknowns']=['领唱旧纸入水后去向原文未明确；本方案不展示它完整露出，如镜头需要，应先回剧本核对。']
            dims=payload['dimensions'];primary=next(k for k in ('appearance','layout','structure','lyrics_scope') if k in dims)
            dims[primary]=ENTITIES[key][1]
            for field,value in list(dims.items()):
                if any(word in value for word in ['待审','未明确','以上述描述','按本场','随身及手持物','未写内容']):
                    dims[field]=ENTITIES[key][2] if field=='voice' else STATES[sid]
            put(row['object_id'],'STATE',payload)
        # Explicitly reviewed planned-use links follow the enriched complete states.
        # Historical actual media, calls, adoptions and decisions never follow automatically.
        for kind in ('PREPARATION','SHOT_DESIGN'):
            for row in original:
                if row['kind']==kind:put(row['object_id'],kind,update_refs(deepcopy(row['payload'])))
        for row in original:
            if row['kind']=='REQUIREMENT' and row['payload'].get('status')!='withdrawn':
                payload=update_refs(deepcopy(row['payload']))
                if row['payload']['scope']['object_id'] not in {f['object_id'] for f in forms}:put(row['object_id'],'REQUIREMENT',payload)
        # Root image references are generated from text, state derivations use only
        # that root, and optional angle/detail drawings are at most one level deeper.
        masters={};voices={};bases={key:form(key+'-'+value[0]) for key,value in ENTITIES.items()}
        for key,state in bases.items():
            if key=='stage-drum':continue # the first appearance is intentionally offscreen
            if key=='boat-song':continue
            plan=image_plan(key,STATES[state['object_id'].removeprefix('form-')],entity(key)['payload']['title']+' · 干净整体母版')
            masters[key]=need(state,'overall','image',plan,'overall',original_need='need-'+state['object_id']+'-overall')
        for row in forms:
            key=row['payload']['entity']['object_id'].removeprefix('entity-');state=resolved[row['object_id']]
            if key=='boat-song' or state['object_id']=='form-stage-drum-audible':continue
            if key=='stage-drum':
                masters[key]=need(state,'overall','image',image_plan(key,STATES['stage-drum-base'],'台鼓完整外观'),'overall',original_need='need-'+state['object_id']+'-overall');continue
            if state['id']==bases[key]['id']:continue
            description=STATES[state['object_id'].removeprefix('form-')]
            plan=image_plan(key,description,entity(key)['payload']['title']+' · '+state['payload']['title'].split('·')[-1]+'整体参考',[input_for(masters[key],'只用已选干净根母版锁定身份与基准形态；按本状态作第一代局部变化')])
            need(state,'overall','image',plan,'overall',original_need='need-'+state['object_id']+'-overall')
        cues=json.loads((ROOT/'production/episode01/dialogue-cues.json').read_text())
        for key in ('li-ji','a-heng','zhou','zhao','woodcutter','rice-listeners','street-passers'):
            matching=[c for c in cues if c['type']=='dialogue' and c['entity']['object_id']=='entity-'+key]
            if not matching:raise ValueError('missing actual dialogue for '+key)
            spoken='\n'.join('“'+c['text']+'”' for c in matching[:3])
            voices[key]=need(bases[key],'voice','audio',audio_plan(key,'只说以下定稿原句，不改字、不加词：\n'+spoken,entity(key)['payload']['title']+' · 日常声线母版','用不同句子核对同一音色、咬字与自然呼吸；各句之间留一秒安静。'))
        for key in ('li-ji','a-heng','zhou','zhao'):
            for row in forms:
                if row['payload']['entity']['object_id']!='entity-'+key or row['object_id']==bases[key]['object_id']:continue
                state=resolved[row['object_id']];sid=state['object_id'].removeprefix('form-');changed=any(word in sid for word in ('hoarse','wet-shoes','tears','spent','blood','rewrapped'))
                text=next(c['text'] for c in cues if c['type']=='dialogue' and c['entity']['object_id']=='entity-'+key)
                description=('作为状态声线样本，以第一集已有短句核对发声，不将其当作此场对白。状态表演：'+STATES[sid]) if changed else '此状态没有持续改变的声线；复用日常声线母版作为音色参考，实际镜内对白仍单独录制。'
                need(state,'voice','audio',audio_plan(key,'只说原句：“'+text+'”',state['payload']['title'].split('·')[-1]+' · 声线参考',description,[input_for(voices[key],'固定同一说话人的音色')],reuse=not changed))
        song_plan=audio_plan('boat-song','只唱以下两句，不加词：“一道险滩水急，船头慢慢行——”“船靠岸，灯来迎，家里人等到如今——”。','舟行曲两句清唱母版',ENTITIES['boat-song'][2],[input_for(voices['a-heng'],'@音频1 锁定阿蘅说话与演唱的同一声线；不沿用样本中的对白词')])
        song=need(bases['boat-song'],'overall','audio',song_plan,'overall',original_need='need-form-boat-song-short-overall')
        for key,description in [('mo-er','约8秒：犬爪在石路小跑三四步后停下，轻呼吸和吃小饼角的两次咀嚼；各动作之间留一秒，无吠叫。'),('stage-drum','约8秒：两下疏落轻鼓试敲，相隔约一秒，停两秒，再一记中强击自然衰减；无伴奏无连续节拍。')]:
            slot='overall' if key=='stage-drum' else 'action-sound';need(bases[key],slot,'audio',audio_plan(key,'只生成描述中的声音，不朗读说明。',entity(key)['payload']['title']+' · 第一集动作声',description),'overall' if key=='stage-drum' else 'detail',original_need='need-form-stage-drum-audible-overall' if key=='stage-drum' else None)
        for key,description in [('river-street','约20秒平稳河水与微风底声，无可辨对白；远近层次松，首尾留重叠余量供淡化，不能声称已无缝循环。'),('shaving-knife','约10秒近距削竹：三个短刮削动作，停3秒，再两下慢刮；含极轻竹屑落下，无配乐。'),('grain','约8秒：一小木斗米连续倒入布袋后停，再一小把米加入；两段中间留两秒安静，米粒颗粒清楚而不刺耳。'),('cloth','约8秒：手搓干浆糊，湿薄布巾擦掌两下，翻面后再擦；低音量近距，无台词。')]:
            need(bases[key],'action-sound','audio',audio_plan(key,'只生成描述中的声音，不朗读说明。',entity(key)['payload']['title']+' · 第一集声音分轨',description))
        # First-episode spoken/sung lines have individual, exact scripts and timing,
        # not placeholders or a vague intention to record them later.
        for cue in cues:
            key=cue['entity']['object_id'].removeprefix('entity-');shot=p.record(clone,cue['shot_id']);formref=next((r for r in shot['payload']['states'] if p.ref_record(clone,r)['payload']['entity']['object_id']==cue['entity']['object_id']),None)
            if not formref:raise ValueError('cue has no exact state')
            # A shot can include both sides of a transition. The spoken line
            # follows the exact screenplay block, not the first state in a list.
            for transition in shot['payload'].get('state_transitions',[]):
                if p.ref_record(clone,transition['to'])['payload']['entity']['object_id']==cue['entity']['object_id'] and max(transition['source']['block_ids'])<=min(cue['source']['block_ids']):
                    formref=transition['to']
            state=p.ref_record(clone,formref)
            is_song=cue['type']=='singing'
            if is_song:state=bases['boat-song'];key='boat-song'
            upstream=song if is_song else voices[key]
            duration=(cue['planned_end_frame']-cue['planned_start_frame'])/cue['fps']
            description=f"第1集第{shot['payload']['number']}镜 · {shot['payload']['title'].split(' ',1)[-1]}。{cue['speaker']}{'演唱' if is_song else '对白'}预计 {duration:.2f} 秒；镜内暂排 {cue['planned_start_frame']/cue['fps']:.2f}–{cue['planned_end_frame']/cue['fps']:.2f} 秒，实录后复核节奏。"
            plan=audio_plan(key,('只唱' if is_song else '只说')+'以下原句，不改字、不加词：“'+cue['text']+'”。保留自然表演，不机械变速。',cue['speaker']+' · '+cue['text'][:18]+('…' if len(cue['text'])>18 else ''),description,[input_for(upstream,'锁定已选声线'+('和旋律；只演唱本句' if is_song else '；只说本条原句'))])
            need(state,cue['id'],'audio',plan,source=[cue['source']],shots=[ref(shot)])
        # Useful angle/space references, independent of any final shot generation.
        for key in ('li-ji','a-heng','zhou','zhao','mo-er','woodcutter','tao','rice-listeners','street-passers'):
            state=bases[key];description='同一状态的正面、侧面、背面比例与衣饰承接；三视图等高分列，不加文字标签；'+STATES[state['object_id'].removeprefix('form-')]
            plan=image_plan(key,description,entity(key)['payload']['title']+' · 三向辨识参考',[input_for(masters[key],'只引用干净根母版，保持轮廓比例与配色；各视角不重设身份')],ratio='4:3');need(state,'angles','image',plan)
        for key in ('river-street','rice-shop','bamboo-stall','prop-house'):
            state=bases[key]
            for slot,name,description in [('layout','俯视布局','同一空间的纯俯视布局，保留尺度、通道与出入口关系；'),('reverse-view','反向机位','从主视图视线终点回望的反向视线参考，不改门窗、河岸与道具位置；')]:
                need(state,slot,'image',image_plan(key,description+ENTITIES[key][1],entity(key)['payload']['title']+' · '+name,[input_for(masters[key],'锁定已选空间尺寸、出入口和固定布置；生成新观察方向')],ratio='16:9'))
        for key in ('li-ji','a-heng'):
            state=bases[key];description=('双手掌纹、浆糊与指缝羊毛的近景；肩红印单独小幅参考；仍为第一集未受掌心额角伤状态。' if key=='li-ji' else '整齐挽起的洗旧青衣袖口与护书双手近景，手指自然正常，无首饰。')
            need(state,'detail','image',image_plan(key,description,entity(key)['payload']['title']+' · 手部细节',[input_for(masters[key],'锁定基础人物，放大必要细节，不增加皮肤纹理')],ratio='4:3'))
        if len({r['object_id'] for r in changes})!=len(changes):raise ValueError('one object changed twice')
        for key in ENTITIES:
            workspace=g.snapshot(clone,'entity-'+key)
            if not workspace['preparation']['complete']:raise ValueError((key,workspace['preparation']))
        protected={r['object_id']:r['id'] for r in original if r['kind'] in ('ASSET','CALL','RELATION','JUDGMENT')}
        if any(p.record(clone,oid)['id']!=rid for oid,rid in protected.items()):raise ValueError('actual history changed')
        # Explicit candidate association review, not compatibility acceptance.
        # The image was re-viewed; audio is matched by its original request,
        # subtitles and file bounds and still requires listening review.
        associations={
          'asset-liji-image':['need-form-li-ji-paste-overall'],
          'asset-liji-voice-01':['need-form-li-ji-paste-voice','need-form-li-ji-clean-voice'],
          'asset-aheng-voice-01':['need-form-a-heng-blue-voice'],
          'asset-aheng-song-01':['need-form-boat-song-short-overall'],
          'asset-zhou-voice-01':['need-form-zhou-base-voice'],
          'asset-zhao-voice-01':['need-form-zhao-base-voice'],
        }
        for oid,reqs in associations.items():
            row=by[oid];payload=deepcopy(row['payload'])
            for key in ('subjects','states','state_coverage'):update_refs(payload[key])
            payload['candidate_requirements']=[ref(p.record(clone,rid)) for rid in reqs]
            payload['association_review']='按现有原件与实际调用文本核对候选归属；新增状态描述属于待采纳制作选择，未确认素材达标，不改写原调用输入。图像仍缺原生4K与手部细节；声音仍待实际听审。'
            put(oid,'ASSET',payload)
            saved=p.record(clone,oid)['payload']
            if any(saved[k]!=row['payload'][k] for k in ('components','production','lineage')):raise ValueError('candidate review changed actual production')
        from review_desk.production_states import scope_coverage
        rows=p.current_records(clone);coverage=scope_coverage(clone,[r for r in rows if r['kind'] in ('PREPARATION','SHOT_DESIGN')],rows)
        if coverage['issues']:raise ValueError(coverage['issues'][:5])
        if len({r['object_id'] for r in changes})!=len(changes):raise ValueError('one object changed twice')
        document={'format':'production-import-v1','expected_heads':{r['object_id']:r['id'] for r in original},'records':changes}
        return {'format':'generation-preparation-batch-v1','source_sha256':source_hash,'document':document,'document_sha256':digest(document),
                'summary':{'entities':len(actual),'complete_states':len(forms),'generation_plans':len(needs),'episode01_lines':len(cues),'changed_records':len(changes),
                   'changed_by_kind':dict(Counter(r['kind'] for r in changes)),'checked_uses':coverage['checked_count'],'protected_heads_sha256':digest(protected)},
                'entities':[{'entity':ref(entity(key)),'title':entity(key)['payload']['title'],'states':[ref(resolved[f['object_id']]) for f in forms if f['payload']['entity']['object_id']=='entity-'+key]} for key in ENTITIES],
                'requirements':[{'reference':ref(r),'state':r['payload']['scope'],'name':r['payload']['generation']['output']['name'],'media_type':r['payload']['media_type']} for r in needs]}
    finally:clone.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['plan','apply']);parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True);parser.add_argument('--file',type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p
    store=Store(args.instance.resolve()/'.runtime/review.sqlite3')
    try:
        if args.command=='plan':
            value=prepare(store,p);args.file.parent.mkdir(parents=True,exist_ok=True);args.file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps(value['summary'],ensure_ascii=False))
        else:
            value=json.loads(args.file.read_text())
            if value['document_sha256']!=digest(value['document']):raise ValueError('batch checksum changed')
            if value['source_sha256']!=hashlib.sha256((ROOT/'imports/screenplay-04.json').read_bytes()).hexdigest():raise ValueError('screenplay changed')
            result=p.import_records(store,value['document']);print(json.dumps({'applied_records':len(result['records'])}))
    finally:store.close()

if __name__=='__main__':main()
