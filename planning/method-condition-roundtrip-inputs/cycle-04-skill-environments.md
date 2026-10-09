# 工作环节如何取得 SKILL：本轮只读调查与隔离回写线索

本笔记回答的是：当前故事采编、结构、小说、剧本、视听和素材制作是否有准确的方法入口，执行者收到的是否为完整方法，以及哪些环节仍需要根实际操作。调查在 2026-10-10 03:45—04:00（北京时间）进行。正式 `http://127.0.0.1:3000` 仅 GET；本辅助调查没有操作浏览器、执行创作任务、调用生成模型、修改正式配置或发布任务。页面实践由根负责。

当前最具体的问题已由根隔离页面保存和本辅助调查独立 GET 复核：只修改“用途”，方法编辑页就把布尔加载条件变成字符串，原本请求调度章节的布尔条件不再取得章节。现有准确方法、来源投影及外部作者入口总体可读，不能把这个问题扩成“全部环节仍在使用旧 Prompt”。另有一个较小的本地导出入口链接差异，正文并未丢失。

## 依据和准确环境

已按当前项目入口读取 AGENTS、KNOWLEDGE、STATE，并重读 `skills/creative-system-review/SKILL.md`、项目适配、愿景及受管方法文档；RUNBOOK 只作运行交接，不作为方法正文。使用 document-writing 的读者目的与回读要求成稿。没有全量加载旧聊天或旧 Review 报告。

故事主目录 HEAD 为 `3ca503d501bef61048d6c13f2b87ba85993ba2f7`；故事配置与系统 HEAD 的审阅台提交均为 `b3fa3fef77851c544c5350cb4a99ab0af622cbd3`。本轮读取了任务 0001 的准确交付回执和少量方法恢复证据，不把其执行者验收当作本轮独立操作。

当前正式 Review 方法的三个完整资源与本地唯一正文逐字节相同：

| 唯一正文 | SHA-256 |
| --- | --- |
| `skills/creative-system-review/SKILL.md` | `269b0c37e472908e79963cc75a86069517f9231dfa2763aa259a1adf7cbfc40e` |
| `skills/creative-system-review/references/project-context.md` | `16c6fcf6b6539c79b4d539e9b1a6d35ad3dcf78904d5a1a062f6c231339243a4` |
| `production/system-vision.md` | `bf0914b7750a92a5482cf179e3325164930e3933213f9e2829db2aeeba3655fd` |

当前 `creative-system-review` 绑定为 `f2967da37152121304cf2b25d1049c7f1e47e0e50624407c065978343b8053f0`；入口方法第 1 版修订 `8f6dfbb6094cb6f4ef2f2402596455b3c478c4066bda16fa6523046fb5e90fe6`；共用全文资源修订 `50b71fd8105a70264942c77673fa6b098b99fe450b20e3731ad118159f93424c`。简短入口不等于只有简短方法：完整三份正文实际在 resources 内。

任务 0001 的既有隔离 prepare→导出→新空实例恢复回执记载同一执行修订 `d81635063ea5d3db52572b1452579b6a6872ade876f309247a29922418601870` 与同一资源；本轮没有重新 POST prepare 或恢复数据库。该回执证明当次恢复，不证明所有创作环节已经实际按方法完成作品。

## 当前环节与正常对照

以下版本和所取章节来自当前正式 GET resolve；“取得”只表示包中真实存在全文。没有把字符长度当作方法质量评分，也没有把取得方法当作已理解或已创作。

