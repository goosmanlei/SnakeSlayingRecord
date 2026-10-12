#!/usr/bin/env python3
"""Bind final Prompt paragraphs after checking exact speech and event order.

Legacy plans retain their existing rendered ranges. Authored current plans are
checked against the locked vocal events without requiring the old rendering.
The map stores offsets and hashes, never a second copy of the Prompt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from audiovisual_design import ROOT, read_score
from audiovisual_events import ReviewedEvents
from audiovisual_materials import casting
from generation_workspace import generation_root, isolated_instance
from video_input_design import load_audit


def vocal_ranges(prompt, sources, reviewed):
    """Check literal original words, speaker and order in the actual new prose."""
    events = [e for e in reviewed.for_sources(sources) if e['words'] == 'exact']
    expected = {}
    identities = ({v[0] for v in reviewed.voice.VOICES.values()} | set(reviewed.voice.LABELS)
                  | {e['speaker'] for e in events if e['speaker'] not in reviewed.voice.VOICES})
    occurrences = {}
    for event in events:
        expected[event['content']] = expected.get(event['content'], 0) + 1
    utterances = []
    for quoted in re.finditer(r'“([^”]*)”|「([^」]*)」|"([^"]*)"', prompt):
        group = next(n for n in range(1, 4) if quoted.group(n) is not None)
        if quoted.group(group) in expected:
            utterances.append((quoted.start(group), quoted.end(group), quoted.group(group)))
    for words, count in expected.items():
        # A spoken name can also occur in reference duties or stage directions.
        # Only its quoted utterance is a vocal event, not every identity mention.
        pattern = (r'(?<=[“「"])' + re.escape(words) + r'(?=[”」"])'
                   if words.rstrip('。！？?!') in identities else re.escape(words))
        occurrences[words] = [m.start() for m in re.finditer(pattern, prompt)
                              if not any(begin <= m.start() and m.end() <= end
                                         and utterance != words
                                         for begin, end, utterance in utterances)]
        if len(occurrences[words]) != count:
            raise ValueError('original words missing or repeated: ' + words)
    result, previous = [], 0
    for event in events:
        words = event['content']
        starts = [value for value in occurrences[words] if value >= previous]
        if not starts:
            raise ValueError('vocal event order differs: ' + event['source'])
        start = starts[0]
        speaker = (reviewed.voice.VOICES[event['speaker']][0]
                   if event['speaker'] in reviewed.voice.VOICES else event['speaker'])
        names = {speaker, *(name for name, identity in reviewed.voice.LABELS.items()
                             if identity == event['speaker'])}
        # The event's clause must identify its own speaker, not borrow the
        # reference paragraph or a previous speaker's dialogue attribution.
        attribution = prompt[max(previous, prompt.rfind('\n', previous, start) + 1, start - 180):start]
        # Match the longest known identity first: 阿蘅母亲 is not 阿蘅,
        # and 程差役 is not the other actor whose label is 差役.
        identified = {m[0] for m in re.finditer('|'.join(re.escape(n) for n in
                      sorted(identities, key=lambda n: (-len(n), n))), attribution)}
        if not names.intersection(identified):
            raise ValueError('vocal event speaker is not explicit: ' + event['source'] + ' ' + speaker)
        result.append({'start': start, 'end': start + len(words), 'source': event['source'],
                       'speaker': event['speaker']})
        previous = start + len(words)
    return result


def descriptor(shot, need, reviewed, choice, executable):
    sources = shot['payload']['sources']
    scope = need['payload'].get('scope', {})
    bound = any(item['requirement'] == {'object_id':need['object_id'], 'revision_id':need.get('id')}
                for item in shot['payload'].get('products', []))
    if scope.get('object_id') != shot['object_id'] or not (bound or scope.get('revision_id') == shot['id']):
        raise ValueError('requirement is outside exact shot')
    prompt = need['payload']['generation']['prompt']
    events = reviewed.render(sources, choice.get('narration'), executable=executable)
    detail = choice.get('video_detail')
    sequence = events + ('\n' + detail if detail else '')
    if need['payload'].get('method_basis') and (not sequence or prompt.count(sequence) != 1):
        vocals = vocal_ranges(prompt, sources, reviewed)
        parts = []
        for match in re.finditer(r'[^\n]+', prompt):
            parts.append({'start': match.start(), 'end': match.end(),
                          'role': 'voice' if any(match.start() <= v['start'] < match.end()
                                                 for v in vocals) else 'detail'})
        if not parts:
            raise ValueError('authored Prompt is empty')
        return {'object_id': need['object_id'], 'scope': need['payload']['scope'],
                'field': 'generation.prompt', 'sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                'parts': parts}
    if not sequence or prompt.count(sequence) != 1:
        raise ValueError('reviewed sequence is not unique in exact saved Prompt: ' + need['object_id'])
    offset = prompt.index(sequence)
    parts = []
    for line in sequence.splitlines(keepends=True):
        raw = line.rstrip('\n')
        if raw not in ('声音（依序；注明同时者重叠）：', '本段发声（依序；注明同时者重叠）：'):
            match = re.match(r'^(动作与叙述依据：|动作：|声音：|\d+\. )', raw)
            prefix = match[0] if match else ''
            role = 'action' if prefix.startswith('动作') else 'voice' if prefix.startswith('声音') or re.fullmatch(r'\d+\. ', prefix) else 'detail'
            if raw[len(prefix):].strip():
                parts.append({'start': offset + len(prefix), 'end': offset + len(raw), 'role': role})
        offset += len(line)
    return {'object_id': need['object_id'], 'scope': need['payload']['scope'],
            'field': 'generation.prompt', 'sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'parts': parts}


def compile_reading(instance, shot_ids):
    from review_desk import production as p
    from review_desk.store import Store
    lock = json.loads((ROOT / 'production/source-lock.json').read_text())
    if hashlib.sha256((ROOT / lock['screenplay']['source_file']).read_bytes()).hexdigest() != lock['screenplay']['file_sha256']:
        raise ValueError('locked screenplay bytes changed')
    locked = {e['object_id']: e['revision_id'] for e in lock['episodes']}
    reviewed = ReviewedEvents(ROOT, read_score(), casting())
    choices = json.loads((ROOT / 'production/audiovisual/exact-text.json').read_text())['shots']
    audit = load_audit()
    entries = {}
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        for oid in shot_ids:
            shot = p.record(store, oid)
            for source in shot['payload']['sources']:
                if locked.get(source['object_id']) != source['revision_id']:
                    raise ValueError('shot source is outside locked screenplay: ' + oid)
            needs = [p.ref_record(store, v['requirement'], {'REQUIREMENT'}) for v in shot['payload']['products']]
            needs = [r for r in needs if r['payload']['media_type'] == 'video']
            if len(needs) != 1:
                raise ValueError('one exact video product required: ' + oid)
            need = needs[0]
            value = descriptor(shot, need, reviewed, choices.get(oid, {}), audit[oid]['execution_reviewed'])
            entries[need['id'] + ':' + value['sha256']] = value
    finally:
        store.close()
    return {'format': 'exact-prompt-reading-v1', 'entries': entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--shots', nargs='+')
    selection.add_argument('--all', action='store_true', help='all shots in the reviewed score')
    parser.add_argument('--write-config', action='store_true')
    args = parser.parse_args()
    root = generation_root(ROOT)
    instance = isolated_instance(root, args.instance)
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    shots = args.shots or [f"av-e{episode['number']:02d}-{scene['code'].lower()}-s{number:02d}"
                          for episode in read_score() for scene in episode['scenes']
                          for number, _ in enumerate(scene['shots'], 1)]
    reading = compile_reading(instance, shots)
    if args.write_config:
        config_file = root / 'config/instance.json'
        config = json.loads(config_file.read_text())
        prior = config.get('scene_reading', {})
        config['scene_reading'] = {**reading, 'entries': {**prior.get('entries', {}), **reading['entries']}}
        config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'exact_requirements': len(reading['entries']), 'prompt_writes': 0, 'config_written': args.write_config}))


if __name__ == '__main__':
    main()
