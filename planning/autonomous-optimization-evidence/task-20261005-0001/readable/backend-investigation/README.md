# 本轮后台调查与测量入口

调查针对系统基准 `b874b959af9c918a482e8488dc25cb0204ab5772`。已完成单次探索、50样本基线和 AO-PERF-001 同条件 A/B；最新结论与内存代价见 [A/B摘要](AO-PERF-001-ab-summary.md)，每项原始结果在摘要所指目录。本文保留端点梳理、测量方法及首次探索归属，不能把单次探索当最终结论。故事工作区为本文件上三级目录；下文命令都以故事工作区为当前目录。前置实体读取复用已经存在，保留其归属。

## 测试专用页面探针

`probe_server.py` 复用系统原 `ReviewServer` 单线程服务及其数据访问，只对隔离服务返回的首页注入 `probe.js`。它不修改候选源码，不接触正式服务，不接受任意采集 URL。当前版本不使用日志 POST，测量结果保存在页面隐藏的 JSON 节点，后台只记录本服务自己的请求耗时。

由主协调分配独占窗口后执行，`62606` 仅为建议端口，启动前核对未占用。两次测量应保持探针 SHA、Python、浏览器视口、数据库快照和选择的集场/历史版本一致；若需比较两个代码版本，顺序使用同一地址与相同配置，并分别记录进程和原始日志。

```bash
python3 .runtime/autonomous-optimization/backend-investigation/probe_server.py \
  --system .runtime/autonomous-optimization/system-worktree \
  --instance .runtime/autonomous-optimization/preview \
  --port 62606 --label baseline-b874b95 \
  --output .runtime/autonomous-optimization/backend-investigation/browser-baseline
```

必须由根代理用真实浏览器打开测量地址，执行实际点击、选择和输入。探针忽略 `isTrusted=false` 事件。完成一组操作后，通过浏览器允许的只读 DOM 通道读取：

```javascript
JSON.parse(document.getElementById('performance-probe-results').textContent)
```

`samples` 中每项记录原始时间点、触发类型/控件、前后 URL、可用耗时、稳定确认耗时、隐藏/显示状态与完成原因。只把 `completion_reason=stable`、`request_error_count=0` 且人工确认内容正确、页面前台、无请求未完成的样本用于正常可用耗时；`timeout` 与 `superseded_by_*` 单列。每个页面操作重复至少 5 次用于发现波动；拟作收益结论的路径增加到 10 次或更多，并保留首个冷浏览器导航、后续暖导航和首次进程读取的区别，不能声称清除了操作系统文件缓存。

起点为真实 `click`、`change` 或 `input` 的事件时间，导航起点为 Navigation Timing 的 0。终点为所有被探针观察到的 `fetch`、响应正文消费完成，以及最后一次 DOM 变化之后的两个动画帧。导航另要求 `readyState=complete`，属于完整 load 口径，不与页面内交互混算。再等待 180 毫秒无新变动才确认本项稳定；`content_ready_ms` 不包含这 180 毫秒，`stability_confirm_ms` 包含。连续输入或下一个动作提前发生时，前一项标为被新动作替代，不伪装成正常样本。

此终点是可复验的“网络与 DOM 稳定”代理指标，仍需实际页面验收。图片解码、CSS 动画、原生下拉窗和 Worker 不参与可用终点；图片请求出现在资源列表。音视频 `loadedmetadata`、`loadeddata`、`canplay`、`playing`、`waiting` 和错误另存 `media`，不把正文出现等同可播放。真实 `scrollend` 另存 `scrolls`，双帧不能证明平滑定位完成。`resources`、`longtasks`、`navigation` 保留浏览器原始 Performance Entry；`requests` 区分发起、响应头及 Fetch Promise 结束。资源和长任务回调只积累，不在测量窗口反复序列化整个结果；媒体在动作活动时也只积累。后台 `http.jsonl` 记录 GET/POST/PATCH 的 method、path、实际 status、异常类型及处理墙钟耗时，不记录载荷；日志格式化和追加在计时外。未发出状态行即异常时 status 为 null，不伪装为成功。服务耗时不包括浏览器排队，因此不能代替用户等待。

## 页面到后台的调用链

