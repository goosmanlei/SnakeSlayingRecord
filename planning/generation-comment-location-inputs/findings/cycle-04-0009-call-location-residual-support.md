# task-20261010-0009：CALL 评论回查的局部残留支持证据

task-20261010-0009 已在任务账本 completed（revision 3）。根 Review 在相同交付代码的 49297 隔离副本中，确认原件看审、图像反馈与判断正常；但技术 Prompt 评论回查的限定路径未通过独立复验：定位后额外出现左侧整份生成内容、错误缺项提示，并只框出整段 Prompt，没有指出所选句子。根决定另行发布后续任务，汇聚为“从原件回查准确技术意见”的完整目标；不恢复 0009。本辅助不发布、不执行，也未亲自操作浏览器。

## 准确现场与保留的数据

- 环境：49297，审阅台 `ac735586575f3a0bdd319ae95d23acd188285117`，用途为 `isolated_review_exercise`。正式数据未由本辅助修改。
- 原件 M1612：`asset-fg3-crossbeam-eight-image-04@2ccaa3a630d81b9729277ae9131c7801889031c65e64c3318bf5f123b6ade660`。
- 技术意见 C283：`9654e70d-b935-403c-8b81-ee2ea58d9743`，准确对象 `call-fg3-crossbeam-eight-image-04@dabee604f4cc373e1b8bb47573dcd96fde044c675af3973ac810bc41bd574081`，块 `@review/call/prompt`，字符范围 1375–1409，引用“No hanging rope, no post bindings.”。身份与实操由根提供。
- 本辅助只读调用当前 `/api/production/entity-review?entity_id=entity-crossbeam`：M1612 的 `state=null`，`review_state` 为 ST140 v1 `form-crossbeam-eight@8a7f693c532aa2cb8ff04bbd1ca060ba0a1416dae97cd0310dd1152b9de88db9`，准确旧状态完整记录在该素材的 `associated_states`；API 顶层 `retained_states` 此时为空。实体 ASSET 定位分支可将匹配的旧状态加入前端保留列表，根 DOM 已显示“历史保留”。这是准确旧状态，不应替成当前 v2。
- 同一素材的 `review_context.call` 准确，`review_context.inputs` 完整返回 EN058 v1、ST140 v1、M1392 v1、M1405 v1。四项引用、组成和裁切信息保存在 [小型来源证据](../evidence/cycle-04-0009-call-location-support.json)。右侧原卡也由根实际读到这四项；不能将左侧提示解释为真实记录丢失。

## 已闭合的局部原因链

以下源码路径均相对通用审阅台仓库，依据为上面的准确提交。

1. `review_desk/static/entity-review.js:380` 的 `locateEntityReviewComment` 针对 CALL 先找同一 `review_context.call` 的素材，然后只用 `item.state` 找状态。M1612 的真实旧归属在 `review_state`，因此此分支无法得到 `form`，设置 `data.historicalCall=row`。相比之下，该文件开头的状态素材过滤以及 ASSET 评论分支使用了 `state || review_state`，并支持保留状态。
2. `entity-review.js:266` 在实体基础信息和关系之后，将 `historicalCall` 渲染为 `renderActualGeneration(root,{call:data.historicalCall,inputs:[]})`。实体 EN058 没有被换掉；左侧额外插入了一份 CALL。右侧统一素材卡仍呈现 M1612 和完整 `review_context`，于是同一 CALL 有两个文本表面。
3. `material-review.js:101` 的 `materialInputs` 从传入记录或全局生产索引中寻找准确修订。左侧回退明确传入空 `inputs`，不能用这次调用完整的准确历史记录，因此出现“准确输入记录或文件组成缺失／版本未知”。右侧传入四项完整记录，显示正确。这是本次回退上下文不足，未证明底层缺数据。
4. `material-review.js:75` 的 `materialField` 将完整 Prompt 放进一个 `PRE[data-block-id]`。`materialTextSurface` 和 `production.js:344` 的 `focusProductionReview` 可让同一准确修订的多个表面都持有 `id=production-blocks`。
5. `production.js:429` 的 `productionCommentTextNode` 在全页 `#production-blocks [data-block-id]` 中取第一个匹配块；CALL Prompt 没有分段偏移，范围值不参与句内绘制。`paintProductionReview` 只给该元素加 `comment-flash`，其 CSS 是整元素外框。`locateProductionComment` 也滚动到这一元素。左侧先于右侧，因此根观察到左侧整个 2806 字符 PRE 加框，右侧对应 PRE 未加框且留在下方。
6. `locateEntityReviewComment` 末尾会为所有匹配块打开祖先 `DETAILS`，所以右侧细节确实展开；这不能证明滚动和高亮落在右侧原卡的准确选句。根另外记录了收起右侧详情后左侧副本仍留在页面，符合这个独立渲染分支。

