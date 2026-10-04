# 素材数据迁移与恢复

本交付把明确共享的素材需求归到一个规范身份，并将版本的完整要求和制作方案集中存储。旧对象 ID、修订 ID、评论、采用及原媒体保持原身份；受管请求、回执和制作 JSON 改成可还原原字节的引用容器。Git 已提交历史不重写。

## 候选内容

`migration.json` 是准确增量发布包，引用 `../../export/material-content.json` 的共享内容图和 SHA-256。迁移按准确头、历史载荷、版本索引和归档哈希核对；不会用任务数据库覆盖正式库。`data-evidence.json` 记录物理存储和原字节核验；实际空库恢复、逆向及 HTTP 结果分别见 `restore-evidence.json`、`rollback-evidence.json`、`http-evidence.json`。`data-validation.md` 说明各项测试、统计口径与真实执行版本；独立审查证据另存于同目录的 evidence。

完整定义取自真实旧需求和调用。李寄基础音色 v2 的实际调用通过已保存的 prepared_plan 与显式 reuse 链追溯到原要求；实际输入与计划输入不一致的事实单独保留。更早版本缺少完整要求或输出时保持未知，不能用最新方案补写。

## 读取兼容

审阅台 API、CLI 和 Store 返回旧逻辑 JSON 与原修订身份。后台工具对受管归档使用 `scripts/material_model_io.py` 的 `read_json/read_bytes`，对 Schema 6 的 objects.json 使用 `read_framework`。媒体原件仍按正常文件读取，manifest 中的文件哈希校验物理交付字节；组件和历史请求的哈希校验还原后的原字节。

带 `--system` 的命令加载指定审阅台。独立运行的制作脚本需通过 `PYTHONPATH` 或 `REVIEW_DESK_SYSTEM` 指向本次兼容系统；缺少兼容读取器会明确报错，不把容器当请求发送。已封存的旧任务发布包仍按原准确 Git 提交和数据库基线校验，不能用新候选容器绕过其旧发布条件。

## 隔离复现

以下路径均相对于故事工作区。`INSTANCE` 必须是该工作区 `.runtime/` 内的独立实例，先从批准的基线准备；辅助脚本拒绝正式实例路径。

```bash
python3 scripts/material_model_migration.py --system SYSTEM --instance INSTANCE plan
python3 scripts/material_model_migration.py --system SYSTEM --instance INSTANCE apply --validate-only
python3 scripts/material_model_migration.py --system SYSTEM --instance INSTANCE apply
python3 scripts/material_model_migration.py --system SYSTEM --instance INSTANCE verify
```

`package` 将已应用并验证的隔离导出与引用容器写入当前任务候选，逐项确认媒体原件未变；`rollback --validate-only` 预演准确撤销，`rollback` 实际撤销该隔离增量。回滚保留无关后续写入；如果受影响素材、版本或归档已继续变化则拒绝覆盖。返回旧原始 JSON 基线时清理本功能的数据库触发器；首次初始化失败也通过 `prepare_legacy_runtime` 检查并清理，只有确认无引用载荷和已应用迁移后才能重启旧服务。

正式操作由 `scripts/ui_material_model_release.py` 沿批准的双仓候选编排。其数据库迁移使用 `apply_archives=False`，在故事 Git 归档落盘前，新服务可以读取旧原始文件；引用容器到达后优先从正式活库解析内容。先完成候选审阅和用户确认，再执行正式写入窗口，不将隔离测试视为正式发布。

Schema 6 全量导出包括历史逻辑身份、物理引用、唯一内容图和归档路径目录；空实例恢复会重建受管 production 归档路径。Schema 1—5 保持兼容；旧实例未完成完整定义迁移时继续输出 Schema 5，不输出缺绑定的 Schema 6。
