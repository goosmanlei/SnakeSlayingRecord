#!/usr/bin/env python3
"""Rebuild reviewed shot inputs in an isolated instance, without media execution.

The authored per-shot reviews are mandatory inputs. This compiler does not infer
cast from names, copy a scene's cast into a shot, or select candidate media.
"""
import argparse
import copy
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'production/breakdown-shot-v2'
STYLE = '二维人物与轻手绘背景；轮廓清楚、平涂大色块、正常身体比例，背景薄而干净。不加纸纹、噪点、摄影皮肤和密集织物纹理。'
IMAGE_PARAMS = {'aspectRatio': '16:9', 'quality': 'high', 'resolutionTier': '4k',
                'outputFormat': 'png', 'imageCount': 1, 'autoEnhancePrompt': False}


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def ref(row):
    return {'object_id': row['object_id'], 'revision_id': row['id']}


def distinct(values):
    return list(dict.fromkeys(values))


def description(state):
    return '\n'.join(distinct(str(v) for v in state['dimensions'].values()))


def recipe(model, parameters, prompt, inputs, name, blockers=()):
    return {'format': 'generation-plan-v1', 'method': 'generate', 'model': model,
            'parameters': parameters, 'prompt': prompt, 'inputs': inputs,
            'randomization': {'mode': 'random'}, 'blockers': list(blockers),
            'output': {'name': name, 'description': '待制作与审阅的' + name,
                       'review_criteria': ['准确身份、完整状态及动作起止与锁定剧本一致',
                                           '对白歌词逐字核对；未写声音不扩写台词',
                                           '保存真实调用和原件；未选候选不得执行']}}


