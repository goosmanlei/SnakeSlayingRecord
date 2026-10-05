# UX001–003 增量契约审查

当前前端差异未发现新的阻断性契约问题。对最新源码运行的 25 个既有 Node 套件共 355 项通过、0 跳过，进程退出码 0，Node 记录执行时长 277.779 毫秒。原始输出见 `UX001-003-incremental-node.log`。本项由监督者独立执行，不修改产品。主协调暂停浏览器后授予 ≤60 秒测试窗口；结果回报时已释放，不与后台 A/B 或浏览器测量并发。

这些测试验证当时最新源码中的原有阅读、评论、准确版本、导航和弹窗上下文契约；其 DOM 夹具没有真实宽度、字体布局、caret/Range 几何和原生手势。因此不能把通过 355 项写成新可见行恢复算法或四入口原生点击已经验收。其后的外点事件阶段改动及增量测试见本文末尾。无需为收尾重复全套 Python。

## 按变更对应的检查

| 变更 | 本次既有自动回归 | 仍依赖根代理的实际浏览器证据 |
| --- | --- | --- |
| UX001 宽屏为评论留空间、按可见原文恢复 | `reading_context`、`source_navigation`、`structure_scroll`、`structure_navigation`、`comment_location`；评论持久化、存储失败、清理、拒绝及 `story_workspace_drafts` | 采编、结构、剧本在 1440 和 1200 宽度的可见原文及选中评论不遮挡；连续开合无逐行漂移；图片位置保留；窄屏不新增预留；面板进入素材弹窗后外页不预留；输入外 Esc 收起与输入内取消语义。已完成的同一候选证据可复用，不需重做。 |
| UX002 全历史生成结果文案 | `material_review`、`material_navigation`、`material_title`、`material_streamlining`、`ui_material_independent`、`asset_list_labels`、`generated_display_labels` | “有结果／无结果”及列表文案与含历史版本范围一致；旧版本有原件、当前准备版本无原件时，准确大卡仍显示当前状态，不把历史原件借给当前版本。根报告中的阿禾版本 1/2 样本适合此项。 |
| UX003 四类弹窗触发器保留外层评论 | `entity_material_navigation`、`production_navigation`、`ui_unification_compatibility`、`ui_unification_requirements`、`entity_review`、`production_adoption`、`production_reference_names`、`shot_sound_comments`，以及以上结构与素材套件 | 结构放大图、提示词准确引用、本镜素材卡、非中央关系节点：原生 pointerdown 不先关闭评论，再打开弹窗，返回恢复外层准确目标、草稿与可见状态；关系节点的双击与键盘操作保持；普通空白外点仍关闭评论。 |
| PERF002 单出口复制内容图 | 先前独立 67 项 Python 和两组档案失败/精确恢复补验已通过，见 `AO-PERF-002-independent.md` | 独立 A/B 与受影响页面相同条件复测；页面正确性不能仅由接口内容哈希推出。存储源码未变时不重复这 67 项。 |

测试文件名以上均省略 `.test.cjs`。本次测试没有直接断言新增 `reviewDialogTrigger` 标记，也没有构造 `preserveCommentReaderLine` 的真实几何分支；四个新增标记经静态核对均落在实际创建的交互元素上，既有 pointerdown 处理器通过最近的标记祖先识别它们。该修复对象是**打开弹窗前原评论面板被提前收起**，不是新弹窗自身被事件冒泡关闭。

本次源码 SHA-256（静态目录）：`app.js` 为 `9a3e2394f62b605cae200560944ad2f4036c7e74490464177b99fb68c3811967`，`navigation.css` 为 `f62a96150aa21748b7b83137f1cb329b142e3f1925db725ad22c8f19ff4b5b7b`，`structure.js` 为 `477c1620990e0fbd163e9b8c873a5017e31cc981dbac14b0bf34e442d4238dc5`，`entity-relations.js` 为 `7bc2477821dd603715dccd33ed3f05684be4fd9189b99fce8eed0d13d1fe7c3b`，`production-breakdown.js` 为 `4b7f06ca0588fe323003c9fed737f32384e17f830669dcb74c69670cd97d3d6d`，`unified-cards.js` 为 `b57ca50498379d0907e427f62dee97d93eee0b7f46eb106ba9ca06e4dac16c03`。

