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
FIELDS = ('framing', 'action_start', 'action_end', 'performance', 'spatial', 'axis', 'continuity')
EXECUTION = {'channel': 'pippit-tool-cli', 'mode': 'reference', 'start_constraint': 'reference'}
FRAME_USE = '起始图提供构图、手位和已可见主体的参考；本模式不固定首帧像素'
OLD_PROMISE = '@图片1是已选首帧，维持身份、空间和手位；'
FRAME_PROMISE = '@图片1为起始构图参考，维持已可见身份、空间和手位；'
CRITERION = '按本镜显露顺序核对直接图像参考；未入画者不提前出现，音频只约束声源而不代替视觉身份'


def intent_digest(payload):
    return hashlib.sha256(json.dumps({k: payload[k] for k in FIELDS}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def load_audit(shots=None):
    value = json.loads(AUDIT.read_text())
    if value['format'] != 'story-video-input-audit-v1':
        raise ValueError('unsupported video input audit')
    rows = [r for s in value['scenes'] for r in s['shots']]
    by_id = {r['shot']: r for r in rows}
    if len(rows) != len(by_id):
        raise ValueError('duplicate reviewed shot')
    if shots is not None:
        if set(by_id) != {r['object_id'] for r in shots}:
            raise ValueError('reviewed video inputs must cover every current shot exactly once')
        for row in shots:
            decision = by_id[row['object_id']]
            if decision['reviewed_intent_sha256'] != intent_digest(row['payload']):
                raise ValueError('shot intent changed; review the input decision: ' + row['object_id'])
            states = {s['object_id'] for s in row['payload']['states']}
            if any(v['state'] not in states for v in decision.get('supplements', [])):
                raise ValueError('supplement is not an exact state of this shot: ' + row['object_id'])
    return by_id


def frame_plan(plan, decision):
    result = copy.deepcopy(plan)
    if decision.get('first_frame'):
        lines = [line for line in result['prompt'].splitlines() if not line.startswith('本镜起始裁切：')]
        result['prompt'] = '\n'.join([*lines, '本镜起始裁切：' + decision['first_frame']])
    return result


def video_plan(plan, decision, supplement, media_type):
    """Keep audio/action prose and existing exact selections; add reviewed images."""
    result = copy.deepcopy(plan)
    original = [i for i in result['inputs'] if not i.get('relation', {}).get('object_id', '').startswith('mr-video-input-')]
    if not original or media_type(original[0]) != 'image':
        raise ValueError('reviewed route requires its authored starting image first')
    original[0]['use'] = FRAME_USE
    added = [supplement(v) for v in decision.get('supplements', [])]
    result['inputs'] = [original[0], *added, *original[1:]]
    for item in result['inputs']:
        item['role'] = {'image':'reference_image', 'audio':'reference_audio', 'video':'reference_video'}[media_type(item)]
    result['execution'] = copy.deepcopy(EXECUTION)
    result['parameters']['task_type'] = 'reference'
    # Fail rather than quietly overriding a separately authored fixed route.
    if result['parameters'].get('generate_type') not in (None, 0):
        raise ValueError('fixed route needs an explicit new production decision')
    prompt = result['prompt'].replace(OLD_PROMISE, FRAME_PROMISE)
    lines = [line for line in prompt.splitlines() if not line.startswith(('生成方式：', '参考输入职责：'))]
    descriptions = ['@图片1只提供起始构图与已可见内容。']
    descriptions += [f'@图片{i}：{item["use"]}。' for i, item in enumerate(decision.get('supplements', []), 2)]
    descriptions += ['各图是直接普通参考，后显内容按动作先后入画；不把参考图拼贴进首图，不把音色当视觉身份。']
    result['prompt'] = '\n'.join([lines[0], '生成方式：普通参考生成；起点和逐镜身份仍须实际原件审阅，不承诺固定首帧。',
                                 '参考输入职责：' + ''.join(descriptions), *lines[1:]])
    criteria = result['output']['review_criteria']
    if CRITERION not in criteria:
        criteria.append(CRITERION)
    return result
