"""Append current production method definitions; keep past execution facts."""
import copy
from pathlib import Path

REPLACEMENTS = {
    '素材选择继续固定准确版本、候选、组成及片段': '素材选择固定准确候选、组成及片段',
    '实际新修订和必要文字／画面／时间锚点': '实际修改说明、内容摘要和必要局部前后片段',
    '新上游版本不改变旧步骤的准确引用；决定改用新输入时新建步骤并复核影响，不改旧回执': '准备期间上游当前内容改变时重新读取并另起步骤；已经提交的调用继续使用自身快照，不改旧回执',
    '改用新输入须新建步骤；仅出现新的上游版本不使有效旧引用失效': '制作步骤以准备时内容摘要核对输入；改用新输入须新建步骤，真实调用使用已固定快照',
}


def update(store, root):
    from review_desk import methods
    from review_desk.production_current_methods import WORK_TYPES
    changes = {}
    for entry in methods.export_registry(store)['records']:
        oid = entry['object_id'];row = methods.read(store, oid);payload = copy.deepcopy(row['payload'])
        if payload['format'] != methods.FORMATS['skill'] or not (set(payload['work_types']) & WORK_TYPES):continue
        for filename,body in payload['files'].items():
            for old,new in REPLACEMENTS.items():body=body.replace(old,new)
            payload['files'][filename]=body
        rule = (root/'production/current-candidates/README.md').read_text()
        payload['files']['references/current-production.md'] = rule
        body=payload['files']['SKILL.md']
        marker='## 当前制作内容与候选'
        if marker in body:body=body[:body.index(marker)].rstrip()
        payload['files']['SKILL.md']=body+'\n\n'+marker+'\n\n执行前阅读 references/current-production.md。制作对象原地维护，步骤摘要不保存全文历史；只有实际提交保存候选所需完整快照。草稿、回读、自检及完成仍按本方法的必要步骤执行。故事域版本不受此规则影响。\n'
        if payload!=row['payload']:
            changed=methods.save(store,{'category':'skill','name':oid.removeprefix('method.skill.'),'expected_version':row['version'],'payload':payload})
            changes[oid]={'before':row['revision_id'],'after':changed['revision_id']}
    for entry in methods.export_registry(store)['records']:
        oid=entry['object_id'];row=methods.read(store,oid);payload=copy.deepcopy(row['payload'])
        if payload['format']!=methods.FORMATS['binding']:continue
        for rule in payload['rules']:
            if rule['object_id'] in changes:rule['revision_id']=changes[rule['object_id']]['after']
        if payload!=row['payload']:
            changed=methods.save(store,{'category':'binding','name':oid.removeprefix('method.binding.'),'expected_version':row['version'],'payload':payload})
            changes[oid]={'before':row['revision_id'],'after':changed['revision_id']}
    return changes
