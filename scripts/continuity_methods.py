"""Append six continuity handoffs to the actual bound methods, atomically.

Input is an active isolated instance, never the installation seed. The caller
owns publication of the resulting exact registry and formal write window.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile

from approach_foundation import sync_handbook_resource
from method_migration import configuration_registry, restore_configuration

ROOT = Path(__file__).resolve().parents[1]
HEADING = '## 跨镜声画连续性的本步骤职责'
CONTRACT = """
检查结果沿当前方法的 `review`／`result` 阶段保存，不新建永久连续性实体。声明本步覆盖的镜头或接缝标识，逐项记录计划／原片／剪辑层级、准确依据、观察、结论、检查者与读取方式。关键原件缺失写明缺项和补齐后的继续动作；未生成计划的后续媒体义务不能假装已经履行。依据变化后以新步骤复验，不改写旧阶段。

需要机器回查覆盖及变更时，在阶段 JSON 的 `checks` 中使用系统 `method-checks-v1` 契约：`coverage` 列范围，`items` 列实查结果；`basis` 保存准确选择、所读值与摘要。计划使用本次判断所依赖的字段；成片接缝使用准确工程相邻片段和上下文范围，连同相关声音轨与候选原件。摘要只用于检查依据变更。现有阶段回读返回待复核项；`GET /api/methods/checks?object_id=...` 回查该对象的历史使用处。`current` 表示所选依据未变，不代表质量通过、原件仍可访问或用户接受；原件可用性继续由生成／剪辑前检确认。
"""

RESPONSIBILITIES = {
    'audiovisual-scene': """
按完整场景和前后场的真实故事顺序设计，连续性问题令 `need_editing=true`；按实际问题另取调度和声音章节。阅读剪辑章节“跨镜声画连续性”后，`understanding` 锁定必须保留的事件，`principles` 说明连续动作、反打、时空省略和声音跨镜的选择，`design` 写清计划起点／落点与人群、道具、持续状态，`handoff` 指出哪个后续步骤取得实际原件及确认边界。`review` 逐对回读，连同跨场留下的状态；不以全剧无问题概括代替覆盖。
""",
    'image-plan': """
仅镜头画面专项承担相邻镜的可行起点和关键状态参考。遇到这类问题，以 `need_editing=true` 取得新增剪辑章节，按需取得调度章节；角色、场景和道具母版继续按各自用途处理。共同正文不把所有图像变成前镜尾帧的复制。镜头专项交接见本包 `references/shot-image.md`。
""",
    'video-plan': """
普通同场切镜、反打、连续动作和声桥有衔接问题时都令 `need_editing=true`，取得剪辑原则与手册衔接章；不依赖 `case=extension` 才触发。`draft` 分清计划末态、已有准确候选实态与拟用切点，明确身份／空间／动作／声音由哪些完整输入承担。`review` 检查全时间线是否可演、邻镜是否矛盾、必要动作或词句是否重复或丢失，先解决方案与实态冲突。`result` 交付完整 Prompt、参数、准确参考职责和候选／成片须继续验证的范围。参考、固定首帧、视频参考或延长均按本次实际能力和表达选择，不要求串行喂回全部镜头。
""",
    'generation-preflight': """
涉及衔接时令 `need_editing=true`，按问题取调度／声音章节。`draft` 核当前计划和准确原件，分别标明计划落点、可用候选实态、拟用出入点；从实际文件核对身份、状态、参考职责及声画输入，不能只读文件名或 Prompt。若本次成立依赖一个缺失的邻镜原件，`review` 明确缺哪个候选／组件及恢复动作，沿既有 blockers 阻断该执行；未生成镜的计划检查和其他独立工作继续。实际末态与计划冲突先确定最小调整，不能按冲突输入盲交。`result` 保留真实提交／回收，交给结果检查的准确候选与必须连续看听的范围；超时仍沿原请求查询，不重复付费提交。
""",
    'result-review': """
按拟采用的真实切点，把准确候选接上必要邻镜，原速连续看听；连续性令 `need_editing=true`，声桥令 `need_sound=true`。`draft` 固定覆盖与原件，`review` 记录实际发生的动作、人数／身份、持物／持续状态和声音，分别判断原片可用性与这一剪接关系。静帧、模型分析、技术校验、直接动态看听和用户意见各保留来源。确认问题先查设计／参考／切点／混音，源片不足再局部补制；`result` 用同一上下文窗口作前后对比，回查受影响场与后续状态。旧候选接受不抹去新问题，旧未验也不自动推翻接受。
""",
    'episode-editing': """
