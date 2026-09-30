# 当前项目状态

更新日期：2026-09-30。

## 版本四已发布，作品待审阅

- [正式版本四](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-04-lantern-home&episode=screenplay-04-lantern-home-e01)为 17 集、42 场、1,114 个正文块，整版修订 `7287b25a34d4b0db242ec5688f33349fa6d449874a3c6acb30033e2260cd2686`；单集预计正片 3:50—4:55，总计 73:12，非成片实测。[干净稿](imports/screenplay-04-clean.md)、[导入数据](imports/screenplay-04.json)、[审校说明](planning/screenplay-04-review.md)已完成，尚不表示用户接受作品。
- 正式剧本三全部 73 条意见已逐条映射到新稿，含两条已关闭意见；旧 42 场和最终 42 场分别完成八项检查，各 336 项，94 个发现项有原文、决定、新稿引用和改后结论。见 [逐条处理](planning/screenplay-04-comment-handling.md)、[初扫](planning/screenplay-04-baseline-scan.md)、[终审与场次去向](planning/screenplay-04-final-scan.md)。三条联动线已落入正文：应募停祭及母女保护；无预排补位、无援手到场的持续斩蛇；作证、同一县丞责任及具体结案。
- 在本任务 worktree 的 `.runtime/screenplay-04/` 串行写作，53 次保存、56 次独立候选阅读、8 次采用前退回、45 次采用；17 集连读和全稿顺序复读、回修及受影响后场复查已完成。最终检查点 `31e5d05cb9b96cebf66bb3a5d779bbb98213e60ca6e339a67dc845f1c1590901`，无待采用候选。若继续创作，先完整读取 `python3 scripts/screenplay_writing.py --run .runtime/screenplay-04 context --full`，不可只凭摘要续写。
- 独立和正式 Chrome 均回读全部 42 场，正式 17 集概览匹配；正式页面全部 73 条旧评论原话、圈选核对一致。隔离 8875 实例验证新版圈选评论、跨场草稿保留、快捷提交、编辑、定位和恢复，测试内容未写入正式库。60 项故事测试通过，无跳过；57 文件空库恢复再导出逐字节一致。详见 [验证证据](planning/screenplay-04-verification.json)。
- **正式页只读验收存在一次例外：** 快速切集时误关闭 C40，已立即恢复 OPEN。正文、圈选、归属和最终状态未变，记录版本从 1 到 3，新增 CLOSE／REOPEN 两条真实历史；没有回滚或删除审计记录。之后逐步确认页面，重查 73 条无其他变更。此例外及输入差异见 [差异记录](planning/screenplay-04-input-diff.json)，不能报告“正式评论完全未写入”。

## 当前运行与交付边界

- 正式服务仍为 `http://127.0.0.1:3000`，系统镜像 `story-review-desk-creation-ui:e482189`；本任务未改通用系统源码、创作工具或阅读界面。主项目 `.runtime/review.sqlite3` 是运行权威，本次仅增量追加版本四的 18 对象、18 修订、53 依赖，未恢复旧库覆盖正式数据。
- 集成前新增分集摘要通过任务工作区 `content/screenplay-summaries.json` 临时只读挂载到正式容器，原主项目实例、可信 CA、启动命令和凭据保持。72 条摘要对应四版全部分集的精确修订。用户确认集成后，先在本任务 worktree 运行 `python3 .runtime/screenplay-04/runtime_summary_mount.py unmount` 撤去临时文件挂载，再执行受控 `_complete`；成功后只读核对主目录已集成的同一摘要。若受控集成失败，按实际状态恢复候选摘要服务，再准备、验证、确认，不能误报成功。回退容器、worktree 和任务分支均保留。
- 当前成果须随文档提交到任务分支，执行 `_prepare_integration` 并验证返回的候选，再向用户明确请求完成、集成到 `main` 并推送 `origin` 的 `refs/heads/main`。未获确认不执行 `_complete`；成功后停止文件写入。任务发布、执行与完成以主项目账本为唯一权威，正常退出会话才释放独占运行锁。
- 本次只处理 task-20260930-0004。制作系统任务及其他任务的发布、执行、完成状态查主项目账本，不自动领取。UI 统一与 favicon 的旧“待确认”文字是历史交付窗口；2026-09-30 账本已回读为 completed，不作为当前待办。

## 有效故事与恢复入口

- 小说精修九：十章、29,046 字符、622 自然段；对象 `refinement-09-lantern-home-v9`，修订 `fbd8b2f63a059b910f0d4db1515b021a180b0a6228aec678396127475fe88c8a`，源 SHA-256 `5d4bdfe107e528c93ee8d7134fa6762af329edb566900909d220c17dc5c228a8`。
- 结构第十稿：六部分、21 段、九图；修订 `73e1de6bd288b2211f0cd8001cc07a3f5863f99f3414bae67a0a77a3ec899a58`。版本四沿用人物、空间和主题依据，按用户新评论调整准备、高潮与问责；未反向覆盖小说或结构，也未新建作品接受记录。
- 版本一为 17 集／51 场，版本二为 21 集／47 场，版本三为 17 集／42 场；三版原文及不可变修订均保留。版本三整版修订 `3110548d5fa53b349085f4a3fb459df746da5011df95dc9d0b8968d24575adf4`；其 73 条意见当前仍为 71 OPEN、2 CLOSED。各版历史审校见 `planning/screenplay-01-review.md` 至 `planning/screenplay-03-review.md`。
- 最新交付 `export/` 连同 `config/`、`content/` 供空实例恢复，含四版剧本、45 资料、264 评论、293 评论事件、123 对象、132 修订、255 依赖、2 配置和16配置事件；264 个锚点有效。无需重放四版导入，不用交付快照覆盖后续变化的正式库。
- 正式配置仍为版本 5／Schema 4，屋檐灯火图标 `lantern-home-favicon.svg` 由主项目正常挂载读取，原 SVG 与配置纳入恢复包。制作思路保留“故事创作”“生产制作”双 Tab；评论框内 ⌘+Enter 提交、Esc 放弃本次未提交内容，普通 Enter 换行。既有用户草稿存储规则和版本键未改；未操作用户原有标签页中的编辑器。
- 本次无新创作媒体；截图只作本机验收证据。历史后台过程均留各批次 `.runtime/`，不代替正式库；OpenArt 项目、原生 4K 和干净母版规则仍见 `config/openart.json` 与 `AGENTS.md`。
