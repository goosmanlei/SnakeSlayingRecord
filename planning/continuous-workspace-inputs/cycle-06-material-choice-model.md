# M2544 的“准确素材版本”弹窗混淆了当前需求与实际候选

> 这是原调查记录；其中阶段状态、推断和旧运行入口只解释取证时点。当前目标、授权、必要附件与执行基线以[任务正文](../continuous-workspace-task.md)及[交接索引](README.md)为准。

结论：这两个按钮不是同一需求的两个业务版本，也不是卡片所称的两个候选。第一项是 M2544 的当前素材需求，第二项是其候选 1 的真实原件 M1133。当前数据已把二者放入同一个 M2544 工作区；暂未发现 0008 对该对象的归并映射遗漏。问题发生在素材管理的范围入口：后端把用途证据中的不同记录收为可打开引用，客户端却统一要求人“选择准确素材版本”。应回到一份当前方案与真实候选的共同阅读方式，不能为去掉弹窗删除旧 CALL、原件或原评论。

## 本次现场与准确对象

负责人在 0008 正式发布后，从 AE001/AS001 进入素材管理，看到 35 项素材、20 项有结果；点击“阿蘅 · 图像身份参考 M2544，候选 2 个”出现两项选择。截图由负责人保存为 [任务原图2](README.md#media-2)。本辅助调查未操作浏览器。

本轮只读 `GET /api/production/materials?episode=av-e01&scene=av-e01-a01&scope=av&grouped=1&compact=1`，返回同样的 35 项/20 项，M2544 的两个 `scope_references` 如下：

| 弹窗显示 | 数据身份 | 本轮确切含义 |
| --- | --- | --- |
| 阿蘅 · 图像身份参考 · 记录修订 4 · 准确用途 | `REQUIREMENT`，M2544，`material-entity-a-heng-identity` | 唯一当前需求/方案；`current_content=true`。4 是该记录的修订/并发计数，不是供人选择的第四套制作方案 |
| 阿蘅 · 首轮整体候选 · 记录修订 2 · 准确用途 | `ASSET`，M1133，`asset-fg3-aheng-image-01` | 真实历史调用的候选原件；`current_content=false`，有准确 `candidate_id`。2 是原件记录修订，不是 M2544 的方案 2，也不是候选 2 |

两项的用途类型均为 `business_relation`。本例不是“一个当前计划输入和一个真实 CALL 输入”恰好混在一起，而是关系用途收集到当前需求及其真实候选，再被表面当作版本选择。

`production_candidate_targets` 已将 M2544 的真实候选顺序确定为：候选 1＝M1133（首轮整体候选），候选 2＝M1190（点名后日常形态首轮派生候选）。所以列表的“候选 2 个”与弹窗的“两个按钮”只是数量巧合，含义完全不同。

## 最短因果链

以下源码路径以配套审阅台仓库为基准。

1. `review_desk/production_scope.py:74–84` 将需求或原件的用途归入统一素材身份，保留具体 `evidence.record`；`:120–122` 会读取本场的业务关系端点。保留准确证据本身有用途。
2. `review_desk/ui_projection.py:154–164` 遍历符合场次的用途证据，以 `revision_id` 去重生成 `scope_references`，附带记录标题、`version` 和用途，却没有把“当前需求”与“候选原件”区分为不同阅读目标。
3. `review_desk/static/management-cards.js:146–151` 只要引用超过一条，就把它们统一放进“选择此范围的准确素材版本”，按钮一律拼接“记录修订 N”。`business_relation` 又没有对应人话说明，退回“准确用途”。
4. 两项都被加上 `defaultSelection:true`；`static/unified-cards.js:177` 把 REQUIREMENT/ASSET 的目标统一设为 `current`，`:186` 会转到同组当前方案。负责人随后在正式新基线实测第二项“首轮整体候选 · 记录修订 2”：加载后仍为 M2544 当前方案，URL 的 `material_target=current`、`production_revision=01fc3a…` 与第一项一致，确实没有进入候选 1。本辅助调查用源码解释这个结果，不代称自行操作过页面。

这不是只把“版本”改名为“用途”便可解决：普通列表已经确定了 M2544，人要阅读其方案和候选，没有必要先辨认内部记录。当前引用的技术准确性应由打开后的当前方案/候选选择承接；只有从具体旧调用、原评论或准确素材引用进入时，才按那个准确目标直接定位。

## 候选比较也是同一阅读路径的断点

负责人在 M2544 实际比较了两张图，并确认候选 1 的 C284 原意见保留。两图均为青绿衣阿蘅全身四分之三侧向：候选 1 抱本提袋，候选 2 空手、双手在身前相合；这些既有单视角结果不是当前新计划要求的三视图。比较面板仍称“版本 1 · 候选 1/2”；点“审阅此准确候选”只打开 M1133 的图像和下载窗口，没有方案或评论，返回大卡的候选 1 后才可继续读生成快照和评论。这是负责人的实际操作证据，不扩展为对当前三视图方案或新生成效果的认可。

源码对应 `static/material-review.js:393–411`：比较标签拼接 `round.number`，审阅按钮使用通用 `materialReferenceLink`；该函数在 `:590–592` 转到 `openMaterialReference`，`:678–696` 只把需求/实体/状态等导向统一工作区，ASSET 图像进入原件预览分支，评论会话仅为音频/视频创建。因此当前“审阅”按钮实际上执行了图像参考预览。

共同目标应是：普通素材列表直接进入 M2544；比较中选择审阅候选 1，则在同一素材的准确候选工作区读 M1133、其生成快照和原评论，并能返回原比较位置。已有大卡候选 1 能做到后半段，应复用该路径，不新增候选审阅实体，不把所有仅为看参考图的预览窗口扩成大卡。“版本 1”属于当前单方案容器的旧展示用语，可以去掉；但只改标签仍不能消除多余选择和审阅断路。

## 归并是否漏了，与正常入口对照

分别读取 M2544 与 M1133 的准确 `GET /api/production/card`：两者都返回 `material_versions` 唯一键 `material-entity-a-heng-identity`；其中只有一个 `state=current`、`current_content=true` 的容器，内含当前 plan 与 results，`legacy_material_versions` 为空。M2544 返回当前需求，M1133 返回真实候选身份；没有两个可编辑当前方案。

正式库也已登记原阿蘅青衣、点名后形态及对应旧 `current-plan-*` 到 M2544 的语义归并映射；旧 current-plan 对象明确指向 `merged_into`。本例证据支持“列表入口仍按多条准确记录让人选版本”，不支持为它重新做一次数据归并。

本场正常对照是 **M2974 / ASH001 首帧**。同一列表接口只返回它自己的一个 `scope_reference`，类型为 `composed_requirement`。负责人已关闭 M2544 后从素材列表实际点击 M2974：直接打开实体与素材详情，镜头首帧 Tab 选中，显示 M2974 当前方案，没有准确版本选择；随后读了完整 Prompt 及 10 个已归并的参考需求。它有 0 个候选，本对照证明范围列表已有直接进入一项当前需求的可用路径，不比较尚未生成的媒体质量。

对比 0008 前的 desk `4ec278dfff70e187b01f0c1f349e8d379717e4da` 与当前 `123e7d00912414d4ca1241a03ad5e91ee9d18622`，`management-cards.js` 未变，`ui_projection.material_list()` 也逐字相同。0008 对 `production_scope.py` 的变化是跳过撤回记录、准确读取旧调用输入，没有改变上述“引用多于一条就选版本”逻辑。这说明它沿用了旧入口契约；不能仅据代码未改就声称旧正式数据必然出现过完全相同的弹窗。

## 去掉多余选择时必须保留什么

M1133 原件仍由 `call-fg3-aheng-image-01` 产生，候选身份为 `candidate-c06e1e5e62f167c09ef59a1cb017e8f778d439c52667194470fb049167420183`。正式提交快照为 `origin=historical`，保留 1 份当时需求、2 份输入内容和当时模型、参数、Prompt 等请求，`gaps=[]`；本次未将元数据完整误称为实际看过原图。

其 **C284「1. 认可；2. 不补」**仍固定在 M1133 修订 `5d47affb0b0e04fd6bf2a9cfeba4e33268958afb862cbedb4a5c5ce24d964e95`，不能迁为 M2544 当前方案或另一个候选的认可。普通列表直接开 M2544 后，应仍能在候选 1 读此原件、原调用和原评论；准确旧链接直接进入该候选时也不能静默改成当前方案。无需新增信息区或恢复旧方案版本树。

本次只做上述具体入口、两项准确卡片、一个列表正常对照与相关历史保护核对。没有全库内容扫描、业务写入、产品修改或任务发布。观察源码身份：primary `c0fb690adcd7c5c73ceac246ca75c8ef6e2b08aa`，desk `123e7d00912414d4ca1241a03ad5e91ee9d18622`；SQLite 用 `mode=ro`，未初始化 Store。M2544 两项落点、候选比较、C284 及 M2974 正常入口均由负责人实际只读操作；本辅助调查只提供源码、准确 API 和数据库证据。

## 同轮追加：旧灯候选查看准确参考后，刷新丢失候选位置

负责人在0008正式版沿 EN089旧灯 → ST240裂缝补纸透暖光 → M2857候选1，实际查看原图，再点击“实际使用的参考”M1135母版原件并关闭。关闭后候选1按钮仍为 `aria-pressed=true`，但地址已变为 `production_object=call-fg3-lantern-lit-image-01`、`production_revision=4eade4…`，`material_id` 和 `material_target` 消失。随后真实刷新并等待加载完成，M2857显示当前方案，候选1不再选中。截图为 [任务原图3](README.md#media-3)。本辅助未操作页面，只核对该实际反例的源码与准确GET响应。

准确数据仍在：M2857为 `material-form-old-lantern-lit-overall`；候选1原件 `asset-fg3-lantern-lit-image-01` 修订 `2474629030a26ea32e6b4d3d61d5778d83a0ef7034c6d1b90aa37db1f2b7d9ed`，候选身份 `candidate-36bfe8100b38cfd20445d58779422ac53b4df5e95d2eab69dcd1955486baa496`。其准确调用为 `call-fg3-lantern-lit-image-01` 修订 `4eade4dd5c5d9405f515ba242c4453fdc6f3df873f3b79e3d655c78a8bdbe807`；输入中的母版是 `asset-fg3-lantern-image-01` 修订 `c04b3877a5421432067f5bb24be40d19bf1af4b1e2325462de2f884df4e2c3af`、`original`组成及全幅裁切。应继续读取该准确输入，不能为修复导航改用母版当前修订。

发生的并非“参考弹窗把父素材替换为M1135”，而是点击参考前后，候选的**生成说明正文将评论焦点提升成了页面目标CALL**：

1. `static/material-review.js:203–220` 用 `materialTextSurface(box,call)` 包住候选参数、实际参考和Prompt。该正文层在 `:35–39` 为 `pointerdown/focusin` 无条件调用 `focusProductionReview(CALL)`。
2. 实际参考小卡由 `:141–152` 创建，虽然标记了 `data-review-dialog-trigger`，但没有像 `materialReferenceLink()` 在 `:590–592` 那样阻止焦点事件向正文传播。外层素材卡在 `:431` 已跳过参考按钮，内层CALL正文未跳过。所以点击参考时能先触发CALL焦点，关闭弹窗时 `static/review-ui.js:176` 将焦点交还小卡，也会再次经过该正文层。
3. `static/production.js:336–349` 把焦点CALL写入 `production_object/revision`，再用 `materialCommentContext()` 查所属容器。后者（`material-review.js:359–364`）只查容器的 `members/definition_records`；当前M2857容器只有当前需求与原件，`definition_records.call=null`，真实CALL保存在候选的 `review_context.call` 中。因此查不到容器，`:345` 删除 `material_id/target`。准确调用没有遗失，是客户端查找范围与当前候选结构不一致。
4. 参考弹窗的共享历史在 `review-ui.js:176–177` 只压入打开时的地址，关闭后返回该地址；地址在打开前就可能已被CALL焦点改坏。原图预览本身并不恢复父候选路由。内存中的 `selectedCandidates` 没有同步改动，解释了关闭后按钮仍选候选1、地址却已丢失候选的分裂状态。

刷新为什么落当前也有对应路径。本轮只读 `GET /api/production/card` 带上述准确CALL及 `entity_id=entity-old-lantern`，返回旧灯实体和正确候选／调用上下文，但没有任何素材容器将该CALL列为成员。`static/entity-review.js:47–67` 因上下文中知道该CALL而接受它，选中的素材容器却为 `null`；`:16–29` 的CALL恢复仅在已有准确素材卡上下文时回填候选，刷新时没有此上下文。`static/unified-cards.js:74–90` 随后使用当前方案作为缺省（`:3–5`），与负责人实际刷新结果一致。不是候选删除，也不能把“内存画面仍在候选1”当作返回完整。

这个反例应纳入同一项“准确候选连续审阅”的验收：在M2857候选1阅读其实际参数、Prompt，打开准确母版原件、关闭，再刷新，仍回到M2857候选1、同一原件和同一生成快照；候选评论／草稿及阅读位置按原对象恢复。鼠标打开、键盘聚焦后打开和关闭交还焦点都应保持该语义。评论可准确针对候选的调用正文，但不能因此清除父素材与候选身份；应复用现有候选工作区和临时参考预览，不新增CALL审阅页面或恢复旧方案版本。此处只说明实际点击链路及源码可见的同类焦点范围，没有宣称已实操所有键盘或Prompt点击情形。
