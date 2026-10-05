# 隔离页面写性能对照

真实页面对照已完成：基线 `b874b959af9c918a482e8488dc25cb0204ab5772`、候选 `204c4696f0ecd4595b395a14520eacf0c54ef2bf` 各24次写入，包含6类操作各1次预热和3次正式。首尾身份检查通过，离线完整历史检查两端各67项通过。统计与独立复核见 `../reviews/ui-write-independent.md`；小型技术库的结果不外推故事库。

最初 `runs/A` 只用于确认入口，未写库；发现实体页没有整体评论入口后，白名单改为实际正文准确锚点，原方案及替代依据保存在 `text-anchor-protocol-correction.json`。正式结果为 `runs/A-measured`、`runs/B-measured`，浏览器原件在 `../browser/ui-write-reset-01/`。这两个克隆已经写入，不得重置后冒充初始输入；下面命令是流程说明，原地重跑会被保护校验拒绝。

## 真实技术输入和隔离

`prepare.py` 已用只读 SQLite 连接的 `backup` API，从准备时运行在 62609 的 `../technical-readiness/instance` 取得一致事务快照；没有复制活跃 SQLite 文件，也没有操作 62609 服务。源连接设置 `query_only`，备份输出的全部业务表逐行与该读事务相同，外键检查为空。数据库来源状态来自这个一致读事务，不声称对运行中的源库做过前后字节不变证明。

冻结库为 `snapshot/instance/.runtime/review.sqlite3`，SHA-256：`8b15a75d37ca937b9ac1fdadbef6de1c5eab51d4f1bdb80947dc5699a844fca9`。`A/instance`、`B/instance` 由已关闭的冻结快照复制，初始库 SHA 相同、inode 独立，未启动过 Store。五个普通输入文件逐字节 hash 相同；仅有一个 96,044 字节的一秒静音 WAV，原件 SHA 为 `0a8f76d89c709043814cb74f331a4578d17ff61256303bd0019a263d053f86e8`。无密钥文件、符号链接或共享媒体挂载。

冻结初始技术库有 18 个对象、27 个修订、1 个来源、0 条评论、0 个配置记录/事件；A/B测量克隆结束后的新增行以各自回执和独审为准。已存在的技术采用及判断历史全部保留，不能当作本轮新成果。

- 唯一可写评论/采纳实体：`technical-d2-object`，准确修订 `f0657d7bafdac0dfa84f94460c7b2715cd6e6f8ea9feec9e6e3740b8493e88c8`。
- 唯一采纳决定：`entity-generation-738ba0c7d4a5a6d39e9b52ea9f5b14b1`，起始版本 4、未采纳、可以采纳，`acceptance_mode=content`。
- 状态准备不完整，`generation.accepted=None`；采纳只对本技术实体当前内容生效，绝不设生成许可，不对故事作品认可、采用或生成。
- 页面把操作者固定写为“用户”。包装器保留真实产品行为及原请求值，所有审计另外注明实际执行者是 Codex 技术性能操作，不能把记录解释成真人用户确认。

`preparation-receipt.json` 保存源标记、逐文件 hash、快照/克隆身份、初始精确范围及 guard；`snapshot-logical-before.json` 保存历史原始行。准备时已核对新 T0（2026-10-05 13:21:50 +0800）、armed、监督锁及心跳；启动时重新核对。

## 有界启动与取证

以下命令相对故事任务 worktree。必须先确认 62610 没有其他监听，且根已结束其他浏览器/测试/测量负载。不要操作原62609技术实例；其当前是否在线须另行核对。每个 `--output` 必须是本目录内尚不存在的新目录；克隆必须仍是原始 SHA，写过后禁止悄悄复位重跑。

```sh
python3 .runtime/autonomous-optimization/ui-write-performance/serve.py --phase A --output .runtime/autonomous-optimization/ui-write-performance/runs/A --max-seconds 1800
```

完成 A 后停止其 `process.json` 中准确 PID（进程会话 Ctrl-C 或向该 PID 发 SIGTERM），等 `receipt.json`、`logical-after.json`、`technical-state-after.json` 落盘，检查无 error/final_check_error，code/files/snapshot unchanged 均为 true，再确认 62610 已释放。然后启动 B：

```sh
python3 .runtime/autonomous-optimization/ui-write-performance/serve.py --phase B --candidate-commit <最终40位候选SHA> --output .runtime/autonomous-optimization/ui-write-performance/runs/B --max-seconds 1800
```

B 参数必须替换成根确认的真实干净提交，未确定前不能启动。包装器核对准确 HEAD、产品目录干净、DB 独立且初始相同、全部普通文件 hash 与冻结输入相同。限时 1,800 秒且不能越过 T0 后 9 小时；超时保留未完成回执，不伪装通过。不做广泛进程清理。

包装器使用原 `backend-investigation/probe_server.py` 和原 `probe.js`（SHA `74a80b7f730a450f4fc00f5424120f8f60406e7fe9c4c65234e3d317958a804c`）。单线程、实际产品 Store 初始化、原读写路由和页面请求均保留，只给这两个独立技术克隆限定写路径及数据范围。Store 初始化后要求全部历史行不变。POST 仅允许准确技术正文圈选评论（technical 块第0至7个字符“可丢弃技术验收”）及实体内容决定；PATCH 仅允许本批评论编辑和下述两个配置字段。其他写请求、润色、上传、生成、导入均拒绝。

额外请求范围校验也在 handler 内，两端适配相同，结果应称“带同一保护适配的页面/HTTP 测量”。原 handler 计时方法不改；请求/响应审计 JSON 在原计时停止之后追加到 `write-audit.jsonl`，会保存真实 UUID、body、expected_version、准确 scope/decision_ref 和响应。原 `http.jsonl` 保存真实读写请求耗时；页面采样JSON、截图/DOM实际由根保存在 `../browser/ui-write-reset-01/`，服务回执在 `runs/A-measured`与`runs/B-measured`。配置和评论可能还会先查版本或写后刷新，必须保留完整请求序列。