| 用户场景 | 页面实际请求 | 主要数据读取 | 应测起止点 |
| --- | --- | --- | --- |
| 任意页面首次打开 | `app.js:init` 同时加载 `/api/instance`、`sources?with_revision=1`、`comments`、`framework`、`configurations`、`story-structure`、`screenplays`、`screenplay-summaries` | 所有资料、全部评论校验、结构全部修订、全部剧本集正文 | 导航开始→当前页面正确内容可读；各请求单列 |
| 制作思路及两子页 | 首次还加载 `/api/production-approach`；页面内复用已读方法文档 | `approach.read_document` | 真实子页点击→正文稳定；首次导航另列 |
| 采编、结构、剧本的版本/集/场 | 初始化结果在前端切换；评论保存后 `/api/comments` | 既有全量载荷；保存后重新验证所有评论目标 | 点击→准确正文与评论可读；保存返回/刷新分别记录 |
| 制作拆解、全剧镜头制作 | `/api/production/breakdown?episode=…` 后 `/api/production/scene?object_id=…&revision_id=…` | `production_breakdown.catalog`、`ui_projection.scene` | 选集/场→逐镜全文与对应素材可用 |
| 实体管理索引与大卡 | `/api/production/index?view=settings` 后 `/api/production/entity-review` 或 `/api/production/card` | `material_entries`、`entity_summaries`、`generation.snapshot` | 点击→列表或大卡完整；层叠关系操作单列 |
| 素材管理筛选/翻页/素材详情 | `/api/production/breakdown`、`/api/production/materials`、`/api/production/card` | 每次重建 `material_entries`，筛选后分页；准确版本与候选 | 筛选操作→列表和所选详情都可用；输入自带 150ms 防抖须计入用户耗时 |
| 组合与历史 | `/api/production/index?view=history`、`/api/production?object_id=…`；按需 readiness/package | 当前组合索引与准确详情 | 页面/历史切换→准确内容；检查和清单独立 |
| 评论及配置写入 | `POST/PATCH /api/comments…`、`PATCH /api/configurations/…` | 并发版本校验、事件追加、保存后 GET 刷新 | 点击保存→成功且当前界面可见；写入只在可恢复的隔离快照 |
| 图片/音视频预览 | `/api/production/files/…` 与 Range | 原件文件读取；历史受管档案按需重建 | 点击→图片可见或 metadata/canplay；传输及首帧分开 |

## 优先验证的窄候选

1. **全站首次加载等待评论校验。** `server.py:204` 对每条评论执行 `anchor_state`；`Store.validate_target` 逐条读取并解释准确修订、生成可评论文本，`SOURCE` 又重新计算文档摘要。入口没有 `production.read_scope`，集中素材内容树也不能在整批评论间复用。优先测评论数、目标修订去重数、SQL 次数、内容树展开次数、JSON/摘要 CPU。只读事务内复用可减少重复工作，仍必须逐条验证锚点、跨请求立即重新读取；不能缓存整个响应或跳过失效锚点校验。
2. **逐场镜头上下文重复扫描。** `ui_projection.scene` 为每个镜头调用 `production_breakdown.context`，后者两次调用相同的 `exact_scoped(RELATION, revision)`。`exact_scoped` 按对象种类和 JSON 中准确范围修订查历史，再排除该范围内更新版本；需测 SQL 查询计划与扫描成本。先复用同次上下文已经读出的关系列表；若扫描为大头，再评估按 `json_extract(payload,'$.scope.revision_id')` 和对象/版本的窄索引。索引必须保持历史范围语义，不用当前对象头替代。
3. **素材列表/逐镜页面全量重建。** `material_entries` 每次加载需求、当前资产、历史结果关联及适用关系，再为每项调用准确身份与归属；`material_list` 最后才筛选分页，并对所有筛选选项反复计数。需要先测各阶段时间和返回大小，才选择减少投影或单次扫描。不能因此只看当前 40 项而漏掉筛选总数/历史候选/复用归属。
4. **集中定义展开 CPU。** `material_storage.expand` 已在 `_production_reads` 中按内容键缓存，不能再归为待实现缓存；不过返回每个内部对象/数组时都 `deepcopy`，相同大子树在逐层展开和投影时可能重复复制。需 cProfile 证实；任何精简复制都必须防止返回对象与缓存、同次不同投影或重复子节点共享可变引用。未经独立验证不改。
5. **旧详情入口缺少读范围。** `/api/production` 的 `snapshot` 直接读全部准确历史/素材版本；共用卡入口外包读范围，但旧链接、历史切换和关联细节的直接请求没有。可先测试用同一只读事务包裹该 GET 是否在保持完整响应一致前提下减少内容树重复展开。写入入口不套只读清理。

