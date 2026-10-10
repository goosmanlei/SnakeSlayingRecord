"""Append current comment-led methods; preserve all frozen definition history."""
import argparse
import copy
import json
from pathlib import Path
import sys

REPLACEMENTS = {
    '当前参考及用途认可': '准确参考及用途说明',
    '上游变动则新建步骤并复核影响，不改旧回执': '新上游版本不改变旧步骤的准确引用；决定改用新输入时新建步骤并复核影响，不改旧回执',
    '参考、文字、采纳和渠道任一不满足': '准确参考、文字、输入锁和渠道任一不满足',
    '真实生成另过准备、采纳和调用授权': '真实生成另过准确输入准备和调用授权',
    '缺原词、原件、认可或输入锁': '缺原词、原件或输入锁',
    '真实生成仍须重新通过既有采纳、原件、渠道、额度和许可检查': '真实生成仍须重新通过准确输入、原件、渠道、额度和许可检查',
    '新输入／上游变化须新建步骤': '改用新输入须新建步骤；仅出现新的上游版本不使有效旧引用失效',
    '现有准备包、采纳、准确原件、原词、能力和本次授权': '现有准备包、准确原件、原词、能力和本次授权',
    '结构采用沿已有审阅流程；小说作者固定一个具体结构版本，之后逐片段写作并更新真实连续性。方法执行回执不代替用户选择，不自动产生故事认可。': '小说作者在任务授权内明确选择一个具体结构修订，固定该准确输入后逐片段写作并更新真实连续性。作品意见沿评论理解和整改，不要求逐项批准；方法执行回执不代表用户的质量判断。',
    '检查点、读者意见与人工采纳各有边界': '检查点、读者意见与准确版本选择各有边界',
    '既有素材的认可不能自动转授新用途': '既有素材的意见不能自动适用于新用途',
}
WORKFLOW = '''\n## 意见、修订与回查\n\n动笔前读取所选准确修订及其相关原评论；历史意见连同原文、作者、发生时间和范围理解，不把沉默推成质量认可。AI 自检、机器检测与用户反馈分别记录。对意见作出实际修改后，通过现有 comment-handling-v1 回应保存原评论及版本、处置说明、实际新修订和必要文字／画面／时间锚点；未修改则说明依据和边界。读者可从原意见对照原文、实际修订与上下文；不改原锚点，不把旧意见冒充新稿意见。关闭或重开评论只是整理讨论，不是后续工作的批准或阻断条件。\n\n方案在授权内按准确输入、真实原件和质量检查推进，不要求逐对象审批。素材选择继续固定准确版本、候选、组成及片段；改用新输入须重读并更新方案依赖，冻结调用不换输入。缺失、已撤回、错配、无效参数或循环仍按真实约束处理。付费、正式写入和部署仍遵守本次任务授权。\n'''


def update(store, root):
    from review_desk import methods
    before = {r['object_id']: r for r in methods.export_registry(store)['records']}
    changed = {}
    # The authoritative Markdown remains in this project. Only its registered
    # reading projection and the explicit current bindings advance.
    for oid in sorted(before):
        row = methods.read(store, oid)
        payload = row['payload']
        if payload['format'] != methods.FORMATS['resource'] or not payload.get('source'):
            continue
        spec = {'name': oid.removeprefix('method.resource.'), 'title': payload['title'],
                'expected_version': row['version'], 'sections': {}, 'preserve_paths': True}
        for section, filename in payload['sections'].items():
            source = payload['source']['files'][filename]
            spec['sections'][section] = {k:source[k] for k in ('path','section') if k in source}
        # Resources with generated references paths retain their established layout.
        spec['preserve_paths'] = all(name == payload['source']['files'][name]['path'] for name in payload['sections'].values())
        if payload.get('companions'):
            spec['companions'] = payload['companions']
        methods.sync_source(store, root, spec)
        new = methods.read(store, oid)
        if new['revision_id'] != row['revision_id']:
            changed[oid] = new
    for oid in sorted(before):
        row = methods.read(store, oid)
        if row['payload']['format'] != methods.FORMATS['skill']:
            continue
        payload = copy.deepcopy(row['payload'])
        for filename, body in payload['files'].items():
            for old, new in REPLACEMENTS.items():
                body = body.replace(old, new)
            payload['files'][filename] = body
        name = oid.removeprefix('method.skill.')
        if name not in ('comment-polish', 'comment-polish-clear', 'creative-system-review', 'reader-review') and '## 意见、修订与回查' not in payload['files']['SKILL.md']:
            payload['files']['SKILL.md'] = payload['files']['SKILL.md'].rstrip() + '\n' + WORKFLOW
        for ref in payload.get('resources', []):
            resource = methods.read(store, ref['object_id'])
            if ref['object_id'] == 'method.resource.filmcraft-execution' and ref.get('section') == 'animation':
                ref['section'] = 'animation-ai'
            ref['revision_id'] = resource['revision_id']
        if payload != row['payload']:
            methods.save(store, {'category':'skill','name':name,'expected_version':row['version'],'payload':payload})
            changed[oid] = methods.read(store, oid)
    for oid in sorted(before):
        row = methods.read(store, oid)
        if row['payload']['format'] != methods.FORMATS['binding']:
            continue
        payload = copy.deepcopy(row['payload'])
        for rule in payload.get('rules', []):
            rule['revision_id'] = methods.read(store, rule['object_id'])['revision_id']
        if payload != row['payload']:
            methods.save(store, {'category':'binding','name':oid.removeprefix('method.binding.'),'expected_version':row['version'],'payload':payload})
            changed[oid] = methods.read(store, oid)
    return {oid:{'before':before[oid]['revision_id'],'after':row['revision_id'],'version':row['version']} for oid,row in changed.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import methods
    store = Store(args.database)
    try:
        changed = update(store, Path(__file__).resolve().parents[1])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(methods.export_registry(store), ensure_ascii=False, indent=2)+'\n')
        print(json.dumps(changed, ensure_ascii=False, indent=2))
    finally:
        store.close()

if __name__ == '__main__':
    main()