先读剪辑章“跨镜声画连续性”。`sample` 冻结本次实际工程和原件，按时间线排序而非素材编号确定覆盖；`draft` 明确每个实际出入点与跨镜声音，区别计划落点和原片尾部。`review` 覆盖全部实际接缝、每场与整集；反打、局部插入、多次使用同一原片也逐一检查。对合理省略或转场说明依据；必要动作、原词与后果不能为掩盖缺陷而删掉。改候选、顺序、出入点或声音后定向重查，保留其余仍适用的证据。`result` 在需要换片时同步两版成片、PCM 混音、字幕、可编辑工程及来源映射，并交付同窗前后连续对比；无必要变化保留原件，不以“换了版本”代替修复。
""",
}

SHOT_HANDOFF = """
## 相邻镜的起点与参考交接

把本镜第一动作的前提和计划落点分别写清：谁在画内或画外、持物手与落位、姿态及伤湿等持续状态。已生成邻镜时回查准确候选的实际可用范围；只有计划时标为计划，不凭文字发明已发生的末态。身份母版、场景空间、动作姿态与拟用边界各有参考职责，不要求一张图同时承担全部约束，也不为每个反打机械新增所有人物参考。把不可能的起点先修正，再提交视频；真实候选及成片切点仍须各自检查。专业原则沿本步骤按需取得的剪辑章节。
"""


def append_section(body, section, text):
    if section in body:
        raise ValueError('此方法已有同名交接；回读实际版本后再修订，不能重复追加')
    return body.rstrip() + '\n\n' + section + '\n' + text.strip() + '\n'


def migrate(store, root):
    from review_desk import methods
    from review_desk.store import Store
    before = configuration_registry(store)
    with tempfile.TemporaryDirectory(prefix='continuity-methods-') as temp:
        stage = Store(Path(temp) / 'review.sqlite3')
        try:
            restore_configuration(stage, before)
            resources = {}
            for name in ('filmcraft-execution', 'video-handbook'):
                old = methods.read(stage, 'method.resource.' + name)
                p = old['payload']
                spec = {'name': name, 'title': p['title'], 'expected_version': old['version'],
                        'preserve_paths': name == 'filmcraft-execution',
                        'sections': {key: {k: v for k, v in p['source']['files'][file].items()
                                          if k in ('path', 'section')} for key, file in p['sections'].items()}}
                if name == 'video-handbook':
                    spec['sections']['continuity'] = {'path': 'production/seedance-video-handbook.md',
                                                       'section': 'continuity'}
                    new = sync_handbook_resource(stage, root, spec)
                else:
                    spec['companions'] = copy.deepcopy(p.get('companions', {}))
                    new = methods.sync_source(stage, root, spec)
                resources[new['object_id']] = new
            catalog = methods.catalog(stage)
            changed = {}
            for name, prose in RESPONSIBILITIES.items():
                old = methods.read(stage, 'method.skill.' + name)
                p = copy.deepcopy(old['payload'])
                p['files']['SKILL.md'] = append_section(p['files']['SKILL.md'], HEADING, prose + CONTRACT)
                if name == 'image-plan':
                    p['files']['references/shot-image.md'] += '\n' + SHOT_HANDOFF.strip() + '\n'
                for ref in p.get('resources', []):
                    if ref['object_id'] in resources:
                        ref['revision_id'] = resources[ref['object_id']]['revision_id']
                additions = []
                if name in ('image-plan', 'generation-preflight'):
                    additions.append(('filmcraft-execution', 'editing', {'need_editing': True}))
                if name == 'generation-preflight':
                    additions += [('filmcraft-execution', 'staging', {'need_staging': True}),
                                  ('filmcraft-execution', 'sound', {'need_sound': True})]
                if name == 'video-plan':
                    additions.append(('video-handbook', 'continuity', {'need_editing': True}))
                for resource, section, when in additions:
                    p.setdefault('resources', []).append({**methods.reference(resources['method.resource.' + resource]),
                                                         'section': section, 'when': when})
                new = methods.save(stage, {'category': 'skill', 'name': name,
                                          'expected_version': old['version'], 'payload': p})
                changed[old['object_id']] = {'before': methods.reference(old), 'after': methods.reference(new)}
            for binding in catalog['binding']:
                p = copy.deepcopy(binding['payload'])
                for rule in p['rules']:
                    if rule['object_id'] in changed:
                        rule['revision_id'] = changed[rule['object_id']]['after']['revision_id']
                if p != binding['payload']:
                    new = methods.save(stage, {'category': 'binding',
                        'name': binding['object_id'].removeprefix('method.binding.'),
                        'expected_version': binding['version'], 'payload': p})
                    changed[binding['object_id']] = {'before': methods.reference(binding), 'after': methods.reference(new)}
            registry = configuration_registry(stage)
            restore_configuration(store, registry)
            return {'changes': changed, 'registry_sha256': registry['sha256']}
        finally:
            stage.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.exists():
        raise SystemExit('回执已存在；先核对当前准确方法，不重复运行迁移')
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    store = Store.open_existing(args.instance / '.runtime/review.sqlite3')
    try:
        result = migrate(store, ROOT)
    finally:
        store.close()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
