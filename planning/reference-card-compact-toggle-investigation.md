# 参考候选小卡补修的当前依据

## 用户决定与原始输入

用户在 2026-10-13 明确要求为已完成的 task-20261013-0004 发布补充修复任务：保留原素材小卡边框与宽高；原「尚未选定原件」行替换为更小的候选按钮，超宽横滑；按钮 hover 预览、去掉独立预览按钮；点击选择，再点取消。只定义与发布，不执行修复或恢复持续 Review。

原始截图 `user-reference-card-01.png` 为本会话用户提供的 PNG，292 × 134，12960 字节，SHA-256 `d808bd0774428ad73abd025a82bcbec20b05afaa8f9700179dc7ebf806f4ae80`。从本会话准确用户消息提取原始字节，未重画或缩放；通过本任务媒体清单提供。图中 M2624「周家米铺 · 空间布局参考」有缩小的内卡、额外外框、「已选候选 1」文字、大号候选按钮与独立预览按钮。

## 本轮实际页面观察

在当前本机正式 `http://127.0.0.1:3000/` 的 Chrome 中打开视听制作，第 1 集 AS001 / ASH001，查看默认主机位 M2973 的生成方案和参考素材。M2624 显示已选候选 1；相邻 M2627 显示「请选择候选」；二者都出现收缩为窄条的原小卡、外部更大的包装框与独立预览按钮。左侧原素材列表的正常小卡保有标题和状态两行，可作单层外观对照。

本轮只打开、阅读并滚动看了该页面；没有在正式服务点击选择或取消，没有试听/播放，也没有修改正式数据。取消能力的判断来自下述接口源码，不能算交互修复已实测。执行者必须在隔离环境完成真实写入与多媒体交互验收。

调查时故事 HEAD `ef08d4bc853f9808a06b5847be2f97fb299e7edf`，审阅台 HEAD `ade295c4a1ae32f6dccdbd9da4f3d85ac3c536fb`。执行基线以实际开始/恢复时最新主干为准，不冻结到这些调查提交。

## 当前实现与正常对照

以下路径以审阅台仓库为基准，行号只作调查定位，执行时核对最新源码。

- `review_desk/static/unified-cards.js:8-20`：原 `reviewSmallCard`，标题/图标/编号与状态行。原参考小卡尺寸需结合 0004 之前的样式在相同容器下对照，不能以有缺陷的外包卡作为基准。
- `review_desk/static/unified-review.css:299-307`：`.reference-picker-card` 新增边框/内边距；其内原卡被改为无边框、2px padding、无最小高度；候选行 `flex-wrap:wrap`；候选按钮最小高度32px；独立预览按钮最小高度30px。
- `review_desk/static/reference-candidate-picker.js:65,104,118-130`：额外 picker/status/choices，删除原状态文字后追加状态，独立预览按钮和多原件分支。第45行对同候选同原件直接 return，是旧 UI no-op。
- 同文件第72-86行：当前 hover 直接预览图像，音视频借独立按钮进入。去掉独立预览入口后必须完整承接可操作播放器，不能仅删除按钮导致声音不可预览。

## 可复用的准确取消能力

`review_desk/production_operations.py:160-197` 已有 `POST /api/production/shot-reference` 的取消路径：相同 `requirement_id/index/input_key/material_id/expected_content` 下明确传 `candidate:null`，退回同一素材需求的引用，清理 `component_id/crop/range/sha256/material_selection/旧selection_state` 并设 `unselected`；保留 `use/role/relation/necessity` 等槽位属性，仅修改当前输入。

第184行附近 `preserve_bounds:true` 同原件保存 no-op，及第8-38行操作重放保护仍有价值。用户明确再次点击已选候选是新的取消操作；网络重试不是第二次点击。取消清掉原件绑定范围后，再选不应静默复活旧范围。

## 旧交付、查重和相邻工作

0004 账本 completed，回执与验收见 `production/reference-candidate-picker/VERIFICATION.md`、`.runtime/task-receipts/task-20261013-0004/`。原规范 `planning/reference-candidate-picker-task.md` 中候选换行、独立预览、同选 no-op 已被本次用户决定修正。原有正确能力（消费者/槽位隔离、准确原件、范围、历史快照、请求幂等）保留。

0004 既有样例可复用但不能冒充本轮已重新实测：M2974 有 M2973 零候选、M2544 两候选、M2623 单候选；M2974 与 M2714 对 M2544 的选择独立；M2669 有候选2原件0–5.6秒片段；多原件与视频由隔离夹具补足。

发布前账本未完成仅 0005 与 0006。0005「全站素材参考合理性核查与既有候选复用表达」并不承担本次卡片尺寸与交互补修，但旧组合验收包含同候选再点击 no-op；本任务明确其 UI 动作已被用户最新要求取代，同时保留 API 保存和重试幂等。0006「基础流程与 SKILL 按创作职责重构，并保持连续阅读」不重复本目标。开发可隔离并行，正式共享发布串行，集成复验两任务的共同选择行为。