## 后台测量纪律

HTTP 测量与页面互斥；先用 `http_baseline.py` 默认每端点一次发现慢路径，再决定需要 50 样本的窄路径和预算，不对超慢端点自动跑满。正式对照按固定端点顺序串行读取完整响应，首个请求另列，预热 3 次后每端点至少 50 次。原始样本记录状态码、字节数、JSON 规范化 SHA、总时长和顺序；报告中位数、最小/最大、P95（排序后向上取整第 95%）。同条件 A/B 应包括完整响应相等性，不能只比较耗时。

SQLite/CPU 诊断在原一致数据库上通过 `mode=ro` 打开，只读连接不得调用会初始化表结构的 `Store.__init__`。用 `Store.__new__` 绑定现有只读连接并设置 `material_storage.row_factory`，对与 HTTP 相同的函数调用做单独 SQL trace 和 cProfile。计时样本不得同时开启 profiler/trace；统计时保留查询参数，按完整 SQL 和去参数模板分别汇总，区分内容树点查与实际历史范围扫描。查询计划只用 `EXPLAIN QUERY PLAN`。任何写性能样本必须先由主协调批准在独立副本执行并记录准确恢复方式。

`http_baseline.py` 默认只允许本任务的 62605/62606 环回地址，只有 GET；每请求和整批都有严格墙钟上限，超时即停止全批，避免单线程服务仍在计算时叠加请求。输出必须在本调查目录下。`db_diagnostics.py` 提供 `timing`、`profile`、`trace` 三种分离模式；后两种强制单次，不把 profiler/SQL trace 开销混入正式计时。支持素材条目、素材列表、实体索引、准确场次、实体审阅、评论及单条详情，另有只读规模/索引清点；有 SQLite progress handler 和墙钟截止，不初始化/迁移/写业务数据。

## 首次 HTTP 探索结果

主协调于本轮北京时间 08:23 分配独占窗口；执行 62605 串行完整 GET 共 15 项，每项 1 次，整批 4.18 秒，全部 HTTP 200，无超时。原始样本、响应 SHA、环境及摘要见 `http-discovery-1/`，准确请求见 `routes-window1.json`。这是已运行的探索，不是最终性能基线，不能从 n=1 推断稳定波动或收益。

| 请求 | 单次完整响应耗时 | 响应字节数 | 调查意义 |
| --- | ---: | ---: | --- |
| 实体索引 | 1128.3 ms | 1,568,571 | 与素材列表共用条目聚合，优先定位 SQL/CPU |
| S001 准确场次逐镜 | 1037.7 ms | 7,420,969 | 后台聚合和大载荷都需分开观察 |
| 李寄实体审阅 | 753.2 ms | 16,407,761 | 完整历史大载荷，不能仅靠后端耗时代表页面可用 |
| 素材列表 | 651.9 ms | 54,627 | 载荷较小而等待明显，适合先检查全量聚合成本 |
| 评论 | 97.9 ms | 235,487 | 初始假设热点，当前单次结果弱于制作聚合，降低优先级 |
| 系统配置 | 97.6 ms | 5,632 | 需复测是否文件枚举/图标验证占用；暂不下结论 |
| 首集制作目录 | 56.2 ms | 302,194 | 未显示为本次最慢路径 |
| 其余八项 | 1.3–18.9 ms | 原始样本分别记录 | 未显示为本次最慢路径 |

首次探索后已完成 `material_entries` 等只读诊断并实施 AO-PERF-001 有界候选。后台对照及内存代价见 [A/B摘要](AO-PERF-001-ab-summary.md)；真实页面收益、独立最终复核和交付决定由主协调继续推进，不将后台测量写成页面通过。
