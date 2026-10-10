"""Verify existing exact audiovisual products without rebuilding their media plans."""
from collections import Counter
import importlib.util
import hashlib
import json
import re

from audiovisual_design import ROOT, future, reference, union_sources
from video_input_design import load_audit, frame_plan, video_plan, first_frame_states, frame_state_label, FRAME_USE
from state_preparation import decisions
import exact_text_handoffs

STYLE = '二维人物与轻手绘背景，正常人物比例，干净轮廓与清楚色块，背景轻而可读；不新增粗纸纹、颗粒、过锐边缘或写实皮肤。'
IMAGE_CHECK = ['画面中实际需要的身份、结构与状态和准确用途一致', '构图、接触点、空间出入口与轴线可核对',
               '核实际原件尺寸与原生回执，不以请求4K或放大冒充原生', '最深输入图像谱系不超过两代；失真时回干净母版']
AUDIO_CHECK = ['实际逐句听审而非仅据字幕判断', '音色身份、字音、呼吸、旋律用途一致，未混入其他说话人',
               '保留提供方原件、真实编码和时长；转码不冒充原生无损', '明确选定候选、原件与时间范围后才提交下游']
VIDEO_CHECK = ['逐句核对本镜准确剧本，不补写、缩词、提速或抢唱后文', '人物知情、动作顺序、接触点与受力合理',
               '镜前镜后状态和空间方向衔接，音画同期与声源距离可辨', '核实720p原件、真实时长及实际上传参考；无结果时保持未生成']
SONGS = {'entity-boat-song': 'need-form-boat-song-independent-overall',
         'entity-blue-awning-song': 'need-form-blue-awning-song-independent-overall',
         'entity-blessing-stage-song': 'need-form-blessing-song-independent-overall',
         'entity-snake-welcome-song': 'need-form-welcome-song-independent-overall'}


def description(payload):
    if 'production_description' in payload:
        return payload['production_description']
    if payload.get('state_model') == 'complete-v1':
        return '\n'.join(payload['dimensions'].values())
    return '\n'.join(b['text'] for b in payload['blocks'] if b['id'] == 'description')


TYPE_CHECKS = {
    'character': ['同一人物、动物或已定义群组的身份、数量与比例一致；适用的衣着、伤侧和持物按本阶段，不给动物套衣饰或把群组缩成一人'],
    'space': ['固定出入口、通道、尺度和岸船等接触关系一致；临时布置与光时符合本阶段',
              '按相邻镜起点、变化、落点检查，不提前出现新结构，也不把撤去的结构复原'],
    'prop': ['全形、材质、接触部位与内容一致；缺损、开合、装入或取出按动作先后发生',
             '检查持有者与去向；局部细节不冒充物件完整结构'],
    'song': ['只提供已说明的曲词与旋律范围；演唱者、距离、缺词停顿按现场用途核对',
             '独立完整歌曲、角色音色与镜内表演分别判断，不重复准备同一曲调'],
}


