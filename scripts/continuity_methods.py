"""Maintain six continuity handoffs in the actual bound methods, atomically.

Input is an active isolated instance, never the installation seed. The caller
owns publication of the resulting exact registry and formal write window.
"""
import argparse
import copy
import json
import re
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
按完整场景和前后场的真实故事顺序设计，连续性问题令 `need_editing=true`；按实际问题另取调度、表演和声音章节。`understanding` 锁定必须保留的事件与人物关系，`principles` 说明连续动作、反打、时空省略和声音跨镜的选择。`design` 写清计划起落状态，以及观众何时看见足以理解下一反应的证据：谁先伸手、谁看见伤或污损、为何收回或停话。接触、反应、对白和离场分别留时间，必要时调整时长或拆镜，不以旧镜长删掉因果。信息前移后连读后段去重；合理段落省略不机械补运镜。`handoff` 指出谁取得实际原件与确认边界；`review` 逐对回读，连同跨场持续状态，不以全剧无问题概括代替覆盖。
""",
    'image-plan': """
仅镜头画面专项承担相邻镜的可行起点和关键状态参考。以 `need_editing=true` 取得剪辑章节，按需取调度；角色、场景和道具母版继续按各自用途处理。先区分稳定身份与当场伤、污损、干湿、持物，明确哪个可见部位承担后续反应；干净母版不能证明临时状态，也不能用衣服污点替代皮肤伤势。无需每帧露出，但再次显露时须可追踪。共同正文不把所有图像变成前镜尾帧的复制，瞬时状态不因此自动新造实体。镜头专项交接见本包 `references/shot-image.md`。
""",
    'video-plan': """
普通同场切镜、反打、连续动作和声桥有衔接问题时都令 `need_editing=true`；不依赖延长案例。`draft` 分清计划末态、已有准确候选实态与拟用切点，明确完整输入各自的身份、状态、空间和声音职责。时间线写出可见的主动动作、观察与反应：未交接要停在哪一步，指定次数的动作接触哪里、如何分开，停话怎样在眼神与身体上读出。检查收起又打开等回环是否有新动机；有意犹豫可保留。`review` 顺演全时间线、核实际接口负载及跨镜关系，先解决原词重复、状态矛盾和空间突现，再交接。`result` 给出完整 Prompt、参数、准确参考及真实候选仍须验证的范围；不要求每镜运镜或串行喂回全部邻镜。
""",
    'generation-preflight': """
涉及衔接时令 `need_editing=true`，按问题取调度／声音章节。`draft` 从实际完整原件核身份、当场状态和参考职责，分开计划落点、可用候选实态与拟用出入点；完整视频总长与当前模式限制也须相容，不能截取参考以绕过完整原件要求。相同母版与未变输入可复用已完成的检查，但不继承未做过的看听。若执行依赖缺失的邻镜原件，`review` 明确准确缺项及恢复动作，阻断该执行；其他独立制作继续。实际状态冲突先作最小调整。`result` 保留真实提交、回收和待验范围；超时先区分上传失败、提交未知与已受理，只有确证未发送生成且阻断条件已改变时，才沿原调用身份有界恢复，不另开身份重复付费。
""",
    'result-review': """
按拟用真实切点把准确候选接上必要邻镜，原速连续看听；连续性令 `need_editing=true`，声音问题令 `need_sound=true`。`draft` 固定覆盖与原件，`review` 记录观众实际可读的状态、动作次数、接触部位、主动者和支撑归属：空斗不证明拍底，手碰到书不等于接稳，音轨存在不等于停顿有表演。静帧、模型辅助、技术校验、直接动态、直接听觉和用户意见分别注明来源。补录异常按手册把原声、认可母版、独立补录与最终混音同响度、同上下文实听；可用原声优先，不预定根因。先查设计、参考、切点和混音，源片不足再局部补制。`result` 给同窗前后对比及受影响后续状态；未能看听的明确未验，不能用播放器播完或输入 current 代签。旧接受与新问题各保留准确边界。
""",
    'episode-editing': """
