# 正式发布后的 B 阶段清理计划

**仅准备，未停止进程、未删除文件。** 主协调完成用户确认、真实正式 apply、一次正式页面只读验收后，才可在 `_complete` 前执行本计划。[执行脚本](cleanup-after-publication.py) 默认 dry-run；本次只运行基线盘点、语法检查和无正式回执的只读预检，没有伪造成功回执。

范围固定为 PID **96270** 的 **62608** 预览服务，以及以下三个目录。路径均相对 `.runtime/autonomous-optimization/`。脚本没有任意目标参数，不清空 runtime，不删除原始证据或 Git 工作区。

| 固定目录 | 普通文件数 | 字节数 | 当前预检 |
| --- | ---: | ---: | --- |
| `final-preview` | 1,407 | 1,558,918,216 | 内容与基线相同；预览及其父 shell 在使用，另有 VM PID 56230 持有 1,413 个句柄。停止预览后必须重新检查，VM 仍使用则整树保留。 |
| `technical-readiness/instance` | 6 | 391,932 | 内容与基线相同，当前未发现使用者。 |
| `technical-readiness/preflight-instance` | 7 | 463,898 | 内容与基线相同，当前未发现使用者。 |

三个树共 1,420 个普通文件、1,559,774,046 字节。这是计划盘点量，不是实际清理量。完整文件哈希、inode、设备号、mtime、目录集合与使用者记录在 [基线](cleanup-after-publication-baseline.json)，其 SHA-256 固定为 `4f12b9a0c145c85bb0303ea0a53d2ce0c0ec611a6c7e7daeab014bbc5a4d5dd3`。拒绝符号链接、特殊文件、嵌套挂载和 `.git`。基线采用排他创建，不会被下一次运行静默刷新。

精确进程的启动时间为 `Mon Oct 5 19:52:36 2026`，cwd 是本任务工作区。命令必须仍为 Python 执行 `scripts/generation_review.py --instance .runtime/autonomous-optimization/final-preview --system .runtime/autonomous-optimization/system-worktree serve --port 62608`，且端口监听者只能是该 PID。PID、启动时间、命令、cwd、监听者任一变化均拒绝操作。只发送一次 SIGTERM，最多等待约 8 秒；不升级为 SIGKILL，不停止父 shell、VM 或正式容器。

预览活跃库 `.runtime/review.sqlite3` 的基线 SHA 是 `56c2ba0af3666e09bd29186e66f19e1315d5061e0457c113502f9e2a5b94c3c5`。**发布、用户交互或停止服务后，只要该库或其所在树的内容、文件集合、身份与基线不同，就保留整个 `final-preview`，避免丢弃可能的新评论。** 即使变化只是 WAL/checkpoint 或可解释日志，也不自动接受新基线；由主协调复核用途后另行处理。

执行时逐树核验，某树被占用或发生变化不妨碍另外两个独立树通过检查。删除前再次核对完整清单、哈希及使用者；逐项用不跟随符号链接的目录句柄核对 inode 后删除。若中途失败，已删数量和剩余状态保留在回执中，不自动重试或接受重建后的目录。任何 `retained`、`partial_retained_requires_review` 或退出码 2 都需要如实报告，不能称完成清理。

以下输入必须来自真实执行。所有 SHA 均须完整 64 位：

- 最终便携证据 manifest 路径与 SHA：逐一核对其中压缩包、条目及内容哈希；不要求已经被 A 阶段清掉的归档源重新出现，也不以源缺失否定已验证的档案。
- 最终发布 bundle 的 `manifest.json` SHA 和 `image.json` SHA：准确绑定任务、系统候选和镜像来源。
- 该 bundle `run/` 内真实 apply 产生的 `service-*.json` 及 SHA：要求实际状态 `formal_browser_pending`、系统候选匹配、正式源码/实例文件核验通过、3000/64401 入口记录、历史均保留，且没有调用 `_complete`。
- 正式浏览器验收回执及 SHA：必须在实际只读操作后记录 `task`、`system_candidate`、`story_candidate`、`passed: true`、`readonly: true`、`manifest_sha256`、`image_receipt_sha256`、`publication_receipt_sha256`。同时提供非空 `evidence` 数组，每项为本工作区相对路径 `path` 和准确 `sha256`。脚本会逐项回读。不能把预览截图或技术测试通过写成正式验收。

