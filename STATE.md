# 当前项目状态

更新日期：2026-09-30。

## 本次 UI／UX 统一任务候选

- 本任务已在独立系统工作区实现，候选系统 `e48218947a6cf74e48bad7a0b4909ae334562a81`；已按用户追加要求移除采编右上“45份资料”及其更新／显隐代码；左侧分类项数与评论数保留。范围与口径见 [任务说明](planning/story-creation-ui-unification-task.md)。隔离 Chrome 界面统一 78 项、快捷键 76 项、剧本 42 项、圈选 17 项通过；完整数据桌面／390 像素窄屏及真实鼠标／键盘已核对。正式 3000 已应用并只读回查三页，35 项系统与 60 项故事测试（无跳过）通过，已吸收最新故事 main 的 favicon 成果。交付与复验见 [界面统一交付](planning/story-creation-ui-unification-delivery.md)。待用户确认最终双仓候选完成与本地集成，不推送；任务状态仅以主项目账本为准。

## 站点图标已集成

- favicon 任务已获用户确认并完成双仓本地集成，2026-09-30 账本回读为 completed。屋檐灯火图样获认可，设计和验收见 [图标设计](design/favicon/README.md)、[交付记录](planning/favicon-delivery.md)。
- 正式配置为版本 5／Schema 4，图标 `lantern-home-favicon.svg`；目前从主项目正常 `/instance` 挂载读取，原临时素材覆盖已撤去。测试与恢复证据保留，不沿用文档历史段落中的待确认状态。

## 剧本待定稿

- 用户已初步完成剧本审阅，尚待对具体定稿的明确确认；版本三仅为本次规划参考，不预认作最终定稿。
- 下一步为剧本定稿后由用户启动 `task-20260929-0003`，完成制作系统最小实现、全剧实体及状态抽取，以及第一集全部镜头所需素材、逐镜生成输入包和 16:9 有声动态分镜。交付终点为第一集具备正式镜头生成条件；完整范围及两轮用户审阅见[制作系统与第一集生产准备任务说明](planning/production-preparation-task.md)。本次仅更新任务要求，尚未开展该制作目标。

- [版本三正式入口](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-03-lantern-home&episode=screenplay-03-lantern-home-e01)已可阅读完整 17 集、42 场、1,134 个正文块；单集预计正片 3:52—4:53，总计 74:10，均非成片实测。整版修订 `3110548d5fa53b349085f4a3fb459df746da5011df95dc9d0b8968d24575adf4`。干净稿与导入文档在 `imports/screenplay-03-clean.md`、`imports/screenplay-03.json`。
- 用户已明确“已全部提交，以前五场评论推进全剧重构”。正式版本二及全部分集、S01—S05 的 47 条评论、精修九与结构十完成核对后才开始写作；先归纳评论共性，再检查全剧同类问题。发布前吸收 C44 同文编辑后的记录版本 2，未覆盖任何评论。输入与逐场记录仅在本机 `.runtime/screenplay-03/`。
- [John August 方法研究](planning/john-august-screenwriting-research.md)包含原始文章、官方逐字稿、完整场面和真实前后稿分析，区分发言人和作者推断；[版本三审校](planning/screenplay-03-review.md)逐条关联 47 条评论、版本二全场诊断、新稿改编决定及表演容量。研究的资料限制如实列明。
- 42 场由单写作者串行保存、另步回读、采用；17 集体验检查、全篇按序复读及 3 场连续性回修完成。最终创作检查点 `e3c897be2bce62a510e7d2a18595ae910891d5b216403ddb6c6a84c1f5152510`，无待采用候选。恢复创作先读取 `python3 scripts/screenplay_writing.py --run .runtime/screenplay-03 context --full`，不能用旧工作稿覆盖已发布作品。
- 正式发布仅在事务内追加 18 对象、18 修订和 53 依赖。原 45 资料、191 评论、214 评论事件、87 对象、96 修订、149 依赖、2 配置、16 配置事件全部保留；191 个锚点有效。正式 API、库快照、交付 JSON、干净稿一致。Chrome 已逐集回读全部 42 场及旧两版评论；测试评论只在隔离实例。
- 57 文件空库恢复再导出逐字节一致，包含正式已配置的站点图标；11 项既有创作／发布测试通过。证据见 `VERIFICATION.md` 与 `.runtime/screenplay-03/` 下的 `writing-audit.json`、`formal-verification.json`、`formal-browser-verification.json`、`ui-comment-restore.json`。
- 版本三交付与相关集成验证见任务准备回执及本机 `integration-verification.json`。任务状态以主项目 `.codex-project` 账本为唯一权威；本任务不领取或关闭其他任务。作品发布与任务完成不等于用户接受作品。
- 55 集的按修订摘要已保存在 `content/screenplay-summaries.json` 并进入主实例，版本三摘要在隔离与正式页面核对。正式剧本正文与评论已可用，作品发布不等于用户接受。

