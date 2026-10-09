# task-20261010-0001：交付创作协作 Review SKILL 与首屏愿景

本规划供本受管任务独立执行和验收。唯一目标是把已经审定的 Review 方法和人机协作愿景真正落地到项目及既有本机审阅台。用户已通过本次 do --auto 授权本任务实现、双仓集成推送、正式发布、浏览器验收和资源清理；旧持续 Review 的暂停及 only-publish 边界保持，不能恢复旧 Goal 或任务队列。澄清规划已登记，本任务执行由原启动器衔接。

文中项目路径相对故事仓库根目录；本文件的 Markdown 链接相对 planning/。仓库 source 相对主项目解析，不相对本草稿 worktree。输入原路径仅用于记录来历；本规划及同目录的受管输入附件足以独立恢复准备工作。

## 目标与用户原始需求

下列目标字段逐字保留用户原始需求，后半补充调查形成的实施边界。原始需求中的在途状态是提出时事实，当前账本变化见“现场证据与协作”。

## 摘要

<!-- task-field:summary:start -->
交付创作协作 Review SKILL 与制作思路首屏愿景
<!-- task-field:summary:end -->

## 目标字段

<!-- task-field:goal:start -->
本次用户明确授权的唯一实际交付：把本项目系统与创作 Review 能力沉淀为可移植 SKILL，并把人和 AI 协作愿景发布为“制作思路”的第一子页。使用本次 do --auto 的完整交付授权完成澄清、实现、受管双仓集成推送、既有本机正式实例发布、真实浏览器验收与本任务资源清理，不停在发布任务。此前持续 Review 的 only-publish 与暂停状态仍适用于旧工作，不得据此阻断这次新交付，也不得恢复旧 Goal 或执行旧任务队列。

先全文读取并核对主项目批准规格：/Users/bytedance/codex-path/creative/SnakeSlayingRecord/.runtime/system-review/skill-delivery/delivery-request.md，SHA256 d99ac3b56769e8aa22f59869a94350240c7fad3eb00693c275d568b91c48db77。该目录下三份准确输入：
skills/creative-system-review/SKILL.md SHA256 fdb12e2b4eab3164473ee56c75299ef4b759fc5d47f43fe947c585f9517d1402；
skills/creative-system-review/references/project-context.md SHA256 3b9941b1a7173c80a2eda19cae0e8a8ceca581eec0eceed222717c7a94dbfcce；
system-vision.md SHA256 bf0914b7750a92a5482cf179e3325164930e3933213f9e2829db2aeeba3655fd。
全文为已经根审定的交付正文；主项目输入只读。沿 document-writing 和 skill-creator 技能完成真正落地与验收，不机械扩大正文；必要路径/能力修正须说明。根已完成 skill quick_validate，独立 forward test 正在并行，后续回执会补入此次任务，不阻止澄清和最小实现准备。

请特别遵守：交付使用普通 skills/creative-system-review/ 唯一包和 AGENTS 精确触发入口，不用 .agents 隐藏路径、不安装全局。愿景唯一正文 production/system-vision.md，由其派生 content/production-approach.json 的 vision 首 tab，无 tab 默认愿景；保留所有旧 tab ID/深链/内容/上下文。系统“工作方法”按现有 method-source 准确只读投影与简短引用接入，实际准备可取得完整方法及资源且导出可恢复，不复制成另一可编辑正文，不绑定所有生成环节。

项目 source 为主故事仓及真实 ../story-review-desk，目标均 main；按原生任务多仓纳管。desk 只做通用兼容/读取/校验，内容和创作工具留故事仓。0021/0030/0031/0033 当前均为独立 running，可并行开发；尤其保护 0021 的方法接口和 0033 的阅读返回契约，不修改其账本/会话，不重开旧任务。开始、阶段保存和最终候选吸收两仓最新 main，冻结发布按原回执处理。并行性按实际语义和隔离判断，不仅因同文件增加硬依赖或全任务独占。共享正式数据库、配置、服务及页面/API 写入必须串行协调，保全评论、认可、采纳、准确历史，不用任务快照覆盖活库。无新增付费生成，无另一个 VPS 部署，无他人资源清理。

根将在正式候选发布后亲自独立复验实际页面。本任务执行者需在自己的正式发布与真实页面复验完成后报告可复验入口、准确版本和实际状态，给外层留出独立验收窗口；最终 _complete 前等待外层转交的根独立正式页面验收结论，不能把尚未完成的根验收当通过。这不是重新向用户索权，不需再问用户。请使用自己的独立浏览器标签，不接管用户/根已有 Chrome 标签。

