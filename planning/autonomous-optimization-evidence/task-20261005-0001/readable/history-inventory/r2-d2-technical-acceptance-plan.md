# D2 纯技术实体采纳与并发验收方案

本方案只补 D2-05 的真实过期页与许可边界，不创建或认可故事实体。**五记录种子已于2026-10-05 16:06:59 +0800准备成功，尚未执行采纳、关系变更或浏览器验收。** 主协调授权独占技术库写入且停止62609服务；完成后已释放写入窗口，未自启服务。前后回执为`../technical-readiness/d2-seed-receipt-before.json`、`../technical-readiness/d2-seed-receipt.json`。

## 实例与最小输入

复用 `technical-readiness/fixture_tools.py::instance_path` 的目录、标记和非符号链接校验。建议在现有 `technical-readiness/instance` 新增全新技术 ID；先由主协调停止62609服务，保留其现有采用、判断与下载证据，不重建或删除此实例。已有 `build_fixture.py` 在目录已存在时会拒绝，**它不会自动添加实体**，不可直接重跑覆盖。已实现`../technical-readiness/seed_d2_fixture.py`，五记录单批validate_only确认全库不变后单批导入；原有各表行逐行保留、FK无错误，CALL/ASSET/JUDGMENT未改。验证历时0.017秒，30秒强制上限未触发。

只需五条新记录，所有标题和正文注明“可丢弃技术验收，不是作品采纳”，来源引用当前技术分集 `technical-script-e1` 的实际修订、`technical-scene-source`/`tone`，不能照抄旧基准哈希：

| 技术 ID | 记录类型 | 必要内容 |
| --- | --- | --- |
| `technical-d2-object` | ENTITY | 道具 `prop/hand_prop`，无别名，事实为纯技术测试物；production_description留空，确保只测试内容采纳。 |
| `technical-d2-peer` | ENTITY | 第二个纯技术道具，用于合法实体关系端点，不使用真实人物。 |
| `technical-d2-state` | STATE | 完整状态 `state_model=complete-v1`，entity精确引用主对象；structure/condition/contents/placement四维分别用中性测试说明，reference_media=audio。当前契约使用STATE，不存在需新造的FORM类型。 |
| `technical-d2-relation` | RELATION | relation_type=entity，entities为两个准确实体引用；direction=forward、category=use、basis=script、label“技术关联一”，sources和applies_to指向技术来源。 |
| `technical-d2-need` | REQUIREMENT | 准确scope为该STATE，slot=overall、required=true、media_type=audio、usage=post_audio，entities/states精确绑定；specification.reference_role=overall。没有generation方案，明确内容采纳不授予生成许可。 |

使用既有 `ProductionTest.spec` 的记录形状和 `production.import_records`，先分批 `validate_only=True` 再实际导入，保留准确父引用。不要调用 `ProductionTest.setUp()` 或 `setup_plans()` 向现有实例灌入“songbook/歌本”等测试默认内容。不生成/导入新媒体、CALL、ASSET或采用关系。新ID任一已存在则拒绝整批，后续修订只允许此白名单对象和准确expected_version。

准备回执至少保存原有对象头/评论/采用/判断清单、新五条payload与实际修订、当前scope，以及 `preparation.complete=false`、`acceptance_mode=content`、`can_accept=true`、`generation.accepted=None`。这是合法的未完成生成方案测试，不是假称生成就绪。既有测试 `test_content_acceptance.py::test_first_incomplete_content_can_cycle_and_restore_without_generation_permission` 证实此最小状态允许内容采纳，当前未运行它。

## 原有入口与真实操作

准备完毕后仍由主协调持62609独占浏览器。原服务脚本可直接复用，不改端口或产品：

```bash
python3 .runtime/autonomous-optimization/technical-readiness/probe_server.py --instance .runtime/autonomous-optimization/technical-readiness/instance --port 62609
```

D2入口使用 `/?workspace=settings.workspace&production_tab=entities&production_entity=technical-d2-object&production_object=technical-d2-object`。`navigation.js:83` 已静态确认 entities 对应实体管理，`entity-review.js:20/78`使用 production_entity；该URL是按现有契约构造，尚未实际打开。也可从制作设定→实体管理→技术对象正常进入。

1. 两个真实页面A/B先读取同一技术实体，均 `decision_version=0`、content模式。主协调顺序操作两个标签，不并发抢浏览器。
2. A点“采纳”应POST201，按钮写后变“取消采纳”，新技术决定v1。B保持旧内容，点击旧“采纳”应POST409“采纳记录已有变化”，不得覆盖A。当前UI没有采纳理由草稿：实际验收待确认提示、保留实体/状态上下文、按钮不能盲目重试。不要硬套P2的“理由输入仍保留”断言。
3. B重新打开技术实体，按当前决定取消→201/v2，再采纳→201/v3。核对历史accepted/revoked/accepted、previous_decision链及准确scope；原件/作品数据不变。
4. 在未完成方案下，三个操作之后 `generation.accepted=None`，need readiness仍不ready，CALL/ASSET/采用关系计数不增加。内容采纳不等于允许调用生成或采用已有媒体。
5. 需要再补关系变化冲突时，先取消采纳并打开待采纳页面，持同一decision_version；由主协调串行经合法import只修改 `technical-d2-relation.label` 为“技术关联二”，expected_version=1。旧页面再采纳应因准确scope变化409，判断历史不增加；重开后显示新关系。这样区分“决定版本过期”和“内容范围过期”，不借真实故事关系变更制造冲突。
6. 选择旧实体/状态或历史采纳记录时按钮应禁用，准确旧内容仍可读。此路径可和现有后台许可测试复用，不新增权限系统或自动修改故事实体。

页面现有POST把actor固定写成“用户”，没有操作者输入框。保留真实请求和产品字段，不改请求绕过UI；报告必须明确这几条来自**纯技术夹具的代理操作，不代表真实用户或故事作品认可**，不能根据该字段推断评论作者。后台辅助导入使用 `Codex technical fixture; not user acceptance` 等明确操作说明，但不改已生成UI回执的事实。

## 兼容与验证边界

现有 `generation.decide` 首先检查decision expected_version，然后按scope校验当前ENTITY/STATE/requirements/relationships；服务对Conflict回409。旧页面失败后entity-review.js保留待确认状态、禁重复提交，要求重新打开核对，并没有通用编辑草稿。因此期望以当前契约为准，不为测试改产品。

小型新增夹具和必要针对性检查只在性能窗口外执行，准备者与最终审查者分开。真实UI POST、保存后按钮/计数、冲突提示及旧scope历史需浏览器留证；只读SQL用于核对精确版本与无覆盖，不能替代页面。保留所有旧技术对象及历史，不导出到正式库、不推送生成包、不产生付费媒体。

## 已准备的受限关系变化命令

此命令尚未执行。主协调先停止62609，保留浏览器旧页面；执行后重启同一服务，再让旧页提交。脚本核对成功种子回执、五对象准确v1、纯技术标记和原关系label，只将关系v1的“技术关联一”改为“技术关联二”；不更新决定或作品。

```bash
python3 .runtime/autonomous-optimization/technical-readiness/seed_d2_fixture.py --instance .runtime/autonomous-optimization/technical-readiness/instance --action advance-relation --output d2-relation-change-receipt.json
```

本覆盖审查者是种子脚本实施者，最终写入安全由另一位审查者复核，不把自验回执当独立验收。
