#!/usr/bin/env python3
"""Export per-shot audiovisual preparation, never submit generation or infer adoption.

Whole voice masters are NOT attached automatically. A later reviewed clip must
name the exact adopted master, component, in/out points, derived file and hash.
The plan remains non-executable until all required selections and quota checks
are present. This exporter intentionally has no network or paid execution path.
"""
import argparse
import json
from pathlib import Path
import sys
from native_audio_workflow import AUDIO_MODE, ref

ROOT=Path(__file__).resolve().parents[1]
VOICES={key:'need-form-'+key+'-'+form+'-voice' for key,form in
        [('li-ji','paste'),('a-heng','blue'),('zhou','base'),('zhao','base'),('woodcutter','base'),('rice-listeners','base'),('street-passers','base')]}


def validate_reference_budget(audio,image_count=0):
    if len(audio)>3:raise ValueError('Seedance 2.0 accepts at most three audio references')
    durations=[r['range']['end_seconds']-r['range']['start_seconds'] for r in audio]
    if any(d<2 or d>15 for d in durations) or sum(durations)>15:
        raise ValueError('audio clips must each be 2–15 seconds and total at most 15 seconds')
    if image_count>9:raise ValueError('deduplicate or compose image references; at most nine per call')


def compile_plan(store,p):
    config=json.loads((ROOT/'config/seedance.json').read_text());rows=p.current_records(store);by={r['object_id']:r for r in rows}
    shots=sorted((r for r in rows if r['kind']=='SHOT_DESIGN'),key=lambda r:r['payload']['number'])
    cues=json.loads((ROOT/'production/episode01/dialogue-cues.json').read_text());result=[]
    for index,shot in enumerate(shots):
        s=shot['payload']
        if s.get('audio_delivery')!=AUDIO_MODE:raise ValueError('shot has not adopted the native audio workflow')
        lines=[c for c in cues if c['shot_id']==shot['object_id']]
        # One reference per speaking identity plus one melody when sung; not
        # one audio file per line. All references remain exact planned needs.
        template_ids=list(dict.fromkeys(VOICES[c['entity']['object_id'].removeprefix('entity-')] for c in lines))
        if any(c['type']=='singing' for c in lines):template_ids.append('need-form-boat-song-short-overall')
        if len(template_ids)>config['reference_audio_max_count']:raise ValueError('split the shot or review a combined voice reference')
        needs=[r for r in rows if r['kind']=='REQUIREMENT' and r['payload']['scope']['object_id']==shot['object_id']]
        if any(r['payload']['media_type']=='audio' for r in needs):raise ValueError('independent line audio must be removed')
        seconds=s['duration_frames']/s['fps'];duration=max(config['duration_min'],seconds)
        if duration>config['duration_max']:raise ValueError('shot exceeds generation duration; redesign before execution')
        prompts=['二维人物＋轻手绘背景；正常身体比例，干净线条与平涂色块，避免纸纹和过度风格化。',
                 '制作有声视听预演，画幅16:9。'+s['purpose'],'构图：'+s['framing'],'空间：'+s['spatial'],
                 '动作开始：'+s['action_start'],'动作结束：'+s['action_end'],'承接：'+s['continuity']]
        for n,oid in enumerate(template_ids,1):
            need=by[oid];role='旋律、节奏与演唱方式' if oid.endswith('song-short-overall') else '说话人的基础音色'
            prompts.append(f'@音频{n} 仅参考{need["payload"]["title"]}的{role}，不要复述参考样本内容。')
        for c in lines:
            prompts.append(f'{c["planned_start_frame"]/c["fps"]:.2f}–{c["planned_end_frame"]/c["fps"]:.2f}秒预计窗口：{c["speaker"]}{"唱" if c["type"]=="singing" else "说"}：“{c["text"]}”')
        for event in s['sound']:
            if event['type']=='environment_and_action':prompts.append('同步环境与动作声：'+event['description'])
        prompts.append('对白和歌词逐字保持；自然停顿与口型、动作协同。时间为表演目标，不能为卡点吞字。无新增旁白、台词或歌词；除指定演唱外不加配乐。')
        if duration!=seconds:prompts.append(f'动作在前{seconds:g}秒完成，尾部保持至{duration:g}秒，供剪辑裁掉多余保持；不要增加剧情。')
        sound=[{'requirement':ref(by[oid]),'role':by[oid]['payload']['audio_role'],'selection':None,'clip_status':'待听审并显式选择准确短片段'} for oid in template_ids]
        result.append({'format':'seedance-shot-plan-v1','shot':ref(shot),'source':s['source'],
            'previous_shot':ref(shots[index-1]) if index else None,'next_shot':ref(shots[index+1]) if index+1<len(shots) else None,
            'model':config['model'],'parameters':{'ratio':config['ratio'],'resolution':config['resolution'],'duration':duration,'generate_audio':True},
            'editorial':{'fps':s['fps'],'planned_start_frame':s['planned_start_frame'],'duration_frames':s['duration_frames'],
                         'trim_generated_range_seconds':[0,seconds]},'prompt':'\n'.join(prompts),
            'image_requirements':[ref(r) for r in needs if r['payload']['media_type']=='image'],'audio_templates':sound,
            'dialogue_and_lyrics':lines,'ready':False,'executed':False,
            'missing':['镜头所需图像须显式采用准确原件','音色／旋律须听审并选定准确短片段，按输入上限组织','实际执行平台和现有可用额度须核对'],
            'review':['逐字听辨台词与歌词，复核说话人、音色、旋律','回看动作、空间、表演与镜间连续性','实测声音时机，调整预计窗口或重新生成；不另造独立台词音轨']})
    if len(result)!=33 or sum(len(x['dialogue_and_lyrics']) for x in result)!=37:raise ValueError('locked first episode coverage differs')
    return {'format':'seedance-episode-plan-v1','config':config,'shots':result,'ready':False,'executed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True);parser.add_argument('--output',type=Path,default=ROOT/'production/episode01/seedance');args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p
    store=Store(args.instance.resolve()/'.runtime/review.sqlite3')
    try:value=compile_plan(store,p)
    finally:store.close()
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'manifest.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    for shot in value['shots']:
        (args.output/(shot['shot']['object_id']+'.txt')).write_text(shot['prompt']+'\n')
    print(json.dumps({'shots':len(value['shots']),'dialogue_and_singing':sum(len(s['dialogue_and_lyrics']) for s in value['shots']),'ready':False,'executed':False}))

if __name__=='__main__':main()
