"""Update the existing extraction method from the current authoritative rules.

This adapter appends one method and its binding. It never changes old executions
or the bindings of concurrent video work, and does not generate any media.
"""
import copy
from pathlib import Path


def update(store, root):
    from review_desk import methods
    row = methods.read(store, 'method.skill.material-assessment')
    payload = copy.deepcopy(row['payload'])
    marker = '## 基础职责直接归实体'
    paragraph = (Path(root) / 'production/current-candidates/README.md').read_text().split(
        '实体自身稳定的基础制作职责直接归实体', 1)[1].split('\n\n', 1)[0]
    rule = '实体自身稳定的基础制作职责直接归实体' + paragraph
    body = payload['files']['SKILL.md']
    if marker not in body:
        body = body.replace('## 由真实需求决定必要状态', marker + '\n\n' + rule + '\n\n## 由真实需求决定必要状态')
    else:
        start = body.index(marker)
        end = body.index('\n## ', start + len(marker))
        body = body[:start] + marker + '\n\n' + rule + '\n' + body[end:]
    payload['files']['SKILL.md'] = body
    payload['files']['references/current-production.md'] = (
        Path(root) / 'production/current-candidates/README.md').read_text()
    changes = {}
    if payload != row['payload']:
        saved = methods.save(store, {'category': 'skill', 'name': 'material-assessment',
            'expected_version': row['version'], 'payload': payload})
        changes[row['object_id']] = {'before': row['revision_id'],
            'after': saved['revision_id'], 'version': saved['version']}
    else:
        saved = row
    binding = methods.read(store, 'method.binding.material-assessment')
    rules = copy.deepcopy(binding['payload'])
    for item in rules['rules']:
        if item['object_id'] == row['object_id']:
            item['revision_id'] = saved['revision_id']
    if rules != binding['payload']:
        changed = methods.save(store, {'category': 'binding', 'name': 'material-assessment',
            'expected_version': binding['version'], 'payload': rules})
        changes[binding['object_id']] = {'before': binding['revision_id'],
            'after': changed['revision_id'], 'version': changed['version']}
    return changes
