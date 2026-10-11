# 制作阶段回读与恢复：输入及历史边界

执行定义见 [完整任务](../method-stage-recovery-task.md)。本目录只有本任务必要的 14 份文字/JSON 证据；不是生产输入库、完整方法包或可以直接复放的正式变更包。复制时保持原文件字节，原路径只作来源定位，不要求执行者访问主目录私有预览或旧聊天。

## 怎样使用

先读三份 findings，区分当前压缩契约与旧完整输出；再读 ASH010 的 request、understanding、design 和原阶段回执，核对字符串与结构化值。媒体样例按 record → draft-record → review → final-record → finish-receipt 连读，并与 draft/review 两份服务回执对应。文件的准确相对入口及原始 SHA-256 见下表。

ASH010 请求里的旧目的和样例历史授权是回归输入；正式目的已由 0008 修正，不据此改正式作品。原 run `review-cycle06-ash010` / step `purpose-check-01` 的 understanding 回执只含摘要；本地原理解全文为 711 字符。媒体样例为 `review-cycle06-ash008-video` / `dialogue-02` / `material-av-e01-a02-s03-video`，同一步草稿和定稿有真实文字差异；review-receipt 保留原 assessment，finish-receipt 保留完整定稿及 method_basis。本目录不含独立 result 服务回执；其准确 artifact 引用在 finish-receipt 的 method_basis 中。执行在最新准确隔离实例建立明确标注的回归步骤，不占用原 Review 身份或将旧样例复放到正式库。

澄清阶段只读计算确认：understanding 的规范 JSON 摘要等于原回执 output.sha256；ASH008 draft 的整值及 requirement/generation 摘要、review assessment 的原值及压缩外层摘要均一致，finish 的方案值等于 final-record，三个阶段所指 execution 相同。这仅验证证据内容和归属；没有运行目标 CLI、模拟故障、导入作品或完成恢复验收。规范规则为服务现有 `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))` 后取 UTF-8 SHA-256；文件字节摘要另列，不能混用。

## 已完成成果与本次缺口

| 已核对任务/草稿 | 已有成果或分工 | 本任务的关系 |
| --- | --- | --- |
| task-20261009-0020、task-20261009-0021（已完成） | 方法管理、准确包/绑定、作者与媒体阶段交接和方法库已交付。 | 复用准确方法与输入契约；它们的旧模式实用验收不代替当前六类压缩模式的全文恢复验收。 |
| task-20261010-0005（已完成） | 修复方法包入口、附属资料相对链接及导出/空实例恢复；旧冻结包保持原文。 | 保留 begin 部分交付恢复与旧包兼容，不重做方法阅读包。 |
| task-20261010-0021（已完成） | 制作单份当前稿、提交快照和新步骤摘要已正式生效；完整过程只留有恢复用途的工作区。 | 保持此边界，补客户端未衔接的全文保存、read 与恢复，不恢复服务制作全文树。 |
| task-20261011-0008（已完成；唯一依赖） | 全量实体/素材语义归并、ASH010 正式目的修正与本机正式交付。 | 从该成果之后的最新有效数据隔离验证，不重做归并、不回灌旧错误。 |
| task-20261012-0003（查重时为澄清草稿） | 人的 SKILL 阅读、评论、编辑和所选绑定应用。 | 独立并行，不在本项重做页面；整轮回收再联合验证新方法→创作→工具回读→作品判断。 |
| task-20261012-0001/0002/0005/0006（查重时为澄清草稿） | 分别处理唯一出处、连续审阅、关系图可靠性和素材检索性能。 | 与阶段全文恢复没有相同交付目标；开发隔离、共享正式写入串行，重叠契约按最新主干复验。 |
| task-20261009-0022/0023（已撤销） | 原全剧重做安排已撤下，历史状态回执确认不再执行。 | 不恢复旧任务写入，也不借本任务重做全剧。编号须含完整日期，不能与后来的同尾号任务混淆。 |

查重按主项目任务账本中已完成任务的相关目标、验收及实际完成说明、六个在途草稿的需求说明，以及相关 0003 的完整定义核对，没有可恢复的同目标未完成任务。0008 账本完成时间为 2026-10-12 00:15:38 +08:00；澄清只读核对其正式增量 `8b1b1758c861fe2caa9ca772d36870dfd266b34a68641881a6eb8283b83c3ba8`、最终配置/源码一致回执和正式 Chrome 回执，没有代做独立浏览器验收。用户已确认四小时发现门槛和 0008 复验通过并授权展示后自主发布。

本次源码核对基线：primary `6a14c238d7fb344fc12cf284be68a11d6bc0a409`，desk `123e7d00912414d4ca1241a03ad5e91ee9d18622`，本机 main 与 origin/main 引用分别相同；执行者仍须按执行时真实 upstream、主干和有效正式数据更新。正常对照报告内更早源码身份只表示当时观察。旧执行全文可读、作者实际理解、用户评论整改与媒体效果是不同结论。

