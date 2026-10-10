#!/usr/bin/env python3
"""Bind readable event ranges to existing exact Prompts; never rewrite them.

The reviewed event compiler is the authority for order. A range is emitted only
when its complete output occurs exactly once in the already saved Prompt.
The instance configuration stores offsets and hashes, never a second text.
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


def descriptor(shot, need, reviewed, choice, executable):
    sources = shot['payload']['sources']
    scope = need['payload'].get('scope', {})
    bound = any(item['requirement'] == {'object_id':need['object_id'], 'revision_id':need.get('id')}
                for item in shot['payload'].get('products', []))
    if scope.get('object_id') != shot['object_id'] or not (bound or scope.get('revision_id') == shot['id']):
        raise ValueError('requirement is outside exact shot')
    events = reviewed.render(sources, choice.get('narration'), executable=executable)
    detail = choice.get('video_detail')
    sequence = events + ('\n' + detail if detail else '')
    prompt = need['payload']['generation']['prompt']
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
            entries[need['id']] = descriptor(shot, need, reviewed, choices.get(oid, {}), audit[oid]['execution_reviewed'])
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
        config['scene_reading'] = reading
        config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'exact_requirements': len(reading['entries']), 'prompt_writes': 0, 'config_written': args.write_config}))


if __name__ == '__main__':
    main()
