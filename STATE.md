# 当前状态与下一步

## 当前成果与运行依据

- 本机 `codex.task` 已启用 v0.2.0；后续跨仓迭代由一个故事任务管理各仓隔离工作区，项目适配消费逐仓 Git 交付回执。已执行旧任务继续使用原发布后端；历史资源的纳管、保留用途与清理状态读取任务账本。规则与入口见 [生成工作区流程](production/generation-workspaces.md)。
- 后续创作或系统修改按新请求确定范围；发布、依赖、执行和完成状态统一查主项目 `.codex-task/tasks.json`，不在此复制任务列表。不恢复已结束的自主优化计时或单次生成授权。
- 当前作品为方向三《把灯带回家》、故事结构第十稿、精修九定稿候选和剧本版本四。用户已确认版本四为制作终稿；准确依据见 [制作输入锁](production/source-lock.json)，作品与素材的具体认可仍按各自准确记录判断。
- 制作拆解、完整状态、素材版本与候选体系已交付；全剧首轮 251 个图像状态和 42 份新音色已有成果，逐项用户认可范围见 [素材交付](production/full-generation/README.md)及其认可记录。四首歌曲的 10 份整曲录音已增量发布到正式审阅入口，最新草稿与已有录音分开，见 [歌曲入口](production/song-publication/README.md)。这些成果不表示全部素材或音频质量已接受，也不表示动态分镜或成片已就绪。
- 正式入口为 `http://127.0.0.1:3000/`，正式库为主目录 `.runtime/review.sqlite3`；运行身份从正式主目录的 `config/instance.json.review_desk_commit`、实际容器镜像与准确挂载回读。当前工作区配置锁定交付候选；正式应用、页面验收和双仓推送是否完成，以主项目任务账本及对应冻结发布包的实际回执为准。

自主优化任务的历史发布与验收回执位于 `.codex-task/worktrees/task-20261005-0001/.runtime/autonomous-optimization/delivery/`；任务完成及故事推送结果以主项目账本为准。[运行报告](planning/autonomous-optimization-run-report.md)与[交付说明](planning/autonomous-optimization-delivery.md)保留确认前的测量及操作背景，其“待确认”表述是历史时点，不代表当前任务未完成。小卡任务的实际发布与收尾回执沿下方交付入口读取。

- 前置大卡、编号、引用与旧关系说明清理已正式交付；原 359 项状态归属与 34 份旧说明清理依据见[大卡交付包](production/entity-material/README.md)及任务账本。其确认前文档保留当时测量，不作为当前“待发布”状态。历史保留状态的后续物理清理与现行恢复入口见[实体大卡第二版交付](production/entity-card-v2/README.md)。
- 共用小卡、实体／素材管理三列分组分页、准确集场筛选和多层返回已在双仓隔离实例实现并真实验收。范围、来源、逐项证据、唯一系统候选及代码发布／恢复步骤见[小卡交付](production/small-cards/README.md)。本次不发布隔离测试评论、采纳或合成夹具，不迁移业务数据。

- 制作拆解页的七项阅读优化已在独立双仓工作区和隔离库实现，覆盖全剧目录、准确历史、剧情高亮、评论与素材集合；交付输入、逐项实际证据、准确系统候选和正式发布／恢复入口见[拆解页优化交付](production/breakdown-page/README.md)。隔离夹具及测试评论不发布，业务数据增量为 0。

- 镜头制作导航、版本与准确参考选择已在双仓隔离实例实现并实际验收；整章对应、选择／生产校验、系统候选、正式发布及恢复入口见[镜头制作交付](production/shot-production/README.md)。正式应用和推送以主账本及冻结包回执为准；隔离选择、评论与离线视频不发布，业务增量为 0。

- 实体大卡第二版覆盖标题版本、基础依据、完整关系图、状态双 Tab 和素材选择；90 个历史独立状态及其 143 份正文已在隔离候选中清理，保留 269 个状态对象。准确身份、全部引用、数据保全、浏览器证据与正式应用步骤见[第二版交付](production/entity-card-v2/README.md)。正式交付和清理是否完成，以主任务账本及冻结包实际回执为准；有效恢复只使用该交付的净化包。

- 全站视觉与系统配置已形成双仓候选，十三子页桌面／窄屏、关键交互、完整图标上传与取消路径及必要自动检查完成。覆盖、准确系统候选与恢复步骤见[视觉交付](production/system-page-style/README.md)；正式应用、页面验收、双仓推送和结项以主账本及本机冻结包实际回执为准，隔离测试数据不发布。

- 制作思路两页按故事七步与制作十步重构，覆盖全剧交付和返修；正文、连续例子、准确输入边界、方法专用定位修复与实际验收见[制作思路交付](production/approach/README.md)。正式应用和双仓身份仍由主账本及本任务冻结回执确认。

- 关系图联动选择、完整曲线布局与缩放，以及实体／素材小卡标题和总量信息已在双仓隔离实现并验收；只读计数契约、逐项证据、准确系统候选和发布／恢复步骤见[本次交付](production/entity-cards/README.md)。正式服务与推送结果沿任务账本及本任务 `.runtime/entity-cards/release-final/run/` 实际回执读取，业务数据增量为 0。

- 两页与全剧参考重构已正式应用，覆盖 17 集、42 场、297 镜及全部 297 个当前视频方案。内存问题已修复，集／场编号在准确剧本版本内唯一，镜头及其他对象保持实例内唯一，V/C 保留局部顺序。逐镜语义、连续性、完整路径、生产保护、真实浏览器与发布后独立恢复均有准确证据。交付与恢复入口见[本轮交付说明](production/breakdown-shot-v2/README.md)，最终推送与任务完成状态读取主任务账本。