完整需求和所有验收需成为受管工作区自足规划及正确任务字段，不以根临时目录作为最终内容来源；无需输入媒体。公开最终回复以本次准确 task 编号、原问题、实际可用入口/行为开头，区分真实验证环境与边界、预期/实效和未完成项；给出资源删除数量/范围及保留用途。只执行这一项任务；中断保留原任务/草稿身份，通过支持入口恢复，不能重建重复任务。

执行范围与完成要求补充（依据已核批准规格及当前项目；以下为实施判断，不冒充用户逐项确认）：

完整自足规划为 planning/creative-system-review-delivery-task.md，其中保留上文用户原始需求、批准规格及三份原始正文与根后补输入；七份准确文本原样保存在 planning/creative-system-review-delivery-inputs/，名称与 SHA-256 见规划。规划附件是本次批准输入及后补回执记录，不能作为第二套持续编辑正文。正式交付仅使用项目 skills/creative-system-review/ 和 production/system-vision.md；执行不依赖根 .runtime、旧浏览器标签或旧工作区。当前回合只整理登记，启动器随后衔接本任务完整执行，不在澄清中实施或自行启动 run/mrun。

1. 从真实创作出发沉淀 AI、系统和人的责任、实践价值与成本、持续改进方法。按 document-writing 和 skill-creator 沿三份已审正文落地，不扩成长检查表，不把愿景写成已经具备全部能力。项目 AGENTS 增加精确的适用与读取入口，保持按场景自动适用；普通 skills/creative-system-review/ 为唯一可移植包，不用 .agents、不全局安装、不另建同内容 SKILL。迁移时替换项目适配，不固定本剧人物、集镜数或供应商；临时运行资料不成为执行必需品。必要路径或实际能力适配须说明具体原因和修改，不能机械改写正文。
2. 沿 production/managed-methods.md 和现有 method-source 将包正文、项目适配及必要准确资源作只读投影。系统工作方法仅用简短引用入口与范围相符的 Review 工作类型关联；实际 prepare 返回完整同源正文和适用资源，读取、准备、方法导出与新空实例恢复均能独立成立。只维护一套正文，不把只登记名字/链接当接入，不复制成另一可编辑真相，不绑全部生成环节，不造新加载器、执行服务或审批 UI。方法变更追加准确版本，保留旧绑定与执行快照，不覆盖过去或偷换其他任务方法。
3. 愿景唯一正文 production/system-vision.md；以现有 Markdown→Schema 2 模式确定性派生到 content/production-approach.json，vision 的标签与标题为“愿景与协作”，位于首项且无 tab 默认打开。完整呈现批准正文表达的五点愿景，不为凑五个标题重写正文。保留 story、materials、video-handbook、filmcraft 的既有 ID、内容、章节锚点、深链、显式目标和阅读返回；desk approach.py 只做通用顺序兼容，不改 Schema 或引入页面框架。必要发布协议修正仅纳入本次准确内容范围，保留锁、版本、准确哈希及数据保全检查；打包、挂载和正式服务都能读到正文与方法资源。
4. 仅两仓：primary source=.（主故事仓），desk source=../story-review-desk（相对主项目），均 target=main；唯一附属 desk depends_on=[]。主仓负责内容、方法投影配置、派生与发布适配、验收和准确实例引用；desk 只负责确需的通用读取、展示、校验及必要回归。执行时登记 config/instance.json#/review_desk_commit=desk 的提交约束与 scripts/task_workspace_guard.py 实际摘要，先 desk 后主仓准确引用，按原生多仓整组冻结、受管集成推送及既有本机正式发布。无其他交付仓库。
5. 无硬 task 前置。0020 基础已 completed，可消费最新有效交付；0021 方法库、0031 历史制作读取、0033 方法阅读返回保持独立。用户提交时 0030 为 running，本次账本回读已 completed，只消费其有效成果，不改写用户原始描述或完成历史。0022/0023 为后续全剧重做链，保持其原依赖，不执行或修改旧队列。双仓独立 worktree、数据库、缓存、可写目录、端口和浏览器测试存储用于本任务；使用自有新标签，不接管用户或根标签。共享正式库、配置、服务、镜像标签、页面/API 写入在核对实际写入者后串行；发布锁不自动排除页面写入。与在途任务的有限交汇吸收最新主干后联合复验，真实不能隔离的部分转串行，不据同文件设置全任务独占。
6. 开始、阶段保存及最终候选前核对两仓本地 main 与 upstream，按实际进展吸收最新提交并重验影响。冻结或部分交付只按原回执恢复；换候选重新准备。用准确增量保全活库已有作品、方法、评论、认可、采纳、准确历史及原件，不用任务快照覆盖，不绕过方法启用和兼容保护。无付费媒体生成、无另一 VPS 发布、不恢复旧 Goal、不清理他人资源。
7. 执行者先完成对应正式版本的真实浏览器复验，再向外层提供可复验入口、故事/desk/正式镜像准确版本、实际状态和未验边界，留出根独立正式页面验收窗口。根 quick_validate 和独立 forward test 的后补 validation.md 已读取并纳入自足规划；按回执限定于受限文本材料的 Review 指导，不冒称本会话运行或正式页面通过。最终 _complete 必须等待外层转交的根独立正式页面结论并处理阻断项；此为验收交接，不向用户重复索权，不自行代签通过。
8. 结项清理核对准确 ID/路径、归属、占用、挂载与正式/回退/其他任务引用；清除已无用途的本任务容器、镜像、测试库、缓存及临时产物并回读数量和范围，必要回执/原件/历史保留且说明用途和解除条件。受管交付文件在最终候选及 _complete 前完成，工作区被占用时不强删，退出释放锁后沿受管 cleanup 退役。中断保留同一任务/草稿和必要恢复现场。最终报告以本任务号、原问题及实际可用入口/行为开头，分别说明实际验证环境、范围、预期与实效、未完成项，以及真实清理数量和保留用途。


