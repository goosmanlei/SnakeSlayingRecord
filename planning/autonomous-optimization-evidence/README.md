# 自主优化证据包

本包记录报告冻结时点已完成的产品改动、独立审查和实际验收。系统候选为 `c1da4cdce8c98bd52beafed1dc0a7b70887d8653`；核心收敛结论及限制见[独立综合终审](reviews/final-independent.md)。本包不是正式发布许可，也不声称所有113项均经浏览器通过。正文交付以[运行报告](../autonomous-optimization-run-report.md)为主。

- [基准与计时](run-baseline.json)：首次两仓代码、实际服务42文件SHA、一致快照时点/哈希/计数及监督历史观测。候选新增模块后的43文件与6个实际静态响应另列在最终预览回读，不改写启动基准。
- [历史意见](history-principles.json)、[发现](finding-index.json)、[覆盖](coverage.json)：原来源和ID保留，51项处置、113项不同动作/状态分别记录，分类数量不是通过率。逐行 `verified_scope` 与 `remaining` 决定实际覆盖边界。
- [测试证据](test-evidence.json)、[真实页面证据](browser-evidence.json)、[状态补充](status-addenda.json)：保留原失败与后续修复，区分Chrome、HTTP/数据库、真实函数和静态核对。技术媒体与假润色不是故事认可或真实模型效果。
- [源文件与目标哈希](source-index.json)、[体积与脱敏清单](pack-review.json)、[截图元数据](image-metadata-review.json)：摘要与源文件分别计SHA，截图逐张查看后按原字节复制，未编辑图片。
- [稳定引用映射](runtime-link-map.md)按准确 `source` 文件名定位聚合JSON；[发布入口](release-entrypoints.json)指向任务分支的受管脚本、README与三字段PROJECT包。`publication/`保留输入副本与历史护栏证据，不是执行回执。

本包含AO026单一可修订结论、AO049–051准确历史、用户素材准备阶段、两版组合/输出恢复、旧采纳与启动模型的证据。初审缺陷与根页面发现均保留。组合镜头清单只有真实点击、提示及后台200，未核到落盘JSON；旧采纳直链不等于完整可见历史链；同图重传因浏览器权限仍未实际验收。这些限制不因归包而消失。

路径符号：`TASK_WORKTREE` 是本任务工作区，`SYSTEM_REPOSITORY` 是独立系统仓库，`STORY_MAIN`/`SYSTEM_MAIN` 是两个主仓，`LOCAL_RUNTIME`/`LOCAL_PATH` 是本机未交付证据。原runtime文件名可在source-index查询；未收入者只是本机留存指针。环回页面URL仅说明验收实例，服务可能随后停止。截图来自各批当时状态，不改造为最终全页截图。

没有收入数据库、WAL/SHM、备份、媒体原件、依赖、工作区树、凭据/.env、活动监督租约、完整HTTP事件流或重复原始日志。正式实例在最后只读核对时仍为5b7de33、PROJECT v14，本轮未写正式库或切换服务。

AO044 在首次最终发布准备时另遇到 Docker 未设置用户的 `null`／空串等价误判，原失败和只读字段差异已保留。仅该字段的窄修通过24项作者检查及38个独立分支，见[发布护栏补审](reviews/release-process-normalization.md)；未把离线补验写成修后真实prepare、build或正式切换成功。原系统产品候选和覆盖矩阵不变。

故事最终提交、`_prepare_integration`、准确发布包prepare/build/preflight和真实优化停止回执在报告冻结后按序产生，单独留在本机`.runtime/`，由最终交付答复或任务回执引用；不再补写本包改变已冻结候选。本包不预设这些动作成功，也不代替用户最后明确确认。默认本地集成，不含推送。