| 工作目的 | 当前方法 | 如何取得并继续工作 | 本轮确认和边界 |
| --- | --- | --- | --- |
| 故事结构 | 故事结构设计与修订，第 2 版 | `creative_method.py` | 包含 SKILL、叙事与连续性；draft/review/result。未进行新的结构修订 |
| 小说 | 逐段逐章小说创作与修订，第 3 版 | `novel_writing.py begin` | 完整 SKILL 与连续性；新步骤必须取得方法，旧无方法检查点只读。未新写小说 |
| 剧本与表演原词 | 影视改编与表演原词，第 2 版 | `screenplay_writing.py context --full`、begin/save/read/accept | SKILL 与叙事、表演、声音、连续性均可取。前后场理解与实际回读仍由作者完成 |
| 逐集逐场视听 | 逐集逐场视听设计，第 4 版 | `creative_method.py` | understanding/principles/design/handoff/review 五阶段；默认无章节是按需选择，布尔 need_staging=true 能取得调度，不应误判默认空资源为失效 |
| 实体状态与素材用途 | 实体状态与素材用途判断，第 2 版 | `creative_method.py` | 调度、美术、连续性；声音可按需加。没有真实看听原件就不能完成用途判断 |
| 图像／声音／视频方案 | 分别为图像方案与提示词、音色与演唱制作方案、镜头视频方案与 Prompt，第 3 版 | `media_method.py begin` 从准确需求判断 image/audio/video | 取得 SKILL、record-contract 与相应章节。视频 case=dialogue、need_sound=true 能补对话案例和声音资料；完整方法与最终模型 Prompt 分开 |
| 字层、生成准备、结果返修 | 字层第 3 版；生成准备第 1 版；结果审阅第 2 版 | 通用作者入口与既有生成准备入口 | 均有准确方法与阶段；准备和登记不授予付费生成许可，也不能替代看片、试听 |
| 独立读者 | 独立逐段阅读第 1 版及各模式方法 | `reader_review.py` 新运行按 full、summary-reader、summary、recall-reader、grounding 固定包 | 基础文件较短不表示摘要流程丢失；mode=summary 实际取专门正文。未进行新的付费读者调用 |
| 评论润色 | 审阅意见清晰表达，第 3 版 | 页面润色→服务端实际请求 | 当前源码将完整 SKILL、包内文件和资源放进 instructions；没有新路径回退到旧硬编码自由 Prompt。未实际调用润色 |
| 创作协作 Review | 专用入口第 1 版 | AGENTS 本地场景入口，或专用工作类型 | 本轮完整三份资源匹配。Review 不应绑定到所有生成环节 |

故事采编阅读页没有独立作者方法绑定，不足以证明缺项。当前在该页面可见的 AI 动作要按实际功能判定，例如评论润色已有独立方法；“每个页面都必须有一个 SKILL”会额外增加实体，不符合愿景。

根另已亲自查看正式工作环节：`media-plan` 第 9 版按 image/audio/video 选择三个第 3 版方法，`audiovisual-design` 第 4 版默认选择逐集逐场视听设计第 4 版。这是根 UI 观察；本辅助调查没有代替根操作页面。

准确执行链的主要源码依据（系统路径相对 `../story-review-desk/`）：

- `scripts/creative_method.py:31`、`media_method.py:28`：prepare 后交付完整文件，恢复比对原执行；阶段产物依真实记录推进。
- `scripts/novel_writing.py:143`、`screenplay_writing.py:77`：新 begin 取得方法；后续校验原执行，不能给历史候选补造新方法履历。
- `review_desk/polish.py:163,257`：预算预览解析方法，执行固定快照后用 `methods.instructions` 装入真实请求。
- `scripts/reader_review.py:487,528`：新运行固定五种方法；实际请求 instructions 必须等于对应冻结包。保留的 INSTRUCTIONS 常量供旧运行兼容，不代表新运行仍绕过方法。
- `review_desk/methods.py:225` 和 `scripts/method_runtime.py:89`：instructions 实际拼接所有包内文件及已选资源全文。其他专业材料仍须依当前问题选取，未选章节不能声称读过。

## 已实证的配置回写问题：用途未改条件，条件类型却改变

人要完成的工作是改进某个创作方法的说明，并让后续作者仍按原判断得到所需知识。当前编辑器却可能悄悄改变知识选择，因此影响的是作者能否按本来选定的方法工作。

当前方法 `method.skill.audiovisual-scene` 第 4 版修订为 `9ac798963959078533328f3dc481a295cee20788e29f817436a2b0824a3a81d6`，例如调度章节的条件是 JSON 布尔值 `{"need_staging": true}`。

1. `static/methods.js:60` 把值展示为文字 `need_staging=true`。
2. 保存时第 63 行重新解析全部已启用章节，即使人没有修改条件。
3. 第 96 行 `parseMethodConditions` 只返回字符串；`true` 变成 `"true"`。
4. `methods.py:193,208` 按类型和值精确比较，因此外部工具仍传布尔 true 时，不再匹配字符串条件。

