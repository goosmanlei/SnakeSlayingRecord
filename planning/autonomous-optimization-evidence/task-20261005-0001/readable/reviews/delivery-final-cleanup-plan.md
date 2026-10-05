# 本任务结项清理精确计划

**状态：仅计划，未删除任何资源。** 已盘点 18 个可回收目标，共 6,504 个普通文件、5,990,693,557 字节（约 5.58 GiB）。它们只在主协调确认实验结束、真实便携证据包独立验收通过、且执行前再次确认无使用者后删除。当前新 `final-preview`、技术验收夹具、冻结性能输入及全部 Git worktree 不计入该数字。

范围基于当前任务账本的 running / retained 状态、当前 AGENTS 清理规则、交付说明及主协调 2026-10-05 的明确授权。本计划不包含主目录历史镜像清理、歌曲任务清理或其他项目。用户要求保留本任务 worktree 和分支；本轮必要清理与实际回执均安排在 `_complete` 前。

## 先补齐交付，再释放副本

打包器已补列三份新代理登记与 `resume-1855-guard.json`。独立增量核验确认，去掉这四项后脚本 SHA 恰等于既有 17 项合成测试版本；四份实际新输入均正确脱敏、真实敏感值不残留，重复脱敏字节不再变化。31 项旧脱敏检查和 17 项合成检查未重跑。回执见 [四项增量检查](delivery-final-clock-incremental.json)。真实最终包仍须独立核对，不能凭该检查开始删除原证据。

## A 阶段：包验收后可删的副本

下表相对 `.runtime/autonomous-optimization/`。每个目标的准确 inode、mtime、大小及完整文件清单保存在 [机器可读清单](delivery-final-cleanup-plan.json)，执行前按清单重算一致才可操作。

| 精确目标 | 文件数 | 字节 | 用途与保留依据 |
| --- | ---: | ---: | --- |
| `schema6-roundtrip-reset-01/source` | 1317 | 1,327,868,172 | Schema 6 源克隆；22 表、10,160 载荷与 1,314 输出项已独审；依据 `reviews/schema6-roundtrip-independent.md; schema6-roundtrip-reset-01/receipt.json and three CLI logs` |
| `schema6-roundtrip-reset-01/empty` | 2335 | 1,316,747,441 | Schema 6 恢复副本；该轮恢复实验已结束；依据 `same Schema 6 independent audit and receipt` |
| `functional` | 1412 | 1,509,339,305 | UI 写入与故障实验副本；主协调确认不再作为用户预览；依据 `functional-clone.json; browser and functional coverage evidence` |
| `preview/.runtime/review.sqlite3` | 1 | 163,000,320 | 旧可写预览库；由 final-preview 接续最终预览；依据 `run-baseline.json; preserve preview/.runtime/generation-base.sqlite3 and generation-base.json` |
| `preview/config` | 4 | 35,870 | 旧预览配置副本；最新配置由 final-preview 提供；依据 `run-baseline.json; system/source identities in preserved performance evidence` |
| `preview/content` | 2 | 59,486 | 旧预览内容副本；不再启动旧预览服务；依据 `run-baseline.json; protected Git history contains inputs` |
| `preview/export` | 1405 | 1,346,243,629 | 旧预览导出及媒体副本；不再启动旧预览服务；依据 `Schema 6 CLI manifest; Git history and current formal originals remain protected` |
| `backend-investigation/write-ab/reset-window-01/baseline/instance/.runtime/review.sqlite3` | 1 | 163,000,320 | API 写入对照已完成的可丢弃库；依据 `write-ab/reset-window-01/*/evidence; receipt.json; server-stop-check.json` |
| `backend-investigation/write-ab/reset-window-01/candidate/instance/.runtime/review.sqlite3` | 1 | 163,000,320 | API 写入对照已完成的可丢弃库；依据 `same write AB evidence` |
| `ui-write-performance/A` | 7 | 428,131 | 已完成 UI 写入 A 组夹具副本；依据 `ui-write-performance/runs/A-measured; reviews/ui-write-independent*` |
| `ui-write-performance/B` | 7 | 428,131 | 已完成 UI 写入 B 组夹具副本；依据 `ui-write-performance/runs/B-measured; reviews/ui-write-independent*` |
| `ui-write-performance/snapshot` | 6 | 391,932 | UI 写入快照副本；保留原技术夹具；依据 `ui-write-performance/snapshot-logical-before.json; technical-readiness/instance` |
| `backend-investigation/startup-comments-profile-reset-01/profile.pstats` | 1 | 35,371 | 性能分析二进制临时文件；文本摘要保留作为证据；依据 `backend-investigation/startup-comments-profile-reset-01` |
| `backend-investigation/window2/entity-profile/profile.pstats` | 1 | 48,247 | 性能分析二进制临时文件；文本摘要保留作为证据；依据 `backend-investigation/window2/entity-profile` |
| `backend-investigation/window2/material_entries-profile/profile.pstats` | 1 | 13,658 | 性能分析二进制临时文件；文本摘要保留作为证据；依据 `backend-investigation/window2/material_entries-profile` |
| `backend-investigation/window2/production-profile/profile.pstats` | 1 | 14,315 | 性能分析二进制临时文件；文本摘要保留作为证据；依据 `backend-investigation/window2/production-profile` |
| `backend-investigation/window2/scene-profile/profile.pstats` | 1 | 34,408 | 性能分析二进制临时文件；文本摘要保留作为证据；依据 `backend-investigation/window2/scene-profile` |
| `backend-investigation/window2/history-profile/profile.pstats` | 1 | 4,501 | 性能分析二进制临时文件；文本摘要保留作为证据；依据 `backend-investigation/window2/history-profile` |

