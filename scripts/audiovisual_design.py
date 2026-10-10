#!/usr/bin/env python3
"""Read the authored audiovisual score and bind it to exact screenplay evidence.

This story-side compiler does not read retired preparation/shot objects, invent
shots from paragraph counts, or call a generation provider. The individually authored reading JSON is the
authoritative creative input; checks never supply narrative prose. Exact media
plans are revised independently through media_method.py, not rebuilt in bulk.
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
    """Read authored prose and exact products; no inherited scene conditions."""
    result = []
    for path in sorted((directory / 'readings').glob('e[0-9][0-9].json')):
        doc = json.loads(path.read_text())
        if doc.get('format') != 'audiovisual-reading-v1':
            raise ValueError('unsupported audiovisual reading: ' + str(path))
        source = (ROOT / doc['reading']['source']).resolve(strict=True)
        if not source.is_relative_to(ROOT) or hashlib.sha256(source.read_bytes()).hexdigest() != doc['reading']['source_sha256']:
            raise ValueError('locked screenplay changed; re-read before authoring')
        scenes = {}
        for item in doc['shots']:
            oid = item['object_id']; scene_id = oid.rsplit('-s', 1)[0]
            if not item['purpose'].strip():
                raise ValueError('shot needs an authored narrative purpose: ' + oid)
            spans = []
            for ref in item['sources']:
                numbers = [int(b.rsplit('-b', 1)[1]) for b in ref['block_ids']]
                if numbers != list(range(min(numbers), max(numbers)+1)):
                    raise ValueError('source block range must remain contiguous: ' + oid)
                spans.append((ref['scene_id'], min(numbers), max(numbers)))
            scene = scenes.setdefault(scene_id, {'code':scene_id.rsplit('-',1)[1].upper(), 'shots':[]})
            scene['shots'].append({**item, 'source':spans, 'seconds':item.get('planned_seconds', 0)})
        result.append({'number':doc['episode'], 'file':path.relative_to(ROOT).as_posix(),
                       'title':doc.get('title',''), 'scenes':list(scenes.values()),
                       'reading':doc['reading'], 'working_notes':doc['working_notes']})
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



def render_readings(score, directory=ROOT / 'production/audiovisual'):
    """A readable projection of authored JSON, never a second creative source."""
    paths = []
    for episode in score:
        oid = f"av-e{episode['number']:02}"
        lines = ['# ' + episode['title'], '',
                 '本文由 [' + Path(episode['file']).name + '](readings/' + Path(episode['file']).name + ') 派生；修订唯一源稿后重新运行 `audiovisual_design.py render`。', '',
                 episode['working_notes'][oid], '']
        for scene in episode['scenes']:
            sid = oid + '-' + scene['code'].lower()
            lines += ['## ' + scene['code'], '', episode['working_notes'][sid], '']
            for shot in scene['shots']:
                lines += ['### ' + shot['label'], '', shot['purpose'], '', '关键状态：', '']
                if not shot['key_states']:
                    lines += ['此镜没有另行准备状态素材。', '']
                for state in shot['key_states']:
                    names = [next(v['label'] for v in shot['products'] if v['requirement'] == ref) for ref in state['requirements']]
                    lines += ['- ' + state['description'] + '（' + '、'.join(names) + '）']
                lines += ['', '产物顺序：' + ' → '.join(v['label'] for v in shot['products']) + '。准确素材引用见源稿；参数、Prompt 与输入保存在该素材方案，不在这里另写副本。', '']
        path = directory / f"e{episode['number']:02}.md"
        path.write_text('\n'.join(lines))
        paths.append(path.relative_to(ROOT).as_posix())
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['audit', 'bind', 'compile', 'render'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--system', type=Path)
    parser.add_argument('--db', type=Path)
    args = parser.parse_args()
    score = read_score()
    screenplay = json.loads((ROOT / 'imports/screenplay-04.json').read_text())
    report = coverage(score, screenplay)
    if args.command == 'render':
        report['rendered'] = render_readings(score)
    report['authored_files_sha256'] = {e['file']: hashlib.sha256((ROOT / e['file']).read_bytes()).hexdigest() for e in score}
    if args.command in ('bind', 'compile'):
        if not args.system or not args.db:
            parser.error('bind/compile requires --system and --db; database is opened read-only')
        sys.path.insert(0, str(args.system.resolve()))
        from review_desk.store import Store
        from review_desk import production as p
        from audiovisual_reading import prepare
        store = Store.open_readonly(args.db)
        try:
            bind_sources(store, screenplay, p)
            report['migration'] = prepare(store, [ROOT/e['file'] for e in score])
            report['preserve_exact_requirements'] = [product['requirement'] for e in score for scene in e['scenes'] for shot in scene['shots'] for product in shot['products']]
        finally:
            store.close()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['totals'], ensure_ascii=False))
    if report.get('state_binding_issues'):
        print(json.dumps(report['state_binding_issues'], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