已实际执行当前解析函数的纯本地输入输出检查：`need_staging=true` 和 `need_sound=false` 均返回 string；`media_type=video` 返回 string，后者正是正常需要的类型。正式只读 resolve 也形成反例：同一第 4 版方法，布尔 need_staging=true 返回 staging，字符串 need_staging="true" 不返回章节。没有证据表明正式方法已经被这条路径损坏。

根隔离实例 `http://127.0.0.1:49292` 的保存前 GET baseline 已独立取得：

- binding：`method.binding.audiovisual-design@277edaaccdbda0fbf05e93c24ea97d02194d2fc33f6c5851b5ca967afd6999ea`。
- method：上述准确第 4 版；用途为“把准确故事事件变成连续可读的声画表达”。
- 布尔 `need_staging=true` 返回 sections=[staging]。
- resource：`method.resource.filmcraft-execution@12485da7ee3aea8d9b95e92b2bbb5e5c81f58e107b6dd06a7c63169c3b2baf35` 的 staging。

根已完成隔离真实操作：在“方法”选“逐集逐场视听设计 · 第 4 版”，只在用途末尾添加“（隔离回写检查）”，没有修改其他任何字段，保存第 5 版；再于“工作环节”将 audiovisual-design 显式选择第 5 版并保存。本辅助调查在 03:59:13 发起只读回查，前后读取同一 GET：

```text
/api/methods/resolve?work_type=audiovisual-design&conditions=%7B%22need_staging%22%3Atrue%7D
```

实际结果与应保持 staging 的预期不同：

| 同一工作请求 | 保存前第 4 版 | 根保存并绑定后第 5 版 |
| --- | --- | --- |
| `{"need_staging":true}` | staging | 空 resources |
| `{"need_staging":"true"}` | 空 resources | staging |
| narrative、coverage、staging 三项布尔 true | 三章可取 | 空 resources |

新绑定第 5 版修订 `96e56b4facbc9c7d3671ce3bd94e2d6cb5b5beafd1c1cd161713e13baf081714`，新方法第 5 版修订 `128647c5bd9bbbeb8ef41ee90964508b8dfb3d2057ab9b591c8fbcb813ce3777`。独立读取旧新方法后比较 payload，改变的字段仅为 purpose 和 resources；15 个章节的 when 值全部成为字符串 "true"。不是人主动修改了章节条件，也不是新绑定尚未生效。

同期正式 3000 只读对照仍为原第 4 版，布尔 need_staging=true 取得 staging。正式配置未写入。完整身份、请求、返回资源及新记录保存在同目录 [cycle-04-method-condition-roundtrip.json](cycle-04-method-condition-roundtrip.json)。根 UI 操作报告与本辅助调查 GET 结果是不同证据来源，已分别注明；本辅助调查没有代操作页面。旧执行继续原快照是必要保护，但本轮未新建旧执行作复验。

最小优化应是让既有编辑器保存不相关修改时保持条件类型，并能准确编辑当前已支持的布尔条件；沿当前契约回归字符串媒体类型及工作环节条件。先修这一个操作样例，再判断条件语法是否还需更多能力，不新增方法管理平台。这次独立回查已经证明根真实页面操作后的效果，但未执行后续付费调用或完整创作。

查重只读了直接相关的 0020、0021 回执和验证。`task-20261009-0020` 已 completed，承诺配置保存、绑定与准确实际执行；其页面验收以评论方法为主要样本。该任务 desk 交付 `c5976ab57900c0c5b248156becec33740a231ee3` 的条件解析函数已经是相同的全字符串实现，所以不能说这是 0001 引入的回归。`task-20261009-0021` 正式接入了主要创作方法及按需布尔章节，回执未证明这些布尔条件经过页面保存后仍正确。现已实证的回写问题应作为 0020 配置编辑能力的后续残留处理并保护 0021 有效方法，不恢复任一旧任务。

## 较小的入口差异：同一资源的两种本地文件名

Review 简短入口明确按 `method-export` 的布局链接 `shared/0.md`、`shared/1.md`、`shared/2.md`；系统 `methods.py:320` 的导出确实写这些路径，这是正常路径，0001 的既有导出恢复回执也覆盖了它。

