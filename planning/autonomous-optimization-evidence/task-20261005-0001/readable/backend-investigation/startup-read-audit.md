# 轻量页面共用启动成本审计

本次只读取既有证据和代码、离线计算已保存 JSON，没有启动服务、发起请求、查询数据库或运行测试。新增文件只有本报告。审计于 2026-10-05 新计时窗口内进行；守卫检查为 `armed`，T0 为 13:21:50，监督锁与心跳有效。以下性能数字全部来自旧窗口，不能算作重置后的新测量。

现有证据支持把 **全量评论读取及准确锚点校验**列为下一项公共启动剖析对象。它已有稳定接口成本，而且旧 C2 页面批次中实际服务处理时间也增加。**尚不能断言该成本就是 C2 的代码回退原因**，不能提前承诺提速。配置接口同样存在约 30 ms 的真实成本，但目前缺少内部归因，优先级次于评论。

## C2 旧信号与服务日志核对

独立页面报告为 `../history-inventory/page-performance-candidate1.md`，原始文件为 `../browser/C2-{baseline,candidate1}-semantic-{0..4}.json`。Chrome 154、1440 × 900、DPR 1、macOS 26.6.2 arm64、62606 与探针 SHA 保持。基线系统 `b874b959af9c918a482e8488dc25cb0204ab5772`；候选准确状态由 `../reviews/candidate-browser-1.patch`（SHA `98d4cd479763f379a8b06e84d3c8a0c6f5c0ac9cdcf12eb091316a889660215b`）限定，不能把它等同于本次审计时的系统 HEAD。

两阶段各 1 次 navigate、4 次 reload。reload 页面语义就绪中位数 324.95 → 377.75 ms，增加 52.8 ms，保留为未解释变慢。连续阶段均值的变化为：导航至首批 API +24.12 ms，API 开始至末个 body 完成 +23.20 ms，最后 body 至语义捕获 +1.75 ms；10 份 C2 样本均无 Long Task 记录。该划分没有支持“评论面板布局拖慢了 C2”的证据。

本次进一步离线核对了 `browser-baseline-v3/http.jsonl` 和 `browser-candidate-v3/http.jsonl`。两份日志在对应时间范围内各恰有 5 条准确 C2 根导航，以 URL、时间范围和出现顺序匹配 5 个页面样本；基线根导航在日志第 3237、3272、3307、3342、3377 行，候选在第 3049、3083、3118、3153、3188 行。每次导航后均有同一组 8 个启动 API，均为 200、无异常。日志只有秒级时间，没有请求关联 ID，因此这是有顺序约束的旧记录对齐，不能推广为任意并发访问下的精确关联方法。

`probe_server.py:48` 的 `server_elapsed_ms` 从 handler 入口计至响应写入结束；不含 handler 前排队、连接等待及停止计时后的日志格式化和落盘，也不是纯 CPU 时间。下面只比较 reload 各 4 次的均值；这些 handler 在单线程服务内顺序执行，可求和，但不能把浏览器各请求累计等待再相加。

| 启动 API | 基线 handler 均值 ms | 候选 handler 均值 ms | 差值 ms |
| --- | ---: | ---: | ---: |
| instance | 0.120 | 0.130 | +0.010 |
| sources?with_revision=1 | 17.021 | 19.895 | +2.874 |
| comments | 45.593 | 57.978 | +12.385 |
| framework | 0.099 | 0.108 | +0.009 |
| configurations | 33.049 | 33.674 | +0.625 |
| story-structure | 1.494 | 1.396 | −0.098 |
| screenplays | 13.624 | 12.419 | −1.205 |
| screenplay-summaries | 0.309 | 0.300 | −0.009 |
| 8 项合计 | 111.309 | 125.900 | +14.591 |

可复核的主要原数组如下，均按样本 0–4 排列，首项 navigate 不进入上表：