在工作区根运行下列命令，先不加 `--apply`。尖括号内容必须替换为实际路径或经过审阅的 SHA；这不是可伪造成功回执的模板。

```bash
python3 .runtime/autonomous-optimization/reviews/cleanup-after-publication.py \
  --baseline-sha256 4f12b9a0c145c85bb0303ea0a53d2ce0c0ec611a6c7e7daeab014bbc5a4d5dd3 \
  --evidence-manifest planning/autonomous-optimization-evidence/task-20261005-0001/manifest.json \
  --evidence-manifest-sha256 <最终证据manifest-SHA> \
  --release-manifest <实际已apply的bundle>/manifest.json \
  --release-manifest-sha256 <发布manifest-SHA> \
  --image-receipt-sha256 <镜像回执SHA> \
  --publication-receipt <同一bundle>/run/service-<真实时间戳>.json \
  --publication-receipt-sha256 <真实apply回执SHA> \
  --formal-receipt <真实正式浏览器验收回执.json> \
  --formal-receipt-sha256 <正式验收回执SHA>
```

主协调审阅真实 dry-run 后，使用同一组输入加 `--apply`。脚本本身不能代替用户确认，也不能独立证明尚未调用 `_complete`；这两个时序由主协调负责。服务已退出或曾执行过部分清理时，重复命令会拒绝，不提供绕过身份检查的 resume 开关。

停止、逐项删除意图和最终实际结果写入固定 `reviews/closing-receipts/`，每次使用新文件名，并 fsync；不覆盖冻结档案中的旧记录。最终证据包冻结后产生的这些收尾回执，由主协调另存 closing receipts 并逐项建立 SHA 映射，不能通过重打旧包丢掉 A 阶段已经清理的 17 条源记录。当前 [只读预检](closing-receipts/cleanup-after-publication-dry-run-1791203646388240000.json) 的状态是 `blocked`，原因是尚无正式 apply／正式浏览器成功回执，`service_action` 为 `none`。

明确保留资源及后续用途：

| 资源 | 保留用途及后续清理条件 |
| --- | --- |
| `browser/` | 保存真实页面状态、操作、原始截图和失败现场，用于正式验收后的比对与必要复算；只有最终 manifest 逐项映射、源 SHA 未变且无待核问题时，才另列逐文件删除计划。 |
| `backend-investigation/` | 保存服务身份、HTTP、负载、中断与重试口径，复核性能分组及异常；按相同逐项条件处理，已明确冻结输入不得归入可删源。 |
| `history-inventory/` | 追踪评论、版本和引用保留，正式发布后发生差异时仍需对照；差异关闭且准确档案验证后再列具体源文件。 |
| `reviews/` | 独立判断、反例源、脚本、计划、基线及实际清理回执；本脚本、计划、基线和 closing receipts 保留，其他审查仅在无继续复核用途且准确归档后另列。 |
| `technical-readiness/` 的非目标部分 | 下载、采用、预检、关系及失败修复证据，解释两个被清理夹具的来历；不得随实例树一起删除。 |
| `functional-media-observation/`、`ui-write-performance/runs/`、`ux009-storage-fault/` | 媒体完成态、写入试验和故障恢复原件，供正式页面差异比对；必要复核结束后才能按 manifest 与当前源 SHA 逐条清理。 |
| 所有 clock、注册、守卫及监督状态 | 解释实际授权、运行窗口与中断边界，持续保留；不因已归档而删除。 |
| `preview/.runtime/generation-base.sqlite3`、旁边 `generation-base.json`、`run-baseline.json` | 精确 6,236 对象冻结数据库及来源，SHA `5c6d00ee…`；执行前后均检查，永久排除本轮清理。 |
| 三个系统 Git worktree、分支与任务 worktree | 复现准确代码与用户要求的保留范围；检查身份/提交且不删除、不剪枝、不改分支。 |
| 最终 evidence 包、发布 bundle、发布前后备份和正式 release 挂载 | 交付、恢复、正式运行依赖；本脚本不写入或删除。 |

本轮没有为 raw 重复源实现删除分支，因而不存在“归档存在即整目录删除”的路径。新的目录、重启后的服务、已变化的预览数据或额外 raw 清理范围，都必须重新形成可审阅的精确计划。