故事通用作者的 `scripts/method_runtime.py:52 deliver_files` 对没有 companions 的资源却写 `shared/0-skill.md`、`shared/1-project-context.md`、`shared/2-vision.md`。本轮仅从正式 GET 取得 Review 包，在本轮临时目录调用这个纯文件交付函数，实际确认 SKILL 中三个相对链接均不存在，而 `RESOURCES.md` 指向的三个文件均存在；全文没有丢失。临时目录已正常删除并回查不存在，没有创建方法执行或后台记录。

影响仅限把 Review 包交给通用作者 helper 后按入口链接阅读的路径；项目本地 AGENTS 和文档要求的 `method-export` 路径是有效对照。当前没有根 UI 失败，也没有创作结果受影响证据。若需要支持通用 helper 的同一 Review 工作类型，可复用统一文件布局或让链接与实际目录一致；不应宣称必须重做方法系统。

## 主工作区与受管任务环境

AGENTS 用场景明确指向普通 `skills/creative-system-review/`；该包是 Git 受管文件。本地普通 skills 路径不在全局技能清单，符合 task 0001 明确的“不全局安装”设计，不是证据充分的发现失败。

已只读核对当前安装的 codex.task 启动器和 task 0001 的实际 launch 提示：启动提示要求先读取工作区 AGENTS/override、STATE 和知识；进程 `-C` 指向真实任务 worktree，附属仓用受管 add-dir 纳管；Git worktree 带入受管方法文件。任务执行时最新主干要求与项目一致。没有证据支持添加另一个全局加载器或用户手动设置任务仓库。

`c` 是交互 shell 的 codex.project 包装入口。非交互 bash 中 command-v c 为空不等于用户终端失效；实际 shell-init 和转发规则已读。没有执行 c task mrun，也没有为了证明入口而创建新任务或工作区。

截至 03:54:43，主账本 77 条任务均已 completed/cancelled，无未结项任务；先前核对草稿为 0。当前 Git worktree 列表仅主目录，0001 两仓生命周期均 cleaned。0001 完成回执中“TUI 仍占用待清理”是当时收尾状态，不是当前仍占用的证据。发布新任务前根仍应回读账本。

## 文档职责与尚未证明的事项

当前正文权威分工基本清楚：Review 和愿景在项目 Markdown，系统为只读准确投影；实例原生创作方法在工作方法管理；登记包是恢复与增量发布历史，种子是空实例初始化。这些规则在 `production/managed-methods.md:9-16` 明确，不能把所有文件都改成同等可编辑的 SKILL 副本。

有少量残留措辞需要谨慎解释：`managed-methods.md:18` 的“全剧重做另行开展”、旧试用验证 `professional-methods/VERIFICATION.md:69` 的“后续仍须逐集重做”，以及结构方法内“本轮方法试用”的一次性范围，会让脱离原交付背景的读者误以为旧全剧重做计划仍有效。用户本轮已明确撤销 0022/0023 且不预排全剧重做；这些历史措辞不产生新授权。前者可随相关当前入口维护改成依当前目标判断，后者是历史证据，不宜为制造一致而抹写旧事实。README 的四个制作思路子页说明也落后于当前五页，属于低影响入口文案。

尚未证明的事项：

- 本轮没有逐一新建各创作阶段的完整执行，所以阶段产物是否让人减少返工，仍要随真实创作观察。
- 没有完整观看/试听素材或生成新样片，不能从方法包完备推断影视质量。
- 外部作者工具交付了准确文件，但无法证明执行者读过；系统阶段校验也不证明理解。现有规则已经如此界定，不应添加“已读即合格”的伪确认。
- 工作方法配置页目前对较新工作类型显示英文标识（`methodWorkLabels` 只映射旧四项）；根可结合实际找方法的成本判断，不能仅因英文存在就发任务。
- 没有观察到本次启动中 AGENTS 遗失或旧 worktree 错用方法。可能的环境故障应有具体实际失败再调查。

根隔离的条件回写样例已经证明问题，应按“修改方法仍保留原知识选择”的完整目标发布有限任务。此后继续沿真实镜头工作看执行者如何选择知识、取得准确上下游材料、交付可审作品；单纯文件存在、方法数量或历史 completed 不是验收结果。