根后补输入与版本取舍：最初四份输入均已全文读取并匹配用户所列哈希，随后根在同目录修订了 SKILL 和项目适配，并写入 validation.md；同任务 do-recovery.json 的 source_update 明确关联本草稿/会话与新摘要。本规划保留原稿作批准基线，实际落地采用后补 SKILL SHA256 269b0c37e472908e79963cc75a86069517f9231dfa2763aa259a1adf7cbfc40e、项目适配 SHA256 16c6fcf6b6539c79b4d539e9b1a6d35ad3dcf78904d5a1a062f6c231339243a4；愿景和规格继续原哈希。增量仅为关键路径/既有习惯/可操作样例判断与产品演化原则原始依据链接，不复制内部文档，不让访问该文档成为方法使用前提。后补 validation.md SHA256 948cac7673df86f5dac91f8715019b7cbf2707ae2d6b22bb6ebc77ae12b43b46 一并作为输入保存。回执说明受限材料独立试用的具体结果及限制，不代表页面或全阶段通过；最终包仍需 quick_validate、路径/资源检查、实际准备与正式页面验收。外层如进一步转交修订，沿同任务核对差异和准确哈希，不覆盖或混淆已保存原件。

<!-- task-field:goal:end -->

## 验收字段

<!-- task-field:acceptance:start -->
1. 批准内容准确落地：三份已审正文完整交付，除有证据且已说明的必要路径/能力适配外不机械扩写；普通 skills/creative-system-review/ 为唯一包，production/system-vision.md 为唯一愿景正文。无空模板、个人绝对路径、固定本剧集镜数或私有运行现场依赖；AGENTS 精确触发且自动适用，不全局安装、不用 .agents、不另建重复包。执行者对最终包运行 skill quick_validate，回读必要链接和资源，并接收、核对根独立前向试用回执，处理实际有效发现，不将格式校验当行为效果。
2. 工作方法真实可用且保持唯一维护关系：系统中能找到 Review 方法；以现有 method-source 的来源路径、全文/投影摘要和准确修订形成只读投影与简短引用，prepare 实际返回同一完整方法、项目适配和本步适用的准确资源。不能只返回名字或不可恢复链接；仅绑定范围相符的 Review 类型，不改变无关生成绑定。方法定义与必要资源可导出并在新空实例恢复、重取核对；旧执行仍使用原快照，导出与系统投影不成为另一可编辑正文，不依赖根临时目录。
3. 制作思路首屏正确：真实浏览器打开 http://127.0.0.1:3000/?workspace=production.approach（无 tab）及默认站点入口，第一子页、选中态、标题、正文均为“愿景与协作”；刷新后仍正确。页面全文与 production/system-vision.md 的确定性派生相符，完整表达批准稿的五点愿景；逐段回读及截图检查，无截断、遗漏、调试信息或实现/验收日志。
4. 旧阅读与返回不退化：story、materials、video-handbook、filmcraft 的 ID、旧正文、章节锚点和深链保留；逐一打开、切换、刷新并回读。从实际制作上下文查愿景/方法，沿方法正文互链后返回，保留原子页、准确集场/版本、搜索筛选、阅读位置与隔离功能测试草稿；同时保留明确作品目标、新标签、外部链接、历史前后退的既有语义，尤其回归 0033 已交付契约。仅使用自己的独立浏览器标签，不接管用户/根标签。
5. 发布与数据保全：两仓在开始、阶段保存和最终候选前按实际变化吸收最新 main/upstream；最终实例引用与 desk 准确提交一致，原生任务多仓集成及必要 push 有实际回执。沿既有协议把本次 production-approach 与方法准确增量发布到既有本机正式实例，打包/挂载/重启后仍可读取；不改 Schema、不绕过发布锁、版本或保全校验。已有作品、方法、评论、认可、采纳、原件与历史逐项按适用契约核对保留，不拿测试快照覆盖活库；共享页面/API 和服务写入串行协调，无新增付费生成或 VPS 部署。
6. 验证证据与结项门槛明确：针对顺序兼容、派生一致性、完整方法准备与导出恢复、旧绑定保护运行必要自动检查；在隔离实例真实操作，再在准确正式版本只读复走。自动检查、接口、隔离页面、正式页面与根独立验收分别记录，不能互相替代。执行者正式发布和实测后报告复验入口、准确版本及实际状态，等待外层转交根独立正式页面结论，处理有效阻断后才允许 _complete；未收到结论保持待验，不重复问用户权限，不把根尚未验收写成通过。
7. 本任务过程资源按准确归属完成清理回读：报告容器/镜像、测试库、缓存和临时文件实际删除数量及范围，保留正式资源、历史、原件和必要恢复证据并说明用途、责任及解除条件。仍占用的工作区不强删，释放会话/锁后受管退役；不清理他人资源、不全局 prune、不在 _complete 后补改交付文件。未清项如实列明原因、责任和下一步。
8. 最终公开回复开头为“task-20261010-0001”及原问题、用户现在可用入口/行为，随后说明实际变化与收益、准确验证环境/范围、预期与已实现效果、根独立验收状态、未完成事项与下一步及清理结果。不得把规划、根既有 quick_validate、加载记录或接口通过冒充正式页面和行为已验收；失败或中断同样如实报告并保留原身份。
<!-- task-field:acceptance:end -->