原 findings 中未随任务复制的综合调查名、旧 `.runtime/` 回执及端口仅为历史来源，不是必需输入；当前定义和本目录已保留判断及回归所需事实。M3170 的旧完整记录可按随附正常对照末尾 object_id/revision_id 通过现有只读接口取回，方法与专业资料沿项目权威入口取得。本次没有待用户决定的范围问题，具体布局和恢复实现由执行者在上述契约内确定。

## 原件清单

下表来源前缀为主项目 `.runtime/system-review/`，目标链接相对本文件。SHA-256 是复制文件的原始字节摘要。

| 随任务文件 | 原始来源 | 字节 | SHA-256 |
| --- | --- | ---: | --- |
| [findings/cycle-06-stage-scope-final-check.md](findings/cycle-06-stage-scope-final-check.md) | `findings/cycle-06-stage-scope-final-check.md` | 7986 | `d4d3c5cc00d07e5cdb15519642b94b25da7c0614e7bda79d9582b43be4d07636` |
| [findings/cycle-06-method-stage-read.md](findings/cycle-06-method-stage-read.md) | `findings/cycle-06-method-stage-read.md` | 1620 | `8040181820154ea5354e0e3888a9794f64eb94d9c9493d6c33f6aef1501be87b` |
| [findings/cycle-06-method-execution-normal-control.md](findings/cycle-06-method-execution-normal-control.md) | `findings/cycle-06-method-execution-normal-control.md` | 9338 | `416cb28266915c8089966aa9b9ffefc556545a51dcd897fa19e5eed656d9a42d` |
| [evidence/ash010/request.json](evidence/ash010/request.json) | `practice/cycle-06-ash010/request.json` | 23118 | `d1c717855733e5aab05ff31829c6ca7f7b6d694b1708399b0086bda4f53a17fa` |
| [evidence/ash010/understanding.md](evidence/ash010/understanding.md) | `practice/cycle-06-ash010/understanding.md` | 1887 | `7cab450009fe0fb3f621225c6b81010728dc457a9377e57056df7dd3956708d7` |
| [evidence/ash010/design.json](evidence/ash010/design.json) | `practice/cycle-06-ash010/design.json` | 2099 | `0c7320ff02be47a66d0ac13774dc20e8c674a3f364aac09aed5881fd3419bf42` |
| [evidence/ash010/step-01/stage-understanding.json](evidence/ash010/step-01/stage-understanding.json) | `practice/cycle-06-ash010/step-01/stage-understanding.json` | 1051 | `136dc648d7cde008730e8e5cb7c8fed12c6295e33ed02cf6794becb4e1f0a040` |
| [evidence/ash008/record.json](evidence/ash008/record.json) | `practice/cycle-06-ash008-video/record.json` | 9825 | `110cd21d455b3ec78aa3eb6941bc1791ab1b1cf17e26dd69f59fe25fa157d522` |
| [evidence/ash008/draft-record.json](evidence/ash008/draft-record.json) | `practice/cycle-06-ash008-video/draft-record.json` | 9979 | `15a454a7fb685cd8afa7297f6287bff6efae446e08010e3b68e79266a6994f00` |
| [evidence/ash008/review.md](evidence/ash008/review.md) | `practice/cycle-06-ash008-video/review.md` | 2450 | `665e66b26fcded02c24dc247e99c38fc824f1c5e80199aa41c5a78017cda47f4` |
| [evidence/ash008/final-record.json](evidence/ash008/final-record.json) | `practice/cycle-06-ash008-video/final-record.json` | 9949 | `9d7fa0eac3191b44211f2b45abdc99aee02752608fd2acdaadcd47eb62574984` |
| [evidence/ash008/draft-receipt.json](evidence/ash008/draft-receipt.json) | `practice/cycle-06-ash008-video/draft-receipt.json` | 1250 | `6990edba8e183b691f5f56735da212470fd6de909f564e9980f3c86e99b31069` |
| [evidence/ash008/review-receipt.json](evidence/ash008/review-receipt.json) | `practice/cycle-06-ash008-video/review-receipt.json` | 3553 | `fe89c4d2828f6e5dc7f1b2a7bfe13a99f726fe53346399db0787e42691802bc7` |
| [evidence/ash008/finish-receipt.json](evidence/ash008/finish-receipt.json) | `practice/cycle-06-ash008-video/finish-receipt.json` | 10262 | `7370112f8d6370a7b865f2858ba633c1e7394bd7c7ad0769737e8afcc776dc04` |

14 份文字证据均逐字节与源文件一致；不将它们登记成会话媒体。工作区中的试用全文只保留到恢复和验收用途结束，必要交付证据沿项目流程收敛；本任务不建立永久草稿库。