## 后续工作边界

- 歌曲尚有实唱词音不对应、Lyria 原生无损 WAV、逐句时间／新曲调短参考、角色演法及正式剧本唱词同步等缺口。用户要求以现状完成阶段交付，尚未接受音频质量；后续另定制作范围和调用授权。准确成果、意见与用法见 [歌曲交接](production/songs-review.md)。
- 后续视频、动态分镜及组合工程按准确剧本、素材与采用逐项推进；不能将首轮素材覆盖视为第一集完整媒体交付。已有设计入口见 [制作总览](production/README.md)、[逐镜拆解](production/breakdown/README.md)。
- 最近优化报告记录了重复评论定位约 850 毫秒的成本，未证实稳定写入提速；功能覆盖中图标上传部分验证受阻，方法文件缺失／损坏两项未实测，部分窄屏标题布局和历史生成说明仍有已披露限制。后续触及这些路径时按报告补验，不继承“全面通过”的结论。完整边界见运行报告。

## 尚需收尾的本机资源

- 用户明确要求保留 `task-20261005-0001` 的故事／系统 worktree 与分支，用于准确追溯，不自动执行工作区退役。
- `task-20261005-0001` 工作区 `.runtime/autonomous-optimization/` 下的 `final-preview/`、`final-coverage-song-restore/` 仍存在。结项回执记载当时因共享 VM 文件句柄保留；62608 预览已停止。本轮只确认目录存在，未重查占用。下一次资源清理由执行清理的 Agent 核对当前使用者、文件身份及恢复用途，释放后按原清单精确处置，不停止共享 VM；依据为该任务 `delivery/cleanup-final-apply.json`、`delivery/pre-complete-receipt.json` 和受管收尾独审。
- 正式发布目录、正式库、原件，以及尚用于发布追溯／恢复的回执与数据库保留；较新恢复基线替代且追溯用途结束后再核对移除。已删除资源的数量与经过只留原清理回执，不在本文件累计。

- `task-20261005-0002` 保留故事 worktree、双仓分支、正式冻结包、净化恢复包及必要验收回执，用于准确追溯；第二版正式应用后其旧恢复数据不得回灌，向前恢复沿第二版净化包。旧关系原文、测试库与预览重复副本已清除。入口为该任务 `.runtime/entity-material/release/run/completion-operational-receipt.json`。工作区须在会话、进程和挂载释放后通过受管入口清理；恢复包在被新基线替代且追溯用途结束后再核对移除。
- 小卡任务保留故事 worktree 与双仓分支，发布冻结包及一致性备份用于准确恢复。隔离预览在正式页面验收后停止并按准确路径清理；实际删除与回读在[资源记录](production/small-cards/evidence/cleanup-before.json)及任务本机 `.runtime/small-cards/release/run/cleanup-final.json`，后者以实际执行回执为准。工作区退役须待 TUI 退出释放清理锁，另用 `codex.project task cleanup`。

- 拆解页优化任务保留故事 worktree 与双仓分支，冻结发布包、正式一致性备份和回执用于恢复；预览库与夹具在正式验收后清理，实际结果见本任务 `.runtime/breakdown-page/release-final/run/cleanup-final.json`，首轮清理回执在原 `release/run/`。待 TUI 退出释放锁后，工作区另由 `codex.project task cleanup` 退役。

- 镜头制作任务保留故事 worktree、双仓分支与冻结发布包，供准确追溯及恢复；正式验收后停止隔离预览并清理无效库与夹具，实际删除及回读读取本任务 `.runtime/shot-production/release/run/cleanup-final.json`。待 TUI 退出释放锁后再由受管清理入口退役 worktree。

- 实体大卡第二版任务保留故事 worktree、双仓分支、冻结发布包和净化恢复入口，用于准确追溯与向前恢复；实际过程资源清理读取本任务 `.runtime/entity-card-v2/release-final/run/cleanup-final.json`。旧库、浏览器夹具及重复预览在正式验收后核对清除，worktree 退役待 TUI 退出释放锁后另走受管入口。

- 视觉任务保留故事 worktree、双仓分支、最终冻结包、正式一致性备份与必要检查日志，用于准确追溯与向前恢复；实际过程资源清理和仍占用文件读取本机 `.runtime/system-page-style/release-accepted/run/cleanup-final.json`。责任为该任务执行者：正式验收后停止隔离服务并清除无效库、夹具及重复副本；共享 VM 持有的文件待释放后按回执清单处置，不停止共享 VM。故事 worktree 待 TUI 退出释放锁后受管退役。

- 制作思路任务保留故事 worktree、双仓分支、准确冻结包和必要正式一致性备份，用于追溯与恢复；隔离过程资源在正式验收后清理，实际结果读取本任务 `.runtime/approach/release/run/cleanup-final.json`。TUI 退出释放锁后再受管退役工作区。

- 关系图与小卡任务保留故事 worktree、双仓分支、冻结包及正式一致性备份用于追溯和代码恢复；预览与夹具在正式验收后核对清除，实际删除和占用项见本任务 `.runtime/entity-cards/release/run/cleanup-final.json`。TUI 退出释放锁后由受管入口退役工作区。

- 两页与全剧参考任务保留双仓工作区与分支、准确逐镜基线、最新正式数据独立恢复和冻结发布回执；本任务预览已停止，失效过程资源的实际删除与回读见[本轮交付说明](production/breakdown-shot-v2/README.md)。恢复资料被新基线替代并结束追溯用途后再移除，工作区退役等待 TUI 释放锁。
