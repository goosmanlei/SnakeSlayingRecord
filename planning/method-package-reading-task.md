# SKILL 交付包从入口读到完整方法与项目适配

本规划供 task-20261010-0005 的执行者独立恢复、实现和验收。当前 add 澄清会话只读查重、整理输入、登记完整仓库范围并发布任务；不执行下文的 begin、导出恢复、实现、集成、推送或部署。用户本次已明确授权查清后自主发布，无需逐条再确认；该授权不转化为本澄清会话执行目标的许可。

## 任务字段与读者目标

| 字段 | 确定值 |
| --- | --- |
| 摘要 | 交付的 SKILL 能从入口直接读完整方法、项目适配与愿景 |
| 优先级 | P1：阻碍已授权 Review 的直接阅读和可移植方法交接；仍可绕索引读取，未发现正文损坏，不按P0处理 |
| 复杂度／模型／推理 | 常规；gpt-6.1-sol / high |
| 同项目 task-id 依赖 | 空列表；已结项能力可复用，在途协作不冒充硬前置 |
| 可与其他任务并行 | 是，限定于下述隔离开发条件；正式共享写入串行 |
| 完整交付仓库 | primary 与唯一附属 desk；均以 main 为目标 |
| 会话媒体 | _media 已运行，零项；无保留或跳过的会话媒体 |
| 本地输入 | 指定的四份文字证据原名、原字节纳入本规划旁 inputs 目录，见后表 |

常规 high 的依据是现有路径保留与附属资料机制已经存在，改动目标和边界明确，但需联合核验两个交付实现、不可变历史、新旧绑定、空实例恢复及真实阅读，采用常规档较高推理强度。没有相对 high/xhigh/max 明确、可验证的自动委派收益，不选 ultra，不预设固定提速或质量提升。

### 目标

让新的创作/Review 执行者把受管方法包放到项目外新目录后，能够只沿 SKILL 入口读取完整方法、内链项目适配和愿景，知道本次授权、正式只读边界、项目路径基准及尚需补齐的材料，无需查源码或猜文件名。完整执行说明和原始证据见 planning/method-package-reading-task.md 与 planning/method-package-reading-inputs/。

先读 AGENTS、KNOWLEDGE、STATE、creative-system-review SKILL、项目适配与愿景，核对执行时双仓最新 main/upstream 和准确接口，在自有隔离环境复现两层断点，再完成可操作包样例。受管作者交付把无附属资料的正文写为 shared/0-skill.md 等，入口却写死标准导出的 shared/0.md 等；两种平面交付都会使完整 SKILL 内 references/project-context.md 失效。优先复用 preserve_paths（保留源路径）与 companions（同章必要附属文件），修正必要源定义、引用入口、交付布局及说明，不新增方法平台、导航页、知识复制体系或操作者手工改名步骤，不以改写批准正文的业务含义规避问题。

发现时系统为 b3fa3fef77851c544c5350cb4a99ab0af622cbd3；原 Review 执行为 method.execution.d3a77a479f3e556a6ccf7e5312a24d6d5d001b68d181f3a99d87cfc25bfc5ae0@6375033709d6ea5fb46f72238842208aa1dd4dc10e3495fbe3287d892cfa8ff5；准确资源为 method.resource.creative-system-review-texts@50b71fd8105a70264942c77673fa6b098b99fe450b20e3731ad118159f93424c。根先 begin 取方法再做 AS003 十镜 Review，三份正文原字节正确，历史不得补写为采用新方法。需要修正定义时只追加必要资源/方法版本并显式更新准确绑定，旧方法、来源、请求、冻结执行和恢复信息保留；区分导出布局兼容与执行正文替换，旧执行仍导出原正文，不能静默升级。无法修复旧定义阅读入口时如实交代兼容限制。

这是已结项 task-20261010-0001 的具体可读交付残留，复用 task-20261009-0020/0021 已交付能力，不恢复旧任务或已撤销0022/0023，不重做全剧。与0002人物比较、0003条件类型保存及0004镜头顺读目标不同；0003已触及同一 methods.py 的条件解析/保存，须按实际重叠吸收最新main并联合复验。无付费调用，不改正式故事或Prompt，不接管根Review实例。

