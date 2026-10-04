# 当前工作区入口

本工作区仅处理 `task-20261005-0001`：在前置任务完成后，自主检查并优化审阅台体验和各主要页面、功能的性能。范围、6／9／10小时边界和完成标准见[任务说明](planning/autonomous-optimization-task.md)；意见依据见[检查重点](planning/autonomous-optimization-focus.md)，计时及恢复方式见[运行工具](planning/autonomous-optimization-runtime.md)，交付要求见[报告模板](planning/autonomous-optimization-report-template.md)。任务完成、确认及推送结果只由主项目唯一任务账本和回执记录。

## 当前恢复状态

当前会话已绑定本任务。启动器进入合并恢复，合并来源为 `6c7b1d3bd256ba3a1de184f7778e8b89da007ecb`，唯一冲突为本文件：本任务澄清状态与前置任务交付状态重叠。按双方有效内容合并，保留前置成果及本任务要求；合并提交和 `_prepare_integration` 的实际结果以 Git 和准备回执为准，不能仅凭冲突文字已解决宣称上游同步成功。

既有计时工具拒绝当前执行入口，原始错误为：`必须在正在执行的 task mrun 中初始化或结束守卫`。任务账本的本次执行方式确为 `run`；`status` 返回 `initialized=false`。尚未取得 T0、监督锁／心跳或停止回执，当前会话没有 Goal，也未创建子代理或开展优化。不能绕过鉴权、伪造 mrun 标记、修改通用任务机制或用当前时间替代 T0。

## 前置成果与归属

已通过任务命令回读：`task-20261004-0009` 为 `completed`，故事交付提交为上述合并来源，系统交付提交为 `b874b959af9c918a482e8488dc25cb0204ab5772`；账本记录两仓已推送及正式迁移、页面验收。当前 `config/instance.json` 引用该系统提交。这是前置任务完成证据，不代替本轮实际服务、代码和一致数据快照基准。

前置成果包括五页固定顶栏、集场镜代号、逐镜分栏与筛选、共用实体／素材卡、层叠关系大卡、准确评论与采用、集中素材版本定义及历史物理去重。完整要求见[前置任务说明](planning/ui-material-model-task.md)，实现与迁移／恢复入口见[交付说明](production/ui-material-model/README.md)，33项检查及真实浏览器证据见[验收表](production/ui-material-model/acceptance.md)。这些成果和历史证据保留其原任务归属，不算本轮改进。

前置的 `.runtime/ui-material-model/` 实例及发布回执属于前置任务工作区，未随 Git 复制到本工作区。正式增量迁移已经交付，不在本轮重复执行前置的发布／恢复命令；必要时只读其准确回执。本轮须另建故事与系统隔离环境、预览库和端口，核对旧修订、真实调用、原件、评论、采纳与采用；历史验证不等于本轮已复验。

## 下一步

先在当前工作区提交合并，再执行本任务 `_prepare_integration`，解决可能出现的新冲突并补验实际影响范围。启动阻断和恢复检查点写入本轮[运行报告](planning/autonomous-optimization-run-report.md)，不继承上一轮报告的成功结论。

当前入口无法提供任务要求的监督。正常退出本会话、释放运行锁后，使用 `codex.project task mrun -g creative -p SnakeSlayingRecord --task task-20261005-0001` 恢复同一任务。恢复时先绑定、运行原守卫并核对 T0 来源、锁和心跳；若不能从真实执行历史恢复，保留错误并报告，不重写历史。守卫有效后才建立持续 Goal、登记后代、建立现场基准和展开优化。

本轮没有最终可验收的双仓优化候选，尚不请求完成确认。全部实现、报告、验证和必要增量／恢复方案齐备后，重新准备并展示候选及 `main / origin / refs/heads/main` 目标，取得明确确认后才执行既定交付和 `_complete`。本次不修改正式数据库或服务、不集成主分支、不推送；保留工作区和分支。
