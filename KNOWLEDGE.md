# 项目稳定知识

本页是稳定约定和按工作查阅的入口。当前成果与缺口见 [STATE.md](STATE.md)，协作与交付规则见 [AGENTS.md](AGENTS.md)。具体操作、业务契约和验收只在所链接的正文维护；无需为无关任务展开全部链接。任务授权、完成与运行身份以主项目 `.codex-task/tasks.json` 和准确回执为准，历史报告不能当作现状。

## 项目与权威入口

- 作品以《搜神记·李寄斩蛇》为原型，扩写方向三《把灯带回家》，最终载体为漫剧。资料、结构、小说、剧本和制作逐步迭代，用户通过审阅台阅读、评论与判断。已确认输入见下节。
- 本仓为 `goosmanlei/SnakeSlayingRecord`；通用 Python 审阅台为 `goosmanlei/story-review-desk`，真实源目录在主项目同级 `../story-review-desk`，交付目标均为 `main`。`config/instance.json.review_desk_commit` 固定实例所需系统提交。历史 `story-review-desk-python` 路径已改名，恢复旧包时核验当前 Git 身份并显式指定系统目录，不改冻结包。
- 任务数据统一在主项目 `.codex-task/`。历史 `.codex-project/` 路径按当前目录和原任务身份核对；不另建账本。定义／发布沿 [项目任务 SKILL](skills/task-definition-publish/SKILL.md)，执行沿本次启动指令；多仓、发布和恢复沿 [工作区流程](production/generation-workspaces.md)。方法不注册为系统工作类型。
- 全局侧栏下方提供故事实例与通用系统的GitHub入口，在新标签打开；公开仓库地址沿实例 `config/instance.json` 的 `repository`／`review_desk_repository`，其他实例不默认指向本故事。缺失、非法配置及窄屏交互沿系统仓 `docs/interface.md`，实例交付见[源码入口记录](production/reports/task-20261020-0005/README.md)。
- 本机正式入口为 `http://127.0.0.1:3000/`，Docker 中的 Nginx 代理 Python 服务；正式 SQLite 为主目录 `.runtime/review.sqlite3`。凭据与运行库不公开。通用展示与数据管理归系统仓，故事创作工具归本仓。
- 《九头案》仅作已确认范围内的框架和交互参考，不继承业务设定或数据。历史入口 `../2026.08.06.九头案/review-software` 使用前核可用性，不与当前通用系统混淆。

## 作品输入与创作

- 当前故事依据为结构第十稿 `imports/story-structure-01.json`、精修九《把灯带回家》`imports/story-refinement-09.json`；用户已确认剧本版本四为制作终稿。准确剧本修订由 [制作输入锁](production/source-lock.json) 固定：17 集、42 场、1,114 个正文块。最新指针或代码更新不能替换作品输入锁；单集 3—5 分钟是规划，不是成片实测。
- 核心设计：阿蘅是第三个将被献祭的孩子，前年阿禾、去年小满遇害；李诞、孙六与阿蘅已故父亲为深交，李寄与阿蘅如姐妹。李寄早期有无意识的冲动和处境盲点；保留成人求援、隔离确认、可停手与艰难斩蛇。蛇受洞穴、封闭短石道约束，平日两端门闸交替开启喂食；乡亲共同压闸，结尾惩奸、庆功饭、补歌本、提灯归家。旧寻路、远行和多处追逐救援不再是当前设计。依据为上述已确认结构与小说。
- 采用现代白话和清楚因果；方向稿须有不同主题、人物与情节，保留李寄主动应募、斩蛇止祸。早期每方向 20—30 分钟不限制小说篇幅。小说先交完整结构，再逐段逐章创作、保存、回读和采用，结构与正文同步回修；剧本逐场编制可见可闻动作和表演，不为每句台词机械配动作。
- 创作入口：[小说方案](planning/novel-creation-plan.md)、[逐步写作](planning/incremental-writing-workflow.md)、[剧本四审校](planning/screenplay-04-review.md)。工具为 `scripts/novel_writing.py`、`scripts/screenplay_writing.py`、`scripts/publish_screenplay.py`。小说普通新稿保留旧版本和评论，历史精修一／七的原位修改是单次授权；普通导入不能据此覆盖旧稿。系统替换条件见系统仓 `docs/source-replacement.md`。
- 独立首次阅读只取得当前位置以前的原文和读者自身判断；不继承作者、未来文本或旧意见。无父会话不保证无自动记忆，须核实际输入；回看不能越过阅读位置。操作、费用和验证沿 [读者审阅](planning/reader-review-workflow.md)。

