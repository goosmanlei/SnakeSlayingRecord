# AO-UX-003：放大及关系弹窗入口提前收起评论

这是应修的既有连续性问题。当前真实浏览器记录显示，S2 第 8 稿已打开评论时点击照片，照片弹窗内的 `panelHidden` 已经是 `true`。事件原因不是 Esc：打开入口的 pointerdown 先冒泡到文档，将它当作面板外点击；后续 click 才创建弹窗，Esc 只能关闭弹窗，无法恢复此前已经收起的面板。

本代理只做静态代码及已有证据审查，没有操作浏览器、发请求、执行测试或修改产品代码。该问题由主协调发现并真实复现，独审补全同类入口与修复范围。

## 依据及基线归属

- `browser/S2-photo-zoom.json`：结构照片大图已出现；图像 complete=true，原始尺寸 1536×1024，路径 `/assets/lantern-structure-v7-site.png`，面板 hidden=true。第 8 稿引用第 7 稿命名原件本身不是串版本证据，应以准确稿件引用为准。
- `browser/AO-UX-001-structure-image-cycle.json`：开关评论前后图像位置及 reader scrollTop 相等，说明之前的避让循环验证成立；这份文件没有放大返回后的面板状态，不能拿它否定新发现。
- 基线系统提交 `b874b959af9c918a482e8488dc25cb0204ab5772` 的 `app.js:845–848` 已有相同的外点关闭器，只豁免 `.material-reference,[data-review-dialog-trigger]`。基线 `structure.js:158–161` 的实际放大图像只带 `aria-haspopup=dialog`，缺少该 dataset；`review-ui.js:141–152` 的弹窗创建、Esc 阻泡及关闭焦点恢复与当前相同。故这是本轮发现的基线既有问题，不是本轮评论避让引入的回退。
- `docs/comment-checklist.md:46,84` 已规定大图 Esc 只关大图，关闭大图不连带关闭原评论面板。无需推断新的用户偏好或提出改变工作方式的取舍。

## 所有实际调用入口

| 入口 | 原有防护与判断 | 此轮最小处理 |
| --- | --- | --- |
| `structure.js` 的 `renderStructureVisual(..., true)` | img 无标记；用于结构图、照片，以及 `materialMedia` / 制作预览共用图片。S2 已真实复现。 | 在创建实际可放大的 img 时设置 `dataset.reviewDialogTrigger=''`。 |
| `production-breakdown.js` 的 `renderLinkedPrompt` | 有效的 `.prompt-reference` 在 click 调 `openMaterialReference`，pointerdown 未豁免。静态同根因，待真实验证。 | 仅给存在实际输入的链接设置标记；缺失引用仍为普通文本。 |
| `production-breakdown.js` 的本镜素材／视频小卡 | click 调 `openUnifiedMaterial`，进入函数时保存的 hidden 可能已经变成 true，关闭大卡也会还原成关闭。静态同根因，待真实验证。 | 仅给该调用点的 `materialSmallCard` 返回按钮设置标记，不改全站 `reviewSmallCard`。 |
| `entity-relations.js` 的非中央关系节点 | 双击才开大卡，第一次 pointerdown 已可关闭面板。静态同根因，待真实验证。 | 仅给有打开行为的非中央节点设置标记；中央节点不改。 |
| `materialReferenceLink` 的按钮 | 已带 `.material-reference`，并阻止 pointerdown/focusin 冒泡。 | 无需重复修改。 |
| `material-review.js` 的参考弹窗内部图片 | 图片未带标记，但父 dialog 已阻止 pointerdown 冒泡，因此不触发文档外点关闭器。 | 未证明同样问题，不为一致外观扩改。仍须真实嵌套图像回归。 |
| `openMaterialPlanHistory` | 由评论定位路径调用；按钮在评论面板内，`panel.contains` 已豁免。 | 不新增无依据的恢复逻辑。 |

## 已实现 diff 独审

主协调按上述前四类入口分别加了一处 dataset，独审已核对准确 diff。属性选择器按属性存在匹配，空字符串值有效；标记在 DOM 创建时就存在，早于第一次 pointerdown。图片仍受原 drawMode / structureDrawing 防误放大约束，真实圈选需回归。SVG 关系节点子元素通过 `closest` 能到带标记的 g；仍保留双击和键盘激活行为。

未改普通选卡、非触发器区域、全局外点关闭、Esc 或任何关闭后强制重开逻辑。未改故事、版本、评论锚点、数据库或 API。修复在源头保留进入弹窗前的面板状态，已关闭的评论不会被新逻辑主动打开。

静态未发现该 4 处 diff 的高影响问题。不能仅在 `openReviewDialog` 内标记 trigger：调用发生在 click 时，第一次 pointerdown 已过去。也不应在关闭大图时无条件打开评论，避免制造此前未打开的面板或跨上下文恢复。

## 仍需主协调的真实验收

四类入口逐一测试打开前后／关闭后的面板、准确上下文和草稿；S2 照片与 SVG 需各测鼠标打开、Esc／关闭按钮返回，记录原阅读位置。素材大卡和关系大卡需测面板搬入／归还、嵌套返回和慢请求关闭。普通空白处仍应收起且保留草稿，圈选模式拖动不能误放大。没有原始证据的路径保持待验，不把静态同根因写成已复现或已验收。