## 优先级

<!-- task-field:priority:start -->
P1
<!-- task-field:priority:end -->

## 复杂度

<!-- task-field:complexity:start -->
复杂
<!-- task-field:complexity:end -->

## 推理强度

<!-- task-field:effort:start -->
xhigh
<!-- task-field:effort:end -->

任务最初按 `gpt-6.1-sol / xhigh` 发布，账本保留该历史配置。执行中用户通过官方 `/model` 选择 `gpt-6-astra / max`，仅覆盖当前会话；后续执行按用户最新选择，恢复时先重新认证并核验实际会话模型。复杂度依据是双仓方法与页面兼容、准确增量发布、恢复和真实页面验收的结合；已审定正文不需重新做开放式创作研究，不因执行耗时选择 ultra。

## 并行许可

<!-- task-field:parallel:start -->
yes
<!-- task-field:parallel:end -->

## 并行依据

<!-- task-field:parallel-reason:start -->
本任务只新增项目 Review 方法包、愿景首 tab 及必要通用顺序/读取/校验和发布适配；与 0021 方法库、0031 历史制作读取、0033 阅读返回存在有限接口交汇，使用各自受管双仓 worktree、隔离数据库/缓存/可写目录/端口及浏览器测试存储，并用自有标签，可独立开发。保护 0021 方法契约及 0033 返回语义，开始、阶段保存和最终候选前吸收最新 main 后复验，不因同文件加硬依赖；0030 已完成仅消费成果，0022/0023 不执行。正式数据库、配置、服务、镜像标签、页面/API 写入及发布窗口必须核对写入者后互斥串行，发布锁不自动排除页面写入，不用任务快照覆盖活库。实际资源不能隔离或出现语义冲突时只将相关部分转串行；并行许可不代替根独立正式页面验收。
<!-- task-field:parallel-reason:end -->

## 双仓范围与交付顺序

| 仓库 | source 及真实源目录 | 修改边界 | 目标与交付依赖 |
| --- | --- | --- | --- |
| 主仓 primary | `.`；`/Users/bytedance/codex-path/creative/SnakeSlayingRecord` | 普通 SKILL 包、愿景 Markdown、AGENTS 精确入口、制作思路派生内容与必要派生工具、方法投影/配置/必要恢复数据、已有发布适配及验收资料；必要时按职责更新现有知识/状态 | `main`，upstream `origin/main`；准确引用 desk 候选 |
| 附属 desk | `../story-review-desk`；`/Users/bytedance/codex-path/creative/story-review-desk` | 通用 tab 顺序兼容，以及本次实际需要的读取/展示/校验、契约与回归；不保存本剧正文或导入故事创作工具 | `main`，upstream `origin/main`；附属 `depends_on=[]` |