先读剪辑章“跨镜声画连续性”。`sample` 冻结实际工程和原件，按时间线确定覆盖；`draft` 逐段明确实际出入点及跨镜声音，不把计划落点或原片尾部当作成片事实。相近构图出现位置跳变时，先比较保留必要事件的切点、景别和进入过程；合理叙事省略保留，不强加运镜。`review` 覆盖实际接缝、每场和整集，检查指定动作是否完整、信息是否重复、台词停顿是否有画面反应；局部插入及同一原片多次使用分别核验。换原声或补录时回听完整上下文、音色、嘴形和接缝，转写时间戳超界或漂移不得直接作为字幕依据。时长或拆镜变化同步所有声音、字幕、人名条和新旧映射；定向重验受影响项，保留未变证据。`result` 交两版成片、PCM 混音、字幕、工程和来源映射及同窗对比；必要动作、原词与后果不能为遮缺陷被删掉。
""",
}

# Keep the detailed procedure in the handbook; each stage owns its handoff.
TAIL_FRAME_HANDOFFS = {
    'audiovisual-scene': '同场连续动作要延续站位、持物或伤污时，在 handoff 指定由谁核前镜实际尾部、何时交给下镜方案；前镜尚未产出时保留计划与实态复核的区别。反打或合理时空省略不机械继承同一构图。',
    'image-plan': '镜头画面需要衔接实际状态时，按视频手册“前镜尾帧如何成为下镜参考”优先检查并使用合适的前镜尾部画面；它承担状态，干净母版承担身份与风格。新视角另设计起点，派生图保留准确来源与谱系。',
    'video-plan': '连续画面按视频手册“前镜尾帧如何成为下镜参考”选择实际出点与参考角色：前镜尾帧用于下镜开头时是首帧职责，普通参考不冒充硬性首帧。draft 说明下一动作与允许改变的构图，review 核派生出处、接口组合和动作方向，result 留后镜实际接缝待验。',
    'generation-preflight': '尾帧派生输入按视频手册核准确候选、画面出点、取帧位置、派生图哈希及实际提交角色；前镜或切点改变后重新核对，不把音轨末端当画面末端。清楚但动作阶段错误的帧不能放行，首帧与音色等输入组合以真实接口能力为准。',
    'result-review': '使用尾帧参考的候选仍须按视频手册比较实际前镜出点与新镜入点，核动作是否重做、跳过或停滞；同一参考图或相似姿态不证明运动与声音连续。先区分端点选择错误、参考职责不足和生成偏离，再决定最小返修范围。',
    'episode-editing': '工程若为后镜制作提供尾帧，按视频手册分别交出实际画面出点、原件映射与跨镜声音；前镜候选、裁切或出点变更后，沿已有参考和检查记录定向复核下游派生图及接缝，不把旧尾帧自动沿用，也不无条件重生成全部后镜。',
}

SHOT_HANDOFF = """
## 相邻镜的起点与参考交接

把本镜第一动作的前提和计划落点分别写清：谁在画内或画外、持物手与落位、姿态及伤湿等持续状态。已生成邻镜时回查准确候选的实际可用范围；只有计划时标为计划，不凭文字发明已发生的末态。连续画面优先检查前镜实际出点附近能读清关键状态的画面，按本步骤取得的视频手册“前镜尾帧如何成为下镜参考”选择直接承接或重新设计新视角起点，保留取帧来源。身份母版、场景空间、动作姿态与拟用边界各有参考职责，不要求一张图同时承担全部约束，也不为每个反打机械新增所有人物参考。把不可能的起点先修正，再提交视频；真实候选及成片切点仍须各自检查。专业原则沿本步骤按需取得的剪辑章节。
"""


def append_section(body, section, text):
    if section in body:
        raise ValueError('此方法已有同名交接；回读实际版本后再修订，不能重复追加')
    return body.rstrip() + '\n\n' + section + '\n' + text.strip() + '\n'


def replace_section(body, section, text):
    matches = list(re.finditer(r'^' + re.escape(section) + r'\s*$', body, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError('修订须找到唯一已有章节；先回读当前方法')
    start = matches[0].start()
    following = re.search(r'^## ', body[matches[0].end():], re.MULTILINE)
    end = matches[0].end() + following.start() if following else len(body)
    return body[:start] + section + '\n' + text.strip() + '\n\n' + body[end:].lstrip('\n')


def migrate(store, root, revise=False):
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
                update = replace_section if revise else append_section
                p['files']['SKILL.md'] = update(p['files']['SKILL.md'], HEADING,
                    prose + '\n' + TAIL_FRAME_HANDOFFS[name] + '\n' + CONTRACT)
                if name == 'image-plan':
                    title, text = SHOT_HANDOFF.strip().split('\n', 1)
                    p['files']['references/shot-image.md'] = update(
                        p['files']['references/shot-image.md'], title, text)
                for ref in p.get('resources', []):
                    if ref['object_id'] in resources:
                        ref['revision_id'] = resources[ref['object_id']]['revision_id']
                additions = []
                if name in ('image-plan', 'generation-preflight'):
                    additions.append(('filmcraft-execution', 'editing', {'need_editing': True}))
                if name == 'generation-preflight':
                    additions += [('filmcraft-execution', 'staging', {'need_staging': True}),
                                  ('filmcraft-execution', 'sound', {'need_sound': True})]
                if name in ('image-plan', 'video-plan', 'generation-preflight', 'result-review', 'episode-editing'):
                    when = {'need_editing': True}
                    if name == 'image-plan':
                        when['material_category'] = 'shot-image'
                    additions.append(('video-handbook', 'continuity', when))
                for resource, section, when in additions:
                    ref = {**methods.reference(resources['method.resource.' + resource]),
                           'section': section, 'when': when}
                    if not any(all(old.get(k) == ref.get(k) for k in ('object_id', 'section', 'when'))
                               for old in p.setdefault('resources', [])):
                        p['resources'].append(ref)
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
    parser.add_argument('--revise', action='store_true', help='Revise the existing handoff sections without duplicating them')
    args = parser.parse_args()
    if args.receipt.exists():
        raise SystemExit('回执已存在；先核对当前准确方法，不重复运行迁移')
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    store = Store.open_existing(args.instance / '.runtime/review.sqlite3')
    try:
        result = migrate(store, ROOT, revise=args.revise)
    finally:
        store.close()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
