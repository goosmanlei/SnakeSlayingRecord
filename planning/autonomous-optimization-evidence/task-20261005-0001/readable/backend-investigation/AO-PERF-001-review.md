# AO-PERF-001 候选变更

实现仅修改系统 `review_desk/material_storage.py` 和 `tests/test_material_model.py`，尚未提交。准确补丁及摘要在本目录 `AO-PERF-001.patch`、`AO-PERF-001-implementation.json`。已完成两个文件的 AST 语法解析和 `git diff --check`；未运行测试、修改后的性能负载或真实页面验证。

`row_factory` 在既有 `_production_reads` 范围内，以完整原始 payload 字符串为键，复用 `hydrate` 成功返回的字符串。没有读取范围时仍每次执行原路径，失败结果不进入复用表。`hydrate`、`expand`、自定义 resolver 以及可变记录投影均未修改；范围结束和异常清理由原 `read_scope` 承担。复用不减少响应字段或原件，不改变数据库结构。

新增三个测试，分别覆盖同次范围内复用与独立投影、跨范围重新读取、未包范围时不复用；相同素材字段而不同标题/归属/原始JSON排版不串；自定义 resolver 不受影响；丢失/物理损坏内容重复报错、异常清理及修复后的下一次读取可见。物理损坏只在测试临时库中注入，正式约束未改。

主协调安排测试窗口后，建议在系统工作区执行：

```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost PYTHONPATH=.:tests \
  python3 -m unittest test_material_model test_entity_read_scope test_material_plans test_ui_material_independent -v
```

这组覆盖新增边界、原有并发写后可见、异常事务释放、准确历史、导出及空实例恢复。随后用同一实例、端点和数据复测 HTTP 完整响应 SHA 及时间；独立进程对照 RSS，确认复用字符串的内存代价。根代理的浏览器进程在本变更完成时仍加载旧 Python 代码，必须由根代理明确重启并标识新候选，不能将已打开服务当作新代码验证。

建议独立审查重点是原始完整字符串作为键是否覆盖全部身份/原始排版、异常是否可能缓存半成品、`record_view` 是否继续构造独立对象，以及新增测试是否真正走两次数据库 row factory。没有性能复测前不将 AO-PERF-001 标为收益已证实。