完整交付范围为 primary=. 与 desk=../story-review-desk，均 target=main；路径相对主项目。primary 负责受管定义、必要作者交付客户端、交接说明及准确 config/instance.json.review_desk_commit；desk 负责必要通用导出/恢复契约和测试，若现有能力足够则验证兼容，不为双仓强造改动。执行时登记准确提交引用约束和 workspace guard 实际摘要，先 desk 后 primary 固定候选，经受管整组交付和共享窗口正式增量发布、只读回验，禁止隔离快照覆盖活库。四份指定文字证据原名原字节随任务分支保留，不依赖根临时目录、端口或进程长存。预期减少猜测与阅读中断，以实际阅读验证，不承诺固定提速。本会话只澄清并发布；目标由其他终端执行。

### 可验证的完成标准

1. 在自有当前准确隔离环境复现作者交付顶层文件名和两种交付共同内链两层断点。先完成一个新 Review 可操作样例，真实运行 creative_method.py begin；将包复制或移动到本任务归属明确、位于项目外的干净临时目录，从 SKILL 实际打开完整方法、正文内项目适配，再按入口读愿景，均读到结尾，不查源码猜路径。读后能复述本次授权、正式只读边界、项目路径基准和仍缺材料；自动链接扫描不作主要验收。

2. 对同一准确执行使用现有标准 method-export，在另一干净目录重复上述阅读；逐项核对必要目录/文件、原文字节、来源、输入、方法、绑定与执行身份，两条路径均实际验证，一种成功不代表另一种。

3. 将标准导出的 registry 恢复到新空隔离实例，重取同一执行、再导出并顺序阅读；冻结执行原文和来源不变。保留变更前的准确冻结样本，再以显式新绑定准备新一步，证明新包采用新定义、旧包没有混入最新版。对旧定义及历史包分别记录再导出/恢复兼容结果，未能提供的旧入口如实说明，不改写历史事实。

4. 实际阅读已有专业正常对照：媒体方法内 record-contract 可达；所选影视 staging 章节能打开 sources.md 中准确来源和所需图示，并实际观看图示确认交付可用。未选延伸章节仍按需取得，不复制整套知识、不运行真实生成；文件存在或打开不冒充已看图/听音。

5. 明确方法包、项目 AGENTS/KNOWLEDGE/STATE、作品输入及本次授权的边界，缺少的项目材料沿项目或本次输入补齐；方法可读不等于创作完成。保护工作方法管理页及0003条件类型修复；按实际重叠在最终候选上复验相关页面和专业资料选择路径，页面受阻时不以接口代替通过。

6. 适当测试覆盖两种真实布局、相对路径、空实例恢复、准确源字节及旧执行不漂移，真实阅读验收另记。执行时核验双仓最新main/upstream，完成准确提交引用约束、workspace guard摘要和受管交付；必要正式方法增量在共享锁/停写窗口串行应用，另核页面/API写入者，保全作品、评论、判断、原件和历史。正式只读回验记录准确运行及数据版本与效果边界，不能以prepare、哈希或文件数通过代替收益。

7. 最终可见回复先写准确任务编号及实际解决的问题，用“以前入口失败、绕索引后适配仍失败；以后能从入口直接读完整方法及适配”的前后例说明实际变化、收益、真实阅读环境/版本/范围、未解决事项及下一步。分开执行者完成报告、正式交付和根后续独立复验，未经根复验不代签通过，预期收益不写成已实现。

8. 按AGENTS核对归属、占用、挂载与依赖，清理自有无效容器/镜像、临时导出、测试数据库、缓存和文件；按准确ID/路径回读并报告实际数量/范围。保留项说明用途、责任及解除条件，不清理根Review或其他任务资源，不全局prune。工作区使用中不强删，退出释放锁后受管退役；受管交付文件在最终候选与_complete前收敛，之后不补改。

## 原问题及可复核依据

根在准确隔离实例中用 `creative_method.py begin` 真正开启 AS003 阅读 Review：先取方法，再读十镜及正常对照、写反馈，最后 record/read 实际结果。三份完整正文已经实际读过，不是事后补方法。这些是用户和指定证据记录的既往实践，本澄清没有重新运行或冒充完成这些验收。