## 既有机制、正常对照与 0009 验收边界

0009 前基线 `34da92041a1ceba624ee8b1d1fe94a7dab1fe774` 到本次 `ac735586…`，`production.js`、`entity-review.js`、`unified-cards.js` 均无差异。上述回退与首项定位实现已在前基线存在；0009 修改的是 `material-review.js` 的原件生成细节折叠，以及 `production-breakdown.js` 的工程文件/文字交接默认阅读。因此有证据说这是本次交付仍保留的既有机制，不能称 0009 新造的回归。没有在旧版浏览器重跑，不能把源码对照写成旧版实操。

可复用的正常机制也已经存在：`production-breakdown.js:69` 的素材用途评论使用 `blockMarks`／`renderBlock`，按原字符范围绘制 `.comment-mark.selected` 并定位；`app.js:680`、`:699` 依据准确对象、修订和 start/end 切分文字，`screenplay.js:213` 的剧本文字定位优先滚动到所选标记。它们是源码层面的正常对照，辅助没有在本次浏览器另行验证，也不据此宣称所有其他评论无问题。根此前图像区域反馈与准确对象保存正常，范围局限于当前 CALL 文本回查。

0009 规划验收第 4 条明确要求：“定位折叠技术段的已有评论时，必要区域自动展开并准确高亮；保存后重开／定位回原处。”执行者 `production/original-judgment-layout/VERIFICATION.md` 说明使用自有隔离 CALL 夹具，没有真实旧技术评论样本；其夹具文件 `.runtime/task-20261010-0009/evidence/technical-comment.json` 选中开头 0–25 字符。辅助实际查看其 `technical-comment-location.jpg`，该图同样显示左侧整段 Prompt 橙框和右侧原卡生成细节。故执行者证据支持“准确 CALL 可打开、原锚点保留”，不足以支持“只指明原选段、无重复错误呈现”。根的真实原生圈选 C283 补足了这一验收差异。

现有单测覆盖详情折叠状态、返回位置及历史 CALL 的准确身份；所读测试没有覆盖此准确 `state=null / review_state=历史状态` 的重复表面与句内高亮组合。没有为本辅助运行或新增测试。

## 后续范围建议与保护边界

最小可审目标是：从 M1612 原件评论回查这句技术意见时，保留原素材和准确历史 CALL，在原有技术详情内展开、滚动并明确标出原句；四项真实输入可继续查看，返回原件不产生另一份缺上下文内容。这是同一次回查操作的两个相连残留，适合一个后续目标。

不应改写评论锚点、历史 CALL 或输入；不应用 ST140 当前版本修补旧调用；不改变图像判断、采用、候选或原件。保留直接 CALL／真实历史独立页的必要读取能力；没有对应原卡的历史 CALL 仍须诚实可读，不能简单删除所有回退。按普通 CALL、历史原件 CALL 与已有用途/剧本文字评论做必要对照即可，不据此扩展全站评论重做。

本辅助交付的是源码、API 和已有验收资料的原因澄清。根负责实际使用结论、后续任务发布与独立复验。当前没有修复，也没有把执行者 completed 等同于本轮全面复验通过。