附属仓库完整列表仅 desk。只读技能、主项目批准输入及历史任务资料不列交付仓库；澄清不创建 desk worktree。先 desk 提交，再更新 primary 的 `config/instance.json.review_desk_commit`；执行会话登记提交引用约束和 `scripts/task_workspace_guard.py` 当时实际摘要。Git 集成与 push 由原生任务工具交付，项目发布消费逐仓回执；按 [工作区流程](../production/generation-workspaces.md) 完成 `_prepare_integration --push`、准确发布包、`_deliver`、正式发布及实测，根独立页面结论与清理均满足后才 `_complete`。本次 do --auto 已授权，无需重新索权。

完整附属计划：

```json
{
  "repositories": [
    {
      "name": "desk",
      "source": "../story-review-desk",
      "purpose": "通用制作思路 tab 顺序兼容及本方法接入确需的读取、展示、校验与必要回归；沿用 method-source、现有方法准备/导出恢复及阅读返回契约。SKILL、愿景、方法内容、故事特有创作工具与正式数据留主仓，不引入新加载器、Schema 或页面框架。",
      "target": "main",
      "depends_on": []
    }
  ],
  "complete": true
}
```

## 现场证据与协作

本段为 2026-10-10 需求整理中的只读核查，不是实现或页面验收结论。主项目 AGENTS、KNOWLEDGE、STATE 和必要入口已读，`codex.project context check` 识别 v1；仅提示 KNOWLEDGE 体积，未发现需本任务扩大维护的协议问题。会话标题工具识别内部非交互会话，未接管标题。主仓与 desk 当时均为 main、跟踪 origin/main，工作区干净；执行仍须重新取最新基线，不冻结本段快照。

- 主仓起始快照 `8929ebdd4cef4c547b6c05d2b220a46646c09b40`，desk `f416784b6c82d397e4cc8e45fd68cf63f7c0e184`，当时各自与本地 origin/main 引用一致。本回合未 fetch、merge 或 push；并行任务已使主仓上下文继续前进，不据草稿文件宣称最新正式状态。
- `content/production-approach.json` 当前 Schema 2，依次为 story（8 节）、materials（11 节）、video-handbook（23 节）、filmcraft（16 节）。这些数量只是本次定位快照，验收保留实际最新有效内容，不固定未来章节数。
- desk `review_desk/approach.py:read_document` 当前要求前两项为 story/materials，确需最小通用兼容。前端已有取第一有效 tab 的路径，实施时复核整个默认选择与导航链，不另造框架。
- `scripts/material_review_release.py:prepare` 对 production-approach 变化有旧 task 白名单；本次在原协议内加入准确授权范围并保留冻结包/版本/哈希/锁/保全检查，不能直接绕过或撤销保护。
- desk `review_desk/methods.py:sync_source` 已支持项目 Markdown 的 source 路径、全文与投影摘要、准确只读资源；`prepare`、`method-export`、`method-registry`、`method-restore` 已有完整文件/资源与恢复契约。主仓 [受管方法](../production/managed-methods.md) 规定原文和投影维护关系，通用接口详见 desk 的 `docs/managed-methods.md`。本任务在现有能力上接入，实际返回全文仍需执行验收。
- 现有 `scripts/sync_video_handbook.py`、`scripts/sync_filmcraft.py` 提供 Markdown→Schema 2 的派生模式。批准愿景未带手册章节锚点，实施时按最小需要适配稳定锚点/派生，保持可读正文和旧页签不变，并说明必要适配。

已读取未完成任务目标、范围和依赖：

| 任务 | 本次账本状态与作用 | 本任务边界 |
| --- | --- | --- |
| task-20261009-0020 | completed；现有方法资源、绑定、准备与恢复基础 | 使用最新有效交付，无需再加已完成硬依赖 |
| task-20261009-0021 | running，依赖 0020；主要创作制作 SKILL 及专业方法库 | 本任务只交付 Review 方法，保留其接口、资源和编辑历史；有限方法配置/文档重叠在各自候选集成 |
| task-20261009-0022 | published，依赖 0021；逐集重作视听与必要需求 | 不启动、不改作品，不挪用其任务授权 |
| task-20261009-0023 | published，依赖 0022；全剧生成方案与 Prompt | 不启动、不绑定全生成环节，不新增生成 |
| task-20261009-0030 | 最新回读 completed；准确参考原件已有人工判断读取 | 仅保留已交付行为，不重开或修改历史 |
| task-20261009-0031 | running，无依赖；历史设计对应准确制作需求与方案 | 不改历史制作定义、评论归属与当前编辑契约；必要交汇仅做兼容复验 |
| task-20261009-0033 | running，无依赖；查方法后返回原制作工作 | 保护方法正文互链、显式作品目标、独立新标签和阅读/草稿恢复；从最新 main 消费有效成果 |

