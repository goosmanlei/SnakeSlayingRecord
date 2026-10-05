# 隔离写性能测量方法与边界

现有结果没有写性能基线。`window2/*/environment.json` 全部标记 `read_only: true`；`db_diagnostics.py` 使用 SQLite `mode=ro` 和 `query_only=ON`，已完成 HTTP discovery、50 次基线及两个 A/B 窗口全部为 GET。这些结果不能替代 POST/PATCH 或数据库写入耗时。

目标是补齐已有写操作的实际耗时、写后可见性和版本冲突覆盖，不增加产品接口或功能。首个窗口已于 2026-10-05 13:37:49—13:38:15 执行，原始值与回执在 `write-ab/reset-window-01/`；本文解释可复现方法，结果以单独结果报告为准。再次执行仍须另获独占窗口，不能覆盖已有输出。

## 隔离与对照

从不可变 `preview/.runtime/generation-base.sqlite3` 创建两份新的普通文件副本，写入 `backend-investigation/write-ab/<本次输出名>/<baseline|candidate>/instance/.runtime/review.sqlite3`。启动前核对源 SHA256 为 `5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0`，两副本初始 SHA 相同；禁止路径任何一级经过 symlink，禁止将可写 DB 指向原快照、preview、functional 或正式目录。初始化和全部写入都发生在副本中，结束后保留回执和可丢弃副本，不执行恢复到活库。

建议比较本轮最初系统基线 `system-baseline`（`b874b959af9c918a482e8488dc25cb0204ab5772`）与最终已冻结候选，这样覆盖 001+002 对写路径的整体影响。根代理也可明确改为 001→002 增量，但报告必须写实际版本，不混用现有 GET 窗口。

仅 127.0.0.1:62607，逐个启动测试包装服务，保留现有 `ReviewHandler` 写处理。包装器仅允许本方案评论、PROJECT 配置和测试实体决定路径，阻止其他 POST/PATCH/PUT。只关闭自身启动的 PID。实例不挂载媒体目录、不装载密钥，不调用润色、生成、文件上传或导出。主体 API/Store 均取对应候选原实现；计时适配只写调查目录。

为避免把测试变为对故事的认可，使用现有测试数据模型建立独立命名空间的合成 EPISODE/ENTITY/完整 STATE；演员与原因固定为“隔离性能技术测试，非作品认可”。两个副本写入相同 fixture（仅供技术测试的合成数据），准备阶段不计入性能样本并记录 fixture SHA。通过已有 Store/production import 入口建数据，不手工改业务表。实体没有媒体依赖，`reference_media=none`，不触发外部调用。整体评论只指向合成 ENTITY 的准确版本，并在服务就绪前通过原 `Store.validate_target` 检查；普通 EPISODE 不支持整体评论。不会编辑原有评论、实体或判断。

## 现有 API 与样本

每端每项 1 次预热、5 次正式重复，成功样本与冲突样本分别统计，不能混入一个延迟分布。POST/PATCH 的接口字段来自现有 `server.py`、`store.py` 和 `generation.py`，不添加测量字段到产品协议。

| 场景 | 现有请求 | 成功与回读 |
|---|---|---|
| 创建评论 | `POST /api/comments`；`id`、`target_object_id`、`target_revision_id`、`anchor:{type:global}`、`body` | 201；GET comments 精确过滤对象和版本；ID、原文、锚点、OPEN、version=1 与 CREATE 事件一致 |
| 编辑评论 | `PATCH /api/comments/<id>`；`action:EDIT`、`expected_version`、`body` | 200；正文与版本增加一次，原创建事件保留，新增一个 EDIT 事件；重复旧版本返回 409 |
| 项目配置 | `PATCH /api/configurations/PROJECT`；`updates:{audience:<测试值>}`、`expected_version` | 200；GET configurations 的 PROJECT 值/版本匹配，configuration_events 增加一次；重复旧版本 409。只改副本中已支持的 audience 字段 |
| 采纳/取消测试实体 | `POST /api/production/entity-decision`；`entity_id`、`action:accept/revoke`、`expected_version`、`scope`、`acceptance_mode`、`decision_ref`（取消时准确引用）、`actor`、`reason` | 201；scope、模式、决定版本和引用取当前真实 snapshot，不拼猜；回读 entity-review 和准确 JUDGMENT 历史验证 accept→revoke，取消后历史采纳仍可读取；重复旧版本 409 |

实体每次先读取 `/api/production/entity-review?entity_id=<fixture>`，使用返回的 `decision_scope || scope`、`acceptance_mode`、`decision_version`、`revoke_target`。不可用的动作登记受阻，不能修改校验使其可用。重复循环在两个副本执行相同序列，fixture 的媒体与生成许可边界保持原逻辑。

