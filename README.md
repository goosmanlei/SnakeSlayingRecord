# 李寄斩蛇 · 故事采编实例

本仓库是公开故事实例，不包含审阅台系统代码。系统代码及后续迭代在 [story-review-desk](https://github.com/goosmanlei/story-review-desk)；所需系统版本固定于 [config/instance.json](config/instance.json)；本实例的集场阅读、评论与正式运行状态分别见 [验证记录](VERIFICATION.md) 和 [当前状态](STATE.md)。已选方向三《把灯带回家》，当前作品包括[故事结构第十稿](http://127.0.0.1:3000/?workspace=story.outline)、[故事精修九 · 定稿候选](http://127.0.0.1:3000/?workspace=story.sources&source=refinement-09-lantern-home-v9)和[剧本版本四](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-04-lantern-home&episode=screenplay-04-lantern-home-e01)。旧版本及评论保留；用户已确认版本四为本次制作终稿，精确输入与两轮制作审阅边界见 [当前状态](STATE.md)。

## 故事创作导航与评论数

故事采编、故事结构和故事剧本均选中一级“故事创作”，顶部 Tab 区分当前子页。采编不再提供右上搜索框、资料总数及正文重复“审阅意见”按钮；浮动“查看评论”、正文高亮和圈选入口继续使用共用评论面板。

采编每份资料和精修版本显示当前修订的“评论 N”，分类分别显示资料项数与评论合计；结构每个“第 N 稿”显示该稿评论总数。总数包含已关闭评论，不计删除记录或编辑／状态历史；新增后增加，编辑、关闭和重开不改变。共用面板继续显示未关闭／历史待决，不应把两种数字当作相同口径。使用、验证和本机候选版本见 [界面统一交付](planning/story-creation-ui-unification-delivery.md)。

当前素材审阅、恢复及退役范围见 [生产制作](production/README.md)，正式发布状态见 [STATE.md](STATE.md)。

## 评论输入

故事采编、故事结构和剧本分集共用评论输入框。聚焦输入框时按 ⌘+Enter 提交或保存修改，按 Esc 取消并放弃本次未提交内容，已保存评论不变；普通 Enter 换行。输入框外 Esc 仍收起面板并保留草稿。中文输入法组合期间不触发快捷操作，保存中不能重复提交。实现、验证与验收范围见[快捷键交付说明](planning/comment-shortcuts-delivery.md)。

## 制作与审阅

[生产制作](production/README.md)统一组织视听制作、实体管理和素材管理。当前[全剧视听设计](production/audiovisual/README.md)覆盖版本四的 17 集、42 故事场，重编为 65 个视听场、344 镜；1,534 项新需求与四项保留歌曲需求共用准确素材关系。6021 秒是为表演和动作预留的保守方案估计，约 100 分钟，不是成片实测。用户允许适度加长，以动作和表演读得清楚为先。

“制作思路”有故事创作、生产制作、[视频生成手册](production/seedance-video-handbook.md)和[影视专业知识](production/filmcraft/README.md)四个子页。正文由 [content/production-approach.json](content/production-approach.json) 与相应方法原文维护；桌面常驻目录，窄屏横向目录，支持准确章节链接。

每镜支持多个需求、每需多个方案版本和候选；实体状态、准确来源、关系、候选比较、评论和采纳共用详情。管理列表按四列基准行分页，窄屏只重排当前集合。技术验收不代表用户接受新设计，已有图像与音频不代表镜头视频已生成。本任务没有媒体生成调用。

生成、登记、预览、增量发布和恢复均按 [受管工作区流程](production/generation-workspaces.md) 执行。当前发布状态只认主项目任务账本与实际运行回执；候选文件与正式服务分别核对。

## 资料与出处

最新交付为[《把灯带回家》版本四](imports/screenplay-04-clean.md)：17 集、42 场，单集预计正片 3:50—4:55，总计 73:12，非成片实测。[正式入口](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-04-lantern-home&episode=screenplay-04-lantern-home-e01)可逐集逐场阅读和评论。全部 73 条意见已映射到新稿，旧稿和最终稿各有 336 项检查；[审校说明](planning/screenplay-04-review.md)集中列出三条联动修改、真实逐场过程、表演估时与验证边界。旧三版保留，用户已确认版本四为本次制作终稿，接受记录见 [输入锁定](production/source-lock.json)。正式浏览器验收中 C40 曾被误关闭并已恢复，其记录版本与两条审计历史如实保留，详见[输入差异](planning/screenplay-04-input-diff.json)。版本四创作时的候选挂载和受控集成证据保留在该任务交付文件；当前制作输入、运行边界及工作区见 [当前状态](STATE.md)。

此前发布的[分集影视剧本版本三](imports/screenplay-03-clean.md)：17 集、42 场，单集预计正片 3:52—4:53，总计 74:10，均非成片实测。[版本三入口](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-03-lantern-home&episode=screenplay-03-lantern-home-e01)可逐集、逐场阅读和评论。先归纳版本二前五场 47 条评论的共性，再结合[John August 原始资料研究](planning/john-august-screenwriting-research.md)重构全剧；[历史审校说明](planning/screenplay-03-review.md)列明该版全部评论处理、版本二全场诊断、结构调整与具体表演估时。版本一、二及旧评论均保留。作品发布与任务集成、用户接受分别记录。

此前发布的[分集影视剧本版本二](imports/screenplay-02-clean.md)：21 集、47 场，每集预计正片 3 分 35 秒至 4 分 55 秒，总计 93 分 25 秒，均非成片实测。依据精修九、结构第十稿及版本一首场六条评论逐场重构，完本后另做弹性描写密度审校并原地回修。[正式版本二入口](http://127.0.0.1:3000/?workspace=story.script&script=screenplay-02-lantern-home&episode=screenplay-02-lantern-home-e01)可阅读全文并评论。正式集场界面与采编、结构共用顶部页签，版本栏只显示版号；横向分集与左侧场次均显示各自评论数，选集自动打开第一场，常驻本集概览，右侧阅读该场完整正文；[两版逐集摘要](content/screenplay-summaries.json)按分集精确修订匹配，不修改已发布正文与评论。旧“剧本一”仅显示为“版本一”，其 17 集、51 场及全部原评论保留。集场界面及评论快捷键已正式可用；详见[验证记录](VERIFICATION.md)。创作过程、逐条处理和估时见[版本二审校](planning/screenplay-02-review.md)，版本一的历史审校仍见[原记录](planning/screenplay-01-review.md)。各版均保留供用户审阅。

当前保留本项目写作的[白话直译与词语说明](export/materials.json)，原文出处仍链接至《搜神记》卷十九。它是现代整理材料，不是古籍底本或改编。两份文言资料、陈峰福州评话外链索引及共用异文图已按任务要求从当前实例清除；Git 历史仍可回溯。故事采编另收录 32 则通俗白话情节素材（其中缇萦为历史叙事、木兰为叙事歌谣，已明确标注）和 3 个并列的原创完整扩写方向。演绎媒体与转写子项已由用户允许取消，不计入本轮交付；用户已于 2026-09-22 确认该任务按调整后的范围完成。

三篇扩写的干净正文可单独阅读：[九女有名](imports/direction-01-clean.md)、[山心水](imports/direction-02-clean.md)、[把灯带回家](imports/direction-03-clean.md)。它们均为七场连续故事和 25 分钟制作估算，用户已于 2026-09-22 确认文字优化完成。方向一、二的评论已关闭，方向三原稿及评论保留。小说独立阅读，不把原梗概的 25 分钟估算当作小说的成片时长；历史清理与验收见 [VERIFICATION.md](VERIFICATION.md)。

[故事结构](imports/story-structure-01-clean.md)当前为修订 10，包含主题、人物、关系、空间、故事线和时间线六部分，21 段说明与九张图。三张原生 4K 图片沿用已经核对的庙院、短石道剖视和八人站位；六张示意图中更新人物变化、机关与因果三张，其余沿用。人物关系与场所未改，求援和停止尝试仍可选择，李寄在成人确认隔离条件后主动试刀。旧结构修订、旧图及 11 条结构评论保持原位。

[故事精修九：《把灯带回家》· 定稿候选](imports/story-refinement-09-clean.md)是完整、独立可读的十章干净稿，正文 29,046 字符（含标点和章内换行，不含章名）、622 个正文自然段。前半保留毁本、失约、生计与父辈承担；后半补实际求援、李寄主动请试、父亲核看和可停手的过程，继续写足惊惧、失手与疲劳。十章串行保存、另次回读后采用，全稿复核跨章因果、人物、对白、时空和照应。原有 44 份资料、136 条评论及 154 条评论事件未变，新增两条精修八审阅评论仍保留在原文。

本故事沿用[小说创作方案](planning/novel-creation-plan.md)与[后台执行流程](planning/incremental-writing-workflow.md)：先整理并发布可审阅的结构图文稿，再依据其具体版本逐段修小说；发现设计与正文冲突时，联动回修。创作工具 [scripts/novel_writing.py](scripts/novel_writing.py)只依赖 Python 标准库，不属于审阅台系统。未完成正文、候选、构想和检查点仅保存在本机工作库；小说只发布完本干净稿，结构稿作为独立阶段成果供审阅。

精修六已完成[独立逐段审阅](planning/reader-review-workflow.md)：每次只向独立模型开放一个自然段，明确问题直接评论到精修六。按用户 2026-09-28 的费用调整要求，从第 314 段起每 20 段汇总一次，后续携带短摘要、本组已读原文和问题记录，并有限回看已读原文核对评论；前 313 段原始请求保留。它不继承作者背景，也不使用会自动附带整稿的 AI 润色接口。全部 1,032 段及文末步骤已完成，共挂 4 条评论：2 条仍建议澄清，1 条后文已解释，1 条摘要误读已撤回，正文未改。程序为 [scripts/reader_review.py](scripts/reader_review.py)，批次 `refinement-06-cold-reader` 的报告、检查点与费用证据位于本机 `.runtime/reader-review/`。完整审计、49 项测试及导出恢复通过；摘要模式调用用量折算约 17.55 美元，费用口径与该批次最终状态见 [VERIFICATION.md](VERIFICATION.md)。

当前交付证据在本机 `.runtime/task-20260929-0001/`：严格隔离审阅十章、604 段，实际输入只含截至当前章的原文和读者自己的先前判断。最初子代理获自动记忆，其结果仅作补充，不计冷读验收；重新完成的 API 冷读提出 1 条时间指代问题，补充审阅另有 1 条人手调度观点，两者在正式评论中区分。`writer/comment-handling.json` 保存逐条决定与新稿精确引用；`evidence/` 保存覆盖、全稿、浏览器、数据一致性和空库恢复证明。API、导入、干净稿与导出一致，恢复再导出的 56 个文件逐字节相同。`.runtime/refinement-08/` 等旧批次仅作历史证据，不可重放覆盖当前作品。作者审校不等于用户接受；本次公开提交包含故事实例的正式作品、评论、结构素材与创作工具，运行边界见 [STATE.md](STATE.md)。

通用审阅台支持对 `folk-tales`、`expansion-directions`、`story-refinements` 分类的独立二级菜单；本实例的分类、正文与出处分别保存在 `export/materials.json`，采编输入见 `imports/`。三组默认收起且可独立展开。资料条目只显示标题，版本类型与来源在右侧详情查看。精修一至九的菜单标题省略重复的“第N版”，各版本下另有可展开的章节三级菜单：前五版各 12 章，精修六 15 章，精修七、八、九各 10 章，共 105 个入口。点击章名跳到章首，目录随正文滚动高亮，收起章节不改变阅读位置；故事结构目录也随阅读位置高亮。桌面页面滑至顶栏后，左侧目录与右侧正文各自滚动；切换资料不会把整页拉回顶部，窄屏目录也可内部滚动。评论浮窗可按 Esc、点击窗外或点关闭按钮收起；重新打开时未保存的编辑状态仍在。

已有高清图片统一在 OpenArt 独立项目“李寄斩蛇 · 把灯带回家”创作，项目 ID、CLI 优先及原生 4K 参数见 [config/openart.json](config/openart.json)。精修八生成时 CLI 登录请求超时，使用已连接的 OpenArt 连接器生成；沿用的三张正式 PNG 分别为 5056×3392、5056×3392、5504×3072。用户已将相关图片移入新项目，列表回读核实全部 11 个生成记录。页面整图随阅读栏等比缩放，保留高清原文件与准确的圈选边界。结构中的全部图片和图示可点击在当前页面放大，按 Esc 或右上角关闭按钮退出。

## 准备两仓并启动

项目迭代从故事目录发起一项任务。使用支持多仓库的 `codex.task` 时，Agent 自动核验所需仓库并管理各仓隔离工作区；用户仍使用原来的任务命令。候选引用、逐仓 Git 交付与项目发布的衔接见 [工作区流程](production/generation-workspaces.md)，当前启用状态见 [STATE.md](STATE.md)。

新发布使用 `story-review-desk:current`、`:previous`、`:base` 三个固定镜像标签；准确版本和恢复继续以发布包中的镜像 ID 为准。现有标签收敛与构建规则见 [镜像发布流程](production/generation-workspaces.md#审阅台镜像的固定名称)。

需要 Docker Compose、Python 3.9+ 和 FFmpeg／ffprobe。两个仓库放在同级目录；系统目录的提交必须与 [config/instance.json](config/instance.json) 一致，准确版本以该配置为准；最近正式发布依据见 [当前状态](STATE.md)。正式运行版本需同时核对镜像源码与实例挂载，不能只由配置文件推断。

完成本地集成后，以故事根目录为工作目录，核对同级系统版本。以下启动命令只适用于已有数据库且未使用独立发布挂载的普通实例；已有正式服务按 `STATE.md` 的发布入口恢复／重启。空实例须先按下方生产恢复入口完成恢复：

```bash
production_system=../story-review-desk
required_system=$(python3 -c 'import json; print(json.load(open("config/instance.json"))["review_desk_commit"])')
test "$(git -C "$production_system" rev-parse HEAD)" = "$required_system"
REVIEW_DESK_BUILD_CONTEXT="$production_system" docker compose up -d --build
```

已有运行数据库时跳过恢复，不能用快照覆盖活库。当前 Schema 9 完整导出及发布凭据只能通过 [生产恢复入口](production/README.md#恢复) 恢复到新的空实例；旧歌曲、旧编排与旧格式重放已经退役。迁移同时保留 `config/`、`content/`、`export/` 和准确恢复索引。正式服务使用对应冻结发布包，不能用普通构建覆盖准确挂载。

打开 [本机审阅台](http://127.0.0.1:3000/)：Nginx 长期运行在 Docker 容器 3000 端口并代理容器内 Python 服务；Nginx 镜像与通用代理规则由审阅台仓库维护，故事仓库只保留实例 Compose 配置。主机仅绑定 `127.0.0.1:3000`。`docker compose ps` 检查状态，`docker compose restart` 重启；`restart: unless-stopped` 保证 Docker 恢复时服务随之恢复。已有 `.runtime/review.sqlite3` 时跳过 `restore`。本机与公开克隆的系统目录名统一为 `story-review-desk`，同级放置时使用 Compose 默认构建路径；系统位于其他位置时设置 `REVIEW_DESK_BUILD_CONTEXT`。不要把 3000 端口转发到公网，本服务没有公网鉴权。

`OPENAI_API_KEY` 默认只在本机启动 Compose 的环境中提供，不提交到仓库；无密钥时其他审阅功能不受影响。系统配置“系统与 AI”可选择评论润色模型、推理强度，并设置润色 API Key 的环境变量名（只保存名称，绝不保存密钥值）。若使用自定义名称，必须用本机、不入库的 `compose.override.yaml` 将同名环境变量透传给 `app` 容器；改页面配置不会自动透传宿主机变量。若本机网络需要私有可信 CA，也可在该覆盖文件中只读挂载 CA 并设置容器 `SSL_CERT_FILE`，不可关闭 TLS 校验。新建或编辑评论有文字即可点 AI 润色，系统自动生成并核验草稿、圈选、故事/创作背景、创作阶段、原文上下文及各版本资料的参考快照；也可单独点击“查看润色参考”。建议必须手动采用、保存。

## 站点图标

“系统管理 → 系统与 AI”可上传、选择和替换图标；点“恢复默认图标”并保存可恢复书页图标。当前图标与待保存预览分开，上传成功只登记文件，保存配置后才应用。当前设计为屋檐护着灯火，源 SVG、ICO 和 PNG 在 `export/assets/`，16／32 像素深浅背景预览在[图标设计](design/favicon/README.md)。配置与当前源 SVG 随清单校验和空库恢复；Git 另保留派生文件与渲染脚本。图样已于 2026-09-30 获用户认可。设计交付见[原交付记录](planning/favicon-delivery.md)。

## Codex 读取与公开同步

本机源数据以 `.runtime/review.sqlite3` 为运行权威；公开仓库的 `export/` 是可恢复的快照。Codex 可从系统仓库运行以下命令读取评论及其原文关联：

```bash
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord comments
```

添加资料时准备 JSON 数组并运行 `import-sources /path/to/sources.json`；字段与 API 契约见[系统说明](https://github.com/goosmanlei/story-review-desk#数据访问与公开同步)。故事结构是“故事创作”下的子页：未选方向时提供初始方向选择；已有结构的阅读页保留版本、章节、图文圈选与浮动评论入口，移除方向回看／重选、顶部重复评论按钮和底部版本确认控件。Codex 通过 `structure-get`、`structure-review` 读取方向与意见，以 `structure-import complete.json --expected-version N` 导入完整图文稿；历史确认及 `script-input` 接口保留兼容，页面精简不自动创建确认。格式见[故事结构接口说明](https://github.com/goosmanlei/story-review-desk/blob/main/docs/story-structure.md)。每次资料、评论、配置或创作稿变化后，从系统仓库执行 `PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord export`。公开同步须按用户授权审阅全部变更后执行，例如：

```bash
git add config/instance.json compose.yaml content export imports
git commit -m "Sync story review data"
git push origin main
```

公开推送前须审阅评论内容；推送意味着评论也会公开。`export/` 含资料、素材、评论及事件、对象修订/依赖、公开配置及事件，运行凭据与 SQLite 本机库不入仓。评论已锚定稳定对象与精确修订，资料评论仍可用 `source_id` 访问；后续创作稿沿同一账本和导出/校验/同步/恢复协议，不能仅留在本地运行库。

验收记录见 [VERIFICATION.md](VERIFICATION.md)。