以前，从交付包 SKILL 点完整方法失败，必须改从 RESOURCES.md 找正文，再点正文的项目适配仍失败。目标是把包放到项目外的新目录后，直接走“SKILL → 完整方法 → 内链项目适配”，并从入口读到愿景结尾。读者无需原作者解释或手改文件名，能知道自己获准做什么及还有什么输入缺失。预期减少人工猜测与中断；改善是否实现由两条路径的真实阅读证明。

| 身份 | 发现时准确值 |
| --- | --- |
| 系统提交 | b3fa3fef77851c544c5350cb4a99ab0af622cbd3 |
| 原执行对象 | method.execution.d3a77a479f3e556a6ccf7e5312a24d6d5d001b68d181f3a99d87cfc25bfc5ae0 |
| 原执行修订 | 6375033709d6ea5fb46f72238842208aa1dd4dc10e3495fbe3287d892cfa8ff5 |
| 原Review资源 | method.resource.creative-system-review-texts@50b71fd8105a70264942c77673fa6b098b99fe450b20e3731ad118159f93424c |
| 完整方法原文 SHA-256 | 269b0c37e472908e79963cc75a86069517f9231dfa2763aa259a1adf7cbfc40e |
| 项目适配原文 SHA-256 | 16c6fcf6b6539c79b4d539e9b1a6d35ad3dcf78904d5a1a062f6c231339243a4 |
| 愿景原文 SHA-256 | bf0914b7750a92a5482cf179e3325164930e3933213f9e2829db2aeeba3655fd |

作者交付入口链接 `shared/0.md`、`1.md`、`2.md`，实际文件为 `shared/0-skill.md`、`1-project-context.md`、`2-vision.md`。根读 `0.md` 得 FileNotFoundError；通过索引取到的三份字节仍匹配准确源。标准导出真实执行过现有 `export_execution`，顶层 `0.md` 可读，但完整SKILL内的 `references/project-context.md` 在两种平面布局中都不存在。因此改顶层文件名只处理第一层断点。

现行源码只读核验支持以下最小调查范围，具体方案由执行时最新接口及可操作样例确定：

- primary 的 `content/creative-system-review-method.json` 把三份正文定义为无 companions 的独立 section，引用入口写死标准导出名。
- primary 的 `scripts/method_runtime.py:deliver_files` 对平面资源使用带章节名的文件；desk 的 `review_desk/methods.py:export_execution` 使用纯序号文件。
- desk 的 `sync_source` 已支持 `preserve_paths` 和准确 `companions`；`resolve` 可携带章节必要 files。两条交付路径对带 files 的资源都使用 `shared/<序号>/<原路径>`。优先复用，不预先要求一定改通用导出器。
- 原文、摘要、准确来源与执行身份是保护对象，不能手改导出正文、变更批准方法的业务含义或让旧执行重新选择当前绑定。
- 包内应提供已承诺的完整方法、适配、愿景及必要附件；AGENTS/STATE、准确作品与未选专业材料按项目和本次输入补齐，不扩展为复制所有知识、项目和运行状态。

正常专业对照用准确视听方法第4版选择 staging：资源 `method.resource.filmcraft-execution@12485da7ee3aea8d9b95e92b2bbb5e5c81f58e107b6dd06a7c63169c3b2baf35`，交付 `shared/0/production/filmcraft/05-staging.md`，其 `sources.md#sp04` 与 `diagrams/sp-axis.svg` 文件已实际打开。辅助调查没有视觉观看SVG；本任务执行验收须补真实观看，不能把既往文件读取算作看图。媒体方法的 `references/record-contract.md` 属原位交付。未选 `01-narrative.md` 保持按需取得的既有边界。

## 实际工作顺序与历史兼容

执行前沿 [项目规则](../AGENTS.md)、[稳定知识](../KNOWLEDGE.md)、[当前状态](../STATE.md)、[Review方法](../skills/creative-system-review/SKILL.md)、[项目适配](../skills/creative-system-review/references/project-context.md)、[愿景](../production/system-vision.md) 读取。方法更新及恢复沿 [受管方法](../production/managed-methods.md)，工作区及交付沿 [生成工作区](../production/generation-workspaces.md)。本次具体授权优先于旧运行资料里的暂停、计时和计划；这不授权澄清会话恢复长期Review。

