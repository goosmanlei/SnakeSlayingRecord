# 制作思路全过程重构交付

本轮任务 `task-20261006-0006` 直接更新 `content/production-approach.json` 两页干净正文。先研究原型、方向、结构、逐段写作、读者审阅、剧本定稿及制作能力的形成，再按创作者的阅读和交接顺序成稿。生产制作重点解释全剧拆解、完整状态、素材方案、候选审阅、准确输入、有声预演、组合、交付与返修。

## 修改摘要

- 开头用简明流程总览串起全程；各阶段用自然因果说明为什么做、后台做什么、用户判断什么、得到什么以及何时继续或回修，去掉重复栏目和操作清单。
- 以歌本的劳动用途、毁本、补词、装订和归家贯穿两条流程；制作以已确认的剧本四为准，解释与小说较早设计的差异。
- 以1009最终SH007替换过时的少量参考例子，讲清完整人物道具路径、Prompt引用和尚未选齐的输入。方案采纳、候选审阅、浏览V/C、保存本镜参考、真实生成和作品接受分别说明。
- 按1008—1011最终能力核对状态卡、总版本/候选数、四列管理、筛选和准确剧本高亮。只保留影响判断的必要操作，不把开发史放进方法正文。
- 现有图像、音色和歌曲成果有明确范围；组合编辑、完整有声预演、镜头成片和最终工程交付仍待实际制作或实施验收，没有写成已完成成果。
- 全部旧章节ID保留。最终desk基线代码已经满足本轮呈现要求，未修改审阅台，也未写业务数据库、生成媒体或代用户接受作品。

## 来源与有效版本

四前置均已完成并有实际双仓交付。完成说明、提交和内容哈希见 [输入快照](evidence/1012/input.json)。主项目基线为 `732f647438cd82904f9d6138ccf9b0d6636d483c`；任务工作区合入该基线；desk准确提交为 `e05f1d812ea92988a6d7ea0cd8b587855bc979b1`，与 `config/instance.json.review_desk_commit` 一致。

|前置|交付入口|本轮使用的最终依据|
|---|---|---|
|1008 / 0002|[实体卡片](../entity-cards/README.md)|实体状态、关系与规范素材数、真实总版本候选数|
|1009 / 0003|[全剧拆解与镜头](../breakdown-shot-v2/README.md)|17集42场297镜、完整参考路径、场/镜准确剧本、Prompt对应|
|1010 / 0004|[管理页](../management-pages/README.md)|四列基准分页、集场和名称筛选、唯一身份与分组展示数量|
|1011 / 0005|[读取性能](../system-performance/README.md)|最终双仓代码、正式发布与保全回执；本轮不重复共享压测|

[来源与流程对应](evidence/1012/source-flow.md)保留全程的主要阶段、能力形成原因、关键决定、连续例子的准确版本、历史冲突和1008—1012映射。原始任务完整要求在 [任务依据](../../planning/creation-approach-optimization-task.md)。作品依据沿 [制作锁](../source-lock.json)、[剧本四审阅](../../planning/screenplay-04-review.md)、[首轮素材](../full-generation/README.md)和[歌曲交接](../songs-review.md)回查。

## 实际验收

[阅读走查](evidence/1012/reading-review.md)记录一条故事路径、一条制作路径、一次发现问题后的回修路径，以及实际理解断点和修订。浏览器正文143项文字与文件一致，详见 [内容对应](evidence/1012/content-match.json)。

真实Chrome使用独立实例及一致性备份，覆盖两Tab全部19目录、桌面1280×900/窄屏390×844共38次目录点击、滚动高亮、直接链接、刷新、前进后退、旧链接、相关页面往返和评论草稿。全部目录标题可见、横向溢出0；窄屏深处刷新滚动6426→6426，SH007后退恢复生产章节及滚动3736。草稿返回后准确正文修订、圈选与文本保留，已取消且没有提交。见 [目录实测](evidence/1012/browser-directories.json)、[桌面总览](evidence/1012/production-overview-desktop.png)、[窄屏总览](evidence/1012/production-overview-narrow.png)、[草稿](evidence/1012/draft-preserved.png)。

