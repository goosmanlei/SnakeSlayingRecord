"""Apply this story's reviewed, direct video references without selecting originals.

The audit is authored per shot, independent of dialogue/action translation.
Generic channel checks live in the review desk, never in this story module.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'production/audiovisual/video-inputs.json'
EXECUTION = {'channel': 'pippit-tool-cli', 'mode': 'reference', 'start_constraint': 'reference'}
FRAME_USE = '起始图提供构图、手位和已可见主体的参考；本模式不固定首帧像素'


def load_audit(shots=None):
    value = json.loads(AUDIT.read_text())
    if value['format'] != 'story-video-input-audit-v1':
        raise ValueError('unsupported video input audit')
    rows = [dict(r, execution_reviewed=s.get('execution_reviewed', False))
            for s in value['scenes'] for r in s['shots']]
    by_id = {r['shot']: r for r in rows}
    if len(rows) != len(by_id):
        raise ValueError('duplicate reviewed shot')
    for row in rows:
        for owner, ref in row.get('first_frame_states', {}).items():
            if set(ref) != {'state', 'revision_id'} or not all(isinstance(v, str) and v.strip() for v in ref.values()):
                raise ValueError('invalid first-frame state reference: ' + row['shot'] + ' ' + owner)
        for state, text in row.get('frame_state_text', {}).items():
            if (not {'revision_id', 'text'} <= set(text) or set(text) - {'revision_id', 'text', 'model_label'}
                    or not all(isinstance(v, str) and v.strip() for v in text.values())):
                raise ValueError('invalid first-frame state text: ' + row['shot'] + ' ' + state)
        for item in row.get('supplements', []):
            if item.get('reference_basis', 'state') not in ('state', 'identity_master'):
                raise ValueError('unknown reviewed reference basis: ' + row['shot'])
    if shots is not None:
        if set(by_id) != {r['object_id'] for r in shots}:
            raise ValueError('reviewed video inputs must cover every current shot exactly once')
        for row in shots:
            decision = by_id[row['object_id']]
            if decision['reviewed_product_references'] != [v['requirement'] for v in row['payload']['products']]:
                raise ValueError('exact product plan changed; review the input decision: ' + row['object_id'])
            states = {s['object_id'] for s in row['payload']['states']}
            if any(v['state'] not in states for v in decision.get('supplements', [])):
                raise ValueError('supplement is not an exact state of this shot: ' + row['object_id'])
    return by_id


def frame_state_label(state, decision):
    """An explicitly reviewed local name can exclude another scene's placement."""
    text = decision.get('frame_state_text', {}).get(state['object_id'])
    if text and text['revision_id'] != state['id']:
        raise ValueError('first-frame state text needs re-review: ' + state['object_id'])
    return text.get('model_label', state['payload']['title']) if text else state['payload']['title']


def first_frame_states(states, available, decision):
    """Use an explicit starting state when the source paragraph also has its result."""
    selected = {}
    for state in states:
        selected.setdefault(state['payload']['entity']['object_id'], state)
    for owner, ref in decision.get('first_frame_states', {}).items():
        if owner not in selected:
            raise ValueError('first-frame state has no subject in shot: ' + owner)
        state = available.get(ref['state'])
        if not state or state['id'] != ref['revision_id']:
            raise ValueError('first-frame state needs re-review: ' + ref['state'])
        if state['payload']['entity']['object_id'] != owner:
            raise ValueError('first-frame state belongs to another subject: ' + ref['state'])
        selected[owner] = state
    return list(selected.values())


def frame_plan(plan, decision):
    result = copy.deepcopy(plan)
    if decision.get('first_frame'):
        lines = [line for line in result['prompt'].splitlines() if not line.startswith('本镜起始裁切：')]
        result['prompt'] = '\n'.join([*lines, '本镜起始裁切：' + decision['first_frame']])
    return result