从执行时有效正式数据和两仓最新主干建立自有隔离环境，复现旧定义的两层断点并冻结变更前样本，先做新Review可操作包。读取准确方法后才进行有关判断、反馈和记录，不用事后补取方法冒充过程。当前隔离实例指本任务新建或准确恢复的自有实例，不是要求复用根Review端口、数据库或浏览器标签。

在项目外、归属本任务的两个不同干净目录，分别用作者 begin 交付和同一执行的标准 method-export 从入口读到结尾。保留足够阅读记录：打开的入口、所循链接、准确正文、读后的授权/材料边界复述与实际失败；不要变成仅检查链接存在或粘贴测试数量。

将该执行的 registry 恢复到新空实例，重取同一执行并再次标准导出、阅读。保留变更前冻结样本与变更后新绑定步骤的区别：旧执行原文、输入、来源、绑定不得改变；新步骤显式取新定义。历史包若只能保持旧布局或旧入口限制，应逐项报告并给准确取回方式，不能通过替换其正文或自动绑定最新版伪装修复。原发现执行的准确身份供追溯，不依赖其临时库常驻；若原始记录缺失，不凭身份补造历史，以所保留证据限定既往结论，并在可恢复的准确旧定义上建立明确标识的新复现样本。

随后做上述专业正常对照和适当自动测试。涉及最终候选中实际变化的管理页/条件选择，联合复验0003对应路径；不把本任务扩大为重新实现0003。开始、阶段成果保存后和最终候选前核对主干是否前进，按项目规则合并并复验受影响部分。冻结或部分交付沿原回执恢复；换候选重新准备，不在恢复中隐式替换。

正式交付沿现有受管多仓流程；定义改动只追加准确版本/绑定，以必要增量发布，正式阅读回验只读。不把根隔离快照灌入正式，不改正式故事、Prompt、评论、判断或旧采用，不触发真实媒体或付费模型生成。准确方法可读、执行者验收、正式生效和根后续独立复验分别报告。

## 查重、仓库与并行

2026-10-10澄清时只读核对主项目任务账本及在途工作区：

| 已有任务 | 当前核对与边界 |
| --- | --- |
| task-20261010-0001 | completed；提供Review方法、愿景、准确来源和导出恢复。本项承接具体阅读残留，不重开或否定其其他有效成果 |
| task-20261009-0020／0021 | completed；复用方法管理/执行及专业资料已有路径保留能力 |
| task-20261009-0022／0023 | 用户已撤销；不恢复、换号重发或重做全剧 |
| task-20261010-0002 | running；人物已有形象比较；在途主要为app、production-breakdown、review-ui、screenplay、unified-cards |
| task-20261010-0003 | running；条件类型无损回写；在途methods.py修改catalog、条件解析与save，另有methods.js，不是本项导出阅读目标 |
| task-20261010-0004 | 发布前回读已为published；场镜动作正文与按需生成细节，不承接本项方法包阅读链 |

以上为核对时点，不冻结其他任务状态，也不据此要求其停工。发布前和执行时再查最新在途内容。

仓库 source 均相对主项目 `/Users/bytedance/codex-path/creative/SnakeSlayingRecord` 解析，不相对草稿worktree。

| 仓库 | source及已核实源目录 | 用途与修改边界 | target | 交付依赖 |
| --- | --- | --- | --- | --- |
| primary | `.`；`/Users/bytedance/codex-path/creative/SnakeSlayingRecord` | 受管Review源定义、必要作者交付客户端及测试、交接说明、必要定义登记包和准确实例引用、发布/验收 | main | 固定desk准确候选后提交primary |
| desk | `../story-review-desk`；`/Users/bytedance/codex-path/creative/story-review-desk` | 必要通用导出、源路径/附属资料、恢复契约及测试；不反向依赖故事工具，不为双仓强造改动 | main | `depends_on=[]`；先desk后primary |

