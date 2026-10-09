"""Compile explicit material routes for the newly authored audiovisual score.

No provider calls, approvals, candidate choices or retrospective call edits.
The four still-useful independent-song materials retain their exact identities.
"""
from collections import Counter
import importlib.util
import hashlib
import json
import re

from audiovisual_design import ROOT, future, reference, union_sources
from video_input_design import load_audit, frame_plan, video_plan, FRAME_USE

STYLE = '二维人物与轻手绘背景，正常人物比例，干净轮廓与清楚色块，背景轻而可读；不新增粗纸纹、颗粒、过锐边缘或写实皮肤。'
IMAGE_CHECK = ['身份、配色、服装与伤侧和准确实体状态一致', '构图、接触点、空间出入口与轴线可核对',
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
    return payload.get('production_description') or '\n'.join(b['text'] for b in payload['blocks'])


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


class Builder:
    def __init__(self, store, p, av_records, reviewed):
        self.store, self.p, self.av = store, p, av_records
        self.reviewed = reviewed
        self.rows, self.generated, self.keep = [], {}, {}
        self.entities = {r['object_id']: r for r in p.current_records(store, {'ENTITY'})}
        self.states = {r['object_id']: r for r in p.current_records(store, {'STATE'})}
        self.image_config = json.loads((ROOT / 'config/openart.json').read_text())
        self.voice = casting()
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
                 necessity='required', group=None, route=None, semantics='reference', type_id='reference', identity=None):
        values = {'title': purpose, 'purpose': purpose, 'upstream': self.resolve(upstream),
            'downstream_id': downstream, 'context': context, 'preserve': preserve, 'change': change, 'check': check,
            'type_id': type_id, 'type_label': {'identity-state': '身份到实体状态', 'space-camera': '空间到机位',
                'frame-video': '起始图到镜头视频', 'reference': '准确素材参考', 'state-frame': '实体状态到首帧',
                'voice-performance': '音色到现场表演', 'state-video': '镜内后续内容到视频'}.get(type_id, type_id),
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
        return {'reference': self.resolve(upstream), 'relation': future(oid), 'selection_state': 'unselected', 'use': purpose}

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

    def need(self, oid, scope, slot, media, purpose, plan, *, sources, entities=(), states=(), required=True, specification=None):
        spec = specification or {}
        if media == 'image':
            spec['native_resolution_policy'] = 'highest_provider_native'
        return self.put(oid, 'REQUIREMENT', {'title': plan['output']['name'], 'scope': scope, 'slot': slot,
            'media_type': media, 'purpose': purpose, 'required': required, 'usage': 'generation_input' if media != 'video' else 'editorial',
            'entities': list(entities), 'states': list(states), 'sources': sources, 'specification': spec, 'generation': plan})

    def roots(self):
        used = {r['object_id'] for row in self.av if row['kind'] == 'AV_SHOT' for r in row['payload']['states']}
        visual_owners = {self.states[oid]['payload']['entity']['object_id'] for oid in used
                         if self.states[oid]['payload']['reference_media'] == 'image'}
        for owner in sorted(visual_owners):
            row = self.entities[owner]; payload = row['payload']; kind = payload['entity_type']
            oid = 'material-' + owner + '-identity'
            composition = {'character': '单一人物等比例正面、侧面、背面并排，手脚完整可见；中性站姿，背景浅灰，无现场伤势或剧情动作。',
                           'space': '空间全景与清楚的出入口、通道和固定结构关系，不画临时人物；先确定左右与尺度，不用镜像变体。',
                           'prop': '单一物件全形与接触结构清楚，保留真实材质与轮廓，中性背景，不加入使用者或现场动作。'}.get(kind, '主体完整入画，身份与结构清楚。')
            description = payload.get('production_description') or '\n'.join(payload['facts'])
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
            self.need(oid, reference(row), 'voice-' + key, 'audio', name + '的可复用说话身份；现场对白、呼吸和环境交给镜头原生音频。',
                self.plan('audio', prompt, name=name + ' · 音色参考', description=direction), sources=row['payload']['sources'],
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
        for state_id in sorted(used):
            row = self.states[state_id]; payload = row['payload']; media = payload['reference_media']
            if media == 'none' or payload.get('reference_mode') == 'description':
                continue
            owner = payload['entity']['object_id']; entity = self.entities[owner]
            oid = 'material-' + state_id + '-overall'
            purpose = payload['title'] + '的整体状态参考，不能用一个局部图声片段冒充完整覆盖。'
            inputs = []
            if owner in self.masters:
                upstream = self.masters[owner]
                inputs.append(self.relation(upstream, oid, reference(row), '固定身份与结构，按此版状态表现差异',
                    '保持同一主体的比例、轮廓、配色和空间拓扑或曲调', description(payload),
                    '逐项核对完整状态各维度；参考是干净母版，最深图像代数不超过一代', sources=payload['sources'], type_id='identity-state', semantics='variant'))
            prefix = ('图片1只固定干净母版的身份与结构；' if media == 'image' else '@音频1只锁定已明确的旋律范围，不自动继承独立歌手身份；') if inputs else ''
            prompt = prefix + description(payload)
            if media == 'image':
                prompt = STYLE + '\n' + prompt + '\n清楚呈现本状态的全形与指定细节，不添加别场才有的伤、湿痕、持物。中性背景或已说明的空间，全体轮廓完整。'
            else:
                prompt += '\n这是独立状态声音参考，原生视频负责现场表演；不自动制作每一句对白分轨。只用本状态明确的曲词范围。'
            self.need(oid, reference(row), 'overall', media, purpose,
                self.plan(media, prompt, inputs, name=payload['title'] + ' · 整体参考', description=description(payload),
                          image_ratio='3:4' if entity['payload']['entity_type'] == 'character' else '16:9'),
                sources=payload['sources'], entities=[reference(entity)], states=[reference(row)],
                specification={'reference_role': 'overall', 'planned_i2i_depth': 1 if media == 'image' else None})
            self.state_needs[state_id] = oid

    def shots(self):
        for row in self.av:
            if row['kind'] != 'AV_SHOT':
                continue
            payload, shot_id = row['payload'], row['object_id']
            states = [self.states[r['object_id']] for r in payload['states']]
            owners = {r['object_id']: self.entities[r['object_id']] for r in payload['entities']}
            spaces = [r for r in owners.values() if r['payload']['entity_type'] == 'space']
            source = payload['sources']; scope = future(shot_id)
            camera_ids = []
            # The alternate camera is useful where the enclosing stone passage
            # makes a reversed view especially easy to misunderstand.
            alternate = any(s['scene_id'] in ('s018', 's023', 's029', 's030', 's031', 's032', 's033') for s in source)
            for view in ('main', 'reverse') if alternate else ('main',):
                oid = 'material-' + shot_id + '-camera-' + view
                purpose = ('主机位' if view == 'main' else '同侧备用观察机位') + '确认本镜空间方向和可拍范围。'
                inputs = [self.relation(self.masters[s['object_id']], oid, scope, '沿准确空间母版确定本镜机位，固定出入口与尺度',
                    '空间拓扑、固定结构、北南东西及真实距离', '只改变相机位置、景别和本场光线，不左右镜像空间',
                    payload['axis'] + '；以人物可站位置和通道尺度核对', sources=source, type_id='space-camera', semantics='variant') for s in spaces]
                labels = '\n'.join(f'图片{i}固定空间：{s["payload"]["title"]}。' for i, s in enumerate(spaces, 1))
                choice = payload['framing'] if view == 'main' else '在已定轴线同侧改为略偏侧的观察视点，保留相同左右，不跨轴、不镜像；供明确改选路线时比较。'
                prompt = f'{STYLE}\n{labels}\n空间：{payload["spatial"]}\n轴线：{payload["axis"]}\n机位：{choice}\n光线：{payload["lighting"]}\n色彩：{payload["color"]}\n只出环境和固定器物的机位参考，不放人物、不生成未来动作或文字标记。'
                self.need(oid, scope, 'camera-' + view, 'image', purpose,
                    self.plan('image', prompt, inputs, name=payload['title'] + ' · ' + ('主机位' if view == 'main' else '侧机位'), description=purpose),
                    sources=source, entities=[reference(s) for s in spaces], required=view == 'main',
                    specification={'planned_i2i_depth': 1, 'camera_route': view})
                camera_ids.append(oid)
            oid = 'material-' + shot_id + '-first-frame'
            inputs = []
            for camera, route in zip(camera_ids, ('main', 'reverse')):
                inputs.append(self.relation(camera, oid, scope, '选择此镜机位作为首帧构图依据',
                    '轴线、出入口、固定物距离与镜头景别', '按动作起点加入准确人物和道具，不照搬空景为成片',
                    payload['action_start'], sources=source, necessity='one_of', group='camera', route=route))
            start_states = {}
            for state in states:
                start_states.setdefault(state['payload']['entity']['object_id'], state)
            visible = [s for s in start_states.values() if s['payload']['reference_media'] == 'image' and
                       self.entities[s['payload']['entity']['object_id']]['payload']['entity_type'] != 'space']
            if shot_id in self.frame_subjects:
                wanted = self.frame_subjects[shot_id]
                if wanted - {s['payload']['entity']['object_id'] for s in visible}:
                    raise ValueError('first-frame choice lacks an applicable state: ' + shot_id + ' ' + str(wanted - {s['payload']['entity']['object_id'] for s in visible}))
                visible = [s for s in visible if s['payload']['entity']['object_id'] in wanted]
            if len(visible) + 1 > 16:
                raise ValueError('first frame exceeds OpenArt input limit; author a narrower shot or route: ' + shot_id)
            for state in visible:
                inputs.append(self.relation(self.state_needs[state['object_id']], oid, scope, '首帧使用：' + state['payload']['title'],
                    '人物或道具身份、完整状态、伤侧和比例', '只调整本镜站位、手位、朝向与构图',
                    payload['continuity'], sources=source, type_id='state-frame'))
            labels = '图片1为选定机位；' + ''.join(f'图片{i}为{s["payload"]["title"]}；' for i, s in enumerate(visible, 2))
            prompt = f'{STYLE}\n{labels}\n准确状态参考只固定可见主体的轮廓、衣着、伤侧、材质与结构；其制作说明中的其他使用场合和动作不在本首帧重演。\n拍摄位置：{payload["framing"]}。{payload["axis"]}\n只画动作开始的瞬间：{payload["action_start"]}。参考只约束真正入画的主体，镜内后续才入画的人物和画外声不提前塞入首帧。\n场所：{payload["spatial"]}\n{payload["lighting"]}。{payload["color"]}\n镜尾将发生“{payload["action_end"]}”，此首帧不得提前表现完成结果。\n连续性：{payload["continuity"]}。不加字幕、水印和装饰边框。'
            self.need(oid, scope, 'first-frame', 'image', '固定本镜动作起点、人物身份、手位和机位，供视频原生表演延续。',
                frame_plan(self.plan('image', prompt, inputs, name=payload['title'] + ' · 首帧', description=payload['action_start'], selected_routes={'camera': 'main'}), self.input_audit[shot_id]),
                sources=source, entities=[s['payload']['entity'] for s in visible], states=[reference(s) for s in visible],
                specification={'planned_i2i_depth': 2, 'first_frame': True})
            frame_id = oid
            oid = 'material-' + shot_id + '-video'
            inputs = [self.relation(frame_id, oid, scope, FRAME_USE,
                payload['action_start'] + '；固定主体与空间', '原生生成下述连续动作、对白、呼吸、环境与表演',
                '普通参考不保证固定首帧；' + payload['action_end'] + '；' + payload['continuity'], sources=source, type_id='frame-video')]
            events = self.reviewed.for_sources(source)
            speakers = list(dict.fromkeys(e['speaker'] for e in events if e['speaker'] in self.voice.VOICES))
            audio_labels = []
            for key in speakers:
                inputs.append(self.relation(self.voices[key], oid, scope, self.voice.VOICES[key][0] + '：只锁定说话身份的干净短参考',
                    '同一人物的音区、共鸣与咬字', '按本镜正文和身体状态重新表演，不照搬试样文字或静音口型',
                    '明确选取约2至4秒可辨音色片段，所有音频参考总长在模型上限内', sources=source, type_id='voice-performance'))
                audio_labels.append('@音频' + str(len(audio_labels) + 1) + '只参考' + self.voice.VOICES[key][0] + '的音色。')
            song_owners = list(dict.fromkeys(e['song'] for e in events if e.get('song')))
            for owner in song_owners:
                inputs.append(self.relation(SONGS[owner], oid, scope, '曲调短参考：' + self.entities[owner]['payload']['title'],
                    '已明确曲调的旋律轮廓和节拍', '角色自己唱本镜输入锁规定词句；不加入独立整曲的额外歌词，不继承独立歌手音色',
                    '听审后准确选择对应乐句2至8秒；缺词状态必须真的停，不用母版补唱', sources=source))
                audio_labels.append('@音频' + str(len(audio_labels) + 1) + '只参考' + self.entities[owner]['payload']['title'] + '的指定曲调片段。')
            seconds = payload['duration_frames'] // payload['fps']
            maximum = 3 if seconds <= 15 else 10
            if len(audio_labels) > maximum:
                raise ValueError('too many voice references for authored duration; revise route explicitly: ' + shot_id)
            prompt = f'{STYLE}\n{seconds}秒，16:9，720p。@图片1为起始构图参考，维持已可见身份、空间和手位；' + ''.join(audio_labels)
            prompt += f'\n意图与表演：{payload["performance"]}\n镜头：{payload["framing"]}。轴线：{payload["axis"]}\n从{payload["action_start"]}开始，到{payload["action_end"]}结束。\n{payload["spatial"]}\n光色：{payload["lighting"]}；{payload["color"]}\n声音和剪接：' + '\n'.join(payload['sound'][:2])
            prompt += '\n本镜准确动作与发声执行顺序（叙述转成动作，发声事件实际出声；不朗读叙述、角色名或制作说明）：\n' + self.reviewed.render(source)
            prompt += '\n连续性：' + payload['continuity'] + '\n不添加对白、旁白、抢先信息、炫技切镜或慢动作。没有画外声的台词由实际说话人同步说出；保留自然气口和动作停顿。'
            def supplement(value):
                state = self.states[value['state']]
                return self.relation(self.state_needs[value['state']], oid, scope, value['use'],
                    state['payload']['title'] + '的身份与完整状态；只取本镜需要显露的部分',
                    '按本镜时间顺序入画，不提前露脸、改站位或提前展示状态变化结果',
                    value['use'] + '；只选本直接参考的准确候选，不自动附带祖先', sources=source,
                    type_id='state-video', identity='mr-video-input-' + shot_id + '-' + value['state'])
            def media_type(item):
                key = item['reference']['object_id']
                return (self.generated[key] if key in self.generated else self.p.record(self.store, key))['payload']['media_type']
            plan = self.plan('video', prompt, inputs, seconds=seconds, name=payload['title'] + ' · 视频',
                description=payload['action_start'] + ' → ' + payload['action_end'])
            plan['blockers'] = self.reviewed.blockers(source)
            planned = video_plan(plan, self.input_audit[shot_id], supplement, media_type)
            self.need(oid, scope, 'video', 'video', '原生音画完成这一镜；图像候选不计为视频结果。',
                planned,
                sources=source, entities=payload['entities'], states=payload['states'], specification={'resolution': '720p', 'aspect_ratio': '16:9'})

    def build(self):
        self.roots(); self.forms(); self.shots()
        # Exact existing candidates are reviewable alternatives. This declares
        # their purpose without adopting them or attaching them to a new call.
        for asset in self.p.current_records(self.store, {'ASSET'}):
            targets = set()
            voice_targets = self.existing_voice_targets(asset)
            targets.update(voice_targets)
            for state in asset['payload'].get('states', []):
                target = self.state_needs.get(state['object_id'])
                if target and self.states[state['object_id']]['id'] == state['revision_id']:
                    targets.add(target)
            for entity in asset['payload'].get('subjects', []):
                target = self.masters.get(entity['object_id'])
                if target in self.generated:
                    targets.add(target)
            for target in sorted(targets):
                need = self.generated[target]['payload']
                if need['media_type'] != asset['payload']['media_type']: continue
                if target in voice_targets:
                    self.relation(asset['object_id'], target, need['scope'], '已有音色候选，待听审与用途比较',
                        '准确旧原件、真实调用与原说话身份；历史母版认可只限旧原件',
                        '只取声音身份，现场重新表演本镜正文；不继承旧试读台词、语气、呼吸或环境，也不冒充新试样的生成结果',
                        '逐项实际听辨说话者、音区音色、字音、噪声伴奏与表达；明确原件组成和起止范围，按具体镜头渠道核时长；未听审或未选段保持待准备',
                        sources=need['sources'], necessity='optional', semantics='alternative', type_id='existing-candidate')
                    continue
                self.relation(asset['object_id'], target, need['scope'], '已有候选可供本需求比较和复用选择',
                    '原件身份、真实调用及已知身份或状态依据；不把旧认可迁到新方案',
                    '本次未选择候选；先核当前完整状态、风格、原生规格与图像谱系，再明确改选输入路线',
                    '打开本候选原件逐项审阅；资料缺失继续标为未知，不用新方案补造生成来历',
                    sources=need['sources'], necessity='optional', semantics='alternative', type_id='existing-candidate')
        return {'records': self.rows, 'preserve_exact_requirements': list(self.keep.values()), 'counts': dict(self.counts)}

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
