# 自主优化证据包候选

这是本轮可提交的最小证据候选，尚未完成最终候选绑定、独立终审和真实停止回执；不是发布许可或正式服务已切换证明。正文交付以 [运行报告](../autonomous-optimization-run-report.md) 为主，本包提供可核对证据。

- [基准与计时](run-baseline.json)：首次两仓代码、实际服务42文件SHA、一致快照时点/哈希/计数及一次监督观察；不含数据库或活动守卫状态。
- [历史意见](history-principles.json)、[发现](finding-index.json)、[覆盖](coverage.json)：保留原来源、原ID与原状态，逐项区分Chrome、HTTP/数据库和函数，113条分类不是通过率。
- [测试证据](test-evidence.json)、[真实页面证据](browser-evidence.json)、[后续权威状态](status-addenda.json)：原失败未抹除，后续修复另有明确证据。技术夹具和假润色不代表故事认可或真实模型效果。
- [源文件与目标哈希](source-index.json)、[体积与脱敏清单](pack-review.json)：摘要与源文件分别计SHA，截图逐张可见检查后原字节复制。
- `reviews/` 保留每批完整实质独审；`publication/` 保存准确三字段发布输入（两段背景与用户选择的素材准备阶段）及历史护栏证据，不能直接当可执行包或已发布结果。

路径符号：`TASK_WORKTREE` 是本任务工作区，`SYSTEM_REPOSITORY` 是独立通用审阅台仓库，`STORY_MAIN`/`SYSTEM_MAIN` 是两个主仓，`LOCAL_RUNTIME`/`LOCAL_PATH` 只指本机未交付证据。正文中的原runtime文件名可在 source-index 查询；未收入者仅为本机留存指针，不是可点击承诺。页面URL仅说明验收时的环回实例，服务可能随后停止。

目前未交付数据库、WAL/SHM、备份、媒体原件、依赖、工作区树、任何凭据/.env、活动监督租约、完整HTTP事件流或重复原始日志。早期截图中未涉及本项的旧界面元素可能被后续批次改变，按status-addenda解释；不把历史截图改造为最终截图。

最新补入 AO049–051、用户阶段选择与三字段增量独审、组合输出 v1/v2 和非空恢复、旧采纳补核及实际启动模型核对。覆盖表保留其原快照标签；新增页面与独审状态见 [状态补充](status-addenda.json)，不能将旧表中的待补项当作截至本包时仍未验。AO026 已有用户规则选择，当前实现／独审尚未归包，终版需另吸收。

[稳定引用映射](runtime-link-map.md) 提供 runtime 路径到包内目标；聚合证据按准确 source 查询。[发布入口](release-entrypoints.json) 指向受管脚本及当前三字段包。原两字段 Docker 演练与当前三字段真实 HTTP 核验分项保留，正式未 apply。[截图元数据](image-metadata-review.json) 核查全部选定 JPEG，未编辑图片。

本包可供根审阅与提交准备。最终绑定、停止和确认状态需真实产生后另行补齐，不能使用占位值冒充。