无其他附属交付仓库；只读专业资料不是独立交付仓。澄清只用 `_repositories --draft` 登记完整计划，不创建附属worktree。执行时登记并验证 `primary:config/instance.json#/review_desk_commit=desk` 引用约束，以及 `scripts/task_workspace_guard.py` 的实际SHA-256。

本地main、origin/main及远端main已只读核对一致：primary为 `3ca503d501bef61048d6c13f2b87ba85993ba2f7`，desk为 `b3fa3fef77851c544c5350cb4a99ab0af622cbd3`；两仓源目录均在main且干净。当前草稿工作区为受管任务分支，不据草稿创建提交固定未来执行基线。

并行理由：可在受管独立双仓worktree中与0002人物比较、0004镜头顺读及其他目标可分任务并行。已只读核对0003的methods.py在途修改为catalog/条件解析/save，本任务主要为来源定义、作者交付和export/restore，属同文件有限重叠，无成果硬前置；执行时复查、吸收最新main并联合复验，实际无法隔离或语义冲突部分转串行。各任务独立数据库、端口、缓存、可写/媒体目录、临时镜像标签及浏览器存储/标签，浏览器控制另协调，不使用根Review或他人实例。共享正式DB、方法配置、服务、部署入口、固定镜像标签和发布窗口按已有锁互斥串行，页面/API业务写入另核，发布锁不自动排除业务写入；开发可并行不授权并发正式发布。

## 原始输入、上下文与收尾

四份指定文件均全文读取并核验，以下路径相对本规划所在planning目录；原件在主项目本机目录只读获取。保留findings/evidence结构以维持证据之间的相对链接，原文内指向历史临时包/库的链接仅为既往记录，执行不要求那些目录存活。所有必要身份、问题、边界和继续入口已经在本规划说明。

| 原字节保留文件 | 用途 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| [cycle-04-method-package-links.md](method-package-reading-inputs/findings/cycle-04-method-package-links.md) | 两层断点、根因线索、正常对照和既往实践边界 | 11323 | 9889c26a1c2d35f2329801ba7c91f501932b7653eb10cdc200eb458eda94a520 |
| [cycle-04-method-files.json](method-package-reading-inputs/evidence/cycle-04-method-files.json) | 作者交付实际文件名、入口缺失、准确源字节 | 924 | 7580cb8b5e5c97571a3a572ff957601465ba4e68895d2b555947aabb5a0c24b9 |
| [cycle-04-standard-method-export-links.json](method-package-reading-inputs/evidence/cycle-04-standard-method-export-links.json) | 同一执行标准导出及适配FileNotFoundError | 1585 | ded382831bcbf597f1d0974cf3df514595d9997017736f317fc67c7bd1c46314 |
| [cycle-04-professional-package-control.json](method-package-reading-inputs/evidence/cycle-04-professional-package-control.json) | 专业章节来源/图示可达及尚未视觉观看的准确边界 | 3532 | 354de56de7750b2b84c6cc7679967cb2fa3027aebed1562b9a2272d14ba02ed0 |

任务媒体接口只支持图片/音频，本次没有会话媒体，也没有图片、音频、视频附件或待取得的媒体链接。四份Markdown/JSON通过Git随本任务规划原样保存，不改后缀伪装媒体，不重复复制进媒体账本；没有漏选或跳过媒体项。原始证据与任务规划在本任务分支即可读取，不全量带入旧报告、数据库或根运行环境。

AGENTS、KNOWLEDGE与STATE本次不新增任务状态：已有长期机制和职责继续有效，本次局部问题、准确输入及验收放本规划，发布/执行/完成仍以主项目唯一账本为准。发布后仅回读，不再追加文件修改。

执行结项按验收第8项清理。容器/镜像须记录准确ID、用途、新建或复用及实际引用，先清理无用容器，再清理无正式/回退/他人/恢复用途的任务镜像；删标签不等于镜像清除。不全局清缓存或prune。保留必要原件、版本、回执与最小证据并注明责任和解除条件；工作区仍被会话/进程/挂载使用时先清内部无效资源，释放后由受管cleanup退役，保留分支与会话历史。
