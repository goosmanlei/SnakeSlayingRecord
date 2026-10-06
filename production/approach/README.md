# 制作思路重构交付

两页直接更新 `content/production-approach.json`，故事创作按七步组织，生产制作按十步贯通定稿到全剧交付与返修，另先解释实体、完整状态、素材、版本和候选。正文自成完整说明；用户负责审阅、评论和明确选择，后台负责创作、登记、生成与剪辑。

## 变更与准确版本

- 故事页增加独立方向选择，拆开写作、回修与交付；生产页补全完整状态、准确参考、有声预演、场／集／全剧组合、质量与工程恢复。
- 全剧 17 集、42 场、297 镜仅表示设计范围；移除失效的实体／状态数量。四首歌曲的 10 份整曲录音已登记，最新未生成草稿、词音与无损母版缺口分别表述。
- 平铺版本、独立候选、共用大小卡、集场镜导航与剧情高亮按前置最终页面说明。方案采纳、候选审阅、本镜参考选择、真实生成和作品接受分别解释。
- 当前新组合编辑与最终交付能力尚待实施和验证；完整有声预演、镜头媒体和全剧成片未冒称就绪。本任务不生成媒体、不接受素材或作品、不写业务数据库。
- 系统独立工作区候选为 `6b7f9e781c97041769a8d31b0fd7096f0a965f69`，基线为 `166b766560273e9cdab533da22fc5636f60ec94a`。仅修改方法页目录滚动和刷新定位，保留深处阅读上下文；补 5 项定位回归。故事准确候选及远端身份由任务账本和冻结包记录，不在正文复制变化的 SHA。

## 前置成果与事实依据

核对主账本五项依赖均为 completed / pushed，并在真实正式页面读取其交付行为；原始 Notebook 截图没有作为完成证据。

|任务|故事交付提交|本次实际核对|
|---|---|---|
|0002|`f5fe993443959b90f56f5412e8650071930446a7`|编号、大卡、版本候选、完整状态；第二版有效状态以当前正式库为准|
|0003|`53ab6949b0f0413c024c4c4f0b1f3261d905113b`|共用小卡、分组分页、打开大卡|
|0004|`dae66880fa78ecb2d925cb05b127456a779ec196`|17 集卡、场镜导航、准确原句高亮和本镜素材|
|0005|`fd9d70f00f69a267b2d80585f38ff775cbfc3588`|独立 Prompt、上游引用、准确槽选择及未生成禁用|
|0006|`42c7598c66648eea04b66d4c206851060de79b04`|统一页首、配色、两 Tab、目录与窄屏表格|

细节沿各任务的 [大卡](../entity-material/README.md)、[第二版](../entity-card-v2/README.md)、[小卡](../small-cards/README.md)、[拆解页](../breakdown-page/README.md)、[镜头制作](../shot-production/README.md)、[视觉](../system-page-style/README.md)交付及当前正式准确对象核对。制作边界沿 [制作输入锁](../source-lock.json)、[全剧拆解](../breakdown/README.md)、[原生声音流程](../native-audio-workflow.md)、[歌曲交接](../songs-review.md)读取。

连续例子使用剧本版本四 E01 / S001 的唱险滩、翻过两页、唱归家原句；对应 SH001–SH003。两份米分别为当天工米和许家预付，接续歌本转手、毁本补本及提灯归家的全剧回收。原句在剧情弹窗准确高亮，见 [截图](evidence/plot-reference.png)。抬河石、翻页后压稳是逐镜制作设计，明确不新增为剧情事实。

M822 版本 1／候选 1 有真实阿蘅原件，版本 2 无候选；SH002 的直接上游 M020 关键画面和 M1621 声音参考均未生成。“图片1”打开大卡后无候选，选为本镜参考禁用。母版必须先成为关键画面的准确上游，再审阅关键画面并逐槽选择；本文只说明将来交接，不代替用户选定。见 [已有候选](evidence/existing-candidate.png)、[未生成](evidence/not-generated.png)、[未选定参考](evidence/unselected-reference.png)、[实际参考快照](evidence/shot-reference-actual.txt)。

## 完成标准逐项验收

