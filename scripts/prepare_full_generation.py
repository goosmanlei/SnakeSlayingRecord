#!/usr/bin/env python3
"""Prepare source-locked non-song recipes; no provider calls or formal writes."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from full_generation_design import BASE_KEYS, DESIGN, STATE_CHOICES, STYLE
from full_generation_voice_design import BORROWED, EMBEDDED, GROUP_ENTITIES, LABELS, SUPPLEMENTS, VOICES
from production_forms import DIMENSION_LABELS

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ref(row):
    return {'object_id': row['id'], 'revision_id': row['current_revision']}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load_snapshot(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    rows = [{**dict(r), 'payload': json.loads(r['payload'])} for r in db.execute(
        'select o.*,r.payload from objects o join revisions r on r.id=o.current_revision order by o.id')]
    comments = [dict(r) for r in db.execute('select * from comments order by id')]
    counts = {table: db.execute('select count(*) from ' + table).fetchone()[0] for table in (
        'objects', 'revisions', 'dependencies', 'comments', 'comment_events', 'material_rounds', 'material_members')}
    db.close()
    return rows, comments, counts


def source_map(by):
    locked = json.loads((ROOT / 'production/source-lock.json').read_text())
    script = json.loads((ROOT / 'imports/screenplay-04.json').read_text())
    assert hashlib.sha256((ROOT / 'imports/screenplay-04.json').read_bytes()).hexdigest() == locked['screenplay']['file_sha256']
    assert by[locked['screenplay']['object_id']]['current_revision'] == locked['screenplay']['revision_id']
    blocks, episodes = {}, []
    for e in locked['episodes']:
        row = by[e['object_id']]
        assert row['current_revision'] == e['revision_id'], 'formal episode changed: ' + e['object_id']
        local = next(x for x in script['episodes'] if x['id'] == e['object_id'])
        assert local['blocks'] == row['payload']['blocks'], 'local screenplay differs from formal episode'
        episodes.append(ref(row))
        for b in local['blocks']:
            blocks[b['id']] = {'text': b['text'], 'source': {**ref(row), 'scene_id': b['id'].split('-')[-2], 'block_ids': [b['id']]}}
    assert len(blocks) == 1114
    return locked, episodes, blocks


def concrete_dimensions(payload):
    """Keep stated coexistence; unspecified art is supplied by authored choices."""
    out = []
    for key, value in payload['dimensions'].items():
        if key == 'voice':
            continue
        pieces = re.split(r'(?<=[。；\n])', value)
        kept = [s for s in pieces if s.strip() and not any(x in s for x in (
            '待审', '待首轮', '按本场', '以本场', '依本场', '未明确', '未写内容', '以上述描述',
            '见完整形态描述', '具体时段见本场', '维持上述完整形态'))]
        text = ''.join(kept).strip()
        if text:
            out.append(DIMENSION_LABELS.get(key, key) + '：' + text)
    return '\n'.join(out)


def image_plans(rows, by, apply_scope_amendment=True):
    states = [r for r in rows if r['kind'] == 'STATE' and r['payload'].get('state_model') == 'complete-v1']
    targets = [r for r in states if r['payload']['reference_media'] == 'image'
               and by[r['payload']['entity']['object_id']]['payload']['entity_type'] != 'song']
    assert len(states) == 267 and len(targets) == 255, 'scope changed; review differences before proceeding'
    baseline_count=126
    amendment_path=ROOT/'production/full-generation/scope-amendment.json'
    if apply_scope_amendment and amendment_path.exists():
        amendment=json.loads(amendment_path.read_text())
        assert amendment['approval']['actor']=='user' and amendment['approval']['reply'], 'scope amendment lacks user confirmation'
        excluded={item['old']['object_id'] for item in amendment['state_mapping']}
        assert excluded <= {r['id'] for r in targets}, 'scope amendment does not match inventory'
        assert len(targets)==amendment['before_image_count'], 'scope changed before amendment'
        targets=[r for r in targets if r['id'] not in excluded]
        assert len(targets)==amendment['after_image_count'], 'scope changed after amendment'
        baseline_count=amendment['after_image_baselines']
    keys = {s['payload']['entity']['object_id'][7:] for s in targets}
    assert len(keys) == baseline_count and keys <= DESIGN.keys()
    out = []
    for state in targets:
        p = state['payload']; entity = by[p['entity']['object_id']]; ep = entity['payload']
        key = entity['id'][7:]; sid = state['id'][5:]
        base_id = 'form-' + key + '-' + BASE_KEYS.get(key, 'base')
        assert base_id in by, 'missing authored baseline ' + base_id
        base = by[base_id]; need = by['need-' + state['id'] + '-overall']
        base_need = by['need-' + base_id + '-overall']; is_base = state['id'] == base_id
        shape = STATE_CHOICES.get(sid) or concrete_dimensions(p)
        assert shape, state['id']
        if ep['entity_type'] == 'space':
            ratio = '16:9'
            composition = '单幅可理解的空间全景，轻微俯视而不压扁高度，前中后景和出入口清楚，主要通道完整入画；保留状态规定的固定布置，不用人物遮住空间，不新增剧情动作。'
            shape += '\n画面时刻选择所述状态中最早已成立的完整布置；日间用柔和自然光，暮色用低饱和灰蓝天光，夜间只保留所述灯源暖光，不在一张图拼接多时刻。'
        elif ep['subtype'] == 'group' or key == 'snake':
            ratio = '16:9' if key == 'snake' else '4:3'
            composition = '所有指定组成完整入画，留边不切头脚；群组成员错位但不互挡脸和衣着，大蛇展示首尾完整轮廓。浅暖灰简底，非镜头叙事画面。'
        elif ep['entity_type'] == 'character':
            ratio = '3:4'; composition = '单一人物全身、三分之四视角，头至鞋完整入画，手掌和关键伤布可看清，浅暖灰简底、柔和中性光。状态需要承重或坐姿时保留全身和必要支撑，不强改为站姿。'
        else:
            ratio = '4:3'; composition = '完整道具或该状态全部组成作为单幅整体参考，三分之四视角，轮廓清楚、比例可辨，浅暖灰简底、柔和中性光。必要承托部位仅帮助理解附着和受力，不能用细节裁切替代全部形态。'
        if key == 'paste-wool' and sid != 'paste-wool-paste':
            composition += ' 本对象是附着材料；用双手和布巾承托完整分布，双手从腕至指尖全入画，不另生成角色脸或身体。'
        if key in {'crossbeam', 'cave-gate', 'feeding-channel', 'feeding-door', 'snake'}:
            shape += '\n涉及门闸时北在画面后方、南在前方；示意背景与剧情分开。封顶石道、人留院外、蛇身留北洞的关系不可改写；剖切仅是图示，不是新增开口。'
        continuity = ('本张为独立文字生成的干净基准，没有提交参考图片，不声称使用旧候选。' if is_base else
            '实际参考图片按提交顺序编号：参考图1是本实体已认可的基准整体原件，使用整幅。严格保留其身份、身体/器物比例、轮廓、颜色、线条与空间方向，只按下述完整状态改变已明确部位；不要加重纸纹、颗粒或锐化。')
        comparison = ('基础状态，同时覆盖实体身份；本任务不另外为实体再生成一张。' if is_base else
            '与基准“' + base['payload']['title'] + '”相比，本张改为“' + p['title'] + '”；完整差异及仍须并存的特征如下。未列明改变的身份轮廓、配色与结构保持基准。')
        prompt = '\n'.join([STYLE, '用途：全剧非歌曲实体的完整状态整体参考，不是分镜画面或多状态拼图。',
            '实体：' + ep['title'] + '。', '固定身份与制作造型：' + DESIGN[key], comparison,
            '本张完整形态：' + shape, continuity, '画幅 ' + ratio + '。' + composition,
            '不要添加水印、装饰边框或状态标题。必要道具文字只使用已指定的原句；其余用不可辨稀疏笔迹或留白，不补造歌词、日期、人物姓名或新剧情。'])
        params = {'imageCount': 1, 'aspectRatio': ratio, 'resolutionTier': '4k', 'quality': 'high',
                  'lockAspectRatio': True, 'outputFormat': 'png', 'autoEnhancePrompt': False, 'variant': 'sunburst'}
        inputs = [] if is_base else [{'reference': ref(base_need), 'use': '参考图1；本实体认可的干净根母版，完整原图，锁定身份、轮廓与画风。'}]
        out.append({'id': state['id'], 'entity': ref(entity), 'state': ref(state), 'requirement': ref(need),
            'expected_requirement_version': need['version'], 'baseline_state': ref(base), 'is_baseline': is_base,
            'title': p['title'], 'facts': p['facts'], 'sources': p['sources'], 'production_choices': DESIGN[key],
            'full_shape': shape, 'difference_from_baseline': comparison,
            'generation': {'format': 'generation-plan-v1', 'method': 'generate', 'model': 'gpt-image-2-5-sunburst',
                'parameters': params, 'prompt': prompt, 'inputs': inputs,
                'output': {'name': '完整状态整体参考', 'description': p['title'] + '：' + shape,
                    'review_criteria': ['完整形态与定稿及本轮制作选择相符', '身份、比例、线条、配色与所绑母版一致',
                        '保存平台最高档直接返回的原件尺寸，不放大冒充4K', '整体入画，无纸纹噪点漂移；图生图最深谱系不超过两代']},
                'blockers': [] if is_base else ['等待用户认可本实体准确母版，绑定其素材修订、原件组成、SHA-256后才可调用。']},
            'execution': {'channel': 'OpenArt connector', 'project_id': '8K6WcbrPLghSBJXBtWAE',
                'mode': 'text2image' if is_base else 'image2image', 'reference_bindings': [],
                'binding_status': 'no_reference_required' if is_base else 'pending_approved_master',
                'planned_i2i_depth': 0 if is_base else 1, 'actual_call': None}})
    return out, states


def voice_plans(rows, by, blocks):
    spoken = defaultdict(list); excluded = []; unresolved = []
    for bid, block in blocks.items():
        match = re.match(r'^([^：\n]{1,24})：(.*)$', block['text'], re.S)
        if not match:
            continue
        label, text = match.groups(); scene = int(block['source']['scene_id'][1:])
        if label.endswith('（唱）') or label == '字幕':
            excluded.append({'source': block['source'], 'label': label, 'reason': '歌曲演唱或无声字幕'}); continue
        identity = LABELS.get(label)
        if label == '书吏':
            identity = 'clerk-notice' if scene == 13 else 'clerk-proclamation' if scene == 37 else None
        if identity:
            spoken[identity].append({'text': text, 'source': block['source'], 'original_speaker': label})
        elif label in {'经过人群，有人贴着家人的耳朵说','远处祈福戏重新响起。唱腔顺着河面飘来','李诞回忆中的短暂画面','贴纸揭下，旧字完整露出来'}:
            excluded.append({'source': block['source'], 'label': label, 'reason': '嵌入对白单独核对，或非对白叙述/歌曲/纸上文字'})
        else:
            unresolved.append({'source': block['source'], 'label': label})
    assert not unresolved, unresolved
    def get(scene, number):
        return blocks[f'screenplay-04-lantern-home-s{scene:03d}-b{number:03d}']
    for identity, (scene, number, text) in EMBEDDED.items():
        block = get(scene, number)
        if text:
            assert text in block['text']
        spoken[identity].append({'text': text, 'source': block['source'], 'original_speaker': VOICES[identity][0],
            'indirect_speech': text is None})
    assert spoken.keys() == VOICES.keys(), (spoken.keys() - VOICES.keys(), VOICES.keys() - spoken.keys())
    states = [r for r in rows if r['kind'] == 'STATE' and r['payload'].get('state_model') == 'complete-v1']
    audio_parameters = {'audio_config': {'format':'wav','sample_rate':48000,'pitch_rate':0,
        'speech_rate':0,'loudness_rate':0,'enable_subtitle':True}, 'watermark':{}}
    out = []
    for identity, (title, direction) in VOICES.items():
        key = GROUP_ENTITIES.get(identity, identity); entity = by['entity-' + key]
        coverage = [ref(s) for s in states if s['payload']['entity']['object_id'] == entity['id']]
        alternate = {sid for choice in SUPPLEMENTS.values() if choice['identity'] == identity for sid in choice['states']}
        coverage = [s for s in coverage if s['object_id'] not in alternate | {'form-li-dan-memory'}]
        # A quoted sample stays an exact substring. Short roles stay short;
        # the provider is not asked to invent or repeat filler to reach a timer.
        samples = []
        for line in spoken[identity]:
            if line['text']:
                samples.append(line)
            if sum(len(s['text']) for s in samples) >= 85 or len(samples) >= 4:
                break
        sample_policy = '本角色定稿原句，不生产逐句配音轨。'
        if not samples:
            original_speaker, scene, number = BORROWED[identity]
            block = get(scene, number); text = block['text'].split('：', 1)[1]
            assert text
            samples = [{'text': text, 'source': block['source'], 'original_speaker': VOICES[original_speaker][0]}]
            sample_policy = '原文只说明此人说话，未给逐字台词；借用所列其他角色的定稿原句作音色试读，不把试读归为本角色剧情台词，不新增或改写剧本。'
        prompt = ('生成一份单人干净音色核对录音。说话身份：' + title + '。声音方向：' + direction + '。\n'
            + '只说以下定稿试读原文，不念角色名、说明或引号，不改字、不加词、不延长为新对白；句间留自然短停顿。\n'
            + '\n'.join('“' + s['text'] + '”' for s in samples)
            + '\n单一说话者，普通话自然口语，近距离干净录音；无歌唱、音乐、环境声、他人声和混响。开头结尾各留约半秒安静。输出48 kHz WAV，声道及编码以实际回执与原件检测登记。')
        out.append({'id':'voice-' + identity + '-base','identity':identity,'title':title + ' · 基础音色',
            'entity':ref(entity),'coverage':coverage,'kind':'base','speaking_evidence':spoken[identity],
            'samples':samples,'sample_policy':sample_policy,'direction':direction,'reuse_reason':'同一说话身份的衣着、持物、普通情绪和场所变化复用母版；不生成未说话成员的声线。',
            'generation':{'model':'seed-audio-1.0','parameters':deepcopy(audio_parameters),'prompt':prompt,'references':[]},
            'execution':{'channel':'Doubao Speech HTTP','binding_status':'no_reference_required','actual_call':None}})
    for key, choice in SUPPLEMENTS.items():
        identity=choice['identity'];samples=[]
        for n in choice['sample_blocks']:
            b=get(choice['sample_scene'],n);assert b['text'].startswith('阿蘅：')
            samples.append({'text':b['text'].split('：',1)[1],'source':b['source'],'original_speaker':'阿蘅'})
        prompt=('参考@音频1，严格保持该音频的阿蘅身份。'+choice['direction']+'\n只说以下定稿原文，不读标签，不改字、不加词：\n'
            +'\n'.join('“'+s['text']+'”' for s in samples)+'\n干净单人48 kHz WAV；无歌曲、音乐、环境声、他人声或空间混响，首尾各半秒安静。')
        out.append({'id':'voice-'+key,'identity':identity,'title':'阿蘅 · '+('嗓哑补充' if key.endswith('hoarse') else '泪后哽咽补充'),
            'entity':ref(by['entity-a-heng']),'coverage':[ref(by[x]) for x in choice['states']],
            'kind':'supplement','reason':choice['reason'],'samples':samples,'direction':choice['direction'],
            'sample_policy':'同角色在对应状态的定稿原句。','generation':{'model':'seed-audio-1.0','parameters':deepcopy(audio_parameters),'prompt':prompt,
                'references':[{'number':1,'pending_master':'voice-a-heng-base','use':'经用户认可的基础音色原件，完整片段不超过30秒；绑定准确文件与修订后调用'}]},
            'execution':{'channel':'Doubao Speech HTTP','binding_status':'pending_approved_master','actual_call':None}})
    speaking_entities = {r['entity']['object_id'] for r in out}
    exclusions = [{'entity':ref(r),'title':r['payload']['title'],
        'reason':'无明确说话身份；歌曲演唱、动物发声、笑/哭/喘/喝彩等非词汇声和仅提及不补造独立声线。'} for r in rows
        if r['kind']=='ENTITY' and r['payload']['entity_type']=='character'
        and r['id'] not in speaking_entities | {'entity-temple-children'}]
    assert len(out)==42 and sum(x['kind']=='base' for x in out)==40
    return out, exclusions, excluded


def prepare(snapshot, destination):
    rows, comments, counts=load_snapshot(snapshot);by={r['id']:r for r in rows}
    locked, episodes, blocks=source_map(by)
    images,states=image_plans(rows,by);voices,voice_exclusions,non_dialogue=voice_plans(rows,by,blocks)
    pending_voice_scope = [
        {'identity':'temple-children-questioner','title':'扯母亲问月亮去哪了的孩子',
         'source':blocks['screenplay-04-lantern-home-s008-b028']['source'],
         'text':blocks['screenplay-04-lantern-home-s008-b028']['text'],
         'proposed_entity':ref(by['entity-temple-children']),
         'proposal':'群体中仅此明确发问者增加一份音色；不等同已经离开的领粮妇人孩子。'},
        {'identity':'county-offscreen-caller','title':'屋内唤程差役的人',
         'source':blocks['screenplay-04-lantern-home-s035-b009']['source'],
         'text':blocks['screenplay-04-lantern-home-s035-b009']['text'],
         'proposed_entity':None,
         'proposal':'现有133实体未抽取此未具名身份；拟新增仅声音实体和状态，不关联成梁书吏或其他现有人物，不新增图像。'}]
    original=json.loads((ROOT/'production/inventory.json').read_text())['records']
    inventory={r['object_id']:r for r in original}
    changes=[{'object_id':r['id'],'current_revision':r['current_revision'],'current_version':r['version'],
        'changed_fields':sorted(k for k in r['payload'].keys() | inventory[r['id']]['payload'].keys()
            if r['payload'].get(k)!=inventory[r['id']]['payload'].get(k))}
        for r in rows if r['id'] in inventory and r['payload']!=inventory[r['id']]['payload']]
    exclusions=[{'state':ref(r),'title':r['payload']['title'],'media':r['payload']['reference_media'],
        'reason':'歌曲' if by[r['payload']['entity']['object_id']]['payload']['entity_type']=='song' else '仅声音或仅提及，不生成图像'}
        for r in states if r['id'] not in {i['id'] for i in images}]
    heads=[{'object_id':r['id'],'revision_id':r['current_revision'],'version':r['version'],'kind':r['kind']} for r in rows]
    source_lock={'format':'full-generation-source-lock-v1','task':'task-20261002-0003','screenplay':locked['screenplay'],
        'episodes':episodes,'formal_snapshot_counts':counts,'formal_heads':heads,'formal_comments_sha256':digest(comments),
        'current_records_sha256':digest(rows),'image_count':len(images),'image_entities':len({i['entity']['object_id'] for i in images}),
        'image_exclusions':exclusions,'voice_base_count':40,'voice_supplement_count':2,'voice_identity_exclusions':voice_exclusions,
        'pending_voice_scope':pending_voice_scope,
        'non_dialogue_colon_blocks':non_dialogue,'changed_records_since_initial_inventory':changes,
        'scope_delta':{'entity_ids_added':[],'entity_ids_removed':[],'image_state_ids_added':[],'image_state_ids_removed':[]},
        'known_content_correction':{'state':'form-paste-wool-paste','source':'screenplay-04-lantern-home-s003-b005/b006',
            'reason':'现有制作描述误写手上残渣；本轮按定稿端来制作浆糊纠正，不改变实体或状态数量。'}}
    initial_entities={r['object_id'] for r in original if r['kind']=='ENTITY'}
    assert initial_entities=={r['id'] for r in rows if r['kind']=='ENTITY'}
    initial_states={r['object_id'] for r in original if r['kind']=='STATE' and r['payload'].get('state_model')=='complete-v1'}
    assert initial_states=={r['id'] for r in states}
    bundle={'format':'full-generation-recipes-v1','task':'task-20261002-0003','source_lock_sha256':digest(source_lock),
        'images':images,'voices':voices,'summary':{'images':255,'image_baselines':sum(i['is_baseline'] for i in images),
            'image_derived':sum(not i['is_baseline'] for i in images),'voice_baselines':40,'voice_supplements':2,
            'voice_state_associations':sum(len(v['coverage']) for v in voices),
            'voice_reuse_associations':sum(len(v['coverage'])-1 for v in voices)},
        'stage':'prepared_for_review_and_binding','user_master_acceptances':[],
        'voice_scope_status':'40份母版加2份补充已编制；另2处间接发声已向用户展示差异并请求范围确认，尚未纳入正式需求或调用。',
        'pending_voice_scope':pending_voice_scope,
        'boundary':'提示词与范围已编制不等于生成、登记或用户认可。未认可母版的派生输入待绑定，不能提交占位参考。'}
    bundle['reference_binding_contract'] = {
        'OpenArt image2image': '逐项取得用户认可的准确素材修订与 original 组成，核对 SHA-256、完整区域和最深谱系；把同一原件的平台 URL 与 resource ID 依次放入 params.visualReferences，字段为 type=image、id、url、label=参考图1；下载回验与本地原件一致。不得提交占位 URL。',
        'Doubao Speech HTTP': '准确母版 WAV 不超过30秒，登记修订、组成、SHA-256、完整片段；payload.references 按顺序放 audio_data，提示词以 @音频1 指同一项。',
        'channel_switch': '内置图像渠道尚未调用。切换时重新读取当时工具能力和输入约定，不能沿用 OpenArt 参数或虚构底层模型。'}
    for item in images+voices:
        assert len(item['generation']['prompt'])>70
    for item in voices:
        assert len(item['generation']['prompt'])<=3000
    write(destination/'source-lock.json',source_lock);write(destination/'recipes.json',bundle)
    print(json.dumps(bundle['summary'],ensure_ascii=False))
    print('Inventory payload changes retained from formal data:',len(changes))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.snapshot,args.output)