## 当前正式运行与其他任务

- 正式服务 `http://127.0.0.1:3000` 实际运行系统候选 `e48218947a6cf74e48bad7a0b4909ae334562a81`，含三子页导航、精确修订评论总数及已有集场／快捷键／图标能力。25 份系统 Python／静态文件与候选逐文件哈希一致，正常主项目 `/instance` 和原可信 CA 挂载保留。两个仓库 main 仍待本任务确认后受控集成；正式运行候选不等于任务完成。
- 系统配置已为 schema 4，现有图标由主项目正常目录挂载。版本三恢复验证保留其原始 SVG 与配置，未另作图标设计；旧 schema 3 系统不能恢复当前配置。favicon 已完成，当前用户配置和图样保持有效。
- 其他任务的当前发布、执行与完成状态从主项目任务账本读取，不在本文件重复维护。并行开发与共享正式资源的互斥约束见本次任务说明。
- 制作思路保留“故事创作”“生产制作”双 Tab；方法正文在 `content/production-approach.json`。评论框聚焦时 ⌘+Enter 提交／保存，Esc 放弃本次未提交内容；框外 Esc 收起并保留草稿。旧链接、修订锚点与用户草稿仍按现有接口使用。快捷键和制作思路的完整操作／既有验证分别见 `planning/comment-shortcuts-delivery.md`、`planning/production-approach-delivery.md`，历史记录继续保留。

## 有效故事与恢复入口

- 小说精修九：十章、29,046 字符、622 自然段；对象 `refinement-09-lantern-home-v9`，修订 `fbd8b2f63a059b910f0d4db1515b021a180b0a6228aec678396127475fe88c8a`，源 SHA-256 `5d4bdfe107e528c93ee8d7134fa6762af329edb566900909d220c17dc5c228a8`。
- 结构第十稿：六部分、21 段、九图；修订 `73e1de6bd288b2211f0cd8001cc07a3f5863f99f3414bae67a0a77a3ec899a58`。版本三保留该稿人物关系、核心因果、求援、主动试刀与停止条件，无另建冲突设定。
- 版本一：17 集、51 场，预计 72:20；修订 `83a7e27c89ed1ef192dccf4d99c0091c2831522caafb465e07a751f0dccab220`。版本二：21 集、47 场，预计 93:25；修订 `f70cb33952914226481eaff660c50413bcad73231fea3e9337f5a9ef9d2aa0dc`。原文、各版评论及精确锚点均保留，审校分别在 `planning/screenplay-01-review.md`、`planning/screenplay-02-review.md`。
- 正式运行权威为主项目 `.runtime/review.sqlite3`；本 worktree 的库与导出只作已验证交付。共享正式库仅通过既有增量发布接口按最新数据写入，不恢复旧快照。`export/` 连同 `config/`、`content/` 供空实例恢复；当前三个剧本版本无需重放导入。
- 旧创作、冷读、发布过程仍在各批次本机 `.runtime/`，详见对应审校和 `VERIFICATION.md`；它们不能代替当前运行库。作者自审、系统校验、任务完成与用户接受作品分别表述。
- 本任务未生成创作媒体；隔离／正式浏览器截图仅作本机验收证据。OpenArt 固定项目、原生 4K 与干净母版规则仍见 `config/openart.json` 和 `AGENTS.md`。