任务依赖为空是基于目标可独立完成与已有方法基础，不是依据任务小或只因存在 worktree。登记 parallel=yes 的条件见并行字段；正式写入、部署标签及 API/页面写入必须协调串行。开发过程中出现真实不能隔离或语义冲突时只暂停相关部分，不改旧账本/会话，不擅停其他执行者。

## 执行顺序与验收交接

1. 沿本任务支持入口领取两仓并核对最新规则、main/upstream、正式身份和在途发布；重验受管规划附件哈希。读 document-writing、skill-creator、受管方法与工作区流程，先把三份已审正文落到唯一维护位置。不得把本回合的规划或输入纳管写成已实现。
2. 完成最小 method-source 投影/简短入口与 Review 工作绑定；在任务隔离实例实取 prepare、读完整正文及准确资源，导出并恢复到新空实例核对，保留旧执行。复核可移植包不依赖本机私有运行目录，跨项目时只替换适配。
3. 派生 vision 首 tab，做 desk 通用兼容及必要发布适配；检查所有旧 tab/锚点/深链。使用任务独立端口、数据、浏览器测试存储与自有标签真实回读；按当前工具先查可用浏览器，优先连接的 Chrome。遵守项目明确的浏览器初始化失败处理，工具失败只记受影响项，不以接口冒充浏览器通过。
4. 吸收阶段最新双仓成果，复验实际重叠，精确准备候选、提交引用、清理检查器和发布包。只在协调后的正式写入窗口由既有工具完成集成推送、配置/内容准确增量及正式服务发布；保全实时用户数据，不回灌测试库。
5. 执行者在自有正式页标签复走无 tab 愿景首屏、刷新、四旧深链、实际方法读取及阅读返回。记录真正运行的版本和入口、逐段阅读/截图、必要方法准备和恢复证据，区分只读页面、隔离写入与接口验证边界。
6. 向外层转交正式复验入口、准确版本、已经验证的行为和未验事项。根会在正式候选上独立复验；核对附录已收到的 forward test 回执、适用输入版本和可得产物，收到根独立正式页面结论且有效阻断处理完成后才结项。没有根结论时保持待验、保留必要现场，沿现有会话等待外层交接，不把等待当新授权问题，也不代签验收。
7. 清理本任务无效过程资源并按准确 ID/路径回读；受管交付文件在 _complete 前整理完成。正式当前/回退/基底、原件、历史和必要恢复证据保留并说明用途；会话/锁释放后再受管退役双仓。最终答复以任务号、原问题、可用入口开头，报告真实验收边界及删除数量/范围，不把尚待根复验或仍占用资源说成已通过/已清理。

根独立 forward test 的 validation.md 后补回执已收到，全文与边界在附录；根独立正式页面回执仍须外层稍后交入同一任务。前向试用不证明正式页面，必须明确区分已接收的受限试用结论与尚待正式复验，不自造回执或推定通过。以上验收交接不恢复根旧持续 Review Goal。

## 批准原件与恢复

`_media` 已执行，本会话无待保留媒体，用户明确无需输入媒体。以下四份文本原件逐一按 SHA-256 核对，连同后三份根补充文本，保存在 `planning/creative-system-review-delivery-inputs/`。登记工具拒绝 Markdown 类型的媒体输入，本任务无需媒体，因此将准确文本作为受管规划附件提交，不声称存在账本媒体 inputs。原始规格全文和附件使工作区自足；这是批准输入记录，正式实现的唯一正文仍分别位于普通 SKILL 包和 production/system-vision.md，不能反向编辑附件代替维护正文。

| 输入相对批准目录路径 | 受管输入名 | SHA-256 |
| --- | --- | --- |
| `delivery-request.md` | `delivery-request.md` | `d99ac3b56769e8aa22f59869a94350240c7fad3eb00693c275d568b91c48db77` |
| `skills/creative-system-review/SKILL.md` | `creative-system-review-SKILL.md` | `fdb12e2b4eab3164473ee56c75299ef4b759fc5d47f43fe947c585f9517d1402` |
| `skills/creative-system-review/references/project-context.md` | `creative-system-review-project-context.md` | `3b9941b1a7173c80a2eda19cae0e8a8ceca581eec0eceed222717c7a94dbfcce` |
| `system-vision.md` | `system-vision.md` | `bf0914b7750a92a5482cf179e3325164930e3933213f9e2829db2aeeba3655fd` |