- 评论 handler 基线：50.938、45.386、46.651、43.016、47.317 ms；候选：59.209、56.662、54.411、59.813、61.025 ms。
- 配置 handler 基线：41.332、33.234、33.285、32.443、33.234 ms；候选：34.043、34.861、32.861、33.209、33.764 ms。
- 8 项 handler 总和基线：128.084、112.592、108.919、113.727、109.999 ms；候选：127.585、127.313、119.476、128.636、128.174 ms。
- 根导航后、首个 API 前的 23 个脚本/CSS/探针 handler 总和，基线：7.932、11.281、4.876、8.220、10.184 ms；候选：11.336、9.083、7.064、11.197、11.738 ms。reload 均值只增加约 1.130 ms，不能解释浏览器该阶段约 24 ms 的全部差值；其余时间可能含连接、调度、传输、执行等，现有记录无法再分解。

这次对齐把旧 API 等待增加的一部分落到评论 handler，但两批相隔约 33 分钟、候选混有后端与 UI 改动，仍然缺少同轮交错对照。当前结论是“值得继续定位的成本和关联信号”，不是“已证明回退”或“已修复”。

## 所有页面共用的等待路径

`../system-worktree/review_desk/static/app.js` 的 `init()` 用 `Promise.all` 等待 instance、sources、comments、framework、configurations、story-structure、screenplays、screenplay-summaries 全部返回，之后才设置状态并切换到目标工作区。C2 因而也等待完整评论、故事和剧本数据。评论不是后台可自由丢弃的数据；这些请求目前同时支撑切页、准确定位和导航恢复，不能简单跳过或删减。

`ReviewServer` 继承 `HTTPServer`，单线程持有一个 Store。浏览器同时发起 8 个请求，不代表服务器并行计算。Store 初始化和迁移在服务构造时运行，不能当作每个启动请求的重复成本。服务已有空闲预连接的 2 秒超时；当前 C2 只有几十毫秒差值，没有证据支持改线程模型或超时设置。

独立暖态 HTTP 基线 `http-baseline-50/{environment,summary}.json`、`samples.jsonl` 和 `routes-window1.json`：每端点 3 次预热、50 次完整响应，未清 OS 缓存；系统为上述 b874 基线。评论 39.35 ms（38.64–41.43），配置 29.78（28.89–32.65），剧本 12.87（11.77–15.78），来源 10.02（9.37–11.32）；其他 4 个启动端点中位数 0.59–2.34 ms。它们证明绝对成本存在，但与页面批次、handler 埋点口径不同，不能混算节省量。

## 可证实的代码行为与待剖析原因

| 对象 | 当前可证实行为 | 证据强度及边界 |
| --- | --- | --- |
| 全量评论 | `server.py:204` 无筛选启动；`store.py:402–422` 为每条评论分别读取材料评论范围和计划评论范围；`validate_target` 再读对象、准确修订并校验各条锚点 | 旧库 271 条评论、42 个目标修订。按代码可推导至少 542 次范围查询及重复 target 读取机会，这是静态推导，尚无本端点 SQL trace；不能写成已测热点占比 |
| 评论的生产修订 | `validate_target` 的修订 SELECT 走全局 row factory；集中内容 payload 可触发 `material_storage.hydrate`，生产文本也会构造文本块；本路由没有 `production.read_scope` | C2 没有打开素材 UI，也不能断言完全不走材料还原。旧 `material_entries` 的数万条 SQL 或 profile 占比不能搬来解释评论 |
| 配置与 favicon | `store.configurations()` 只读 SYSTEM/PROJECT 两行；路由还调用 current favicon、catalog 和 `favicon.choices`。后者遍历 `export/assets/*`，对符合扩展名的文件调用安全路径、大小和内容验证 | 可疑的是目录扫描及逐文件验证，而不是两行配置读取；尚无其函数 profile。大于 256 KiB 的文件在内容读取前拒绝，不能夸大为每次解码所有生产图片 |
| 来源准确版本 | sources 路由调用 `store.objects()` 读取所有对象元数据，然后在 Python 中选 SOURCE 来附准确 revision | 当前 6,236 个对象，存在可以缩小查询范围的候选；尚未证明此部分占据 10–20 ms 中的多少，不能仅凭全表调用实施优化 |
| 剧本版本 | `screenplay.snapshot` 同样先遍历所有对象，再读取 STORY 及其准确分集 revision 内容 | 它交付完整版本/分集信息，不能为速度少返回历史。旧页面批次此 handler 反而略降，不应列为 C2 回退原因 |

