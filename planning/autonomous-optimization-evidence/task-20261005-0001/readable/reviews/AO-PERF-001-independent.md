# AO-PERF-001 独立审查

审查者 `01a10965-5d9d-7e12-b37f-7f4b4ba15ed6` 未参与本项实现。初审按主协调要求只读核对系统 worktree 未提交 diff 及实现者说明；随后在根代理明确授予的独占 CPU 窗口运行聚焦回归和独立边界验证，完成后立即释放窗口。未操作浏览器、正式资源或采集性能统计。

2026-10-05 08:41:37 +08:00 核对 SHA-256：`material_storage.py` 为 `d62db9375dd85647aa54df9acbec3d67e84a2236324410f713523c99d07c3b8b`，`test_material_model.py` 为 `86a2c59ef70e63ea024d8eb90dc1a9a0ac9b4430cdbaa2ac802fd383d2bb37cc`。

## 静态结论

未发现当前实现缺陷，**正确性独立复验通过：46 项聚焦回归及 2 项独立组合边界验证全部通过**。尚未据此证明性能收益或完成最终页面验收。产品改动仅为 `review_desk/material_storage.py` 的 row factory 内部缓存，新增测试仅在 `tests/test_material_model.py`。未改 schema、API 字段、媒体、版本或生成／采纳方式。

缓存只存在于已有 `_production_reads`，以完整物理 payload 字符串作键、成功还原的字符串作值。命中分支不会调用 hydrate；没有误用会预先求值的 `setdefault(raw, hydrate(...))`。失败前不入表，原 hydrate／expand 校验保持。`record_view` 仍每次 `json.loads`，不会共享调用方可修改的 dict/list。已有 read_scope 的 finally 删除整个范围缓存；未添加持久 Store 缓存或跨请求失效机制。

现有 read_scope 是一致读事务与生命周期边界，不是 SQLite 强制只读权限；本改动没有扩大它或新增写流程包裹。完整内容地址不可变约束与完整 envelope 键保证同次范围的准确读取，不应另把可变记录投影放入该缓存。

## 六项边界与证据

| 边界 | 当前代码／测试证据 | 状态 |
| --- | --- | --- |
| 相同物理输入复用与输出等价 | 新测试通过实际 SQLite row factory 连续读相同参数，断言 hydrate 次数及 payload 等价 | 聚焦回归通过 |
| 不同身份／原始布局不串 | 完整 raw 作键；新增标题、scope、非规范原始 JSON 排版重复正反顺序读取 | 聚焦回归通过 |
| 可变投影独立 | 缓存 str；新增测试修改首个结果的嵌套 generation.prompt，第二次及后续读取应保持原值 | 聚焦回归通过 |
| 跨范围、异常、并发新写入 | 新测试核对范围删除与未包 scope 时仍重复 hydrate；既有 entity read scope 测试涵盖 concurrent writer 与下一读可见 | 聚焦回归及具体需求修订组合验证通过 |
| 缺失／损坏仍拒绝 | hydrate 仅成功后写 cache；新增用例在临时库注入缺失／物理损坏，连续两次仍调用并报错，异常清理后修复可见 | 聚焦回归通过；另独立验证重叠字段连续拒绝且不缓存失败 |
| 原始文本、解析及恢复准确 | 新测试非规范 JSON 返回准确原串、自定义 resolver 不借用 row factory 缓存；既有 material model／independent 套件含数字、转义、空白、原件与空实例恢复 | 聚焦回归通过；实际数据完整 HTTP 响应等价另验 |

测试本身没有修改生产约束；删触发器／注入损坏只发生在 fixture 临时数据库。SELECT 参数构造用例实际经过 row factory，能覆盖本次修改；真实 material_entries 调用路径仍需完整 HTTP 响应与页面复验，不能仅凭单元样例替代。

## 独占验证结果

系统 worktree 执行 `NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost PYTHONPATH=.:tests python3 -m unittest test_material_model test_entity_read_scope test_material_plans test_ui_material_independent -v`，46 项通过，运行 4.835 秒，退出码 0。原始日志：[聚焦回归](AO-PERF-001-focused-tests.log)。

2026-10-05 08:50:56 +08:00 完成独立组合验证，结果及准确文件哈希见[独立边界日志](AO-PERF-001-independent-boundaries.log)：

1. 临时 SQLite WAL 库建立准确需求并经实际 row factory 缓存。另一 Store 连接提交新提示词修订；原读事务直接重新 SQL 读取仍见旧 ID／完整 payload。退出后缓存与事务均清理；下一 scope 读取新 ID／新提示词，并按旧 revision ID 得到准确旧 payload，同次范围容纳新旧两个缓存键。
2. 在物理 envelope 中加入与素材字段重叠的 purpose，经实际 row factory 连续读取两次，均拒绝 `overlapping material content fields`；两次失败均未进入 hydrated_payloads，退出后正常清理。

独立验证使用既有 fixture 临时库，没有修改测试文件、产品实现或真实预览数据。测试时两产品文件 SHA-256 与初审一致。窗口已向根代理明确释放；相同输入下不重复运行该组。

## 仍待性能与页面验证

性能验收需对应版本的全量 HTTP 响应 SHA／字段内容等价、同条件原始重复耗时和波动，以及独立进程 RSS 对照。缓存会在每次请求内额外持有 raw→hydrated 字符串，应说明峰值内存代价；不能因生命周期短便假定零代价。后端加速不直接证明页面改善；Python 服务重启且版本核实后，主协调以冻结探针完成受影响页面和功能复测。

本记录与实现者的 `backend-investigation/AO-PERF-001-review.md` 分开，后者不是独立审查。未修改产品；正确性独审已通过，性能与页面收益以其实际证据另行判断。