以下附件保留原字节文本与末尾换行；执行时从本规划相邻的受管输入目录取原件并校验哈希。附件正文中的相对路径按各原文件约定解析，不相对规划附件目录解析。

本次澄清暂存的七份重复输入、两份临时脚本和一份 do-recovery 快照共 10 个文件已核准归属并清除，临时目录已退役；正式实现、服务、数据库和其他任务资源在本回合均未修改。七份受管规划附件保留，用于准确输入来源、前向试用回执和必要版本追溯；它们不是另一套可编辑方法，实际交付正文只在指定唯一路径维护。

## 批准输入 1：delivery-request.md

准确原件：[delivery-request.md](creative-system-review-delivery-inputs/delivery-request.md)。原字节和哈希按上表核对。

````markdown
# 创作协作 Review SKILL 与系统愿景交付

用户明确要求把根会话的系统与创作 Review 能力沉淀为本项目通用 SKILL，并将五点系统愿景实际发布到“制作思路”的第一个子页面。请在一个受管双仓任务内完成实现、Git 集成、既有正式实例发布、真实浏览器验收和本任务过程资源清理，不停在发布任务或提交草稿。

## 内容与目的

准确输入来自主项目 `.runtime/system-review/skill-delivery/`：

- `skills/creative-system-review/SKILL.md` → 项目 `skills/creative-system-review/SKILL.md`。
- `skills/creative-system-review/references/project-context.md` → 同包对应路径。
- `system-vision.md` → 项目 `production/system-vision.md`。

这是根基于已发布 31 项任务及当前页面实际使用完成的正文。以这些正文交付；如落地发现路径或能力不符，修正适配表述并告知根，不擅自改成仅供机器追溯的长检查清单。SKILL 的目的是从真实创作出发划分 AI、系统和人的责任，通过实践验证价值与成本，并持续改进作品、方法和系统。愿景是用户能独立理解的产品方向，不夹带任务编号、验收日志或实现说明。

## 最小实现

1. `skills/creative-system-review/` 为本方法可移植包及唯一正文。在项目 AGENTS 的必要入口明确何时读取它，保持自动适用，不安装到全局或另建同内容 SKILL。愿景唯一正文在 `production/system-vision.md`，页面由它派生，不能维护第二份手写正文。
2. 按现有 `production/managed-methods.md` 的资源投影与方法配置契约，使系统“工作方法”中能查到并实际取得这个方法和准确相关资源。本地包与系统正文不得成为两套独立可编辑真相：使用已有 `method-source` 准确只读投影和简短引用入口，说明维护及同步关系，加入范围相符的 Review 工作类型；不要绑定到所有生成步骤，不做新方法加载器、新执行服务或新审批 UI。实际验证取得的完整方法能读到正文及适用资源，而不只是登记一个名字或链接。导出交付能够保留方法及其必要内容，不依赖根的私有 `.runtime`。
3. 将“愿景与协作”作为 `content/production-approach.json` 的独立 `vision` tab 放在首位，未指定子页时默认打开。保留 story、materials、video-handbook、filmcraft 既有 ID、内容、深链与返回行为。现 desk `approach.py` 将前两项写死为 story/materials，应做最小通用兼容调整；不改 Schema，不引入页面框架。复用 Markdown→Schema 2 的现有模式，检查派生正文准确。
4. 更新必要的项目入口和受管方法说明，记录本项目包与实例方法配置的唯一维护关系。源码中的本剧愿景和方法内容留故事仓，desk 只做通用读取/展示/校验能力。确保打包、挂载和正式发布后正文/方法仍可访问。发布脚本有 production-approach.json 的旧任务限制时，在既有发布协议中纳入本次准确范围，不绕过发布锁、版本和保全校验。

## 验收