清理 Schema 6 的 source/empty 不影响既有独审结论：22 公共表、10,160 个准确历史载荷、1,855 个归档及 1,314 项再导出已经独立核过；三份完整 CLI manifest、运行回执和独审必须先入包。删除重复恢复树后，不能再声称它仍是可直接打开的恢复实例。

旧 `preview/.runtime/generation-base.sqlite3` 本轮再次只读计算 SHA，仍为 `5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0`。该 163,000,320 字节冻结输入及旁边 `generation-base.json` 明确保留，不随旧活跃库、配置和媒体树删除。后续若需重跑，应按准确 Git/manifest 输入重新组装环境，不将仅剩基准库目录当可用预览。

性能二进制 `.pstats` 仅在相邻文本摘要/JSON 已入包后删除；清单未包含相邻原始请求、摘要、工具及日志。

## B 阶段：最后验收后、完成前收尾

- `final-preview` 当前承担带新歌曲数据的最终候选兼容及用户预览，必须保留。确认、正式发布及必要正式浏览器验收成功后，按真实 PID/命令停止 62608，核对发布包中的正式发布前只读备份和恢复资料已齐备，再清除此任务预览副本；若中断，保留恢复现场。
- `technical-readiness/instance` 与 `technical-readiness/preflight-instance` 当前保留，直到技术采用验收和恢复用途结束。其日志、真实下载与采用结果入包后，删除具体可丢弃实例，而不删除已选中的技术证据。
- 新歌曲数据隔离恢复目录尚由 final_coverage 使用，路径、文件数和结论尚未冻结。本清单不猜测其路径，不授权清理；独审及成包后增量盘点精确路径，再加入实际回执。
- browser/backend/reviews 等原始记录先保留至最终包冻结。最终包独立验证每个 source→artifact 的准确映射后，可删除 manifest 已覆盖的重复原始文件；变换条目保留明确原 SHA 与脱敏说明。不得整目录删除仍活跃的 builder、最新审查、守卫、待发布包或上面保护的数据库/夹具。无引用临时脚本、草稿、失败前版本若已有准确 Git 或最终包替代，按同一原则回收，不把所有 `.runtime/` 永久归为证据。

## 明确保留的资源及移除条件