def casting():
    path = ROOT / 'production/audiovisual/voices.py'
    spec = importlib.util.spec_from_file_location('audiovisual_casting', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def recorded_voice_identity(asset, call):
    """Read the requested identity from an exact completed call, not its title.

    This is a candidate-discovery basis only. It cannot establish the audible
    speaker, quality, an appropriate excerpt, or suitability for a new use.
    """
    payload = asset['payload']
    if payload.get('media_type') != 'audio' or payload.get('placeholder'):
        return None
    originals = [c for c in payload.get('components', [])
                 if c.get('role') == 'original' and c.get('has_audio')]
    if len(originals) != 1 or call.get('kind') != 'CALL':
        return None
    recorded = call['payload']
    receipt = recorded.get('receipt', {})
    prompt = receipt.get('input', {}).get('text_prompt', '')
    if (recorded.get('method') != 'generation' or receipt.get('status') != 'completed'
            or not originals[0].get('sha256')
            or receipt.get('sha256') != originals[0]['sha256']
            or not prompt or prompt != recorded.get('prompt')):
        return None
    first_line = prompt.split('\n', 1)[0]
    match = re.fullmatch(r'生成一份单人干净音色核对录音。说话身份：(.+?)。声音方向：(.+)。', first_line)
    return match.groups() if match else None


def reviewed_voice_uses(root):
    """Read authored decisions; stale episode evidence never selects an input."""
    path = root / 'production/voice-reuse/reviews.json'
    if not path.exists():
        return {}, {}, False
    doc = json.loads(path.read_text())
    if doc.get('format') != 'reviewed-voice-reuse-v1' or doc.get('audio_generation') is not False:
        raise ValueError('invalid voice review source')
    script_hash = hashlib.sha256((root / 'imports/screenplay-04.json').read_bytes()).hexdigest()
    uses = {}
    for number, episode in enumerate(doc['episode_reviews'], 1):
        actual = hashlib.sha256((root / f'production/audiovisual/e{number:02}.md').read_bytes()).hexdigest()
        if (episode['number'] != number or episode['authored_sha256'] != actual
                or episode['screenplay_sha256'] != script_hash):
            raise ValueError('voice purpose changed; re-review episode ' + str(number))
        for use in episode['uses']:
            key = (use['shot'], use['speaker'])
            if key in uses or use['speaker'] not in episode['voices']:
                raise ValueError('ambiguous or unauthored voice use: ' + str(key))
            uses[key] = {**use, 'purpose': episode['voices'][use['speaker']]}
    return doc['reviews'], uses, doc.get('coverage_complete', False)


class Builder:
    def __init__(self, store, p, av_records, reviewed):
        self.store, self.p, self.av = store, p, av_records
        self.reviewed = reviewed
        self.preparation = decisions()
        self.text_handoffs = exact_text_handoffs.load()
        self.rows, self.generated, self.keep = [], {}, {}
        self.entities = {r['object_id']: r for r in p.current_records(store, {'ENTITY'})}
        self.states = {r['object_id']: r for r in p.current_records(store, {'STATE'})}
        self.image_config = json.loads((ROOT / 'config/openart.json').read_text())
        self.voice = casting()
        self.voice_reviews, self.voice_uses, self.voice_review_complete = {}, {}, False
        self.voice_choices = {}
        self.relations = {}
        for row in p.current_records(store, {'MATERIAL_RELATION'}):
            key = self.relation_key(row['payload'])
            if key in self.relations:
                raise ValueError('ambiguous existing material relation: ' + str(key))
            self.relations[key] = row['object_id']
        self.masters, self.state_needs, self.voices = {}, {}, {}
        self.counts = Counter()
        self.input_audit = load_audit([r for r in av_records if r['kind'] == 'AV_SHOT'])
        self.frame_subjects = {}
        for line in (ROOT / 'production/audiovisual/frame-subjects.txt').read_text().splitlines():
            if not line.strip() or line.startswith('#'): continue
            oid, subjects = (v.strip() for v in line.split('=', 1))
            if oid in self.frame_subjects: raise ValueError('duplicate first-frame selection: ' + oid)
            self.frame_subjects[oid] = {'entity-' + v for v in subjects.split()}
        if self.frame_subjects.keys() - {r['object_id'] for r in av_records if r['kind']=='AV_SHOT'}:
            raise ValueError('first-frame choices refer to absent shots')

    def resolve(self, oid):
        return future(oid) if oid in self.generated else reference(self.p.record(self.store, oid))

    def visual_description(self, row, fallback):
        choice = self.text_handoffs['visual_descriptions'].get(row['object_id'])
        if not choice:
            return fallback
        if choice['revision_id'] != row['id']:
            raise ValueError('text visual responsibility needs review after source change: ' + row['object_id'])
        return choice['text']

    def put(self, oid, kind, payload):
        if oid in self.generated:
            raise ValueError('duplicate authored material identity: ' + oid)
        payload['format'] = 'production-' + {'REQUIREMENT': 'requirement', 'MATERIAL_RELATION': 'material-relation'}[kind] + '-v1'
        payload['blocks'] = [{'id': 'purpose', 'text': payload['purpose']}]
        row = {'object_id': oid, 'kind': kind, 'expected_version': 0, 'payload': payload}
        self.generated[oid] = row
        self.rows.append(row)
        self.counts[kind] += 1
        return oid

    def relation(self, upstream, downstream, context, purpose, preserve, change, check, *, sources,
                 necessity='required', group=None, route=None, semantics='reference', type_id='reference', identity=None,
                 upstream_ref=None):
        exact = upstream_ref or self.resolve(upstream)
        if exact['object_id'] != upstream:
            raise ValueError('exact relation source differs from upstream identity')
        values = {'title': purpose, 'purpose': purpose, 'upstream': exact,
            'downstream_id': downstream, 'context': context, 'preserve': preserve, 'change': change, 'check': check,
            'type_id': type_id, 'type_label': {'identity-state': '身份到实体状态', 'space-camera': '空间到机位',
                'frame-video': '起始图到镜头视频', 'reference': '准确素材参考', 'state-frame': '实体状态到首帧',
                'voice-performance': '音色到现场表演', 'voice-reuse': '已有声音身份复用',
                'state-video': '镜内后续内容到视频'}.get(type_id, type_id),
            'type_version': 1, 'type_definition': {'endpoints': ['REQUIREMENT' if upstream in self.generated else self.p.record(self.store, upstream)['kind'], 'REQUIREMENT'], 'direction': 'directed',
                'attributes': {'i2i_budget': '图像最深参考谱系上限，执行时按实际输入回查，不是已生成代数'}},
            'attributes': {'i2i_budget': 2}, 'semantics': semantics, 'necessity': necessity,
            'basis': 'production_choice', 'sources': sources}
        if group:
            values.update(group=group, route=route)
        key = self.relation_key(values)
        # Position in a batch is not an identity: inserting a voice event must
        # not relabel every subsequent edge or overwrite a different relation.
        oid = self.relations.get(key) or identity or 'mr-' + hashlib.sha256(json.dumps(key).encode()).hexdigest()[:32]
        self.put(oid, 'MATERIAL_RELATION', values)
        return {'reference': exact, 'relation': future(oid), 'selection_state': 'unselected', 'use': purpose}

    def voice_choice(self, key):
        review = self.voice_reviews.get(key)
        if not review:
            if self.voice_review_complete:
                raise ValueError('current voice lacks an individual review: ' + key)
            return None
        if review['need_id'] != 'material-voice-' + key:
            raise ValueError('voice review names another need: ' + key)
        source = review['source']
        exact = {k: source[k] for k in ('object_id', 'revision_id')}
        asset = self.p.record(self.store, **exact)
        call = self.p.record(self.store, **asset['payload']['production'])
        owner = 'entity-' + self.voice.GROUP_ENTITIES.get(key, key)
        if ({v['object_id'] for v in asset['payload']['subjects']} != {owner}
                or recorded_voice_identity(asset, call) != self.voice.VOICES[key]):
            raise ValueError('reviewed voice owner or requested direction changed: ' + key)
        component = next((v for v in asset['payload']['components'] if v['id'] == source['component_id']), None)
        if not component or component['role'] != 'original' or component['sha256'] != source['sha256']:
            raise ValueError('reviewed original component changed: ' + key)
        if not review['analysis_attempts']:
            raise ValueError('voice choice has no actual audio analysis: ' + key)
        for attempt in review['analysis_attempts']:
            evidence = json.loads((ROOT / 'production/voice-reuse/analysis' / (attempt + '.json')).read_text())
            metadata = evidence['request_metadata']['source']
            if (evidence['receipt'].get('state') != 'completed' or metadata['sha256'] != source['sha256']
                    or metadata['asset']['object_id'] != source['object_id']
                    or metadata['asset']['revision_id'] != source['revision_id']
                    or metadata['component'] != source['component_id']):
                raise ValueError('voice analysis refers to another or incomplete original: ' + key)
        selected = review.get('range')
        decision = review['decision']
        if decision not in {'suitable_spoken_identity', 'needs_comparison', 'needs_new_reference', 'needs_longer_reference'}:
            raise ValueError('unrecognised authored voice decision: ' + key)
        if selected:
            start, end = selected['start_seconds'], selected['end_seconds']
            if (type(start) not in (int, float) or type(end) not in (int, float)
                    or not 0 <= start < end <= component['duration_seconds'] or not 2 <= end-start <= 15):
                raise ValueError('reviewed voice range violates actual source/channel bounds: ' + key)
        if (decision == 'suitable_spoken_identity' and not selected
                or decision in {'needs_new_reference', 'needs_longer_reference'} and selected):
            raise ValueError('voice decision and execution range disagree: ' + key)
        return {'review': review, 'reference': exact, 'component': component}

    def voice_input(self, key, downstream, scope, sources, shot):
        name = self.voice.VOICES[key][0]
        use = self.voice_uses.get((shot, key))
        choice = self.voice_choices.get(key)
        if not use and self.voice_review_complete:
            raise ValueError('current voice use lacks an episode judgment: ' + shot + ' ' + key)
        if use:
            actual = [e for e in self.reviewed.for_sources(sources) if e['speaker'] == key]
            if (use['source_keys'] != list(dict.fromkeys(e['source'] for e in actual))
                    or use['modes'] != list(dict.fromkeys(e['mode'] for e in actual))):
                raise ValueError('reviewed voice event changed: ' + shot + ' ' + key)
        purpose = name + '：只锁定说话身份的干净短参考'
        preserve = '同一人物的音区、共鸣与咬字'
        change = '按本镜正文和身体状态重新表演，不照搬试样文字或静音口型'
        check = '明确选取约2至4秒可辨音色片段，所有音频参考总长在模型上限内'
        if use and choice and choice['review']['decision'] == 'suitable_spoken_identity':
            # Keep the existing need-to-shot identity as a descriptive link.
            # Its old required revision remains historical; it is not a second
            # active execution dependency alongside the selected exact asset.
            old_key = (self.voices[key], downstream, scope['object_id'], 'voice-performance',
                       'reference', 'required', None, None)
            self.relation(self.voices[key], downstream, scope, name + '：当前声音需求与本镜用途说明',
                preserve, change, use['purpose'], sources=sources, type_id='voice-performance',
                semantics='description', necessity='optional', identity=self.relations.get(old_key))
            item = self.relation(choice['reference']['object_id'], downstream, scope, purpose,
                preserve, change + '；不继承旧语气、呼吸、空间或演唱旋律',
                '核已选完整短片段及全部音频参考总长；本集复核：' + use['purpose'] + '；新片段及新方案不继承旧母版认可',
                sources=sources, type_id='voice-performance', upstream_ref=choice['reference'])
            item.pop('selection_state')
            item.update(component_id=choice['review']['source']['component_id'], range=choice['review']['range'])
            return item
        return self.relation(self.voices[key], downstream, scope, purpose, preserve, change, check,
            sources=sources, type_id='voice-performance')

    @staticmethod
    def relation_key(payload):
        return (payload['upstream']['object_id'], payload['downstream_id'], payload['context']['object_id'],
                payload['type_id'], payload['semantics'], payload['necessity'], payload.get('group'), payload.get('route'))

    def plan(self, media, prompt, inputs=(), *, seconds=None, name, description, selected_routes=None, image_ratio='16:9'):
        if media == 'image':
            model, tool = self.image_config['preferred_model'], 'openart cli'
            params = {'project_id': self.image_config['project_id'], 'quality': 'high', 'resolution': '4K',
                      'aspect_ratio': image_ratio, 'n': 1}
            criteria = IMAGE_CHECK
        elif media == 'audio':
            model, tool = 'seed-audio-1.0', 'Seed Audio'
            params = {'audio_config': {'format': 'wav', 'sample_rate': 48000, 'pitch_rate': 0,
                       'speech_rate': 0, 'loudness_rate': 0, 'enable_subtitle': True}, 'watermark': {}}
            criteria = AUDIO_CHECK
        else:
            model = 'seedance2.0_fast_vision' if seconds <= 15 else 'Seedance_2.5'
            tool = 'pippit-tool-cli'
            params = {'duration': seconds, 'resolution': '720p', 'aspect_ratio': '16:9'}
            criteria = VIDEO_CHECK
        return {'format': 'generation-plan-v1', 'method': 'generate', 'tool': tool, 'model': model,
                'prompt': prompt, 'parameters': params, 'inputs': list(inputs), 'relation_model': 'context-v1',
                'selected_routes': selected_routes or {}, 'conditions': {}, 'blockers': [],
                'randomization': {'mode': 'random'}, 'output': {'name': name, 'description': description, 'review_criteria': criteria}}

    def need(self, oid, scope, slot, media, purpose, plan, *, sources, entities=(), states=(), required=True, specification=None, usage=None):
        spec = specification or {}
        if media == 'image':
            spec['native_resolution_policy'] = 'highest_provider_native'
        return self.put(oid, 'REQUIREMENT', {'title': plan['output']['name'], 'scope': scope, 'slot': slot,
            'media_type': media, 'purpose': purpose, 'required': required, 'usage': usage or ('generation_input' if media != 'video' else 'editorial'),
            'entities': list(entities), 'states': list(states), 'sources': sources, 'specification': spec, 'generation': plan})

    def roots(self):
        used = {r['object_id'] for row in self.av if row['kind'] == 'AV_SHOT' for r in row['payload']['states']}
        visual_owners = {self.states[oid]['payload']['entity']['object_id'] for oid in used
                         if self.states[oid]['payload']['reference_media'] == 'image'}
        for owner in sorted(visual_owners):
            row = self.entities[owner]; payload = row['payload']; kind = payload['entity_type']
            oid = 'material-' + owner + '-identity'
            composition = {'character': '按对象实际定义呈现一人、一只动物或可逐个辨认的群组；以等比例正侧背面说明身份、轮廓和完整肢体，群组不复制同脸，不给动物套人类衣饰。中性姿态、浅灰背景，无现场伤势或剧情动作。',
                           'space': '空间全景与清楚的出入口、通道和固定结构关系，不画临时人物；先确定左右与尺度，不用镜像变体。',
                           'prop': '按对象定义呈现单件或实际物件组，全形与接触结构清楚，保留真实材质与轮廓，中性背景，不加入使用者或现场动作。'}.get(kind, '主体完整入画，身份与结构清楚。')
            description = self.visual_description(row, payload.get('production_description') or '\n'.join(payload['facts']))
            prompt = f'{STYLE}\n对象：{payload["title"]}。{description}\n{composition}\n这是从文字创建的干净根母版；当前没有选中图像输入，不假称参考现有候选。无装饰边框、水印或额外文字。'
            name = payload['title'] + (' · 空间布局母版' if kind == 'space' else ' · 身份母版' if kind == 'character' else ' · 结构母版')
            purpose = '为全剧固定' + payload['title'] + '的身份、轮廓、配色和可复查结构；实际候选仍须逐项选择。'
            self.need(oid, reference(row), 'layout-master' if kind == 'space' else 'identity-master', 'image', purpose,
                self.plan('image', prompt, name=name, description=composition, image_ratio='3:4' if kind == 'character' else '16:9' if kind == 'space' else '4:3'),
                sources=payload['sources'], entities=[reference(row)], specification={'lineage_role': 'clean_master', 'planned_i2i_depth': 0})
            self.masters[owner] = oid
        for key, (name, direction) in self.voice.VOICES.items():
            owner = 'entity-' + self.voice.GROUP_ENTITIES.get(key, key)
            row = self.entities[owner]; oid = 'material-voice-' + key
            prompt = f'{direction}。这是独立音色试样，不是本剧台词，也不代表作品实际采用。\n试样文字：我把东西放在桌上，等你说完再走。\n单一角色自然普通话，开头结尾各留半秒安静，无伴奏、环境、混响、角色名朗读或字幕提示语。'
            plan = self.plan('audio', prompt, name=name + ' · 音色参考', description=direction)
            purpose = name + '的可复用说话身份；现场对白、呼吸和环境交给镜头原生音频。'
            choice = self.voice_choice(key)
            if choice:
                self.voice_choices[key] = choice
                review = choice['review']
                purpose += '\n当前评估：' + review['reason']
                if review.get('range'):
                    comparing = review['decision'] == 'needs_comparison'
                    use = name + ('：旧原件身份待比较，尚未启用执行' if comparing else '：复用旧原件的说话身份片段；新方案和片段须独立认可')
                    item = self.relation(choice['reference']['object_id'], oid, reference(row), use,
                        review['responsibility'], '不继承：' + '、'.join(review['not_inherited']),
                        '核完整气口、当前声音方向与独立片段认可；不把旧母版认可转授新方案。',
                        sources=row['payload']['sources'], semantics='reuse', type_id='voice-reuse',
                        necessity='optional' if comparing else 'required', upstream_ref=choice['reference'])
                    item.pop('selection_state')
                    item.update(component_id=review['source']['component_id'], range=review['range'])
                    if comparing:
                        item['enabled'] = False
                    plan.update(method='reuse', tool='准确原件复用', model='original-audio', parameters={}, inputs=[item],
                        prompt=f'只复用本方案选定的准确原件片段，锁定{name}的声音身份；起止范围以参考选择为准。\n'
                               + review['reason'] + '\n' + review['responsibility']
                               + '\n不重新生成，不冒充新试读词音轨；旧原件、原词、调用与判断原样保留。',
                        output={'name': name + (' · 待比较身份片段' if comparing else ' · 已有原件身份复用方案'),
                                'description': direction + '\n不继承：' + '、'.join(review['not_inherited']),
                                'review_criteria': AUDIO_CHECK})
                    if comparing:
                        plan['blockers'] = ['先比较当前选角：' + review['reason'] + '；通过后明确启用输入，并独立认可新方案。']
            self.need(oid, reference(row), 'voice-' + key, 'audio', purpose,
                plan, sources=row['payload']['sources'],
                entities=[reference(row)], specification={'voice_reference': True, 'preferred_input_seconds': 4})
            self.voices[key] = oid
        for owner, oid in SONGS.items():
            row = self.p.record(self.store, oid)
            if row['kind'] != 'REQUIREMENT' or row['payload']['media_type'] != 'audio' or not row['payload'].get('generation'):
                raise ValueError('independent song material is not a usable exact source: ' + oid)
            self.keep[oid] = reference(row)
            self.masters[owner] = oid

    def forms(self):
        used = {r['object_id'] for row in self.av if row['kind'] == 'AV_SHOT' for r in row['payload']['states']}
        used.update(ref['state'] for choice in self.input_audit.values() for ref in choice.get('first_frame_states', {}).values())
        for state_id in sorted(used):
            row = self.states[state_id]; payload = row['payload']; media = payload['reference_media']
            owner = payload['entity']['object_id']; entity = self.entities[owner]
            oid = 'material-' + state_id + '-overall'
            decision = self.preparation.get(state_id)
            if media == 'none' or decision and decision['mode'] == '文字检查':
                if decision:
                    try: old = self.p.record(self.store, oid)
                    except KeyError: continue
                    from copy import deepcopy
                    withdrawn = deepcopy(old['payload'])
                    withdrawn.update(status='withdrawn', required=False, withdrawal_reason=decision['purpose'])
                    self.put(oid, 'REQUIREMENT', withdrawn)
                continue
            if payload.get('reference_mode') == 'description' and not decision:
                continue
            kind = entity['payload']['entity_type']
            purpose = decision['purpose'] if decision else payload['title'] + '的整体状态参考，不能用一个局部图声片段冒充完整覆盖。'
            independent = decision and decision['mode'] in ('可选对照', '独立审阅')
            inputs = []
            if owner in self.masters:
                upstream = self.masters[owner]
                inputs.append(self.relation(upstream, oid, reference(row), '固定身份与结构，按此版状态表现差异',
                    TYPE_CHECKS[kind][0], description(payload),
                    '；'.join(TYPE_CHECKS[kind]) + '；图像按最深真实输入核验，当前计划从干净母版一代得到', sources=payload['sources'], type_id='identity-state', semantics='variant'))
            prefix = ('图片1只固定干净母版的身份与结构；' if media == 'image' else '@音频1只锁定已明确的旋律范围，不自动继承独立歌手身份；') if inputs else ''
            prompt = prefix + self.visual_description(row, description(payload))
            if decision and state_id not in self.text_handoffs['visual_descriptions']:
                prompt += '\n本次准备的实际用途与限制：' + purpose
            if media == 'image':
                instruction = {'character': '按实体定义呈现同一人物、动物或可辨群组的全形与本阶段可见细节；不复制成员，不给动物套人类衣饰，不添加别场伤势、湿痕或持物。',
                    'space': '呈现同一空间的固定结构与本阶段布置；不画人物，不镜像，不混入此前或此后的布置。',
                    'prop': '按实体定义呈现同一道具或物件组的全形和指定接触细节；不添加使用者，不提前展示后续缺损或内容。'}[kind]
                prompt = STYLE + '\n' + prompt + '\n' + instruction
            else:
                prompt += '\n这是独立状态声音参考，原生视频负责现场表演；不自动制作每一句对白分轨。只用本状态明确的曲词范围。'
            suffix = ' · 可选对照' if decision and decision['mode'] == '可选对照' else ' · 独立审阅' if independent else ' · 整体参考'
            plan = self.plan(media, prompt, inputs, name=payload['title'] + suffix, description=description(payload),
                             image_ratio='3:4' if kind == 'character' else '16:9')
            plan['output']['review_criteria'] = TYPE_CHECKS[kind] + (IMAGE_CHECK[2:] if media == 'image' else AUDIO_CHECK)
            self.need(oid, reference(row), 'overall', media, purpose, plan,
                sources=payload['sources'], entities=[reference(entity)], states=[reference(row)],
                required=not decision or decision['mode'] != '可选对照', usage='review_reference' if independent else None,
                specification={'reference_role': 'overall', 'planned_i2i_depth': 1 if media == 'image' else None})
            if not independent:
                self.state_needs[state_id] = oid

    def shots(self):
        """Keep each explicitly named plan; purpose edits never recompile it."""
        for row in self.av:
            if row['kind'] != 'AV_SHOT':
                continue
            payload = row['payload']
            if payload.get('reading_contract') != 'audiovisual-three-part-v1':
                raise ValueError('author the three-part reading before material handoff')
            for product in payload['products']:
                need = self.p.ref_record(self.store, product['requirement'], {'REQUIREMENT'})
                if need['payload']['scope']['object_id'] != row['object_id']:
                    raise ValueError('product belongs to another shot')
                self.keep[need['object_id']] = reference(need)

    def build(self):
        self.shots()
        return {'records': [], 'preserve_exact_requirements': list(self.keep.values()),
                'counts': {'preserved_products': len(self.keep)}}

    def existing_voice_targets(self, asset):
        """Match owner and exact requested speaker/direction; never a group alone."""
        ref = asset['payload'].get('production')
        if asset['payload'].get('media_type') != 'audio' or not ref:
            return set()
        try:
            call = self.p.record(self.store, **ref)
        except KeyError:
            return set()
        identity = recorded_voice_identity(asset, call)
        if identity is None:
            return set()
        owners = {r['object_id'] for r in asset['payload'].get('subjects', [])}
        return {target for key, target in self.voices.items()
                if owners == {self.generated[target]['payload']['scope']['object_id']}
                and identity == self.voice.VOICES[key]}