优先级：评论剖析第一，配置内部剖析第二；来源/剧本按真正占比再决定。若评论成本主要是不可省略的内容校验，可能不值得改动；若重复读取和重建占主导，可再讨论只在单次请求中复用准确目标解析或批量范围查询。跨请求缓存、跳过锚点有效性、忽略原件变化、弱化写后可见性均不在已论证范围内。

## 最小后续窗口建议（本次未执行）

根先完成计划中的同轮 C2 页面 ABAB：固定准确代码、同一冻结数据、同一服务端口、Chrome/视口/探针、缓存策略；阶段切换记录 restart/warm-up，reload 与首次 navigate 分列。同步保留现有 handler 日志，窗口内其他代理不施加负载。优先回答“52.8 ms 信号是否随代码往返”，不要通过一次候选刷新宣告消失。

若另分配一个最小后台剖析窗口，首选已存在工具的 `comments` 单次 cProfile，而不是重跑全端点或改探针。下例相对故事 worktree；它打开既有一致库 `mode=ro/query_only`、跳过 Store 初始化，执行与现有 GET 同样的全量 comments + anchor_state，**不擅自增加 read_scope**。输出目录必须保持首次未使用；执行前后由根核对代码/库/原件不变和守卫。它只分解当前候选的成本，不单独证明旧版本回退，也不替代真实页面测量。

```bash
python3 .runtime/autonomous-optimization/backend-investigation/db_diagnostics.py \
  --system .runtime/autonomous-optimization/system-worktree \
  --database .runtime/autonomous-optimization/preview/.runtime/generation-base.sqlite3 \
  --output .runtime/autonomous-optimization/backend-investigation/startup-comments-profile-reset-01 \
  --label startup-comments-profile-reset-01 \
  --operation comments --mode profile --repeat 1 --max-seconds 30
```

重点检查 `hydrate/expand`、`production_text_blocks`、JSON 解析、SOURCE 原文摘要与 SQLite 查询各自累计时间和调用次数，累计栈时间不能相加。已有 `window2` 仅有 material/history/scene/entity/production 的 trace/profile，没有 comments、configurations 的实际输出。若 profile 指向重复 SQL，下一步才申请一次独立 trace；不要把 trace/profile 下的时间当作正常基线。配置接口若仍需定位，可另提精确覆盖路由的单次 profile；现有工具不支持 configurations，不在本次私自扩建。

## 本次代码定位身份

只读审计时系统 HEAD 为 `173c36f2de39bf6235d9d62565110226fb8a5dcc`，工作区仍有根代理的后续修改；本报告不将它视作干净最终候选。主要源码读取时 SHA-256 如下，便于区分旧性能批次与当前调查：

| 系统相对文件 | SHA-256 |
| --- | --- |
| review_desk/server.py | da74e2284f4cde80b9511ff75c8b07b94aa8417e00c96dce7676f205de600f6c |
| review_desk/store.py | 6a5fc51def7f6b9f06f59359b77c6429460d8f740ce97b3f02fa3a70abe211f0 |
| review_desk/material_storage.py | 94fee3397c40cd306f060e014d5646aed819fd2e455776efa014340bbb4f3560 |
| review_desk/favicon.py | 050151dea87a19726c1c8751876b7016f64489a1529960748f13da83685bcb65 |
| review_desk/static/app.js | a8af2d373c18b10da98511224657e4c95e710a1111e8f6f714071efded5dc707 |

后续若根调整源码或输入，应以新窗口记录为准；本次没有提交产品修改，也没有产生新的性能收益结论。