| 资源 | 当前用途 | 移除条件 |
| --- | --- | --- |
| `preview/.runtime/generation-base.sqlite3` | 原 6,236 对象的冻结性能输入，供必要独立复核 | 后续明确退休该实验复核用途时另行处理；本次保留 |
| `preview/.runtime/generation-base.json` | 冻结基准来源记录 | 只随明确退休的基准处理，不单独删除 |
| `final-preview` | 最新主干数据的隔离候选预览及最终兼容验收 | 确认、发布和正式浏览器验收后停止准确 62608 进程；完成前清除，中断时保留 |
| `technical-readiness/instance` | 技术采用夹具，保留到最终确认 | 最终技术验收与证据成包核验后、完成前 |
| `technical-readiness/preflight-instance` | 主协调要求保留的技术验收及恢复夹具 | 主协调确认验收和恢复用途结束后、完成前 |
| `system-worktree` | 用户要求保留的任务 worktree 和分支、候选源码与提交历史 | 本任务不删除 |
| `system-baseline` | 已登记嵌套 Git worktree，准确基准提交 b874b959 | 不使用 rm；另行退休且无使用者后，只能通过所属仓库 git worktree remove，保留提交 |
| `system-perf001` | 已登记嵌套 Git worktree，增量基准提交 7ba65822 | 不使用 rm；另行退休且无使用者后，只能通过所属仓库 git worktree remove，保留提交 |
| `state.json; state.lock; watch.lock; watcher.json; watch.log; latest-check.json; last-check.json; register-*.json; completed-window-*` | 活动计时守卫、真实身份与中断窗口来源 | 只经守卫停止；完成后保留最小本机回执，不手动删除活动锁 |
| `delivery/build_evidence.py` | 最终证据选择及构建方法；包内 tools/build_evidence.py | 最终包冻结且无需重建后才清运行副本 |
| `browser; backend-investigation; reviews; history-inventory; functional-media-observation; ui-write-performance; ux009-storage-fault` | 待归档的原始观察、准确工具、失败与独审 | 最终包逐条验证来源到交付哈希后，删除 manifest 已覆盖重复原文件；只保留明确仍有用途的资源 |
| `new merged-main restore temporary directory (currently not frozen)` | final_coverage 正生成并独审新歌曲数据恢复证据 | 独审通过且日志/回执入包后，补盘点准确路径及数量 |
| `release bundle (not created yet)` | 发布清单、镜像回执、执行脚本及不可变部署/恢复事实 | 保留至确认、正式发布及恢复窗口结束；证据压缩包不能替代可部署发布包 |

三个系统目录都是已登记 Git worktree，不能用 `rm` 或递归文件删除处理。当前系统候选 worktree 与分支保留；两个 detached 实验检出可继续保留为精确代码输入，若另行决定撤销，必须先确认没有用户/进程并通过所属系统仓库 `git worktree remove <准确路径>`，不删提交或任务分支。

## Docker 与活动依赖核对

当前 Docker 只读盘点为 4 个容器、5 行镜像记录；本任务专属容器 0、本任务命名镜像 0，因此此次没有 Docker 删除指令。正式 app 镜像 `sha256:e6ba94c3d3eb737fec0d891d337d3e6a371bca7a3530bd289640f98fa5aa30fd`、nginx 镜像 `sha256:009d73a160564cce886ee8a8538c4d18f0ea9b961f03db9df410e45b0fdf29b2`、正式主库、旧不可变挂载及全部待发布/恢复备份均保护。正式 app 的 `/instance` 是主目录父级绑定，不把“路径技术上可经父绑定访问”误写为任务专属挂载，也不能为清本任务而停正式容器。

对 A 阶段候选的 `lsof` 精确路径复核为 0 条，进程参数匹配为 0；这是点时状态，删除前必须刷新。较早全工作区 lsof 可见宿主虚拟化共享文件句柄，不能据此关闭共享 VM；应核对实际消费目标路径的进程/容器身份。守卫、Codex 会话及主工作区仍在使用，不能强删工作区或手动删锁。

## 主协调的执行与回读

1. 固定最终包 manifest SHA，独立核验三压缩包及逐项内容 SHA、脱敏、无 SQLite/环境文件，并核对本计划所指 Schema 6 / API 写入 / UI 写入证据均已收录。
2. 执行前按 JSON 清单重新统计每个 A 目标的完整相对文件清单、文件数、字节、inode 和 mtime；任何目标缺失、改变、出现 symlink、`.git` 或新使用者，暂停该项并更新具体判断，不扩大路径。
3. 只对核对通过的准确文件调用 `Path.unlink()`，准确普通目录调用 `shutil.rmtree()`；禁止通配符、上级目录删除、全局 Docker prune、全局缓存清空或 worktree 递归删除。JSON 的 `phase_a[].path` 就是唯一允许路径集合。
4. 执行后记录真正删除的目标/文件数/字节和回读 `exists=false`；同时核对冻结基准 SHA、final-preview、technical fixture、三个 Git worktree、正式容器/镜像身份仍在。没有实际执行的阶段标为待办，不能复用 6,504 这个计划数冒充实际删除数。
5. B 阶段在发布及验收后、`_complete` 前补齐实际清理回执与保留用途；用户保留要求和 `_complete` 后仅回读边界继续生效。

本独审只写上述 `delivery-final-*` 审查产物，没有运行删除、重跑性能/浏览器/完整测试、修改产品/主报告/打包器、构建发布包或改变正式服务。