## 文档与前置成果归属

已对照当前 diff 检查 `README.md`、`docs/comment-checklist.md`、`docs/materials-and-relationships.md`、`docs/production-breakdown.md`。素材结果新文案准确区分全历史列表和准确版本大卡；宽屏评论规则明确 1200 像素边界及素材弹窗例外。逐镜布局、场顶部不重复共用素材以及 Schema 6/旧实例 Schema 5 的变更是修正过时文档，不是本轮新增布局、迁移或导出能力。故事运行报告的 DOC-001 已明确这一点，未见将前置成果冒记本轮的表述。

## 收尾时优先补齐

1. 保留 UX001 几何证据与 UX003 四入口真实事件结果；只运行静态或 Node 测试无法封闭这两项。
2. 隔离功能库内的评论提交/编辑/定位、采纳与取消、配置写后可见和并发冲突、实际音视频预览仍依赖根安排；不能向性能快照写入试验数据。
3. C2 首屏变慢信号、PERF002 增量收益及受影响页面回退必须按相同条件解释。数据不足时记未证实或未关闭，不以 6 小时时长或自动回归通过替代质量收敛。
4. 最终报告将已通过的 PERF002 正确性与本次 355 项补齐，原始日志之外保留读者可理解的结论。候选无新代码/数据变化时复用证据，不为收尾重复测试。

## 外点事件阶段改动后的增量审查

主协调随后在真实浏览器发现首击按钮落空：pointerdown 先关闭面板，宽屏布局随之变化，点击目标在 click 产生前移走。产品处理现已改为 pointerdown capture 仅记录 `commentAction`，click capture 再处理外点关闭；若同一指针动作在 pointerup 创建新草稿，则保留该尾随 click 前刚打开的面板。键盘 click（detail 为 0）不使用陈旧的指针状态。原先冒泡前能拦截的 dialog、review-cue 及准确弹窗触发器均显式豁免。

监督者独立静态审查无阻断发现，仅新增 `tests/comment_outside_click.test.cjs`。该文件调用真实 init、closePanel 和 startDraft，按 document capture→目标回调→bubble 顺序触发事件，保持实际评论动作计数和本机草稿元信息；只替换无关页面渲染。8 项场景包括：

- pointerdown 不改变评论布局；click capture 先收起，原目标回调仍能开启新草稿且没有被 preventDefault/stopPropagation 吞掉。
- pointerup 创建区域草稿后，尾随 click 保留准确 anchor、草稿键与元信息；下一次真实外点仍能正常收起。
- 键盘 detail=0 忽略旧 pointerdown 与新评论动作之间的计数差，仍执行当前目标动作。
- dialog、review-cue、material-reference、显式弹窗触发器的后代元素保留原评论及草稿；普通面板内部点击不收起，普通外点收起但不删除草稿。

主协调暂停浏览器并授予 ≤30 秒窗口。新增 8 项与 7 个相关既有套件合计 143 项通过、0 跳过，125.966 毫秒，退出码 0，结果回报时已释放窗口。首轮新增测试因夹具尝试重新赋值常量 `renderActiveReader` 失败；仅将夹具改为替换其调用的 `renderDocument` 后通过，没有改产品以适应测试。首轮及通过日志分别为 `comment-outside-click-tests.log`、`comment-outside-click-tests-retry.log`。

本批 `app.js` SHA-256 为 `ef5fce982c7c3ad4eb65f95820c55d9ae17b1e6f6c5aec10de36b4ab4445a340`，新增测试为 `c56b12a6d2d4fa204114f377de7ef309b132b12eb315f2f3d610cba0e68d64e5`。测试覆盖事件顺序，不替代原生 hit testing 或布局几何。根代理另回报了原生区域拖选、真实区域评论提交/定位、整体意见首击及准确文字圈选证据；其真实性及具体页面结果以根保存的浏览器证据为准，本审查没有冒用浏览器操作。
