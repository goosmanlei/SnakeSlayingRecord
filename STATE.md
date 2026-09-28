# 当前项目状态

更新日期：2026-09-29。

## 当前交付与下一步

- [故事精修九 · 定稿候选](http://127.0.0.1:3000/?workspace=story.sources&source=refinement-09-lantern-home-v9)与[故事结构第十稿](http://127.0.0.1:3000/?workspace=story.outline)已发布。十章正文 29,046 字符（含标点、章内换行，不含章名）、622 个正文自然段；待用户审阅，未代为接受或推进剧本。
- 精修八固定修订已完成严格隔离顺序精读：十章、604 段；新增 1 条时间表述评论。另 1 条带背景补充意见明确区分，由独立改稿者有限吸收。两条均保留在精修八，处理矩阵含新稿精确位置；旧版本与旧评论不变。
- 结构先发布为修订 `73e1de6bd288b2211f0cd8001cc07a3f5863f99f3414bae67a0a77a3ec899a58`，六部分、21 段、九图；更新人物变化、机关与因果三 SVG，沿用六图。新稿来源引用同一修订，串行候选与回读时间已核对。
- 新小说 ID `refinement-09-lantern-home-v9`，源哈希 `5d4bdfe107e528c93ee8d7134fa6762af329edb566900909d220c17dc5c228a8`，对象修订 `fbd8b2f63a059b910f0d4db1515b021a180b0a6228aec678396127475fe88c8a`。
- API、导入、干净稿和正式导出一致；空库恢复后 56 个文件逐字节一致。原 44 资料、136 评论、154 评论事件及全部旧图、旧修订、旧依赖保留；现有 138 个评论锚点有效。正式库为 45 资料、47 对象、56 修订、31 依赖。PROJECT v14 仅更新故事与创作背景，SYSTEM 和其他字段不变。
- 浏览器核验十章导航、完整正文、两条原评论定位、结构九图与历史切换；修复长章评论跳到整块中点的问题。验收细节见 [VERIFICATION.md](VERIFICATION.md)。用户已在本对话回复“确认完成”；指定完成命令现已成功，账本回读为 `completed`，完成时间 `2026-09-29T03:44:39.748834+08:00`。下一步由用户继续审阅精修九定稿候选。

## OpenArt 与高清图片

- 固定项目为“李寄斩蛇 · 把灯带回家”，ID `8K6WcbrPLghSBJXBtWAE`，配置见 [config/openart.json](config/openart.json)。未来图片优先 OpenArt CLI，显式指定本项目，原生 4K；参考图迭代遵循 AGENTS.md 的干净母版规则。
- 当前沿用精修八的三张原生高清图：庙院与剖视图均为 5056×3392，站位图为 5504×3072；原文件哈希和显示已复核。图像生成与 OpenArt 归档凭据仍保存在精修八批次，后续生成前再核对 CLI 登录状态。
- 用户已自行把 Personal Project 中本项目图片移入独立项目。精修八的列表回读包含当时全部 11 个生成记录，未重复搬移；证据为 `.runtime/refinement-08/openart-project-verification.json`。

## 后台恢复与审阅边界

- 当前批次 `.runtime/task-20260929-0001/` 为 `COMPLETED`。恢复先读 `progress.json`、`evidence/task-completion-receipt.json`、`publication-receipt.json`、`structure-receipt.json` 与 `evidence/delivery-verification.json`。
- `cold-api/` 保留十章实际请求、响应和覆盖记录；无工具、无项目上下文，保留全部已读原文。`reader/` 因自动记忆先验只作辅助，不计冷读验收。`writer/` 保留独立改稿决定、逐章采用、两评论处理与全稿核对；`evidence/parent-readback.json` 是交付者复读，不冒称另一位首次读者。
- `.runtime/refinement-08/`、`.runtime/refinement-07/`、`.runtime/third-sacrifice/` 与精修六 `refinement-06-cold-reader` 均为历史证据，不重新初始化或重放到当前正式库。精修六的摘要模式不适用于本轮精修八逐章完整前文审阅。

## 运行入口与系统待同步内容

- 正式服务为 Docker + Nginx `127.0.0.1:3000`，系统工作树为 `../story-review-desk-python`。既有改进已移除结构页方向回看／重选区、顶部重复评论按钮及底部版本确认控件；版本、章节、图文圈选、浮动评论入口和历史接口继续保留。
- 结构的全部图片和图示完整显示；点击后在当前页面放大，按 Esc 或右上角关闭按钮退出，恢复原阅读位置和图片焦点。原文件保持高清，圈选评论不误触放大。九图、历史 SVG、桌面／窄屏和正式入口均已核验；该轮 `structure.js`、`structure.css` 已同步运行容器并核对 HTTP 内容，没有重启或重建镜像。证据见 `.runtime/structure-image-viewer/verification.json`。
- 实例版本锁已更新为系统提交 `0a4e3cdbda844a779e9d1998a335699978733cde`，已推送 `origin/main`，系统工作树干净。包含文本圈选、资料标题、目录高亮、章节菜单、结构页精简、高清图放大及精确评论定位；正式入口五个静态文件与该提交逐字节一致。本次无重启或重建镜像，后续可按公开版本锁构建。
- 章节菜单从正文生成：前五版各 12 章、第六版 15 章、第七、第八和第九版各 10 章，共 105 个入口。系统配置保持 Schema 3、`gpt-5.6-sol / medium`，润色密钥仅保存环境变量名 `OPENAI_API_KEY`。
- 本轮另外修复精确评论定位，共享 `app.js`、`structure.js` 已同步运行容器并核对 HTTP。隔离浏览器 14 项、系统单测 20 项通过，正式两条引用进入可视区；没有重启。系统 `docs/comment-checklist.md` 已同步。
- 按用户 `git-commit` 及追加“两仓一并提交”指令，故事实例的正式稿件、结构素材、评论导出、创作工具与项目记录，以及通用审阅台的交互改进分别提交；故事实例同步引用上述系统提交。本机完成回执见 `.runtime/task-20260929-0001/evidence/git-publication.json`。正式运行库 `.runtime/review.sqlite3` 为权威，不能用旧 export 覆盖。

## 任务与确认边界

- 用户确认两份完整任务说明后，已正式发布两项独立任务：①`task-20260929-0003` [制作设定与整片素材管理系统设计](.runtime/task-publication/production-planning-20260929/system-design.md)；②`task-20260929-0004` [以“制作思路”替换“当前工作”页面](.runtime/task-publication/production-planning-20260929/production-approach.md)。均为 P1、gpt-6-astra / max，依现有任务系统映射登记为极复杂，无硬依赖；状态 published、执行次数 0，尚未执行。第一项交付设计与验证方案，第二项实施页面替换及专用追踪清理。首次发布凭据在同目录 publication-receipt.json；当前并行配置与回读结果见下条。发布本身不代表系统功能已经交付。
- 当前尚未执行的任务共三项，还包括 `task-20260929-0002`（剧本页面与完整分集影视剧本，P1、gpt-6-astra / xhigh，前置任务 `task-20260921-0003` 已完成）。用户确认本轮并行方案后，已通过 `codex.project task _modify` 将三项均设为允许并行，分别填写理由，并在目标中补充两个仓库独立工作区、明确输入版本、隔离验收实例及按序集成／正式发布的要求。三项回读均为 published、执行次数 0、记录版本 2；原业务目标、验收标准、依赖、优先级、模型与推理强度保持，其他八项任务未变。本次未启动任务。修改与核验凭据见 `.runtime/task-publication/parallel-review-20260929.json`，两份任务说明已与新记录同步；长期并行原则见 `AGENTS.md` 的“任务并行与集成”。下一步可按所选任务分别启动 `task mrun`；启动前须满足主工作区干净的条件，跨仓库集成与正式发布继续按已确认要求协调。
- `task-20260929-0001` 已依据本对话“确认完成”成功登记：`completed`、记录版本 2、执行次数 2、完成时间 `2026-09-29T03:44:39.748834+08:00`，租约已清除。CLI 与账本回读一致；仅完成任务登记，作品保留定稿候选标记。证据：`.runtime/task-20260929-0001/evidence/task-completion-receipt.json`。
- 历次已完成任务的确认保留在 `KNOWLEDGE.md`、`VERIFICATION.md` 与本机任务账本；本次完成登记与用户确认均已记录。
- `task-20260923-0002` 的十二章审阅交付已获确认，只针对该次审阅，不等于接受小说或后续版本。
- `task-20260923-0001` 在任务账本中为 `completed`；本次澄清会话没有改变该任务状态。
