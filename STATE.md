# 当前项目状态

更新日期：2026-09-30。

## 版本四已确认定稿，制作准备执行中

- 用户在本任务会话明确确认“目前的剧本版本四作为终稿定稿推进本任务”。正式制作输入为[版本四](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-04-lantern-home&episode=screenplay-04-lantern-home-e01)，整版修订 `7287b25a34d4b0db242ec5688f33349fa6d449874a3c6acb30033e2260cd2686`：17 集、42 场、1,114 个正文块。公开发布载荷仍保留原始 `pending` 值，本次接受另存于[输入锁定](production/source-lock.json)，不改写历史修订。
- 已逐集核对当前正式 API 与 `imports/screenplay-04.json` 的全部正文、场次一致；锁定分集修订、场 ID、正文哈希、小说／结构依据与评论快照。版本四暂无评论，历史三版共 126 条剧本评论；版本三 73 条的处理见 `planning/screenplay-04-comment-handling.json`。原始启动快照仅在本任务 `.runtime/production/inputs/`。
- 本会话只执行 `task-20260929-0003`。范围为制作系统最小实现、全剧实体与状态抽取、第一集素材、逐镜输入包和 16:9 有声动态分镜；详见[任务说明](planning/production-preparation-task.md)。系统设计、抽取与第一轮制作基准准备为下一步，尚未交付任何制作素材。
- 制作基准须经第一轮用户认可后才批量派生；完整动态分镜与逐镜包经第二轮用户审阅后才办理第一集就绪交接。剧本定稿确认不代表具体造型、声线、旋律或最终交付已获接受。

## 工具与隔离

- 用户指定图片优先 OpenArt CLI 的 GPT IMG 2.5，高质量、按用途选画幅；OpenArt Credit 用完后使用 Codex 内置 GPT IMG 2.5。当前已核验 `gpt-image-2-5-sunburst` 支持高质量与原生 4K，启动时余量 10,479 Credit；未发生本任务生成扣费。选型与母版规则见 `config/openart.json`，实际调用前重新核对余额。
- 图像 I2I 优先一代、累计最多两代，多参考按最深谱系计数；以局部修改、固定轮廓与配色及纹理回看抑制漂移。具体生成记录与校验尚待实现。
- 音频优先豆包语音 `seed-audio-1.0`；用户允许复制九头案已有调用程序。当前只读查找程序与核对当前调用条件，未复制密钥或启动旧项目。
- 故事工作区为本任务 worktree；通用审阅台独立工作区在 `.runtime/review-desk-worktree`，分支 `codex/task-20260929-0003-production`，起始提交 `e48218947a6cf74e48bad7a0b4909ae334562a81`。开发实例与测试数据须独立于正式 3000 服务和主项目 `.runtime/review.sqlite3`。
- 故事 worktree 已吸收最新主线 `363469d81e53f2389e6ac3385b864d93a4edba30` 的版本四内容；本任务的启动与工具补充保留。仅本地集成，不自动推送；最终准备、验证与用户确认完成后才运行 `_complete`。任务账本是执行和完成状态的唯一权威，正常退出会话才释放运行锁。

## 正式运行与恢复入口

- 正式服务 `http://127.0.0.1:3000` 启动核对可读，系统基线 `e48218947a6cf74e48bad7a0b4909ae334562a81`。本任务尚未修改正式数据库、配置、导出或运行服务；不以启动快照覆盖后续正式数据。
- 正式结构仍为第十稿，修订 `73e1de6bd288b2211f0cd8001cc07a3f5863f99f3414bae67a0a77a3ec899a58`；小说精修九修订 `fbd8b2f63a059b910f0d4db1515b021a180b0a6228aec678396127475fe88c8a`。版本四沿用人物、空间与主题依据，调整准备、高潮和问责；生产事实以本次明确接受的剧本为准，差异须保留来源，不自动反写小说或结构。
- 四版剧本及其评论、图标和共用评论功能保持。公开恢复入口为 `export/`、`config/`、`content/`；历史版本四创作、恢复与浏览器证据见 `planning/screenplay-04-review.md`、`planning/screenplay-04-verification.json` 和 `VERIFICATION.md`。这些既有验证不等于本任务制作链路已经验证。
- 制作思路仍为“故事创作”“生产制作”双 Tab，正文在 `content/production-approach.json`。本任务实际经验与成果将在形成后更新，不提前标记已实践。
