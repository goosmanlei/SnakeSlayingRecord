# 当前项目状态

更新日期：2026-09-30。

## 版本三已发布，任务待集成确认

- [版本三正式入口](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-03-lantern-home&episode=screenplay-03-lantern-home-e01)已可阅读完整 17 集、42 场、1,134 个正文块；单集预计正片 3:52—4:53，总计 74:10，均非成片实测。整版修订 `3110548d5fa53b349085f4a3fb459df746da5011df95dc9d0b8968d24575adf4`。干净稿与导入文档在 `imports/screenplay-03-clean.md`、`imports/screenplay-03.json`。
- 用户已明确“已全部提交，以前五场评论推进全剧重构”。正式版本二及全部分集、S01—S05 的 47 条评论、精修九与结构十完成核对后才开始写作；先归纳评论共性，再检查全剧同类问题。发布前吸收 C44 同文编辑后的记录版本 2，未覆盖任何评论。输入与逐场记录仅在本机 `.runtime/screenplay-03/`。
- [John August 方法研究](planning/john-august-screenwriting-research.md)包含原始文章、官方逐字稿、完整场面和真实前后稿分析，区分发言人和作者推断；[版本三审校](planning/screenplay-03-review.md)逐条关联 47 条评论、版本二全场诊断、新稿改编决定及表演容量。研究的资料限制如实列明。
- 42 场由单写作者串行保存、另步回读、采用；17 集体验检查、全篇按序复读及 3 场连续性回修完成。最终创作检查点 `e3c897be2bce62a510e7d2a18595ae910891d5b216403ddb6c6a84c1f5152510`，无待采用候选。恢复创作先读取 `python3 scripts/screenplay_writing.py --run .runtime/screenplay-03 context --full`，不能用旧工作稿覆盖已发布作品。
- 正式发布仅在事务内追加 18 对象、18 修订和 53 依赖。原 45 资料、191 评论、214 评论事件、87 对象、96 修订、149 依赖、2 配置、16 配置事件全部保留；191 个锚点有效。正式 API、库快照、交付 JSON、干净稿一致。Chrome 已逐集回读全部 42 场及旧两版评论；测试评论只在隔离实例。
- 57 文件空库恢复再导出逐字节一致，包含正式已配置的站点图标；11 项既有创作／发布测试通过。证据见 `VERIFICATION.md` 与 `.runtime/screenplay-03/` 下的 `writing-audit.json`、`formal-verification.json`、`formal-browser-verification.json`、`ui-comment-restore.json`。
- `task-20260929-0005` 在独立 worktree 执行，任务账本仍为执行中；完成状态以主项目 `.codex-project` 账本为唯一权威。下一步提交交付、运行 `_prepare_integration`、对返回候选复验，再向用户展示具体提交并确认是否完成及本地集成。未经该确认不运行 `_complete`，不推送。完成后保留分支与 worktree，正常退出会话才释放运行锁。
- 55 集的按修订摘要已保存在 `content/screenplay-summaries.json`，版本三摘要在隔离页面核对；主目录摘要文件及新的可恢复导出随受控集成生效。正式剧本正文与评论已可用，作品发布不等于用户接受。

## 当前正式运行与其他任务

- 正式服务 `http://127.0.0.1:3000` 实际运行系统 `a22b1e408767b1f4ea05363f40fd5d7fa71552dd`，含集场阅读、评论快捷键及站点图标配置。本任务从实际容器核对 13 份 Python 文件，并将实例版本锁同步到该提交；没有重启服务或修改通用系统代码。
- 系统配置已为 schema 4，现有图标由 favicon 任务工作区挂载。版本三恢复验证保留其原始 SVG 与配置，未另作图标设计；旧 schema 3 系统不能恢复当前配置。本任务不替 favicon 任务执行双仓集成，其状态以 `task-20260930-0002` 账本为准。
- 2026-09-30 现场账本：集场阅读 `task-20260929-0006`、评论快捷键 `task-20260930-0001`、制作思路 `task-20260929-0004` 均已 completed；favicon 任务仍 running，制作体系设计 `task-20260929-0003` 为 published。本会话不领取或关闭其他任务。
- 制作思路保留“故事创作”“生产制作”双 Tab；方法正文在 `content/production-approach.json`。评论框聚焦时 ⌘+Enter 提交／保存，Esc 放弃本次未提交内容；框外 Esc 收起并保留草稿。旧链接、修订锚点与用户草稿仍按现有接口使用。

## 有效故事与恢复入口

- 小说精修九：十章、29,046 字符、622 自然段；对象 `refinement-09-lantern-home-v9`，修订 `fbd8b2f63a059b910f0d4db1515b021a180b0a6228aec678396127475fe88c8a`，源 SHA-256 `5d4bdfe107e528c93ee8d7134fa6762af329edb566900909d220c17dc5c228a8`。
- 结构第十稿：六部分、21 段、九图；修订 `73e1de6bd288b2211f0cd8001cc07a3f5863f99f3414bae67a0a77a3ec899a58`。版本三保留该稿人物关系、核心因果、求援、主动试刀与停止条件，无另建冲突设定。
- 版本一：17 集、51 场，预计 72:20；修订 `83a7e27c89ed1ef192dccf4d99c0091c2831522caafb465e07a751f0dccab220`。版本二：21 集、47 场，预计 93:25；修订 `f70cb33952914226481eaff660c50413bcad73231fea3e9337f5a9ef9d2aa0dc`。原文、各版评论及精确锚点均保留，审校分别在 `planning/screenplay-01-review.md`、`planning/screenplay-02-review.md`。
- 正式运行权威为主项目 `.runtime/review.sqlite3`；本 worktree 的库与导出只作已验证交付。共享正式库仅通过既有增量发布接口按最新数据写入，不恢复旧快照。`export/` 连同 `config/`、`content/` 供空实例恢复；当前三个剧本版本无需重放导入。
- 旧创作、冷读、发布过程仍在各批次本机 `.runtime/`，详见对应审校和 `VERIFICATION.md`；它们不能代替当前运行库。作者自审、系统校验、任务完成与用户接受作品分别表述。
- 本任务未生成媒体；OpenArt 固定项目、原生 4K 与干净母版规则仍见 `config/openart.json` 和 `AGENTS.md`。