每项成功写之后，立即通过 HTTP GET 和新的只读 SQLite 连接核对可见结果、版本和事件计数。冲突请求也回读，确认没有额外版本或事件。额外对同一配置/评论版本发两条竞争请求，预期一条成功、一条 409；单线程 HTTPServer 本身按序处理，报告不得将此说成多进程直接写 SQLite 的并发安全证明。真实跨连接写并发仍引用既有针对性回归，不在本次耗时实验中扩大范围。

## 计时与正确性口径

同时保留三个不同指标：

1. HTTP：发起真实 loopback POST/PATCH 到完整响应体读完；单独计后续 GET 到完整回读，不能把写后查询时间加进写请求。
2. Store 逻辑调用：测试包装 `create_comment`、`change_comment`、`set_configuration`、`generation.decide` 的完整调用，含校验读、Python 处理、事务提交和返回投影。此指标不等于纯 SQL 写时间。
3. SQLite：测试专用 `sqlite3.Connection` 子类分别计 `execute/executemany` 的写语句、显式 commit 与已有事务的 context-exit；无事务的 context-exit 单独记为 no-transaction，保留调用次数、耗时及 rollback。SQLite 语句的触发器/校验成本包含在 execute 内，其他 execute 调用另计。后续 cursor 取行、初始化和未包装的其他原生调用不在这些分项内，不能把分项相加称为完整数据库耗时。计时日志的序列化和磁盘落盘在 handler 计时后，客户端 HTTP 计时也在响应体读完后停止；排队和系统调度成本仍属于真实 HTTP 耗时。不能用 trace callback 的开始时刻假称语句完成耗时。

本机 Python 3.9.6 的实际日志确认 context-exit 会调用 Python commit 包装，因而同一事务存在嵌套计时。`explicit_commit` 与 `context_commit` 分别保留，绝不相加；评论和配置路径使用外层 context-exit 作为事务完成边界，实体决定的原实现使用显式 commit。该事实更正了初次静态审查关于 CPython 退出路径的假定，原始值未改写。

若连接适配难以完整覆盖 commit 或既有 Store 初始化，优先保留准确的 HTTP/逻辑指标并将纯数据库分项标为受阻，不提交不可靠计时。产品代码不变，根代理安排独占 CPU/浏览器窗口后才验证探针和测量。

原始结果记录每次请求方法、路径、状态、请求 SHA、响应 SHA、响应字节数、HTTP/逻辑/SQL/commit 原始耗时、版本与事件变化。写入时间戳天然不同，不能要求两端全响应字节或规范化 SHA 相等；保留原始 SHA，并比较固定请求载荷和确定性业务结果。顺序样本完成后的状态只删除以下明确的时间戳，再对两端完整结构比较：PROJECT.updated_at、comments 每行 created_at/updated_at、comment_events 每行 at、decision 对象 created_at/updated_at、decision_history 每行 created_at。业务 payload 内任何字段均不删除；两个竞争请求的随机赢家在该比较之后另验。旧数据表/对象记录做测前后双向 EXCEPT 与外键核对，确认只有 fixture、测试评论和该配置版本历史变化。

## 180 秒预算与交付边界

总窗口硬限 180 秒，从 runner 进入 main 开始，包括哈希、克隆、初始化、预热、测量和收尾；单请求上限 15 秒，剩余 20 秒不启动下一请求，任何非预期错误立即停止相应批次。170 秒正常超时进入清理；180 秒独立 watchdog 为阻塞调用兜底，只杀本脚本启动的服务器并留下 `hard-deadline.json` 后退出，不冒称完成身份和保留性审计。git、guard 和子进程回收均有显式 timeout。预计准备与快照身份核对约 10–20 秒，评论/配置约 10–20 秒，实体约 40–80 秒，冲突与回读约 20–30 秒，至少保留 20 秒停止与回执。这是预算而非测量结果，不保证为凑满样本超时。

启动时核对本任务 ID、守卫 armed、停止字段为空、监督锁/心跳，并核对用户重置后的 T0 `2026-10-05 13:21:50 +0800`。测量复用首次快照和原始版本，它们的采集时间不改写为新 T0。运行前仍须根代理明确授予独占窗口；再次执行不能复用首轮授权。

输出中位、最小/最大与原始值；n=5 只是小样本写路径诊断，不作稳定 P95 或固定提升承诺。没有独立窗口或校验失败时登记未测/受阻，不能用 GET 提速替代。API 和数据库写耗时也不替代真实浏览器保存完成体验，页面保存另行操作验证。前后 guard、候选 SHA、数据库源 SHA、复制路径、写允许列表、结束 PID/端口和所有未完成项随回执保存。
