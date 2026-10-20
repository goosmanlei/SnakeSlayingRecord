# 2026-10-20 生产制作性能诊断证据

本目录为 [任务完整规划](../production-performance-task.md) 的持久文字输入。复用发布前主会话完成的诊断，本澄清回合没有重新运行 profile、访问正式页面或执行优化。报告中的“本轮”指该次诊断，不能用它推断任务此刻的发布状态；任务状态只取主项目账本。

源目录为故事主项目 `.runtime/performance-diagnostics/20261020/`。诊断故事提交 `08c0b83e00d2ecac87b0875e6aee628174c6d9d3`，系统提交 `254d509cbe644f75e90344bc1ae40b7279aa418f`；执行从届时最新主干与正式数据开始，不回退旧代码套用数值。VPS 静态构建不同，准确运行提交仍须执行时核验。

| 文件 | 用途与保留边界 |
| --- | --- |
| [report.md](report.md) | 完整 104 行诊断报告；仅将源码路径说明改为 desk 仓库根及主项目相对 source，事实和数字未改 |
| [browser-scout.json](browser-scout.json) | 本机四页、大卡、静止／短播放、媒体请求的实际侦察值与测量边界 |
| [vps-scout.json](vps-scout.json) | 远端有界只读首包、全实体目录、静态指纹与未验证项 |
| [summary.json](backend-profile/summary.json) | 成片审阅单次隔离 profile、准确成片修订、CPU／调用／SQL 与嵌套耗时 |
| [erased-files-summary.json](backend-profile/erased-files-summary.json) | 删除回执查询单次 profile、操作数据规模和实际扫描计划 |
| [preparation.json](backend-profile/preparation.json) | 一次只读备份、19 份字层 JSON 的 hash／大小、成片与关联身份 |
| [cleanup.json](backend-profile/cleanup.json) | 诊断私有实例清理回执，62 文件／950,834,231 逻辑字节；不是磁盘空间回收实测 |
| [profile_backend.py](backend-profile/profile_backend.py) | 原始复现方法，含只读备份、禁网及准确目录清理；本轮未运行 |
| [task-history.json](task-history.json) | 相关任务实际完成成果及最新结果摘录，供区别已解决、新问题和独立残留；不是第二份任务账本 |
| [manifest.json](manifest.json) | 原取件路径、源／保存文件大小与 SHA256、诊断版本、临时授权请求指纹；JSON／Python 均逐字节一致 |

profile 用于定位重复工作，不等于正式 HTTP 性能或收益。累计函数耗时互相嵌套，不能相加；逻辑读取不等于物理磁盘 I/O。浏览器采样窗包括操作与阅读等待，不是页面加载时间；主线程任务不包括完整 Worker／GPU／解码成本。侦察样本不是严格冷启动或 P95，不能从静止小图推断全站无泄漏。

复现脚本会在自身目录旁创建私有实例并写入摘要。未来复现应先复制脚本到本任务 `.runtime/` 专属目录，核实际运行版本、输入规模、磁盘和路径后再使用；不要在本证据目录运行或覆盖历史摘要，也不把 `/app` 的旧运行路径当作任意环境都可直接执行的命令。源码和行号均须按执行时版本适配，数据副本与缓存按任务边界隔离。

二进制 pstats 保留在原本机诊断目录，未纳入 Git；现有 JSON 足以核核心数值，原 pstats 不作为任务恢复的必要依赖。已删除的约 951MB 实例不复制，正式数据库、媒体原件、凭据与完整签名 URL 不进入此目录。本会话无视听媒体输入；这些文字文件不登记为媒体附件。旧诊断目录归原诊断保留责任，不由本任务顺手清理。

本目录由任务执行者保留用于基线追溯、复现和验收，后续优化证据另在本任务运行目录收敛；不把旧诊断值覆盖成新成绩。确认替代材料能复现必要问题且无剩余追溯用途后，才按项目流程处理无用过程数据。