## 方法与制作模型

- “制作思路”依次包含系统构想、数据模型、基础流程、故事创作、生产制作。唯一正文分别为 [系统构想](production/system-vision.md)、`content/data-model.json`、`content/skill-flow.json` 和 `content/production-approach.json`。系统构想以人与 AI 协作、数据模型和基础流程支撑的两层图表达；其他两张创作工作图由 JSON 派生，不另建同内容 Markdown。
- 方法的唯一正文、共用资料、准确版本、条件、绑定、执行快照及兼容恢复沿 [受管方法](production/managed-methods.md)；按创作职责选取资料和阶段，详见 [创作制作方法](production/professional-methods.md)。结构／小说无影视视频固定依赖。方法文件、只读来源和过去执行不能被新稿静默改写；条件编辑保留 JSON 类型、顺序及准确引用，非法或重复字段整次拒绝。
- 项目 Review 源在 [creative-system-review](skills/creative-system-review/SKILL.md) 及适配，系统按准确只读投影使用。持续 Review 的运行状态仅在主项目 `.runtime/system-review/` 和本次用户授权中确定；加载方法不恢复旧循环、时限或已撤销任务。
- 影视判断查 [filmcraft](production/filmcraft/README.md) 的相关章和 [速查](production/filmcraft/quick-reference.md)；视频方法唯一正文为 [视频生成手册](production/seedance-video-handbook.md)。模型能力、制作选择和真实结果分开，不能以手册或方案估时改写已采用素材。
- 故事版本保留历史；制作实体、状态、关系、集场镜和需求维护稳定身份与一份当前稿，更新校验并发标记。每次真实生成保存准确提交快照，候选按真实调用归组，回调、补文件和下载重试不新建候选；失败且无原件不算结果。六类方法阶段全文留有恢复用途的本机原值，服务保存摘要及执行事实。契约见 [当前制作与候选](production/current-candidates/README.md)、[阶段回读](production/method-stage-recovery/VERIFICATION.md)。
- 2026-10-15 经用户明确授权清空本机全部旧制作层后从锁定剧本重建；旧实体、需求、镜头、方案全文和候选不能从 Git、云端、VPS 或旧库恢复为新制作输入。故事、方法、原评论摘录及调用／费用保留。例外范围与最小事实见 [制作层重置](production/full-production-reset/README.md)。之后六类编号从001起号的单次迁移沿 [编号迁移](production/numbering-restart/README.md)，不改变日常删除不复用编号的规则。

### 按制作问题查阅

| 问题 | 有效约定与准确入口 |
| --- | --- |
| 集、场、镜与作品来源 | 视听集遵循已确认故事集边界；场可在同集内组合原场范围；镜头沿统一 `AV_SHOT`／ASH 身份，不另建影子实体。逐场源、原词区间及镜内顺序见 [视听编制](production/audiovisual/README.md)、[本轮重建](production/rebuild/README.md) 和 `scripts/scene_reading.py` |
| 实体／状态／素材归属 | 身份、音色、完整歌曲、空间与道具基础职责直接归实体，不另建基础状态。独立状态须有独占制作需求，描述同一时刻完整形态；动作、转手、知情和入画不自动建状态或改变唯一出处。沿 [唯一制作出处](production/unique-origin/README.md)、[状态正文](production/state-description/README.md)、[抽取](production/extraction/README.md) |
| 分类与方案 | 需求只有一个 `material_category`：图像四类、声音三类、视频、字层；动物不套人物衣饰，确定性制作不补造模型调用。格式、必备与条件要素须进入真正提交的 Prompt／指令。全剧方案与下游领取沿 [素材方案](production/material-plans/README.md)，分类契约沿 [素材分类](production/material-categories/VERIFICATION.md) |
| 关系与依赖 | 同一对稳定对象维护一条当前关系，阶段差异合并到连贯正文。业务关联、方案直接输入、已选路线和候选真实提交分别表达；仅选中路线参与执行依赖与循环校验。见 [统一关系](production/unified-relations/README.md)、[参考合理性](production/material-reference-rationality/README.md) |
| 准确原件与选择 | 输入固定真实候选和完整原件组成，浏览或第一份结果不代表选择、认可或采用。当前取消只清对应输入选择；新候选不漂移旧提交。已有合格原件按准确身份和用途复用，不因同需求编号误判循环。见 [参考选择](production/reference-selection/VERIFICATION.md)、[完整原件与取消](production/reference-card-compact/VERIFICATION.md) |
| 视频起点与跨镜连续性 | 起点容纳首个必要动作；区分计划落点、实际候选末态与工程出点，身份／空间／动作／声音参考各有职责。方法唯一正文见 [视频生成手册](production/seedance-video-handbook.md)，专业原则见 [剪辑](production/filmcraft/10-editing.md)。检查覆盖与冻结依据沿既有方法产物记录；换候选、顺序、切点或声音后定向复核，依据仍适用不等于质量自动通过。实际全剧与首集应用见 [跨镜Review](production/reports/task-20261020-0010/README.md) |
| 可读字层与声音 | 字层先定准确字稿和显露阶段，同页进度优先复用可编辑源；静图正确不等于运动可读。人物音色按统一中性稿比较，角色实际表演另验；完整歌曲、哼唱、省段和短参考各自判断。具体方法在当前准确方法包，曲目交接见 [歌曲](production/songs-review.md) |
| 集级剪辑与成片 | 每集一个可编辑工程、多个不可变成片，片段入出点与时间线位置分开，准确原件不覆盖。唯一方法正文为 `content/episode-editing-method.json`，通用工程／worker／页面契约见系统仓 `docs/episode-editing.md`。页面仅播放和评论，工程编辑留后台；准确素材开现有大卡，跨轨评论固定不可变成片与追加关联。真实字层登记及使用关系见 [片段审阅](production/reports/task-20261019-0002/README.md)，首集剪辑和感官边界见 [成片交付](production/reports/task-20261019-0001/README.md) |

