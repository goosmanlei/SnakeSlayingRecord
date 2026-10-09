"""Reviewed shot conditions and ordered vocal events over the locked screenplay.

Narrative speech is authored, not inferred from keywords. Only explicit dialogue
labels have a default reading; annotations override that reading per paragraph.
"""
import hashlib
import json
import re

FIELDS = ('空间', '轴线', '光线', '色彩', '声音', '连续性')
NON_DIALOGUE = {'字幕', '李诞回忆中的短暂画面', '贴纸揭下，旧字完整露出来', '经过人群，有人贴着家人的耳朵说'}
SONGS = {'entity-boat-song', 'entity-blue-awning-song', 'entity-blessing-stage-song', 'entity-snake-welcome-song'}


class ReviewedEvents:
    def __init__(self, root, score, voice):
        self.voice = voice
        raw = (root / 'imports/screenplay-04.json').read_bytes()
        self.blocks = {}
        for episode in json.loads(raw)['episodes']:
            texts = {b['id']: b['text'] for b in episode['blocks']}
            for scene in episode['scenes']:
                self.blocks.update({f'{scene["id"]}:{i}': texts[b] for i, b in enumerate(scene['block_ids'], 1)})
        directory = root / 'production/audiovisual'
        self.contexts = json.loads((directory / 'shot-contexts.json').read_text())
        vocals = json.loads((directory / 'vocal-events.json').read_text())
        for doc, name in ((self.contexts, 'reviewed-shot-contexts-v1'), (vocals, 'reviewed-vocal-events-v1')):
            if doc.get('format') != name or doc.get('source_sha256') != hashlib.sha256(raw).hexdigest():
                raise ValueError('reviewed event source changed; re-review before compiling: ' + name)
        self.events = vocals['events']
        self.narration = self.contexts.get('narration', {})
        if self.narration.keys() - self.blocks.keys() or any(not isinstance(v, str) for v in self.narration.values()):
            raise ValueError('reviewed action narration outside locked source')
        self.action_order = self.contexts.get('action_order', {})
        for key, steps in self.action_order.items():
            if key not in self.blocks or not isinstance(steps, list) or not steps:
                raise ValueError('invalid reviewed action order: ' + key)
            voices = []
            for step in steps:
                if set(step) == {'action'} and isinstance(step['action'], str) and step['action'].strip():
                    continue
                if set(step) == {'voice'} and type(step['voice']) is int:
                    voices.append(step['voice'])
                    continue
                raise ValueError('invalid action/voice step: ' + key)
            if voices != list(range(len(self.at(key)))):
                raise ValueError('reviewed action order must preserve every vocal event in order: ' + key)
        scenes = {f'{e["number"]:02}-{s["code"]}': s for e in score for s in e['scenes']}
        if scenes.keys() != self.contexts['scenes'].keys():
            raise ValueError('every audiovisual scene needs reviewed fixed conditions')
        shot_keys = set()
        for key, scene in scenes.items():
            entry = self.contexts['scenes'][key]
            inherit = entry['inherit']
            if len(set(inherit)) != len(inherit) or set(inherit) - set(FIELDS):
                raise ValueError('invalid shared conditions: ' + key)
            if set(entry) != {'inherit', 'inherited_values'} | (set(FIELDS) - set(inherit)):
                raise ValueError('fixed conditions must explicitly replace or inherit each field: ' + key)
            if entry['inherited_values'] != {f: scene[f] for f in inherit}:
                raise ValueError('inherited scene condition changed; re-review: ' + key)
            if any(not isinstance(entry[f], str) or not entry[f].strip() for f in FIELDS if f not in inherit):
                raise ValueError('empty reviewed condition: ' + key)
            shot_keys.update(f'{key}-s{i:02}' for i in range(1, len(scene['shots']) + 1))
        for key, fields in self.contexts['shots'].items():
            if key not in shot_keys or set(fields) - set(FIELDS) or any(not isinstance(v, str) or not v.strip() for v in fields.values()):
                raise ValueError('invalid shot condition override: ' + key)
        if self.events.keys() - self.blocks.keys():
            raise ValueError('vocal event outside locked source')
        for key, events in self.events.items():
            if not isinstance(events, list) or not events:
                raise ValueError('empty vocal annotation: ' + key)
            for event in events:
                if set(event) - {'speaker', 'mode', 'words', 'content', 'direction', 'song', 'model_direction'}:
                    raise ValueError('unknown vocal event field: ' + key)
                for field in ('speaker', 'mode', 'words', 'content', 'direction'):
                    if not isinstance(event.get(field), str):
                        raise ValueError('incomplete vocal annotation: ' + key)
                if event['words'] not in ('exact', 'meaning', 'unspecified', 'none') or not event['speaker'] or not event['mode']:
                    raise ValueError('invalid vocal event: ' + key)
                if event['words'] == 'exact' and not event['content']:
                    raise ValueError('exact words required: ' + key)
                if event['speaker'] not in voice.VOICES and not re.search(r'[\u4e00-\u9fff]', event['speaker']):
                    raise ValueError('unknown cast identity: ' + event['speaker'])
                if event.get('song') and event['song'] not in SONGS:
                    raise ValueError('unknown performed song: ' + key)
                if 'model_direction' in event and not isinstance(event['model_direction'], str):
                    raise ValueError('invalid model vocal direction: ' + key)
        # Validate every explicit dialogue label even when a compile targets a subset.
        for key in self.blocks:
            self.at(key)

    def conditions(self, episode, scene, index):
        key = f'{episode:02}-{scene["code"]}'
        entry = self.contexts['scenes'][key]
        fields = {f: scene[f] if f in entry['inherit'] else entry[f] for f in FIELDS}
        overrides = self.contexts['shots'].get(f'{key}-s{index:02}', {})
        fields.update(overrides)
        return fields, [f for f in entry['inherit'] if f not in overrides]

    def direct(self, key):
        match = re.match(r'^([^：]{1,16})：(.+)$', self.blocks[key])
        if not match or match[1] in NON_DIALOGUE:
            return None
        name, words = match.groups()
        if '（唱）' in name:
            if key not in self.events:
                raise ValueError('song needs an explicit reviewed tune and range: ' + key)
            return name, words
        speaker = self.voice.LABELS.get(name)
        if name == '书吏':
            speaker = 'clerk-notice' if key.startswith('s013:') else 'clerk-proclamation' if key.startswith('s037:') else 'clerk-liang'
        if not speaker:
            raise ValueError('dialogue label needs reviewed casting: ' + name)
        return speaker, words

    def at(self, key):
        if key in self.events:
            return self.events[key]
        direct = self.direct(key)
        return [dict(speaker=direct[0], mode='说话', words='exact', content=direct[1], direction='按原文说出，保留自然气口')] if direct else []

    def keys(self, sources):
        return [f'{s["scene_id"]}:{int(b.rsplit("-b", 1)[1])}' for s in sources for b in s['block_ids']]

    def for_sources(self, sources):
        return [dict(event, source=key) for key in self.keys(sources) for event in self.at(key)]

    def describe(self, event, *, executable=False):
        speaker = self.voice.VOICES[event['speaker']][0] if event['speaker'] in self.voice.VOICES else event['speaker']
        body = {'exact': '说唱原词「' + event['content'] + '」',
                'meaning': '只确定语意「' + event['content'] + '」，原词待准备，不将语意当逐字台词',
                'unspecified': '词句或句段未指定：' + (event['content'] or '待准备，不自行补词'),
                'none': '无新增词句' + ('；' + event['content'] if event['content'] else '')}[event['words']]
        direction = event.get('model_direction', event['direction']) if executable else event['direction']
        return f'{speaker}／{event["mode"]}：{body}。{direction}'

    def render(self, sources, narration=None, *, executable=False):
        parts = []
        narration = narration or {}
        if set(narration) - set(self.keys(sources)):
            raise ValueError('visual narration is outside the exact shot sources')
        # The stage review may refine an already-authored text handoff. Both
        # remain anchored to the locked paragraph, never inferred from a start.
        if executable:
            narration = {**narration, **{k: self.narration[k] for k in self.keys(sources) if k in self.narration}}
        for key in self.keys(sources):
            events = self.at(key)
            if executable and key in self.action_order:
                for step in self.action_order[key]:
                    if 'action' in step:
                        parts.append('动作：' + step['action'])
                    else:
                        event = events[step['voice']]
                        if event['words'] in ('exact', 'none'):
                            parts.append('声音：' + self.describe(event, executable=True))
                continue
            text = narration.get(key, self.blocks[key])
            # Direct lines occur once as an executable vocal event. Narration is
            # retained as action evidence, with embedded spoken quotes replaced
            # by event markers rather than a second performance of the words.
            if not self.direct(key):
                for i, event in enumerate(events, 1):
                    if event['words'] == 'exact' and event['content'] in text:
                        text = text.replace(event['content'], f'〔本段发声{i}〕', 1)
                if text:
                    parts.append(('动作：' if executable else '动作与叙述依据：') + text)
            if events:
                # Unlocked words belong to blockers, not to a model's to-do
                # list. They still prevent package preparation through blockers().
                known = [e for e in events if not executable or e['words'] in ('exact', 'none')]
                if known:
                    parts.append(('声音（依序；注明同时者重叠）：\n' if executable else
                                  '本段发声（依序；注明同时者重叠）：\n') +
                                 '\n'.join(f'{i}. {self.describe(e, executable=executable)}' for i, e in enumerate(known, 1)))
        return '\n'.join(parts)

    def blockers(self, sources):
        return [f'{e["source"]}：{self.describe(e)}；须先锁定表演原词或句段并复核自然时长，当前预留秒数不代表可直接生成。'
                for e in self.for_sources(sources) if e['words'] in ('meaning', 'unspecified')]