class Builder:
    def __init__(self, store, production):
        self.store, self.p = store, production
        self.heads = {r['object_id']: r for r in production.current_records(store)}
        self.before = copy.deepcopy(self.heads)
        self.records, self.guards, self.audits = [], {}, []
        self.baseline = read(DATA / 'baseline.json')
        self.reviews = {}
        for path in sorted(DATA.glob('review-e*.json')):
            value = read(path)
            for item in value.get('shots', value.get('items', [])):
                oid = item['shot']['object_id']
                if oid in self.reviews:
                    raise ValueError('duplicate authored review: ' + oid)
                self.reviews[oid] = item
        if set(self.reviews) != {r['shot']['object_id'] for r in self.baseline['plans']}:
            raise ValueError('authored reviews do not cover every locked current plan')
        self.issues = read(DATA / 'semantic-issues.json')
        if any(r['status'] != 'resolved-authorized-erratum' for r in self.issues['issues']):
            raise ValueError('unresolved semantic decision')
        self.corrected = set()

    def get(self, oid):
        return self.heads[oid]

    def add(self, oid, kind, payload):
        old = self.before.get(oid)
        if old:
            self.guards[oid] = old['id']
        if oid in {r['object_id'] for r in self.records}:
            raise ValueError('duplicate planned mutation: ' + oid)
        row = {'object_id': oid, 'kind': kind, 'payload': payload,
               'expected_version': old['version'] if old else 0}
        self.records.append(row)
        self.heads[oid] = {**row, 'id': '@' + oid}
        return self.heads[oid]

    def need(self, oid, title, scope, slot, media, purpose, plan, states=()):
        old = self.before.get(oid)
        if slot in ('composition', 'sound-reference', 'shot-video'):
            prior = old['payload'].get('generation', {}).get('inputs', []) if old else []
            for entry in plan['inputs']:
                exact = next((v for v in prior if v['reference'] == entry['reference']), None)
                if exact:
                    for key in ('material_selection', 'selection_state', 'component_id', 'crop', 'range'):
                        if key in exact:entry[key] = copy.deepcopy(exact[key])
                else:
                    previous = next((v for v in prior if v['reference']['object_id'] == entry['reference']['object_id']), None)
                    retained = None
                    if previous and self.before.get(entry['reference']['object_id'], {}).get('kind') == 'REQUIREMENT':
                        pairs = self.store.db.execute('''SELECT m.number,v.frozen FROM material_plan_members m
                            JOIN material_plan_versions v ON v.material_id=m.material_id AND v.number=m.number
                            WHERE m.material_id=? AND m.revision_id=?''',
                            (entry['reference']['object_id'], previous['reference']['revision_id'])).fetchall()
                        if len(pairs) == 1 and not pairs[0]['frozen'] and previous.get('selection_state') != 'unselected':
                            retained = {'material_id': entry['reference']['object_id'], 'number': pairs[0]['number']}
                    if retained:
                        entry['material_selection'] = retained
                        continue
                    # A need identifies the material to browse. It does not
                    # automatically select its latest production version.
                    entry['selection_state'] = 'unselected'
        value = copy.deepcopy(old['payload']) if old else {'format': 'production-requirement-v1'}
        value.update(title=title, scope=scope, slot=slot, media_type=media, purpose=purpose,
                     required=True, usage='generation_input', states=[ref(self.get(s)) for s in states],
                     entities=list({self.get(s)['payload']['entity']['object_id']: self.get(s)['payload']['entity']
                                    for s in states}.values()), generation=plan)
        value.setdefault('specification', {})
        value['blocks'] = [{'id': 'purpose', 'text': purpose}]
        value.pop('status', None)
        return self.add(oid, 'REQUIREMENT', value)

    def source(self, scene_id, numbers):
        value = self.get('preparation-' + scene_id)['payload']['source']
        ids = [b for b in value['block_ids'] if int(b.rsplit('-b', 1)[1]) in numbers]
        if len(ids) != len(numbers):
            raise ValueError('state evidence outside locked scene')
        return {**value, 'block_ids': ids}

    def states(self):
        changes = read(DATA / 'state-corrections.json')
        for item in [*changes['states'], *changes['revisions']]:
            oid = item['object_id']
            base = self.get(item.get('base', oid))
            value = copy.deepcopy(base['payload'])
            value['title'] = item.get('title', value['title'])
            value['dimensions'].update(item['dimensions'])
            value['production_description'] = description(value)
            value['blocks'] = [{'id': 'description', 'text': value['production_description']}]
            if item.get('source'):
                value['sources'] = [self.source(item['source']['scene_id'], item['source']['blocks'])]
                value['facts'] = [f['text'] for s in self.before.values() if s['kind'] == 'SHOT_DESIGN'
                                  for f in s['payload'].get('facts', [])
                                  if f['source']['block_ids'][0] in value['sources'][0]['block_ids']]
                value['facts'] = distinct(value['facts'])
            value['choices'] = [*value.get('choices', []), item['reason']]
            self.add(oid, 'STATE', value)
            self.corrected.add(oid)

    def state_need(self, state_id, media):
        state = self.get(state_id)
        if state['payload'].get('reference_mode') == 'description':
            return None
        candidates = [r for r in self.heads.values() if r['kind'] == 'REQUIREMENT'
                      and r['payload'].get('status') != 'withdrawn'
                      and r['payload']['scope']['object_id'] == state_id
                      and r['payload']['media_type'] == media]
        overall = media == state['payload']['reference_media']
        slot = 'overall' if overall else 'voice'
        candidates = [r for r in candidates if r['payload']['slot'] == slot]
        if len(candidates) > 1:
            raise ValueError('ambiguous exact state need: ' + state_id + '/' + media)
        if candidates and candidates[0]['payload']['scope'] == ref(state):
            return candidates[0]
        oid = candidates[0]['object_id'] if candidates else 'need-' + state_id + '-' + slot
        if any(r['object_id'] == oid for r in self.records):
            return self.get(oid)
        # An unselected demand may be added; it does not certify a candidate or
        # copy a different state's adoption. Existing exact identity masters are
        # retained only when the old demand explicitly named those inputs.
        old = candidates[0] if candidates else None
        if old and media == 'audio' and 'voice' in state['payload']['dimensions']:
            old_state = self.p.ref_record(self.store, old['payload']['scope'])
            if old_state['payload']['dimensions'].get('voice') == state['payload']['dimensions']['voice']:
                # A visual correction (keys, apron, injury depiction) is not a
                # new voice. Keep the exact shared audio recipe and identity;
                # only its complete-state association moves to the corrected
                # revision. Existing calls, choices and aliases stay traceable.
                value = copy.deepcopy(old['payload'])
                value['scope'] = ref(state)
                value['states'] = [ref(state) if s['object_id'] == state_id else s for s in value['states']]
                return self.add(oid, 'REQUIREMENT', value)
        inputs = copy.deepcopy(old['payload'].get('generation', {}).get('inputs', [])) if old else []
        if not old:
            spec = next((v for v in read(DATA / 'state-corrections.json')['states']
                         if v['object_id'] == state_id), None)
            if spec:
                identity_state = spec.get('identity_from', spec['base'])
                base_needs = [r for r in self.before.values() if r['kind'] == 'REQUIREMENT'
                              and r['payload']['scope']['object_id'] == identity_state
                              and r['payload']['media_type'] == media and r['payload']['slot'] == slot]
                if len(base_needs) != 1:
                    raise ValueError('missing exact identity demand: ' + state_id + '/' + media)
                inputs = [{'reference': ref(base_needs[0]), 'selection_state': 'unselected',
                           'use': spec['identity_input_rule']}]
        title = state['payload']['title'] + (' · 整体参考' if overall else ' · 声音身份参考')
        prompt = (STYLE + '\n' if media == 'image' else '准确声音身份参考，不编写新台词。\n')
        prompt += '完整状态：' + state['payload']['title'] + '\n' + description(state['payload'])
        prompt += '\n'.join('\n' + ('图片' if media == 'image' else '@音频') + str(i + 1) + '：' + v['use']
                            for i, v in enumerate(inputs))
        prompt += '\n本需求未生成、未选候选。文字仅使用准确剧本原句；具体选段、原件与谱系须在执行前核对。'
        params = copy.deepcopy(old['payload'].get('generation', {}).get('parameters', {})) if old else {}
        if media == 'image':
            params = params or copy.deepcopy(IMAGE_PARAMS)
        plan = recipe('gpt-image-2-5-sunburst' if media == 'image' else '待选定声音制作渠道', params,
                      prompt, inputs, title, ['必要状态需求待制作和审阅，不自动使用旧状态候选'])
        result = self.need(oid, title, ref(state), slot, media, '按本轮完整状态提供准确' + media + '参考', plan, [state_id])
        result['payload']['specification']['reference_role'] = 'overall' if overall else 'detail'
        return result

    def image_sequence(self, shot, review):
        ids = [r['object_id'] for r in shot['states'] if r['object_id'] not in review['image_remove']]
        ids += review['image_add']
        ids = [s for s in ids if self.get(s)['payload']['reference_media'] == 'image']
        if review.get('image_order'):
            if sorted(ids) != sorted(review['image_order']):
                raise ValueError('authored order must cover the same reviewed states')
            ids = review['image_order']
        return ids

    def build_shot(self, review):
        oid = review['shot']['object_id']
        original = self.before[oid]
        if ref(original) != review['shot']:
            raise ValueError('review input moved: ' + oid)
        value = copy.deepcopy(original['payload'])
        for issue in self.issues['issues']:
            if issue['shot'] != oid:
                continue
            field = issue['field']
            if field == 'review_note':
                if issue['proposed'] not in review['review_note'] or issue['current'] in review['review_note']:
                    raise ValueError('authored review erratum differs: ' + issue['id'])
                continue
            owner = value
            parts = field.split('.')
            for part in parts[:-1]:
                owner = owner[int(part)] if isinstance(owner, list) else owner[part]
            key = int(parts[-1]) if isinstance(owner, list) else parts[-1]
            if owner[key].count(issue['current']) != 1:
                raise ValueError('erratum precondition differs: ' + issue['id'])
            owner[key] = owner[key].replace(issue['current'], issue['proposed'])
            # Spatial text sometimes embeds the exact framing; keep them in sync.
            if field == 'framing' and issue['current'] in value['spatial']:
                value['spatial'] = value['spatial'].replace(issue['current'], issue['proposed'])
        for fix in self.issues['sound_classification_corrections']:
            if fix['shot'] == oid:
                unit = value['sound'][fix['index']]
                if unit['type'] != fix['from']:
                    raise ValueError('sound classification precondition differs')
                unit['type'] = fix['to']
                unit['description'] = unit.pop('speaker') + '：' + unit.pop('text')
        images = self.image_sequence(value, review)
        voice_ids = distinct(review['voice_states'])
        # Presentation states are distinct from mere mentions. Voice-only
        # entities remain present in the shot graph, without gaining an image.
        states = images + [s for s in voice_ids if s not in images]
        groups = defaultdict(list)
        for s in states:
            groups[self.get(s)['payload']['entity']['object_id']].append(s)
        transitions = []
        for entity, sequence in groups.items():
            for a, b in zip(sequence, sequence[1:]):
                if a == b:
                    raise ValueError('redundant consecutive state: ' + oid + '/' + a)
                transitions.append({'from': ref(self.get(a)), 'to': ref(self.get(b)),
                                    'action': value.get('motion', value['action_end']), 'source': value['source']})
        value.update(states=[ref(self.get(s)) for s in states],
                     entities=[self.get(seq[0])['payload']['entity'] for seq in groups.values()],
                     state_transitions=transitions)
        occurrences = []
        for entity, sequence in groups.items():
            visual = any(s in images for s in sequence)
            voice = any(s in voice_ids for s in sequence)
            occurrences.append({'entity': self.get(sequence[0])['payload']['entity'],
                                'mode': 'visual_voice' if visual and voice else 'visual' if visual else 'voice',
                                'states': [ref(self.get(s)) for s in sequence], 'evidence': [value['source']],
                                'transitions': [t for t in transitions if t['from']['object_id'] in sequence]})
        occurrences += [o for o in original['payload'].get('occurrences', [])
                        if o['mode'] == 'mention' and o['entity']['object_id'] not in groups]
        value['occurrences'] = occurrences
        value['reference_review'] = {'format': 'shot-reference-review-v1', 'basis': value['source'],
                                     'note': review['review_note'], 'image_states': [ref(self.get(s)) for s in images],
                                     'voice_states': [ref(self.get(s)) for s in voice_ids]}
        shot = self.add(oid, 'SHOT_DESIGN', value)
        image_groups = defaultdict(list)
        for state in images:
            image_groups[self.get(state)['payload']['entity']['object_id']].append(state)
        initial = [seq[0] for seq in image_groups.values()]
        image_needs = {s: self.state_need(s, 'image') for s in distinct(images)}
        if any(r is None for r in image_needs.values()):
            raise ValueError('image-only description needs explicit handling')
        # Reviewed characters and props constrain the motion itself, including
        # arrivals, handoffs and changes after the first frame. Environment
        # starts travel through the keyframe; later environment states get real
        # additional inputs. No label claims an invisible prop was transferred
        # through a starting image in which it cannot yet appear.
        direct = [s for s in distinct(images) if self.get(self.get(s)['payload']['entity']['object_id'])['payload']['entity_type'] in ('character', 'prop')
                  or s not in initial]
        # New props which enter after the initial view must also be represented
        # in actual video inputs, not claimed to be visible in the keyframe.
        late = review.get('keyframe_exclude', [])
        for s in late:
            if s not in images:
                raise ValueError('late prop is not reviewed in this shot: ' + oid + '/' + s)
        direct = distinct([*direct, *late])
        comp_ids = [s for s in initial if s not in late]
        if len(comp_ids) > 16:
            raise ValueError('keyframe reference limit; author a safe grouping: ' + oid)
        comp_inputs = [{'reference': ref(image_needs[s]), 'use': self.get(s)['payload']['title'] + '；只约束本镜起点实际可见部分，入画时点按准确动作'} for s in comp_ids]
        comp_prompt = STYLE + '\n' + value['framing'] + '\n空间：' + value['spatial'] + '\n起点：' + value['action_start']
        comp_prompt += '\n完整动作供判断前后时点，不把后发生状态画到第一帧：' + value.get('motion', value['action_end'])
        comp_prompt += '\n承接：' + value['continuity'] + '\n本镜核对：' + review['review_note']
        comp_prompt += '\n仅起始关键画面，未入画的人物、道具不提前出现，未完成动作不提前完成；可读文字后期准确排版。'
        comp_prompt += '\n' + '\n'.join('图片' + str(i + 1) + '：' + entry['use'] for i, entry in enumerate(comp_inputs))
        comp_id = 'need-' + oid + '-composition'
        comp = self.need(comp_id, value['title'] + ' · 构图／关键画面', ref(shot), 'composition', 'image',
                         '准确起点构图；仅输入本镜所需身份与起始完整状态',
                         recipe('gpt-image-2-5-sunburst', copy.deepcopy(IMAGE_PARAMS), comp_prompt, comp_inputs,
                                '镜头关键画面', ['需选定准确原件，核对起点可见范围和图生图最深谱系不超过两代']), comp_ids)
        # Each audio input is justified by an authored audible role, not by the
        # whole visible cast. Description-only performances remain descriptions.
        audio_needs = {s: self.state_need(s, 'audio') for s in voice_ids}
        audio_material = [s for s in voice_ids if audio_needs[s] is not None]
        audio_described = [s for s in voice_ids if audio_needs[s] is None]
        speech = '\n'.join(u.get('speaker', '') + ('（唱）' if u['type'] == 'singing' else '') + '：' + u['text']
                           for u in value['sound'] if u['type'] in ('dialogue', 'singing'))
        facts = '\n'.join(f['text'] for f in value['facts'])
        sound_prompt = '本镜准确声音选段方案；叙述不是旁白，不新增台词歌词。\n逐字对白／唱词：\n' + (speech or '没有逐字台词；按下列原文中的自然声与动作时点。')
        sound_prompt += '\n准确正文：\n' + facts + '\n本镜核对：' + review['review_note']
        sound_prompt += '\n' + '\n'.join(self.get(s)['payload']['title'] + '：' + description(self.get(s)['payload']) for s in audio_described)
        sound_inputs = [{'reference': ref(audio_needs[s]), 'use': self.get(s)['payload']['title'] + '；仅本镜实际发声者，歌词范围依正文，不照搬音色试读内容'} for s in audio_material]
        sound_prompt += '\n' + '\n'.join('声音参考' + str(i + 1) + '：' + inp['use'] for i, inp in enumerate(sound_inputs))
        sound_id = 'need-' + oid + '-sound-reference'
        old_video = self.before['need-' + oid + '-video']['payload']
        old_gen = old_video['generation']
        duration = old_gen['parameters']['duration']
        fast = duration <= 15 and 1 + len(direct) <= 9
        model = 'seedance2.0_fast_vision' if fast else 'Seedance_2.5'
        sound = self.need(sound_id, value['title'] + ' · 声音参考选段', ref(shot), 'sound-reference', 'audio',
                          '本镜发声身份、准确台词歌词和动作声；不因人物在画内而添加音色',
                          recipe('待选定声音制作渠道', {'sample_rate': 48000, 'reference_max_seconds': 15 if fast else 30},
                                 sound_prompt, sound_inputs, '声音参考选段',
                                 ['渠道、真实原件和准确选段待听审；描述不是实际声音产物']), voice_ids)
        inputs = [{'reference': ref(comp), 'use': '准确起始构图与空间'}]
        inputs += [{'reference': ref(image_needs[s]), 'use': self.get(s)['payload']['title'] + '；持续身份或动作后状态，出现时点依正文'} for s in direct]
        inputs.append({'reference': ref(sound), 'use': '本镜准确声音选段；校验时长、发声身份和台词歌词'})
        audio_index = len(inputs) - 1
        links = []
        for s in distinct(images):
            path = [1 + direct.index(s)] if s in direct else [0, comp_ids.index(s)]
            links.append({'key': 'image-' + s, 'label': self.get(s)['payload']['title'], 'path': path,
                          'material_id': image_needs[s]['object_id'], 'state': ref(self.get(s)),
                          'entity': self.get(s)['payload']['entity'],
                          'purpose': ('直接约束运动中的身份或状态' if s in direct else '经本镜关键画面传递起始状态')})
        for s in audio_material:
            links.append({'key': 'audio-' + s, 'label': self.get(s)['payload']['title'] + ' · 声音',
                          'path': [audio_index, audio_material.index(s)], 'material_id': audio_needs[s]['object_id'],
                          'state': ref(self.get(s)), 'entity': self.get(s)['payload']['entity'],
                          'purpose': '经本镜声音选段传递发声身份；不独立增加视频音频输入'})
        for s in audio_described:
            links.append({'key': 'performance-' + s, 'label': self.get(s)['payload']['title'], 'path': [audio_index],
                          'material_id': sound_id, 'state': ref(self.get(s)), 'entity': self.get(s)['payload']['entity'],
                          'purpose': '本镜声音选段的表演范围说明，不另造歌曲候选或模型输入'})
        prompt = STYLE + '\n@图片1 约束起始构图与空间；@音频1 约束准确声音身份、选段与时点，不复述试读内容。'
        number = self.store.db.execute("SELECT number FROM business_codes WHERE object_id=? AND prefix='SH'", (oid,)).fetchone()
        if not number:
            raise ValueError('missing global shot identity: ' + oid)
        shot_label = 'SH' + str(number[0]).zfill(3) + ' · ' + re.sub(r'^E\d+-\d+\s*', '', value['title'])
        prompt += '\n' + shot_label + '。叙事目的：' + value['purpose']
        prompt += '\n构图：' + value['framing'] + '\n空间：' + value['spatial']
        prompt += '\n动作：' + value.get('motion', value['action_start'] + ' → ' + value['action_end'])
        prompt += '\n开始：' + value['action_start'] + '\n结束：' + value['action_end'] + '\n连续性：' + value['continuity']
        prompt += '\n逐字对白／演唱：\n' + (speech or '本镜没有逐字对白或歌词，原文自然发声见下。')
        prompt += '\n锁定正文（动作叙述不是旁白；未写的台词歌词不得补写）：\n' + facts
        prompt += '\n声音设计：' + '；'.join(u.get('description', '') for u in value['sound'] if u['type'] == 'environment_and_action')
        prompt += '\n逐镜核对与时序约束：' + review['review_note']
        prompt += '\n实际新增图片输入：\n' + '\n'.join('@图片' + str(i + 2) + '：' + self.get(s)['payload']['title']
                                                        for i, s in enumerate(direct))
        prompt += '\n完整状态顺序（同一实体依动作先后，不同时复制为多人或多件）：\n'
        prompt += '\n'.join(' → '.join(self.get(s)['payload']['title'] for s in seq) for seq in image_groups.values())
        spans = []
        prompt += '\n素材约束：\n'
        for link in links:
            text = link['label']
            start = len(prompt)
            prompt += text
            spans.append({'start': start, 'end': len(prompt), 'quote': text, 'reference_key': link['key']})
            prompt += '：' + link['purpose'] + '。\n'
        prompt += '构图之外的人物不因参考而出现；入画和离场依准确动作。纸上文字用后期准确排版。'
        if len(prompt) > 5000:
            fast = False
            model = 'Seedance_2.5'
            sound['payload']['generation']['parameters']['reference_max_seconds'] = 30
        if len(prompt) > (5000 if fast else 15000) or len(direct) + 1 > (9 if fast else 30):
            raise ValueError('video input or prompt contract exceeded: ' + oid)
        gen = recipe(model, {**old_gen['parameters'], 'duration': duration}, prompt, inputs, '镜头有声视频候选',
                     ['准确关键画面、声音选段及直接状态参考尚待明确选定；本任务不生成或采纳素材'])
        if old_gen.get('takes'):
            gen['takes'] = copy.deepcopy(old_gen['takes'])
        gen.update(reference_links=links, prompt_links=spans)
        video = self.need('need-' + oid + '-video', old_video['title'], ref(shot), 'shot-video', 'video', old_video['purpose'], gen, distinct(states))
        video['payload']['specification'] = copy.deepcopy(old_video['specification'])
        # Historical applicability stays on its old exact shot revision. The
        # new graph has only reviewed image/audio requirements for this shot.
        for link in links:
            rid = 'shot-ref-' + oid + '-' + hashlib.sha256(link['key'].encode()).hexdigest()[:12]
            self.add(rid, 'RELATION', {'format': 'production-relation-v1', 'title': value['title'] + ' · ' + link['label'],
                                      'blocks': [{'id': 'reason', 'text': review['review_note']}],
                                      'relation_type': 'applicability', 'subject': ref(self.get(link['material_id'])),
                                      'scope': ref(shot), 'basis': 'production_choice', 'reason': link['purpose'] + '；' + review['review_note']})
        old_states = distinct(s['object_id'] for s in original['payload']['states'])
        self.audits.append({'shot': ref(shot), 'baseline_shot': ref(original), 'source': value['source'],
                            'script_facts': value['facts'], 'review_note': review['review_note'],
                            'input_review': {'retained': [s for s in distinct(states) if s in old_states and s not in self.corrected],
                                             'added': [s for s in distinct(states) if s not in old_states],
                                             'removed': [s for s in old_states if s not in states],
                                             'corrected': [s for s in distinct(states) if s in self.corrected]},
                            'image_sequence': images, 'voice_states': voice_ids,
                            'initial_keyframe_states': comp_ids, 'direct_video_image_states': direct,
                            'references': links, 'prompt': prompt, 'prompt_links': spans,
                            'video': ref(video), 'model': model,
                            'contract': {'images': 1 + len(direct), 'audio': 1, 'prompt_characters': len(prompt), 'duration': duration},
                            'semantic_output_review': 'pending', 'browser_review': 'pending'})

    def build(self):
        for entry in self.baseline['plans']:
            for key in ('shot', 'video'):
                if ref(self.before[entry[key]['object_id']]) != entry[key]:
                    raise ValueError('baseline has moved: ' + entry[key]['object_id'])
                self.guards[entry[key]['object_id']] = entry[key]['revision_id']
        self.states()
        for oid in sorted(self.reviews):
            self.build_shot(self.reviews[oid])
        return {'format': 'production-import-v1', 'expected_heads': self.guards, 'records': self.records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    from generation_workspace import generation_root, contained
    from review_desk.store import Store
    from review_desk import production as p
    root = generation_root(ROOT)
    instance = contained(root, args.instance)
    if not (instance / '.runtime/generation-base.sqlite3').is_file():
        raise ValueError('requires an initialized isolated generation instance')
    if not instance.resolve().is_relative_to((root / '.runtime').resolve()):
        raise ValueError('only task runtime instances are writable')
    output = contained(root, args.output)
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        builder = Builder(store, p)
        document = builder.build()
        write(output / 'records.json', document)
        write(output / 'shot-output-review.json', {'format': 'shot-output-review-v1', 'coverage': len(builder.audits), 'shots': builder.audits})
        result = p.import_records(store, document, validate_only=not args.apply)
        write(output / 'import-result.json', result)
        print(json.dumps({'shots': len(builder.audits), 'records': len(document['records']),
                          'applied': args.apply, 'output': str(output.relative_to(ROOT))}))
    finally:
        store.close()


if __name__ == '__main__':
    main()
