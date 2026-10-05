# 评论启动读取：单次 SQL trace

本次证明，同一请求会多次读取并重新解析相同来源和准确修订，值得评估**仅在单次请求内复用已读内容**。最清楚的窄切口是 SOURCE 原文及其摘要：127 次读取只涉及 11 个来源。尚未实现优化，也没有测得正常运行或页面收益。

本次仅运行现有 `db_diagnostics.py --operation comments --mode trace --repeat 1 --max-seconds 30`，外层另设 30 秒超时。完整参数见 `identity.json`。诊断工具以 SQLite `mode=ro`、`query_only=ON` 打开既有 `preview/.runtime/generation-base.sqlite3`，跳过 Store 初始化，没有启动服务。返回码 0、`summary.error=null`、仅 1 个样本，采集 1,212 次 SQL、635 条不同 SQL，捕获的语句全部为 SELECT。诊断总计约 0.087 秒，包含 trace 开销，不能作为正常接口基线或与 cProfile 时间比较。

前后守卫均为本任务、新 T0 13:21:50、`armed`、监督有效。系统 HEAD 前后均为 `ddb602e3cd084f0420d16e67eb03a6a6fd25ca5c`，Python 源码指纹与 163,000,320 字节数据库 SHA 前后不变；数据库 SHA 为 `5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0`。规范化完整 JSON 响应 SHA 为 `a83c1d88eb1b1b757db8387c6fd56ae34e9340bdb41a1193e414c80f00ab4d19`，与此前 `startup-comments-profile-reset-01` 完全相同。原始输出见 `run.log`、`sql.json`、`summary.json`；身份回执只保存脱去 lease 的守卫摘要。

## 重复读取的准确规模

下表的“超过每键一次”是查询次数减不同键数量，只表示重复程度，不是已经消除的 SQL，也不是可承诺的时间收益。

| 读取对象 | SQL 次数 | 不同键数量 | 超过每键一次的次数 |
| --- | ---: | ---: | ---: |
| objects，按 object_id | 271 | 39 | 232 |
| revisions，按准确 revision_id | 271 | 42 | 229 |
| sources，按 source_id | 127 | 11 | 116 |
| material_comment_scopes，按 comment_id | 271 | 271 | 0 |
| material_plan_comments，按 comment_id | 271 | 271 | 0 |
| 全量评论列表 | 1 | 1 | 0 |

合计重复 577 次，正好对应 1,212−635。39 个对象涉及 42 个准确修订，说明不能只按 object_id 复用目标，更不能替换成当前 revision。本工具持久化的是 SQL 计数，没有保留各条语句的执行配对顺序，因此本报告分别列出 object 与 revision，不伪造完整 object/revision 配对分布。

11 个 SOURCE 的查询次数按降序为 40、16、12、12、11、11、10、5、4、4、2。最高者是 `refinement-07-lantern-home-v7`（40 次），其次是 `refinement-01-lantern-home-v1`（16 次）。完整键和频数、按查询次数分组的对象数见 `repeat-distribution.json`。

## 与此前 profile 合看

已有 cProfile 显示：271 次准确目标校验累计约 55.1 ms；其中 127 次 `source()` 约 12.6 ms，另有重复的原文规范化、编码及摘要计算。此次 trace 证明其中存在大量相同输入。可以在独立实现窗口评估请求内 SOURCE 内容/摘要复用，再用同条件普通计时和页面测量判断收益；不能把上述累计时间全部算成可节省时间。

其他成本不应混为同一修复：542 次评论范围查询在已有 profile 中仅约 1.3 ms，单独为它们引入批量化不是当前首选；本数据 profile 没有 `hydrate/expand` 调用，不能归因集中材料还原；6 次原件校验约 17.7 ms，其中原件哈希约 14.2 ms，不能为速度略过。首次进程导入也占少量时间，不能据此声称稳态回退。

## 若实现，必须保留的语义

- 请求内复用必须随本次处理释放；下次请求仍重新读取，写后立即可见。不要引入跨请求 SOURCE、当前头或完整评论响应缓存。
- 每条评论仍按自己的 object_id、准确 revision_id 校验归属；SOURCE 原文摘要仍须与该准确修订逐次比较。同一来源的不同历史修订、丢失或不匹配修订、失败后的下一请求都要覆盖。
- 每条文本评论继续核对 block、起止位置和引用文字；全局、时间、视觉、区域锚点分别保留原有规则，不能缓存某条评论的“有效”结果供其他锚点复用。
- 媒体保留准确 component、asset_file、原件存在性、字节数、哈希，以及时间范围和区域合法性检查。本轮没有证明 6 次原件检查引用相同文件，不提出去重或跳过它们。
- 保留所有评论、排序、材料/计划范围和失效原因。候选应与未改版全量响应逐字义一致，另外验证范围筛选、原文被更新、原件缺失/被替换、精确历史与请求后更新可见性。

只读诊断窗口在完成后已通知根代理释放；上述分布归纳由离线读取本目录 JSON 得到，无追加数据库查询、测试、接口调用或产品修改。C2 的旧 +52.8 ms 信号仍等待根安排的同轮页面 ABAB，本结果不单独确认其原因。