## 操作与样本

Chrome 1440×900、DPR 1，同一前台标签、62610 origin 和原 probe。每端每操作一次预热、三次正式，预热编号 0、正式编号 1–3；不合并预热。输入填写和页面定位不是写耗时起点；只测真实保存/采纳按钮的可信点击，到准确成功状态和后续可编辑控件可用。不得用 `evaluate(fetch(...))` 代替页面动作。

先完成 W1 四次，再编辑对应四条做 W2；再 W3、W4，最后 W5 四个采纳→撤回循环。两端相同顺序及相同正文长度。唯一技术实体入口：

`http://127.0.0.1:62610/?workspace=settings.workspace&production_tab=entities&production_object=technical-d2-object`

| 操作 | 真实输入与校验 |
| --- | --- |
| W1 新建评论 | 对实体准确修订选正文圈选评论（technical 块第0至7个字符“可丢弃技术验收”），正文用 `plan.json` 的四条 `comments[].create`；UUID 保留原 UI 随机值。成功 201 后新正文、OPEN、版本 1 和编辑入口可用；每条仅一次 CREATE。 |
| W2 编辑评论 | 分别编辑 W1 的第 0–3 条，正文用 `comments[].edit`；成功 200 后原 ID、准确目标/锚点不变，版本 2，CREATE 与 EDIT 两个事件完整。 |
| W3 PROJECT | 进入故事项目，只改“目标受众”：`隔离技术性能样本 受众 0`、`1`、`2`、`3`。页面提交完整配置时其余字段必须等于当前值；预热保存后版本 1，三次正式后版本 4。 |
| W4 SYSTEM | 进入系统与 AI，只改“AI 参考上下文字数上限”：12001、12002、12003、12004。都是合法非凭据值；不改环境变量名、模型、强度或图标，不调用 AI。其余字段及依赖控件保持，最终版本 4。 |
| W5 采纳/撤回 | 每次使用真实当前 scope/expected_version/revoke_target。内容采纳→取消采纳分成两个指标，共各 1 预热+3正式；初始决定 4，四循环后版本 12、未采纳，旧版本 1–4 仍存在，新增 5–12，生成许可仍为空。 |

例如编号 0 的 W1 正文是“隔离技术性能样本 评论 0：仅技术数据，不表示作品意见。”，W2 改为“隔离技术性能样本 编辑 0：仅技术数据，不表示作品意见。”，其余只替换同位数字。包装器只接受计划里的准确四条原文和四条编辑文。

每个保存都核对 probe 的对应可信 click 样本、stable、无 fetch/body pending、无错误请求，且正确实体、评论正文/目标、配置值/版本或决定状态在语义取证时已经可见。源代码不同引起的错误页面/空候选/错误历史路由必须记作功能失败；UX005/UX006 的旧失败态不能和新正确成功态计算加速。本组不使用 P2 素材采用或判断历史去绕过这一边界。若 A 任一真实动作不可用，停止该项并保留受阻，不能换 API 写入后声称测过页面。

原 probe 中 `scenario_ready_ms` 对交互从事件时间戳开始，180 ms 确认等待不计入。它仍只是 DOM/请求完成规则，不能代替语义正确断言。写请求响应与随后的刷新请求分列；服务器 handler 是墙钟时间，不是 SQL/commit 或 CPU；本次不重复扩建后台细分计时，沿用已验证的独立后台写性能证据，并明确那是另一版本/数据窗口。

## 写后历史检查与恢复边界

两端停止后分别运行离线审计，它只读取已保存 JSON，不打开 DB 或发 HTTP：

```sh
python3 .runtime/autonomous-optimization/ui-write-performance/audit.py --evidence .runtime/autonomous-optimization/ui-write-performance/runs/A-measured
python3 .runtime/autonomous-optimization/ui-write-performance/audit.py --evidence .runtime/autonomous-optimization/ui-write-performance/runs/B-measured
```

预期每端 24 个成功写调用（W1/W2/W3/W4 各 4，W5 共 8）、4 条版本 2 评论与 8 个 CREATE/EDIT 事件、2 个版本 4 配置及 8 个准确完整 body 历史事件、8 个新增内容决定修订。原对象不增删，只有已有技术决定的当前头可变；全部原修订、依赖、源文本、原件、既有采纳/判断均保留，其他业务表不变。配置历史比较完整 body，不能仅比 count。任何未完成、409、写后核对错误保留为失败；本组不额外造冲突负载，版本门禁引用已有独立回归，不能把未测冲突写为通过。

两端新增评论 UUID/时刻本来不同，不能直接要求数据库字节或整个响应 SHA 相等。比较时按计划正文编号映射 UUID，检查真实请求、状态、版本、完整业务值和历史次序；只允许显式忽略元数据时间戳，不能删除 scope、revision、actor、锚点等业务字段。保留全部原始响应及两个数据库，不覆盖任何原件或运行库。

中位数/范围与三个正式原值分别报告；n=3 仅为小样本诊断，不能把不足一毫秒的变化或范围重叠写成已证实优化。这里是小型纯技术实例（18 对象/27 原修订），不能外推为 6,236 对象故事库的保存收益。若没有超出波动的收益，应交付测量证据而不制造改动。

没有恢复到活库的步骤：本批所有新增数据停留在 A/B 克隆。失败或超时保留最近完整日志和数据库；下一次测量必须另建有明确来源的新实例，不能在原克隆上悄悄清空历史重跑。
