"""Compile the story's authored state-use decisions, never infer use from degree.

The Markdown is the human review source. Existing complete states and immutable
references remain the data model; this module adds no parallel runtime ledger.
"""
from copy import deepcopy
import json
import re
from audiovisual_design import ROOT

MODES = {'生成输入', '独立审阅', '可选对照', '文字检查'}


def decisions():
    result = {}
    for line in (ROOT / 'production/audiovisual/state-preparation.md').read_text().splitlines():
        if not line.startswith('| form-'):
            continue
        state, mode, purpose = (v.strip() for v in line.strip('|').split('|'))
        if state in result or mode not in MODES or not purpose:
            raise ValueError('invalid or duplicate authored state preparation: ' + state)
        result[state] = {'mode': mode, 'purpose': purpose}
    return result


def state_records(store, p):
    rows = []
    corrections = {}
    text = (ROOT / 'production/audiovisual/state-preparation.md').read_text()
    for block in re.findall(r'```json state-content\n(.*?)\n```', text, re.S):
        for oid, value in json.loads(block).items():
            if oid in corrections or set(value) - {'dimensions', 'production_blockers', 'entity'}:
                raise ValueError('invalid authored state content correction: ' + oid)
            corrections[oid] = value
    if corrections.keys() - decisions().keys():
        raise ValueError('content correction requires an authored preparation decision')
    for oid, decision in decisions().items():
        row = p.record(store, oid)
        if row['kind'] != 'STATE' or row['payload'].get('state_model') != 'complete-v1':
            raise ValueError('preparation needs a current complete state: ' + oid)
        payload = deepcopy(row['payload'])
        correction = corrections.get(oid, {})
        if 'entity' in correction:
            ref = correction['entity']
            owner = p.ref_record(store, ref, {'ENTITY'})
            if ref['object_id'] != payload['entity']['object_id'] or owner.get('unavailable'):
                raise ValueError('authored state owner must be the same available exact entity: ' + oid)
            payload['entity'] = deepcopy(ref)
        if 'dimensions' in correction:
            payload['dimensions'].update(correction['dimensions'])
            # The corrected typed dimensions become authoritative. Refresh the
            # existing display block; do not ask authors to maintain a second
            # explicit production_description field containing the same text.
            payload.pop('production_description', None)
            for block in payload['blocks']:
                if block['id'] == 'description':
                    block['text'] = '\n'.join(payload['dimensions'].values())
        if 'production_blockers' in correction:
            payload['production_blockers'] = correction['production_blockers']
        payload['reference_mode'] = 'description' if decision['mode'] in ('文字检查', '可选对照') else 'material'
        # This exact character-only boilerplate was incorrectly copied to all
        # types. Preserve other authored choices rather than replacing them.
        old = '同一完整形态跨场复用；未写换装、湿痕消退、伤愈程度的衔接属于待审连续性安排，不冒充新增剧本事实。'
        generic = '本状态的具体湿痕、伤侧、色彩和衔接安排属于制作选择，剧本事实列在下方。'
        payload['choices'] = [v for v in payload.get('choices', [])
                              if v not in (old, generic) and not v.startswith('准备用途：')]
        payload['choices'].append('准备用途：' + decision['mode'] + '。' + decision['purpose'])
        rows.append({'object_id': oid, 'kind': 'STATE', 'payload': payload})
    return rows


class WithStates:
    """A read-only compiler view of the predicted immutable state revisions."""
    def __init__(self, p, rows, identities):
        self.base = p
        self.rows = {r['object_id']: {**r, 'id': identities[r['object_id']],
                     'current_revision': identities[r['object_id']]} for r in rows}

    def __getattr__(self, name):
        return getattr(self.base, name)

    def record(self, store, object_id=None, revision_id=None):
        if object_id in self.rows and revision_id is None:
            return self.rows[object_id]
        return self.base.record(store, object_id=object_id, revision_id=revision_id)

    def current_records(self, store, kinds=None):
        return [self.rows.get(r['object_id'], r) for r in self.base.current_records(store, kinds)]
