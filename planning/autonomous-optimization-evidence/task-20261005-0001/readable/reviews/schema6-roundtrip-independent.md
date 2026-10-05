# Schema 6 实际导出／空实例恢复独立审查

结论：**本次快照和准确 Python 候选的恢复正确性独立复核通过，没有阻断项。** 原始运行总耗时 443.575578 秒；本独审只读复算 14.938 秒，没有重跑恢复、导出、测试、HTTP 或浏览器，也没有修改产品与业务库。

审查者 `/root/reset_supervisor`，真实线程 `01a10a85-fd7a-7021-aa28-a867f6dea1d8`，独立于 PERF002 实施者及本次运行执行者。审查于 2026-10-05T06:58:48.218779+00:00—2026-10-05T06:59:03.156667+00:00。审查前守卫 armed、监督锁和心跳有效、无错误；只读核验结束后已通知根代理释放窗口。

## 实际执行与身份

- 阅读了 `schema6-roundtrip-reset-01.py` 完整执行逻辑、主日志、receipt.json 以及 source-export／empty-restore／empty-export 三份 CLI 日志。三份 CLI 日志均为完整且相等的 Schema 6 manifest，没有异常或截断。
- 回执的系统提交为 `173c36f2de39bf6235d9d62565110226fb8a5dcc`，记录的 53 个 Python/JS/CSS/HTML 文件逐一与该提交 Git blob 的 SHA-256 相符。当前 30 个 Python 文件仍与当次指纹一致。根随后开展的 JS 修改不改变已验证的 Python 存储输入；本审查不把新 JS 认作已在该恢复运行中执行。
- 基准文件为 `preview/.runtime/generation-base.sqlite3`，SHA-256 `5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0`。独立复算前后，冻结快照、源克隆及恢复库三个文件各自的 SHA-256 都未改变。
- 原执行在全新目录下建立 source 与 empty，empty 在恢复前没有数据库和 production 目录。源克隆仅复制 manifest 资产；没有预置 empty/production。独审确认 source/production 仍不存在，而恢复目标确实新建了 1,018 份 production 归档。

## 独立复算结果

| 对象 | 核验方法及结果 |
|---|---|
| 22 张公共业务表 | 只读 SQLite `EXCEPT` 和行数核对冻结源、源克隆与恢复库，随后独立重算原始行指纹，与运行回执一致；包含所有准确修订、依赖、评论、事件、采用/判断、素材版本、归属和配置 |
| 全部 10,160 份准确历史 payload | 只读 URI 连接加候选 row factory，在两个独立 read_scope 中按 revision ID 逐条比较还原后的原始字符串；全部相等，不仅比较解析后 JSON |
| 78,889 内容节点、2,312 定义及 2,547 定义版本 | 全表原始行相等，内容图、定义来源及缺口没有丢失；原执行也实际经过 restore 内置 verify |
| 30 个素材别名 | 完整 alias_id、material_id、原始 evidence 行均相等，没有只用数量或当前头替代历史关联 |
| 1,855 份归档 | 对恢复实体逐个通过活跃事务 resolver 解码，长度和 SHA-256 与冻结目录保存的历史原文字节身份一致；837 份 export/assets，1,018 份 production |
| 1,314 个再导出文件 | source/empty manifest 与冻结公开 manifest 相等；1,313 个受管文件逐一匹配 manifest SHA，外加 manifest 自身物理字节哈希相同 |
| 非清单素材 | 恢复目标只有 1,307 个 assets 文件，preview 里另有的 91 个未列清单文件未被预置或冒充恢复 |
| 源克隆导出保全 | 原执行保存的初始、内存污染探针后、export 后全部表指纹一致；独审再以 SQL 与冻结源核对，包含私有回执和 sequence |
| 恢复库再导出保全 | export 前后全部表指纹一致；独审读取实体库并复算公共表与回执一致 |

真实定义 `a7b0e622d93c7a89cf647e5574a3083d9b566437cd012ae5d623bd1b2924c410` 的返回值隔离探针已在原执行中完成：本地修改第一次返回树，不影响已返回的第二份树、后续读取或存储表。独审检查了探针实现及 passed 回执，未重复执行该修改探针。PERF002 的重复位置和旧 recipe 广泛边界继续复用已通过且文件指纹未变的聚焦测试。

## 必须保留的边界

- `generation_publications` 的 2 行保存在冻结源和 source 克隆，恢复库没有该私有表。这是既有公开 bundle 边界，不是本批性能优化丢失；不能写“任意 SQLite 数据全量恢复”。
- sqlite_sequence 没有作为 bundle 数据序列化。此快照 comment_events=307、configuration_events=20 的计数器恰与导入最大 ID 及源值一致；这不是一般性承诺恢复已删除最大 ID 后留下的高水位。
- 1,855 份归档的“原字节”结论来自登记长度和 SHA-256 逐份核对，production 的源实体文件没有预复制。1,314 项是受管输出文件总数，包含 manifest，不是 1,314 个媒体原件。
- 原运行总计 443.575578 秒包含克隆、隔离探针、两次导出、一次恢复和全部比较。从阶段日志复算，restore 调用阶段间隔为 377.120622 秒（包含 CLI 启动与等待）。本窗口不是性能 A/B，不能与旧任务的 397.746 秒总流程直接比较并宣称收益。
- 原回执只有相对 elapsed，没有绝对 UTC 起止字段。总报告若需准确运行起止，应引用根的当次工具/守卫时间证据；不能将本独审时间或文件 mtime 冒充运行起止。此为报告解释补充，不影响恢复内容结论。
- 本轮只证明该隔离快照的恢复正确性；正式数据库未因此被发布或替换，浏览器验收仍单独成立。

## 证据

- [独立复算 JSON](schema6-roundtrip-independent.json) 与 [独立只读复算脚本](schema6-roundtrip-independent-audit.py)。脚本全部数据库连接为 `mode=ro` 与 `query_only=ON`，未构造 Store，未调用 export/restore。
- [原运行脚本](schema6-roundtrip-reset-01.py)、[原阶段日志](schema6-roundtrip-reset-01.log)、[原回执](../schema6-roundtrip-reset-01/receipt.json)。
- [源导出日志](../schema6-roundtrip-reset-01/source-export.log)、[空实例恢复日志](../schema6-roundtrip-reset-01/empty-restore.log)、[恢复后导出日志](../schema6-roundtrip-reset-01/empty-export.log)。