- Skill frontmatter/name 校验通过；独立试用由根提供回执。无空模板、无个人绝对路径、无固定本剧集镜数或私有运行现场依赖。项目后续会话能沿 AGENTS 明确找到并应用它；系统准备操作实际返回同一正文和准确资源，旧执行不被新方法覆盖。
- 真实浏览器打开“制作思路”无 tab 的入口，第一子页及当前正文为“愿景与协作”，完整呈现用户五点愿景；刷新保持正确，旧子页深链可用，切换与返回维持已有阅读上下文。回读所有段落，截图检查排版、文字无截断和无调试信息。
- 活库已有方法、作品、用户评论、采纳与历史保留；方法新增和内容更新可准确回读。合理检查相关自动化与真实页面，不能只拿单测/API 代替浏览器。
- 结项报告先写准确任务编号、实际解决的问题和用户现在可用的入口；再给验证环境/范围、未解决项、删除数量/范围及保留用途。不能把计划当交付。根会再独立核查正式页面。

## 执行与并行边界

本次用户的明确交付授权允许对这一新任务使用 `codex.task do --auto --wait` 并完成执行、集成及本项目既有正式实例发布；此前根持续 Review 的 only-publish 限制不适用于这次具体交付。除此之外，原持续 Review 仍暂停：不恢复旧 Goal，不启动队列，不改变旧任务的状态或范围，也不附带解决页面复杂性问题。

开始和最终候选时读取实际最新主干；故事仓 + 真实 `../story-review-desk` 沿任务原生多仓工作区纳管，不在主工作区直接实现。0021 方法库和 0033 阅读返回等可能在途，按实际接口与修改保留兼容，不按同文件一律串行。正式共享库和服务写入仍沿发布窗口串行。本次不发起付费媒体生成，不自行部署到另外的 VPS，不清理其他任务资源。
````

## 批准输入 2：skills/creative-system-review/SKILL.md

准确原件：[creative-system-review-SKILL.md](creative-system-review-delivery-inputs/creative-system-review-SKILL.md)。原字节和哈希按上表核对。

## 批准输入 3：skills/creative-system-review/references/project-context.md

准确原件：[creative-system-review-project-context.md](creative-system-review-delivery-inputs/creative-system-review-project-context.md)。原字节和哈希按上表核对。

## 批准输入 4：system-vision.md

准确原件：[system-vision.md](creative-system-review-delivery-inputs/system-vision.md)。原字节和哈希按上表核对。

## 根后补回执与落地输入

初次读取后，主项目输入发生了并发更新；未将新字节冒充原哈希。通过原稿与修订差异恢复的最初输入再次匹配全部四项批准 SHA-256，已在本工作区核对并作为受管规划附件完整保存。下表后补输入连同原四项随本任务规划提交，最终实现采用后补的两份方法文本。保留原稿仅用于解释本次批准与后补的来源，不作为第二套持续维护正文。

同任务 `do-recovery.json` 记录 source_update 的新摘要、validation 路径及排队至本澄清会话的补充消息标识；本回合已从授权输入目录读到文件回执，但未把排队消息写成已消费的用户新发言。此次后补内容不改变两仓范围、授权或验收门槛。

| 后补输入 | 受管输入名 | SHA-256 |
| --- | --- | --- |
| `skills/creative-system-review/SKILL.md` | `creative-system-review-SKILL-updated.md` | `269b0c37e472908e79963cc75a86069517f9231dfa2763aa259a1adf7cbfc40e` |
| `skills/creative-system-review/references/project-context.md` | `creative-system-review-project-context-updated.md` | `16c6fcf6b6539c79b4d539e9b1a6d35ad3dcf78904d5a1a062f6c231339243a4` |
| `validation.md` | `skill-validation.md` | `948cac7673df86f5dac91f8715019b7cbf2707ae2d6b22bb6ebc77ae12b43b46` |

2026-10-10 用户转交的当前回执（2847 bytes）替代早先 2416f041… 回执，新增《归航》模拟创作计划试用，三份交付正文摘要未变。根回执中的独立试用使用页面文本快照、迟到响应反馈及另一故事的模拟材料，没有操作页面、真实制作另一作品或发布任务；对根提供回执的转录不等于本会话执行了试用，也不扩展成所有故事/阶段有效。后补修订只增加一个必要性判断和一条参考来源，不需要为本次交付重读或复制私有飞书正文。最终正式页面仍待根独立验收。

## 后补输入 5：skills/creative-system-review/SKILL.md

准确原件：[creative-system-review-SKILL-updated.md](creative-system-review-delivery-inputs/creative-system-review-SKILL-updated.md)。原字节和哈希按上表核对。

## 后补输入 6：skills/creative-system-review/references/project-context.md

准确原件：[creative-system-review-project-context-updated.md](creative-system-review-delivery-inputs/creative-system-review-project-context-updated.md)。原字节和哈希按上表核对。

## 后补输入 7：validation.md

准确原件：[skill-validation.md](creative-system-review-delivery-inputs/skill-validation.md)。原字节和哈希按上表核对。

