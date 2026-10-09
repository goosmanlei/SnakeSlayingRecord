#!/usr/bin/env python3
"""Read the authored audiovisual score and bind it to exact screenplay evidence.

This story-side compiler does not read retired preparation/shot objects, invent
shots from paragraph counts, or call a generation provider. Markdown is the
authoritative creative input; checks never rewrite it to make a test pass.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('空间', '轴线', '光线', '色彩', '声音', '连续性')
EPISODE_FIELDS = ('意图', '结构', '节奏', '连续性')
RANGE = re.compile(r'(s\d{3}):(\d+)(?:-(\d+))?')


def ranges(text):
    result = []
    for part in text.split(';'):
        part = part.strip()
        if not part:
            continue
        match = RANGE.fullmatch(part)
        if not match:
            raise ValueError('invalid exact source range: ' + part)
        scene, start, end = match.groups()
        start, end = int(start), int(end or start)
        if start < 1 or end < start:
            raise ValueError('invalid source bounds: ' + part)
        result.append((scene, start, end))
    return result


def keys(spans):
    return {(scene, n) for scene, start, end in spans for n in range(start, end + 1)}


def read_score(directory=ROOT / 'production/audiovisual'):
    result = []
    for path in sorted(directory.glob('e[0-9][0-9].md')):
        episode = {'number': int(path.stem[1:]), 'file': str(path.relative_to(ROOT)), 'scenes': []}
        section = episode
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if line.startswith('# '):
                episode['title'] = line[2:].strip()
            elif line.startswith('## '):
                code, title = line[3:].split(' · ', 1)
                if code != f'A{len(episode["scenes"]) + 1:02}':
                    raise ValueError(f'{path}:{line_number}: scene order is not explicit and contiguous')
                section = {'code': code, 'title': title, 'shots': []}
                episode['scenes'].append(section)
            elif re.match(r'\| s\d', line):
                columns = [v.strip() for v in line.strip('|').split('|')]
                if len(columns) != 6 or section is episode:
                    raise ValueError(f'{path}:{line_number}: incomplete authored shot')
                source, seconds, framing, action, purpose, sound_edit = columns
                if ' → ' not in action:
                    raise ValueError(f'{path}:{line_number}: shot needs an authored start and end')
                seconds = int(seconds)
                if not 4 <= seconds <= 30:
                    raise ValueError(f'{path}:{line_number}: unsupported single clip duration')
                start, end = action.split(' → ', 1)
                if not all((framing, start, end, purpose, sound_edit)):
                    raise ValueError(f'{path}:{line_number}: empty design field')
                section['shots'].append({'source': ranges(source), 'seconds': seconds,
                    'framing': framing, 'action_start': start, 'action_end': end,
                    'performance': purpose, 'sound_edit': sound_edit, 'line': line_number})
            elif '：' in line and not line.startswith(('#', '|')):
                label, value = line.split('：', 1)
                if label in (*FIELDS, *EPISODE_FIELDS):
                    if label in section or not value.strip():
                        raise ValueError(f'{path}:{line_number}: duplicate or empty {label}')
                    section[label] = value.strip()
        for field in EPISODE_FIELDS:
            if field not in episode:
                raise ValueError(f'{path}: episode needs {field}')
        for scene in episode['scenes']:
            for field in FIELDS:
                if field not in scene:
                    raise ValueError(f'{path}: {scene["code"]} needs {field}')
            if not scene['shots']:
                raise ValueError(f'{path}: empty audiovisual scene')
        result.append(episode)
    return result


def coverage(score, screenplay):
    if [e['number'] for e in score] != [e['number'] for e in screenplay['episodes']]:
        raise ValueError('authored episodes must match all exact story episodes in order')
    details, all_keys = [], set()
    for edition, original in zip(score, screenplay['episodes']):
        counts = Counter(k for scene in edition['scenes'] for shot in scene['shots'] for k in keys(shot['source']))
        expected = {(s['id'], n) for s in original['scenes'] for n in range(1, len(s['block_ids']) + 1)}
        missing, extra = expected - counts.keys(), counts.keys() - expected
        repeated = [k for k, value in counts.items() if value != 1]
        if missing or extra or repeated:
            raise ValueError(f'episode {edition["number"]}: missing={sorted(missing)}, extra={sorted(extra)}, repeated={repeated}')
        all_keys |= expected
        shots = [shot for scene in edition['scenes'] for shot in scene['shots']]
        details.append({'episode': edition['number'], 'story_scenes': len(original['scenes']),
            'audiovisual_scenes': len(edition['scenes']), 'shots': len(shots),
            'blocks': len(expected), 'planned_seconds': sum(shot['seconds'] for shot in shots),
            'source_estimated_seconds': original['estimated_seconds']})
    return {'format': 'audiovisual-coverage-v1', 'episodes': details,
            'totals': {key: sum(d[key] for d in details) for key in
                       ('story_scenes', 'audiovisual_scenes', 'shots', 'blocks', 'planned_seconds')},
            'complete': True, 'duplicate_blocks': 0, 'uncovered_blocks': 0,
            'timing_status': '方案中的动作与说唱时长估计，尚无实际视频或剪辑时长；未生成剪辑时间线'}


def state_rules(path=ROOT / 'production/audiovisual/state-ranges.txt'):
    result = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, source = line.split('=', 1)
        name = 'form-' + name.strip()
        if name in result:
            raise ValueError('duplicate state rule: ' + name)
        result[name] = ranges(source)
    return result


def transition_rules(path=ROOT / 'production/audiovisual/state-transitions.txt'):
    result = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        spec, action = line.split(' | ', 1)
        source, before, _, after = spec.split()
        result.append({'source': ranges(source), 'before': 'form-' + before,
                       'after': 'form-' + after, 'action': action})
    return sorted(result, key=lambda t: t['source'])


def evidence_keys(row):
    result = set()
    for source in row['payload'].get('sources', []):
        for block in source.get('block_ids', []):
            match = re.search(r'(s\d{3})-b(\d+)$', block)
            if match:
                result.add((match[1], int(match[2])))
    return result


def appearance_rules(path=ROOT / 'production/audiovisual/appearances.txt'):
    result = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        owner, source = (v.strip() for v in line.split('=', 1))
        owner = 'entity-' + owner
        if owner in result:
            raise ValueError('duplicate appearance rule: ' + owner)
        result[owner] = set() if source == '-' else keys(ranges(source))
    return result


def bind_states(store, score, episodes, p):
    states = {r['object_id']: r for r in p.current_records(store, {'STATE'})}
    entities = {r['object_id']: r for r in p.current_records(store, {'ENTITY'})}
    groups = defaultdict(list)
    for row in states.values():
        groups[row['payload']['entity']['object_id']].append(row)
    rules, events, appearances = state_rules(), transition_rules(), appearance_rules()
    if appearances.keys() != entities.keys():
        raise ValueError('every entity needs an explicit appearance decision: ' +
                         str(sorted(appearances.keys() ^ entities.keys())))
    unknown = rules.keys() - states.keys()
    if unknown:
        raise ValueError('state rules refer to absent identities: ' + ', '.join(sorted(unknown)))
    for owner, rows in groups.items():
        if len(rows) > 1 and any(row['object_id'] not in rules for row in rows):
            raise ValueError('multi-state identity needs explicit reviewed ranges: ' + owner)
    for event in events:
        before, after = states[event['before']], states[event['after']]
        if before['payload']['entity']['object_id'] != after['payload']['entity']['object_id']:
            raise ValueError('transition crosses identities')
        event['owner'] = before['payload']['entity']['object_id']
    applicability = {oid: keys(rules[oid]) if oid in rules else evidence_keys(row) for oid, row in states.items()}
    result, issues = {}, []
    for episode in score:
        for scene in episode['scenes']:
            for index, shot in enumerate(scene['shots'], 1):
                oid = f'av-e{episode["number"]:02}-{scene["code"].lower()}-s{index:02}'
                span = keys(shot['source'])
                usage = {'entities': [], 'states': [], 'state_transitions': [], 'continuity_context': []}
                for owner, rows in groups.items():
                    depicted = bool(appearances[owner] & span)
                    matched = [row for row in rows if (applicability[row['object_id']] & span or len(rows) == 1 and depicted)
                               and row['payload']['reference_media'] != 'none']
                    if not matched:
                        if depicted:
                            issues.append({'shot': oid, 'entity': owner, 'reason': 'appearance needs an authored complete state'})
                        continue
                    if not depicted:
                        usage['continuity_context'].extend(reference(r) for r in matched)
                        continue
                    matched.sort(key=lambda row: min(applicability[row['object_id']] & span, default=('', 0)))
                    changes = [e for e in events if e['owner'] == owner and keys(e['source']) & span]
                    sequence = [states[changes[0]['before']]] if changes else matched[:1]
                    coherent = True
                    for event in changes:
                        if sequence[-1]['object_id'] != event['before']:
                            issues.append({'shot': oid, 'entity': owner, 'reason': 'transition chain gap', 'event': event})
                            coherent = False
                            break
                        sequence.append(states[event['after']])
                    if not coherent:
                        continue
                    if not {r['object_id'] for r in matched} <= {r['object_id'] for r in sequence}:
                        issues.append({'shot': oid, 'entity': owner, 'reason': 'state order not authored', 'states': [r['object_id'] for r in matched]})
                        continue
                    usage['entities'].append(reference(entities[owner]))
                    usage['states'].extend(reference(r) for r in sequence)
                    for event in changes:
                        usage['state_transitions'].append({'from': reference(states[event['before']]),
                            'to': reference(states[event['after']]), 'action': event['action'],
                            'source': source_refs(episodes[episode['number']], event['source'])[0]})
                result[oid] = usage
    if issues:
        return result, issues
    return result, []


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def bind_sources(store, screenplay, p):
    lock = p.record(store, 'production-input-screenplay04')
    if lock['kind'] != 'INPUT_LOCK':
        raise ValueError('wrong production input')
    by_number = {}
    for reference in lock['payload']['episodes']:
        row = p.ref_record(store, reference, {'EPISODE'})
        by_number[row['payload']['number']] = row
    for original in screenplay['episodes']:
        row = by_number[original['number']]
        if row['payload']['blocks'] != original['blocks'] or row['payload']['scenes'] != original['scenes']:
            raise ValueError(f'exact story source has drifted: episode {original["number"]}')
    return lock, by_number


def reference(row):
    return {'object_id': row['object_id'], 'revision_id': row['id']}


def future(oid):
    return {'object_id': oid, 'revision_id': '@' + oid}


def source_refs(row, spans):
    scenes = {s['id']: s for s in row['payload']['scenes']}
    result = []
    for sid, start, end in spans:
        result.append({**reference(row), 'scene_id': sid,
                       'block_ids': scenes[sid]['block_ids'][start - 1:end]})
    return result


def union_sources(values):
    result = {}
    for source in values:
        key = (source['object_id'], source['revision_id'], source['scene_id'])
        existing = result.setdefault(key, {**source, 'block_ids': []})
        existing['block_ids'].extend(b for b in source['block_ids'] if b not in existing['block_ids'])
    return list(result.values())


def source_text(row, spans):
    blocks = {b['id']: b['text'] for b in row['payload']['blocks']}
    return '\n'.join(blocks[b] for source in source_refs(row, spans) for b in source['block_ids'])


def score_records(score, lock, episodes, bindings, reviewed):
    """bindings is independently reviewed state usage, never an old shot map."""
    records = []
    for episode in score:
        number = episode['number']
        story = episodes[number]
        scene_refs, episode_sources = [], []
        for scene in episode['scenes']:
            sid = f'av-e{number:02}-{scene["code"].lower()}'
            shot_refs, scene_sources = [], []
            for index, shot in enumerate(scene['shots'], 1):
                oid = f'{sid}-s{index:02}'
                sources = source_refs(story, shot['source'])
                usage = bindings[oid]
                fixed, shared = reviewed.conditions(number, scene, index)
                vocals = reviewed.for_sources(sources)
                payload = {'format': 'production-av-shot-v1', 'title': f'{number:02} · {scene["code"]} · {index:02} {shot["action_end"]}',
                    'number': index, 'input_lock': reference(lock), 'sources': sources,
                    'purpose': shot['performance'], 'framing': shot['framing'],
                    'spatial': fixed['空间'], 'axis': fixed['轴线'], 'movement': shot['framing'],
                    'action_start': shot['action_start'], 'action_end': shot['action_end'],
                    'performance': shot['performance'], 'lighting': fixed['光线'], 'color': fixed['色彩'],
                    'editing': shot['sound_edit'], 'continuity': fixed['连续性'],
                    'sound': [fixed['声音'], shot['sound_edit'], *[reviewed.describe(e) for e in vocals]],
                    'fps': 24, 'duration_frames': shot['seconds'] * 24,
                    'state_model': 'complete-v1', **usage,
                    'authoring': {'file': episode['file'], 'line': shot['line'], 'shared_scene_fields': shared,
                        'conditions': 'production/audiovisual/shot-contexts.json',
                        'vocal_score': 'production/audiovisual/vocal-events.json'}}
                records.append({'object_id': oid, 'kind': 'AV_SHOT', 'payload': payload})
                shot_refs.append(future(oid)); scene_sources.extend(sources)
            sources = union_sources(scene_sources)
            payload = {'format': 'production-av-scene-v1', 'title': scene['title'], 'input_lock': reference(lock),
                'sources': sources, 'shots': shot_refs, 'purpose': episode['意图'],
                'structure': '\n'.join(f'{i:02} {s["action_start"]} → {s["action_end"]}' for i, s in enumerate(scene['shots'], 1)),
                'rhythm': '\n'.join(s['sound_edit'] for s in scene['shots']), 'continuity': scene['连续性'],
                'spatial': scene['空间'], 'axis': scene['轴线'], 'lighting': scene['光线'], 'color': scene['色彩'], 'sound': [scene['声音']]}
            records.append({'object_id': sid, 'kind': 'AV_SCENE', 'payload': payload})
            scene_refs.append(future(sid)); episode_sources.extend(sources)
        records.append({'object_id': f'av-e{number:02}', 'kind': 'AV_EPISODE', 'payload': {
            'format': 'production-av-episode-v1', 'title': episode['title'], 'input_lock': reference(lock),
            'story_episode': reference(story), 'number': number, 'sources': union_sources(episode_sources),
            'scenes': scene_refs, 'purpose': episode['意图'], 'structure': episode['结构'],
            'rhythm': episode['节奏'], 'continuity': episode['连续性']}})
    for row in records:
        row['expected_version'] = 0
        row['payload']['blocks'] = [{'id': 'purpose', 'text': row['payload']['purpose']}]
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['audit', 'bind', 'compile'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--system', type=Path)
    parser.add_argument('--db', type=Path)
    args = parser.parse_args()
    score = read_score()
    screenplay = json.loads((ROOT / 'imports/screenplay-04.json').read_text())
    report = coverage(score, screenplay)
    from audiovisual_events import ReviewedEvents
    from audiovisual_materials import casting
    reviewed = ReviewedEvents(ROOT, score, casting())
    report['authored_files_sha256'] = {e['file']: hashlib.sha256((ROOT / e['file']).read_bytes()).hexdigest() for e in score}
    if args.command in ('bind', 'compile'):
        if not args.system or not args.db:
            parser.error('bind requires --system and --db; database is opened read-only')
        sys.path.insert(0, str(args.system.resolve()))
        from review_desk.store import Store
        from review_desk import production as p
        store = Store.open_readonly(args.db)
        try:
            lock, episodes = bind_sources(store, screenplay, p)
            bindings, issues = bind_states(store, score, episodes, p)
            report['state_binding_issues'] = issues
            report['complete'] = not issues
            if not issues:
                report['records'] = score_records(score, lock, episodes, bindings, reviewed)
                if args.command == 'compile':
                    from audiovisual_materials import Builder
                    materials = Builder(store, p, report['records'], reviewed).build()
                    report['records'].extend(materials['records'])
                    report['material_counts'] = materials['counts']
                    report['preserve_exact_requirements'] = materials['preserve_exact_requirements']
        finally:
            store.db.close()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['totals'], ensure_ascii=False))
    if report.get('state_binding_issues'):
        print(json.dumps(report['state_binding_issues'], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
