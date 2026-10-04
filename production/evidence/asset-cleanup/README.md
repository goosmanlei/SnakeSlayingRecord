# 资产审视证据索引

报告入口为 [资产必要性报告](../../../planning/asset-necessity-cleanup-report.md)。本目录记录执行时观察与验收；正式完成、用户确认和推送由唯一任务账本记录。

文件使用以下定位变量：`${STORY_MAIN}` 为主故事仓根，`${SYSTEM_MAIN}` 为其同级 `../story-review-desk-python`，`${TASK_WORKTREE}` 为本任务根，`${SYSTEM_EXTERNAL_WORKTREE}` 为主故事仓同级 `../story-review-desk-task-20260929-0006`。`${USER_HOME}` 表示执行用户主目录，只用于定位外部工具、LaunchAgents和CA依赖。`current-restore.json` 的 `baseline/`、`restore/` 路径以 `${TASK_WORKTREE}/.runtime/asset-cleanup/` 为基准；Docker预演的 `.runtime/` 路径相对于任务根。未替换的容器 `/instance`、`/app` 是容器内部路径。`runtime-cleanup-manifest.json` 是供安全守卫精确核对的本机操作输入，以 `root + path` 定位原挂载并核对完整容器身份；不是可移植部署模板。

- [物理清单统计](inventory/summary.json) 与 [逐成员清单](inventory/files.jsonl.gz)：包含隐藏、未跟踪、Git、任务账本、注册工作区和 `.runtime/`。按 `root + path` 定位，`rule` 连接 [用途规则](policies.json)；目录、文件、符号链接分别计数。不沿符号链接遍历外部资源，不读取秘密正文。逻辑字节不是唯一磁盘占用或可回收空间，硬链接与 APFS 克隆可共享存储。
- [故事用途](story.json)、[系统用途与接口](system.json)：明确受管文件、脚本/CLI、动态入口和兼容用途。故事清单的两个分工“未知”已分别由物理清单、运行和数据库证据承接，并非未解决的用途判断。
- [全部本地数据库](db-all-instances.json)、[结构签名与成员](db-schema-groups.json)、[正式数据审计](db-audit.json)：历史库只读列出表、列、索引列、外键与行数；正式一致性副本逐身份、关系和原件核验。历史库全量行内容没有重复审阅，保留其恢复/创作证据用途。
- [逐行身份哈希](db-row-fingerprints.jsonl.gz)、[准确关系](db-exact-references.jsonl.gz)、[评论锚点](db-comment-identities.json)、[逐原件哈希](db-media-hashes.json)：承接历史完整性，不能只凭表行数判断。
- [运行资产处置](runtime-decisions.json)、[运行目录用途](runtime-directory-decisions.json)、[进程与调度](runtime-processes-schedulers.json)、[共享构建缓存](runtime-build-cache.json)：按观察时点列明范围。仅4个旧容器进入批准候选，其他容器、镜像、挂载、缓存、卷与工作区保留。
- [准确运行清理输入](runtime-cleanup-manifest.json)、[独立复核](runtime-cleanup-independent-review.md)、[原镜像可用性](runtime-stopped-image-availability.json)、[探测副作用恢复](runtime-probe-side-effect-recovery.json)：清理输入不是执行回执，正式 `--apply` 尚待最终确认。
- [投影等价](system-projection-equivalence.json)、[CSS删除依据](system-css-removal.json)、[CSS保留部分等价](system-css-equivalence.json)、[完整导出恢复](current-restore.json)及[逐行恢复哈希](current-restore-rows.json.gz)、[性能比较](performance-comparison.json)、[真实页面操作](browser-observations.json)：分别回答实现、历史、性能与页面行为是否保持。

清单自己的 `inventory/` 子树显式排除以避免自指，目录节点仍列出；该子树固定只有 `files.jsonl.gz` 和 `summary.json`，由统计文件中的压缩清单哈希及 Git 候选保存。报告与证据生成会增加本任务文件，最终清单取冻结前最后一次观察，之后产生的提交对象、构建回执、运行快照按既有 Git／任务证据规则保留，不将不断生成的元数据伪装为静止分母。