|标准|结果与证据|
|---|---|
|1 前置与两页完整重构|五项已完成并核对真实页面；故事 8 节、制作 11 节覆盖原型到全剧 QA、交付和返修。原始完整要求在 [任务依据](../../planning/creation-approach-rewrite-task.md)。|
|2 输入、动作、产物与交接|最终正文逐节通读，七步／十步均写明目的与输入、后台动作和用户判断、产物与前进条件；[逐节走查](evidence/editorial-review.json)对应实际正文，不依赖聊天。连续例子依据见上。|
|3 概念及操作一致|三种状态均实测，正文明确未选版本／候选／原件不可生产；浏览不保存，没有替用户采纳或选参考。|
|4 能力与过时信息|现行编号、歌曲已登记、平铺版本和全剧范围已修订；已交付、待审阅和未来方法分别说明，故事正文与业务模型未改。|
|5 加载与真实浏览器|现有加载器校验通过；浏览器逐节对比源文无差异。桌面 1280×900、窄屏 390×844 的全部 19 节目录均实际点击通过，标题低于固定区域，横向溢出为 0；旧 15 节 ID 全保留，旧 workspace=current 结构链接实测。刷新、两 Tab 键盘切换、直接链接、前进后退、正文滚动高亮、相关页往返及表格流程截图见 [浏览器证据](evidence/browser.json)。|
|6 草稿、准确上下文、交付与清理|隔离页真实评论草稿跨方法两 Tab 往返恢复，随后取消，未提交；[截图](evidence/draft-preserved.png)。非零方法阅读往返保留准确路由和“返修”章节，布局恢复后滚动值 7804→7555，未声称像素完全相同。正式应用和实际资源清理回执按下述入口读取。|

真实浏览器发现窄屏目录自动回拉打断点击、刷新标题部分遮挡；系统方法专用修复后全部目录及刷新重验通过。没有以自动检查替代浏览器。截图：[故事桌面](evidence/story-desktop.png)、[生产桌面](evidence/production-desktop.png)、[故事窄屏](evidence/story-narrow.png)、[生产窄屏表格](evidence/production-narrow.png)、[准确参考桌面](evidence/reference-desktop.png)、[准确参考窄屏](evidence/reference-narrow.png)。

自动验证：系统完整 Python 297 项、Node 653 项通过；故事冻结发布守卫 9 项通过，新增检查只允许本任务更改方法正文。系统定位测试检查合成几何，不代替实际页面；完整输出保留本机 `.runtime/approach/`。既有方法加载器 3 项通过，正文加载、Git diff 检查通过。

## 正式应用与恢复

本次 `--auto` 明确授权范围内候选验收、双仓提交／集成／推送和服务切换；验收由 Agent 实际执行，不冒称用户逐项验收或接受作品。

1. 故事提交后用 `codex.project task _prepare_integration --push` 固定候选，核对目标、upstream 和前置交付；系统保持独立分支与上述准确提交。
2. `scripts/material_review_release.py prepare` 固定 `.runtime/approach/release`，参数带任务、双仓 candidate／target、`--system-worktree .runtime/approach/system --push-system`；方法原文和系统源码冻结，当前服务与挂载同时记录。
3. 顺序执行 `build`、`preflight`，回读 manifest 与 image 的 SHA-256。该脚本只对本任务允许方法内容更新；其他任务仍禁止内容漂移。
4. 任务 `_deliver` 受控交付故事，随后按冻结摘要执行 `apply`：受控快进系统、切换正式代码镜像和只读 config／content 挂载，保留活库与全部历史。业务数据增量为 0，绝不导入预览库。
5. 在正式 3000 实际验收两页、目录、刷新与链接；用 `publish-system` 普通推送并回读远端。故事推送、系统推送、服务切换、真实页面和任务完成分别记录。

准确参数和实际顺序在本机 `.runtime/approach/release/manifest.json`、`image.json`、`run/system-integration.json`、`run/service-*.json`、`run/system-push.json`、`run/formal-browser.json`。正式永久运行包位于主项目 `.runtime/service-releases/approach-20261005-0007-<故事短SHA>-<系统短SHA>/`，仅作正式只读挂载和恢复入口。回滚仅恢复该包记录的旧代码／挂载，不重置 Git、不回灌旧库；恢复须先核对当前服务身份，沿冻结包 `recover` 入口处理。

## 资源收尾

最终正式验收后停止 62670 隔离服务，按准确归属清理预览库／配置／链接、重复基线、一次性正文写入脚本和任务测试缓存；保留准确冻结包、前后正式一致性备份、必要检查／浏览器证据和双仓提交分支。删除前核对进程、挂载与文件用途；不清理其他任务资源，不使用全局 prune。

实际删除数量、逐路径回读及保留理由在 `.runtime/approach/cleanup-before.json`、`.runtime/approach/release/run/cleanup-final.json`，由结项说明回读。双仓 worktree 保留用于追溯及当前 TUI，会话退出释放锁后再走各自受管退役入口；保留数据在后续有效基线替代且追溯结束后再核对移除。