SH007两原句准确高亮、场级32段0高亮；七状态和Prompt引用完整。M822两版一候选、V1/C1真实图像、V2未生成；M054无候选；人物参考未选齐。浏览并关闭未改变本镜V?/C?，没有保存输入。实体及素材管理四列、全库2073素材身份/2882展示项、E01/S001搜索阿蘅42/42均实际核验。见 [镜头参考](evidence/1012/sh007-reference.txt)、[Prompt目标](evidence/1012/sh007-prompt-links.json)、[剧本高亮](evidence/1012/sh007-plot.png)、[筛选](evidence/1012/management-filter.png)。

现有方法加载3项和发布守卫14项测试通过；守卫仅增列本方法任务可更新方法正文，其他任务的内容漂移仍被拒绝。desk未变，复用前置最终代码验证，不冒称本轮重跑完整系统或性能验收。正式与独立预览均保留285评论、314事件；正式发布会再验证全部业务表和原件保全。

## 准确候选、正式应用与恢复

本次 `--auto` 已授权范围内候选验收、整组交付、服务切换和结项；Agent验收不等于用户接受作品。

1. 检查两仓任务worktree及准确依赖，提交主仓本轮内容，desk保持上述准确提交。用主项目内部 `_prepare_integration --task task-20261006-0006 --push` 固定整组candidate/target/upstream，候选内容变化才重新准备及补验。
2. 按整组回执运行 `scripts/material_review_release.py prepare`，带 `--task task-20261006-0006`、双仓candidate/target、已纳管desk worktree及 `--bundle .runtime/approach-1012/release`。顺序执行 `build`、`preflight`，冻结方法文件、准确系统源码、挂载、镜像与恢复依据。
3. 执行内部 `_deliver` 受控双仓交付并回读远端。然后按manifest及image回执准确SHA执行 `apply --apply`，原生适配消费同一任务交付身份，串行切换正式镜像及只读config/content挂载。保留活库、评论、采用历史和原件，不导入预览库。
4. 正式3000真实浏览器检查两页内容与导航，核对实际镜像、系统提交、内容哈希及保全；`publish-system`在原生后端读取已推送回执，不另建Git交付。全部完成后才内部 `_complete`。

准确整组候选、目标和upstream在主任务账本 `repository_preparation`；运行回执在本任务 `.runtime/approach-1012/release/manifest.json`、`image.json`、`run/service-*.json`、`run/system-integration.json`、`run/system-push.json`和`run/formal-browser.json`。正式永久包位于主项目 `.runtime/service-releases/approach-20261006-0006-<故事短SHA>-<系统短SHA>/`。已交付候选不为补日志而改写，正式验收与清理结果写本机回执和账本完成说明。

恢复时先核对当前服务与准确包，使用包的 `recover` 或正式永久包 `restart` 入口；只恢复准确代码和挂载，不重置Git、不把旧数据库覆盖活库。新的作品或评论继续保留。

## 本任务资源收尾

正式验收后停止本任务独立预览，按归属清理预览库、克隆素材、临时API响应及测试缓存。保留受管研究/阅读/浏览器证据、准确冻结包、必要正式一致性备份与当前/回退正式镜像；不清其他任务、共享数据库或全局缓存。原方法轮次的受管证据保留用于追查导航修复和历史依据，旧正文不另存副本。

实际删除数量、逐路径回读和保留用途在 `.runtime/approach-1012/cleanup-final.json` 及账本结项说明。两仓纳管worktree、分支及当前TUI保留；退出会话释放锁后，由受管清理入口按只读检查器退役。尚有恢复用途的冻结包与一致性备份，只有新有效回退依据替代且追溯结束后才核对移除。