## 生成工具与规格

- 图像优先 OpenArt CLI，固定项目“李寄斩蛇 · 把灯带回家”，ID 取 `config/openart.json`；CLI 显式 `--project`，连接器显式 `projectId`。CLI 无法满足时说明具体原因和实际替代渠道。核实际像素，保存未经放大的原件，不把请求档位当像素或改写旧图规格。
- 画面为二维人物＋轻手绘背景、16:9。原要求为原生4K；全剧首轮经用户允许采用指定模型实际最高原生尺寸，例外不自动改其他任务规格。历史 OpenArt GPT IMG 2.5、Codex 内置图像的能力与额度只能作旧证据，执行时按本次要求与当前模型调用策略核验，不能把文件 ID 当调用 ID。首轮依据见 `production/full-generation/README.md`。
- 本轮 Nano Banana 2.1 按4K、16:9请求实际返回5504×3072，用户在task-20261015-0003采纳保留原生尺寸的建议：约0.8%的比例偏差用于身份／状态参考，记录实际尺寸，不为此裁切、缩放或重复生成，成片镜头仍按16:9。该例外不豁免原生长边至少3840像素及逐图质量检查，也不自动放行其他尺寸。依据见[本轮制作检查点](production/reports/task-20261015-0003/README.md)及其中准确原件回执。
- Higgsfield OpenAPI与网页／MCP套餐分别核对。本轮实际调用的Flare入口为`marketing-studio/image/flare`，4K、16:9返回原生3840×2160 PNG，整图参考已用准确新PNG验证；上传前后核对候选、修订及哈希。该接口契约最多16张有序图片且关闭自动改写提示词；0003验证单图，0004又以5张、3张有序完整参考分别生成4K起点图，实际输入、谱系和输出见[第一集候选](production/reports/task-20261015-0004/README.md)。这些结果不能外推到未实测的数量或其他模型。用户已更正该OpenAPI并无Nano Banana；后续重查接口、余额及自动充值条件，不改变默认渠道顺序。证据见[制作检查点](production/reports/task-20261015-0003/README.md)。
- 以干净母版参考，图生图优先一代修正、累计最多两代；多参考按最深谱系计，加入母版、改名或重新选中不重置。仍不达标回到干净母版重做。局部修改固定轮廓、配色、线条；每轮对照人物比例、背景笔触和纹理，避免纸纹、脏噪点、过锐边缘与细节堆积。
- 河街为可涉水浅滩、低缓岸坡，下游石缝暗水只属局部；横杠保留已认可短石道本体、封顶短段和岩根，长杠高于石盖且两端留成人下压空间。历史母版认可只绑定原件，不转授新结果或镜头。准确旧意见在 `production/full-generation/` 的 river／crossbeam 等反馈文件；新制作不得取回已删旧原件作为输入。
- 音色优先豆包 `seed-audio-1.0`。`scripts/seed_audio.py` 默认预览，显式 `--submit` 才调用；未知请求保留预留额度，先查结果再恢复。当前角色和固定试读稿沿准确方案／人物音色 SKILL，不能套用旧40＋2批次或旧认可。既有合法声音的复用判断见 [音色复用](production/voice-reuse/README.md)。
- 视频通过 `pippit-tool-cli`，默认 Seedance 2.0 Fast（`seedance2.0_fast_vision`）、720p；长镜可采用 Seedance 2.5（`Seedance_2.5`）、720p。执行前重查标识、时长、参考支持和额度；对白、歌声、环境和动作声按方案各负其责，不靠漏词／提速凑时长。角色音色、整曲母版和短参考分别保存。
- 歌曲先创作为可独立聆听的完整词曲与演唱作品，全剧省段、缺词、哼调、重唱及角色演法从准确原曲派生，数量以故事需要为准，不严卡四首。沿用《三道滩》《送青篷》《四邻安》《明月还乡》；本轮以锁定剧本唱句重新创作完整词稿，不恢复已清除的旧制作文本或录音。新词曲标为原创制作选择，保留剧本唱句与揭示顺序；独立歌手不自动代表角色演法。入口见[完整歌曲创作稿](production/rebuild/songs/README.md)，正式生效核发布回执，旧一次性调用授权不继承。依据为用户在task-20261015-0003中的数量及完整原曲要求。
- 歌曲须读完整场次：E01/s002 b019“两段”指迎蛇调，E03/s005 b014是抄写、实际哼唱在b017；E04/s007 b006未定母亲曲目，选《送青篷》是制作选择；扩写位置E17/s041 b009的实际同步沿歌曲交接核对。
- `scripts/lyria_music.py` 默认离线预览，真实调用须 `--submit --max-cost-usd`。WAV请求曾实际返回MP3；用户在task-20261015-0003明确允许本轮全部完整歌曲采用平台原生MP3，保留真实编码，不转码冒称无损。该决定不更改Seed音色WAV规格，也不等于歌曲听审通过；返回歌词或转写不代替可靠实听。代理、认证及恢复见 [Lyria操作](production/lyria-music.md)。Higgsfield 已有标准凭据名为 `HF_CREDENTIAL`／`HF_KEY`，仅说明配置来源，不据此推断鉴权、余额或调用成功。

