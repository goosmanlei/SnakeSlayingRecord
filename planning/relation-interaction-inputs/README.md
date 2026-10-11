# 关系图与 Prompt 引用任务交接

[任务正文](../relation-interaction-task.md) 原字节保存全部已定要求。本轮仅整理、登记、发布和回读，未实现、部署或重新操作浏览器，不恢复持续 Review。

## 资料与原件

[用户原话](user-request.md)对应两图；[现场证据](EVIDENCE.md)记录根 Chrome 操作、版本和边界；[调查](investigation.md)定位真实关系与相关代码。[关系样例](graph-samples.json)保存 ASH001／ASH002／ASH006 的准确节点、修订和边；[几何重放](source-geometry-witness.json)仅为共线片段的源码辅助证据，不能冒充浏览器验收。

| 原文件名 | 原始规格 | 用途 |
| --- | --- | --- |
| user-image-1.png | PNG，1637×1319，185844 字节 | AE001→AS001→ASH001 原图的连线重叠、曲线追踪与单／双击对照 |
| user-image-2.png | PNG，1627×1321，585058 字节 | ASH003／M2980 Prompt 遮挡与移除浮卡后准确打开 M2979 的对照 |

本会话 `_media --draft` 返回零个内嵌媒体；上述本地原件通过两项 `--input-file` 随任务发布，字节不转换。没有待跳过的会话媒体；Markdown／JSON 随规划提交，不当作媒体。

[媒体清单](user-media.json)保留原文件名、SHA-256、字节数及 `task_input`。此路径与主项目账本 `inputs[].path` 一样，均相对故事**主项目**，不是当前目录或任务 worktree；受管原件在主项目 `.codex-task/task-inputs/task-20261011-0006/`。在任一故事 worktree 用 `git rev-parse --git-common-dir` 取得共用 `.git`，其父目录即主项目根；读取该根下 `.codex-task/tasks.json` 中本任务的 `inputs`，按路径打开并核对哈希。执行不再依赖根调查临时目录。

任务正文中的 `planning/`、`config/`、`production/`、`AGENTS.md` 从故事工作区根解析；调查已声明的 `review_desk/`、`tests/` 从 desk 工作区根解析。调查所称 `task.md` 已改指向上面的任务正文；原取证提交、样例数量和源码行号不是未来固定基线。

## 查重与版本边界

本轮账本查重：0004 completed，已交付镜头聚焦和真实关系，连线可辨认性仍有本次证据支持的残留；单击直连／双击开卡为新决定。0003 running，相关代码已集成，原要求保留 Prompt 浮卡；本次新决定替代该选择，不改原在途承诺。0005 completed，其工作图无关。完整编号均为 task-20261011-相应尾号。

历史 task-20261006-0002 针对旧实体大卡关系图，现管理图不使用其渲染函数，仅作参考，不恢复旧任务。未见另一草稿或任务完整承担本次两图；dependencies=[]。旧任务收尾、残留与独立复验仍归原任务，本项交付后由原负责人另行独立复验。

根取证 desk 为 `b5d2d821a869767316c32da8cbf1e93c18e6d4aa`。本轮核对 main 已至故事 `c1fc5adb4d0f447d04e53cc2266318e964075416`、desk `fd04dc5d178f36e0c2d7e9a83129ba56aafbddf9`，工作区干净且与本地 upstream 引用一致；相关 `entity-relations.js`、`production-breakdown.js`、`material-review.js` 未变。这里只核对 Git，不宣称新版本已通过 Chrome；执行／恢复仍从最新两仓主干与有效正式数据开始。

## 两仓与并行边界

| 仓库 | source（相对主项目） | 已核验身份／目标 | 写范围 |
| --- | --- | --- | --- |
| primary | `.` | goosmanlei/SnakeSlayingRecord，main | 规划、准确实例引用、必要验证与发布／恢复交接 |
| desk | `../story-review-desk` | goosmanlei/story-review-desk，main | 图布局／交互、共用 Prompt 浮卡移除、受影响契约及必要测试 |

两仓均 writable；附属完整列表仅 desk，草稿不创建附属 worktree。执行先 desk 准确候选，后 primary 的 `config/instance.json#/review_desk_commit`，登记验证引用约束与 `scripts/task_workspace_guard.py` 实际摘要；受管交付 desk→primary。

允许各自两仓 worktree 并行开发：不重做 0003 数据补齐或 0004 范围抽取，共用文件有限冲突通过最新主干合并并联合复验。可写库、缓存、端口、容器、镜像标识、临时文件和浏览器存储独立。正式库／读缓存／导出、3000 服务、永久发布目录、发布锁及 current／previous／base 标签必须串行。0003 尚收尾不代表持续持锁；本任务执行者在发布前核实实际写入者、准确数据／提交／配置／镜像和回执，协调审阅写入，保全新增意见。正式回读、Chrome 与恢复核验后交接并释放窗口；Chrome 控制另协调。无额外外部系统写入范围。

## 验收和恢复衔接

任务正文五组验收及发布字段全部适用，须保留两图前后画面和操作证据。正式 Chrome 只读；评论草稿、写入保护及故障在准确隔离实例验证。覆盖图／引用读取失败、准确目标失效、加载中切镜／素材后的迟到响应，不以旧图冒充新范围、不借最新版开卡、不串草稿；解除故障后按已有重试／重开，再走 ASH001 高亮／双击返回和 ASH003／M2980→M2979，能继续原工作。

沿[工作区与发布流程](../../production/generation-workspaces.md)完成受管双仓集成和必要推送、本机正式库／3000 服务的必要发布、最终版本 Chrome 复验、准确完整导出及新空实例恢复后继续上述两条路径，再清理无效过程资源，方可 --auto 结项。发布中断先核事务／服务／回执，再沿同一冻结包恢复；候选变化重备复验，不用旧快照覆盖活库。执行者报告清理数量／范围、准确 ID／路径回读、保留用途／责任／解除条件；在用 worktree 退出释锁后受管退役。

不含 VPS、付费生成、正式作品／Prompt 改写或持续 Review。最终报告先写任务编号和实际问题，再给两例效果、收益、准确版本／环境、验证边界与残留；执行自验、正式生效和原负责人独立复验分开，范围外新工作另获授权。