## 审阅与系统开发入口

前台承担阅读、评论、明确采纳和准确选择，后台承担编制、导入、登记与生成；内部日志不进入创作正文。当前主导航为制作思路、故事创作、生产制作、系统管理。生产制作含视听、实体、素材和成片剪辑四页，沿用共用平铺筛选与配色，故事剧本保留准确来源回查。

| 修改对象 | 先核对的契约与实例证据 |
| --- | --- |
| 实体、镜头、素材卡与阅读定位 | 系统仓 `docs/materials-and-relationships.md`、`docs/material-versions.md`、`docs/production-breakdown.md`；[镜头实体工作区](production/entity-shot-workspace/VERIFICATION.md)、[来源素材列表](production/material-source-list/VERIFICATION.md)、[大卡加载](production/stable-material-dialog/VERIFICATION.md)、[连续审阅](production/continuous-workspace/VERIFICATION.md)、[入口默认候选](production/reports/task-20261020-0002/README.md)。普通新进入默认最新候选，已选参考与明确目标优先，卡内往返保留阅读选择。共用容器、准确当前方案／候选快照、草稿和返回上下文不能因迟到响应串对象 |
| 范围、查找和关系图 | 系统仓 `docs/small-cards.md`；[素材范围](production/material-scope-filter/VERIFICATION.md)、[素材分组](production/material-media-groups/VERIFICATION.md)、[镜头聚焦](production/entity-graph-focus/VERIFICATION.md)、[关系交互](production/relation-interaction/VERIFICATION.md)、[曲线路由](production/graph-smooth-routing/VERIFICATION.md)。唯一需求计数，使用关系不增归属；真实有向／无向、循环、孤立节点分别表达 |
| 参考、历史方案和原件 | [候选预览](production/reference-candidate-picker/VERIFICATION.md)、[完整原件规则](production/reference-card-compact/VERIFICATION.md)、[冻结用途](production/frozen-material-relations/VERIFICATION.md)、[历史方案](production/historical-production-definition/VERIFICATION.md)。当前稿、候选当时提交、原件选择与人工判断各有归属，缺项不替换最新版 |
| 评论、润色和历史反馈 | 系统仓 `docs/comment-checklist.md`；[评论流程](production/comment-review/README.md)、[参考上下文](production/review-context/VERIFICATION.md)、[准确原件定位](production/material-comment-location/VERIFICATION.md)、[并行草稿](production/comment-drafts/VERIFICATION.md)、[整稿回应](production/response-full-graphics/VERIFICATION.md)。RV/DC逐项审批已退出，原话、作者、原时间、准确修订和范围继续保存；关闭不等于采纳 |
| 剧情依据、阅读和版本返回 | 系统仓 `docs/interface.md`；[剧情选段](production/source-excerpt-context/VERIFICATION.md)、[长章历史](production/history-reading/VERIFICATION.md)、[方法连续阅读](production/method-reading-application/VERIFICATION.md)、[旧意见回查](production/method-history-followup/VERIFICATION.md)。明确原文省略、准确返回、同URL各次访问和未保存草稿，缺失锚点不猜目标 |
| 页面或接口性能 | 系统仓 `docs/production-performance.md`；[四页与大卡性能证据](production/reports/task-20261020-0003/README.md)、[切集切场](production/av-switch-performance/VERIFICATION.md)、[素材检索](production/material-search-performance/VERIFICATION.md)、[切页迟到保护](production/navigation-consistency/VERIFICATION.md)。独立 `.runtime/read-cache.sqlite3` 可重建，纯目录与评论依赖按事务代号区分，保留DELETE日志模式；原件校验结论不进入纯结构缓存。接口计时不等于页面、图片或声音就绪 |

评论总数含已关闭、不含删除和编辑历史；⌘+Enter提交／保存，普通Enter换行，输入框内Esc放弃当前修改、外部Esc收面板保留草稿，中文组合输入不触发快捷键。历史意见复核沿原评论、结构回应和作者证据，不保存第二套评论状态；未登记不等于未修改，执行者检查不代替用户判断。

## 数据权威、发布与恢复

- 正式库是运行权威，`export/` 是受管快照。Schema 16以准确 OSS SQLite 快照和轻量资源目录保存完整业务表，在故事与方法历史、制作当前稿、候选准确提交、评论及必要发布事实之外，保存集级工程、不可变渲染快照、成片和准确来源；私有渲染队列及进程状态不导出。旧 Schema 14／15完整本地包仍兼容。旧制作全文链和专属版本索引不进入常规恢复。恢复只能到新空实例，沿 `scripts/production_review.py recover`、`production/audiovisual/index.json`、`production/audiovisual/recovery.json` 和完整 `export/manifest.json`。
- 正式写入须按 [工作区流程](production/generation-workspaces.md#合并与正式发布) 的实际锁、容器身份和停服顺序执行，不能只依赖宿主与 Docker Desktop 之间的SQLite文件锁。发布幂等记录与其他任务新评论必须保全，旧基线拒绝重放；完整导出从发布后最新正式数据产生。
- 当前 Git 只保存代码、业务文字和轻量准确目录；业务原件、派生与大包在私有 OSS，读取绑定明确 VersionId、SHA256、大小和 MIME。新 clone 不依赖媒体 LFS pull；历史 Git/LFS 未重写。原件缓存、项目级凭据、线上／离线恢复和旧归档兼容统一见 [资源存储](production/resource-storage.md)。
- 正式镜像仅用 `story-review-desk:current`、`:previous`、`:base`，Compose和候选固定准确ID；任务可建可识别临时镜像。镜像/容器的清理、挂载守卫与历史路径处理见 [结项清理](production/generation-workspaces.md#结项清理)。清单记录构建来源不要求原工作区永存；服务回退不等于数据回退。
- VPS是独立可写完整体验版，代码／存储升级保留其自己的业务库、发布身份与新增修改；普通重启保留操作，不回写本机。只有用户明确允许替换远端体验数据及独立修改时，才沿 `oss_snapshot_release.py` 的独立完整恢复、维护切换和阶段恢复流程同步本机完整快照；不绕过旧全量入口的 OSS 保护。部署控制目录 `~/lijizhanshe/`，体验实例 `~/www/lijizhanshe/`；共用调用计数跨发布保留，每天按北京时间最多100次。公网、代理、HTTPS、密钥及重置边界见 [体验部署约定](planning/vps-experience-deployment-task.md)、[部署操作](production/vps-experience.md)。入口为 `https://leiguoguo.me/lijizhanshe/`，当前版本取远端 `state.json`，不从本机Git推定。
- 站点图标为用户认可的屋檐护灯，源文件和维护见 [图标设计](design/favicon/README.md)。上传、配置、实际生效分别核验。
