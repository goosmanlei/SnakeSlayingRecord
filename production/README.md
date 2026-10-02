# 版本四制作准备

本目录保存《把灯带回家》从定稿剧本走向第一集生产的实际材料。用户已确认版本四为本任务终稿；主视觉为二维人物＋轻手绘背景，主画幅 16:9。原制作目标包括能够开始正式镜头生成的输入、素材和有声动态分镜。用户于 2026-10-02 确认按当前成果结项，后续修改另行发布任务。

当前已完成全剧抽取、第一集逐镜设计、通用系统最小实现和首批实际候选；基准补齐与接受、完整素材、动态分镜及工程转入后续任务，第一集尚未就绪。此处是成果与操作入口，任务执行及完成状态仍只由主项目任务账本管理。

## 阅读与审阅入口

| 要核对什么 | 实际材料 |
| --- | --- |
| 用户确认、剧本与结构依据 | [输入锁定](source-lock.json)，保留整版、17 个分集、42 场和 1,114 个正文块的准确版本 |
| 全剧身份、别名、状态与出场 | [可读清单](inventory.md)和[完整数据](inventory.json)：133 个实体、267 个完整状态，42 场均有检查记录 |
| 全剧直接关系与正文依据 | [关系清单](entity-relationships.md)及[准确批次](entity-relationships.json)：157 条关系、133 个实体检查 |
| 后续各集计划需求 | [集场需求](scene-requirements.md)，其余 40 场登记 566 项图像需求；不要求本任务生产后续集媒体 |
| 原生有声预演方式及执行边界 | [声音契约](native-audio-workflow.md)、[33 镜计划](episode01/seedance/manifest.json)，尚未执行 |
| 第一集动作、空间与声音 | [33 镜设计](episode01/shots.md)、[精确数据及 250 个镜头素材槽位](episode01/shots.json)、[37 个对白／演唱单元](episode01/dialogue-cues.json) |
| 实体完整描述与逐素材方案 | [制作方案](generation-preparation.md)及[只读准确快照](generation-preparation.json)：第一集 33 个实体的全部 77 个状态、122 项方案（94 图像、28 音色／旋律），含模型、参数、提示词、参考和用途；未执行新生成 |
| 现有候选属于哪个实体和状态 | [关联清单](baseline-associations.md)：6 个条目、5 个实体、6 个状态；含具体声音范围与依据 |
| 实际提示词、输入与调用结果 | [requests](requests/)、[receipts](receipts/)和[登记批次](baseline-records/)；均区分计划与实际制作 |
| 完整生产修订历史及文件清单 | [replay.json](replay.json)，包含 2,048 个生产对象、4,503 个修订、14 个实际文件组成；保留 86 个历史局部状态、此前命名复核及 133 份旧送审记录（仅历史追溯） |
| 系统设计、关系图及 API／CLI | 通用系统 [docs/production.md](https://github.com/goosmanlei/story-review-desk/blob/4c0cc62bcf4e5477a1fd2ff22b29ecce3ba44ac1/docs/production.md)，代码版本以本故事 [config/instance.json](../config/instance.json)为准；已集成并推送系统 `main`，实际运行入口为 3000 |
| 已执行验证与具体限制 | [verification.md](verification.md) |

本机统一审阅入口为 [制作设定](http://127.0.0.1:3000/?workspace=settings.workspace)、[素材管理](http://127.0.0.1:3000/?workspace=materials.workspace)、[全剧制作](http://127.0.0.1:3000/?workspace=production.workspace)。3000 由 Docker 与 Nginx 后台运行，不依赖代理会话。用户最终明确授权双仓集成、推送和正式切换；正式库已增量加入制作记录，原有剧本、配置和 264 条评论完整保留。`export/` 是包含制作数据、评论和原件的完整恢复快照。旧 39103 预览已停止，旧实例与技术测试库仅供追溯，不能继续作为制作和导出来源。

制作设定按实体浏览，筛选区平铺全部 133 个实体及角色 51、场景 16、道具 62、歌曲 4。列表每个实体只出现一次，并标出完整状态数；例如“阿蘅米袋 · 5 个完整状态”。打开实体即显示上方的身份、别名、基础说明和其他基础信息，下方平铺完整状态；默认选择按剧情来源排序的首个完整状态并标为“基础状态”，切换时上方信息保持显示。搜索别名、状态或设定描述也能找到所属实体。分类数量保留搜索条件后计算，不重复累计历史版本，零数量项仍可见；“清除筛选”同时清除搜索与分类。状态的旧链接、准确版本与评论保留，镜头引用仍打开当时指定的状态版本。

实体基础信息常驻，关系图优先展示主要关系，再列其他关系；节点不跳转，连线文字直接圈选评论，来源在页内弹窗打开，下方选择完整状态。描述后每份素材固定两列展示（阅读区不足 720 像素时单列），模型、参数、提示词和参考输入默认展开，参考在当前页弹窗打开准确版本，保留阅读位置与评论草稿。制作设定与素材管理使用同一素材卡，原生成信息读取准确实际调用；工具在执行时决定。可评论区域用统一轻边线和图标提示；待确认直接展开。版本只在相应内容旁切换，不另显示采纳时间、历史提示或返回当前按钮。真实音频使用波形播放器，可选段、精调、试听和评论，不显示人物封面；图像占位和缺音频条只对应明确列出的缺失素材。

“采纳”认可当前基础信息、直接关系、所有完整状态及逐素材生成方案，允许推进素材生成；采纳后变为“取消采纳”，评论始终开放。新候选不影响认可，内容、关系或方案变化需重新采纳；实际执行仍需准确采用前置原件并核对额度。现有 6 个素材保持明确状态归属，以新修订对应本轮需求；原件和实际调用不改写。旧送审记录仅保留历史，Codex 没有代替用户采纳。

独立逐句、演唱段及环境动作声的 337 项需求和 987 个修订已清理，实际原件与调用保留。全剧现有 32 项音频需求用于角色音色或歌曲旋律参考；台词、歌词与预计时间保存在镜头设计中。新声音方式见 [视听预演契约](native-audio-workflow.md)，不能把计划当作已生成预演。

“正式输入”不列入制作设定；267 个完整状态在所属实体内部展示，不计入实体数量。全剧制作顶部只显示“剧本依据：版本四 · 已确认 · 17 集”，没有确认说明入口；底层记录与历史引用保留。默认打开第一集 33 镜，切换分集和场次后可点击“检查本集／本场素材缺项”，每页最多显示 20 项。单镜详情显示该镜需求，进入页面不自动展开全剧缺项。这里的剧本确认不代表制作基准或第一集素材已被接受。

状态表示实体在某一时刻的完整形态。李寄的衣着、掌心包布和额角旧伤同时成立时，在一个状态内完整说明；阿蘅米袋从空袋、工米入袋、追加预付米到退米后扎袋、清账接退粮，共五种形态。阿禾和船家各有一个完整状态；普通走动、表情变化或素材候选换版不额外制造状态。

每次实际呈现或发声都绑定准确状态，同场、同镜的变化有先后顺序、动作和正文依据。全剧 618 次场内实体使用与第一集 206 次镜内使用均已检查，没有缺失或错属。小满、许家女儿仅被提及，保留已知事实状态，不要求生产媒体。

需要独立媒体的状态保留一项整体参考，再按需增加局部、角度或声音；当前共 260 项整体参考需求。仅需文字随镜发声的状态保留完整描述，不另要求录音。Codex 按审阅意见通过工具增加补充需求；素材管理可把同一文件组成关联多个准确状态，并说明整体或细节覆盖。新增关联保存为素材的新候选修订，实际调用和已有采用不改写。未选整体参考时，细节不能使状态就绪。当前首批候选已明确状态归属和审阅范围，质量缺口及未获用户接受的状态保留。

旧 86 个局部状态不计入当前完整状态数量，仍保留修订、来源、评论及实际制作引用。完整状态的对应与影响清单见 [迁移核对](evidence/complete-state-migration.json)；它仅供复核，不代表旧素材自动兼容或已经换版。技术验证见 [verification.md](verification.md)。

## 当前实际候选

下面列的是候选原件，不是已经接受的基准。精确修订、SHA-256、制作调用与歌词依据可在素材详情及重放清单核对。

| 素材 | 版本／原件 | 核查结果 |
| --- | --- | --- |
| 李寄造型 | `asset-liji-image` 版本 1、2 保存两张原图；版本 3 补充第二张的状态关联，当前版本 4 对应本轮准确状态和需求；[第一张](../export/assets/82a51fcd631931e43bc0ed5535a1c80827a072fb37dd9a2e8b366d5d13258458.png)、[第二张](../export/assets/cd50ecc53c05dd06c2f592adf164b12f2711ef44538479cd3b55a711590dae33.png) | 均为文字生成根候选，2016×2688，未达到原生 4K；已回看，尚未接受母版 |
| 阿蘅对白 | [17 秒 WAV](../export/assets/a041a61f5f37de8086eba7de160804c785587d1ae1ce024ef67246f846c69e84.wav) | 48 kHz、双声道、PCM 16-bit，待实际听审 |
| 李寄对白 | [12.38 秒 WAV](../export/assets/90227903269315a0fde6b66cdcb91698d0c7737c2e1f6dddf593e6fe7fc8f014.wav) | 同上，待实际听审 |
| 周掌柜对白 | [17 秒 WAV](../export/assets/d242aeb9c0b0069f18a252f62a6a2aedc4625522033aa92c5a5ab03f8da1f76f.wav) | 同上，待实际听审 |
| 赵执事对白 | [11.5 秒 WAV](../export/assets/842ecea98a028fa105e0f30a4f5a6085d412d3c40aecf24516f5a7a10b19ab92.wav) | 同上，待实际听审 |
| 阿蘅舟行曲 | [17.0534 秒 WAV](../export/assets/9edcf64a1d34914d1d406a01aff9617f3759eb51ed699e1380fde6f96993c953.wav) | 实际引用上述阿蘅对白作为声线参考；原歌词未另写，录音是否准确仍需听辨 |

OpenArt CLI 0.1.1 没有暴露所需质量及分辨率参数，两次实际改由 OpenArt 连接器提交明确项目 `8K6WcbrPLghSBJXBtWAE`、GPT Image 2.5、high、4K。第二次还指定 3072×4096，原件仍为 2016×2688。两次共用 500 Credit，最后回读 9,979；没有重复提交相同失败设置。保持 4K、接受该模型实际尺寸或改用其他模型的取舍仍待用户决定，不能将这两张候选标记达标。

豆包音频使用 `seed-audio-1.0`。控制台核对时剩余免费量 45.06 分钟（2,703.6 秒），五次调用共计费 74.9334 秒。该观察值减去本任务调用得到 2,628.6666 秒的本任务保守余量，不代表账户其他会话未发生消费；下次付费制作前应重新核对。模型在当前会话不能直接听辨音频，字幕核查和播放器计时推进均不能代替实际听审。没有充值或新增购买。

首轮基准审阅还缺其他必要人物、代表背景与道具等视觉材料，以及实际声线／演唱听辨。完整基准获得用户对确切版本的认可后才批量派生。24 fps、1080p 动态分镜及 48 kHz 声音是待审制作规格；227 秒是镜头设计估时，不是成片实测。

## 隔离恢复与运行

以下日常命令以故事主项目根目录为工作目录，正式业务库为 `.runtime/review.sqlite3`。通用系统本机目录为同级 `story-review-desk-python`；新克隆可按根 [README](../README.md#准备两仓并启动)恢复，使用 `config/instance.json` 固定的提交。不要新建任务账本、复制凭据或用旧导出覆盖已有运行库。

日常审阅由 `snakeslayingrecord-app-1` 与 `snakeslayingrecord-nginx-1` 提供，仅监听 `127.0.0.1:3000`，采用 `unless-stopped` 重启策略。正式容器使用主项目根目录；凭据和可信 CA 沿用本机已有配置。查看与重启：

```bash
docker compose ps
docker compose restart
docker logs --tail 40 snakeslayingrecord-app-1
```

重建时沿用本机现有凭据与 CA 配置，系统构建路径用 `REVIEW_DESK_BUILD_CONTEXT=../story-review-desk-python`。不要为页面打不开而重新恢复或覆盖数据库。当前镜像为 `story-review-desk:task-20260929-0003-reference-popup`，40 个系统文件与固定提交一致。旧 `snakeslayingrecord-production-task-0003` 容器保持停止；切换时移除已停止的 3000 旧容器，保留镜像和全部挂载数据，避免 Compose 误启动多个正式库写入者。新任务只操作正式库。

以下为空实例恢复，不启动或修改正式服务。Python、FFmpeg／ffprobe 与固定版本通用系统需先可用；最后一条为前台临时验证服务，核对后关闭：

```bash
production_system=../story-review-desk-python
python3 scripts/production_review.py --system "$production_system" recover \
  --destination .runtime/production/fresh-review
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance .runtime/production/fresh-review serve --port 39105
```

目标必须是当前检出目录 `.runtime/` 内尚不存在的目录。当前 `export/` 是完整交付快照，包含故事与制作记录、264 条评论及 293 条事件，清单校验 71 个文件；两条明确标为“隔离验证”的素材意见仅留在本机原库与备份，不计入交付数据。工具核对导出摘要和 14 个生产文件组成，恢复完整库后比较全部生产修订与当前版本，不重复导入已有生产数据。兼容旧的纯故事导出时，才通过共用业务操作重放生产修订；已有生产数据与快照不一致则报错。不会覆盖已有数据库，失败目标保留供检查，换新的空目录重试。

后续任务使用现有正式库，不重新恢复。查看实际缺项：

```bash
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance . production-ready shot-e01-001
```

当前实际制作实例没有正式素材采用，第一集 250 项镜头用途与 67 项状态素材需求（含 40 项整体参考），合计 317 项必要输入均未就绪。`production-package ID --output directory` 只有在必要输入满足时才复制精确文件目录；页面下载的是同一清单。当前不把缺项清单冒充可执行生成包。

继续整理时，`scripts/episode01_shots.py` 与 `scripts/scene_requirements.py` 接受 `--system`、`--instance`，默认只比较并校验，显式 `--import-records` 才写入变化。`production/inventory.json` 是抽取的当前编写数据，历史恢复必须使用 `replay.json`，不能重复按初始版本导入或用编写数据覆盖真实审阅。`scripts/register_production_candidates.py` 用于本轮真实调用首次登记，不应对已有对象重复执行。

新调用音频前，用 `python3 scripts/seed_audio.py production/requests/aheng-song-01.json` 这类具体单个请求文件检查参数；默认只输出预览，不提交。`--submit --quota <最新额度记录>` 才调用服务；使用已有 `VOLCENGINE_SPEECH_API_KEY` 环境变量。未知结果按最长 120 秒保留额度，不自动重复调用。新增请求应使用新 ID，保留旧回执及原件。

后续任务整理完成后，先从真实制作实例一致性备份导出完整 `export/`，再执行 `production_review.py ... snapshot --instance ...` 保存与该导出匹配的精确重放；不要从操作测试实例保存。正式发布前仍须读取最新正式数据与代码，合并候选后复验，不以本次启动快照覆盖用户新增评论。

## 直接审阅与后续修订

内容由 AI 通过共用业务接口新增修订，用户打开实体即可审阅。读取整份实体内容：

```bash
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance . \
  production-entity-review entity-li-ji
```

HTTP 对应 `/api/production/entity-review?entity_id=entity-li-ji`，查询不写数据库。读取过去采纳的准确内容时，CLI 追加 `--revision 采纳判断的修订`，HTTP 追加 `revision_id`。无需执行初始化或准备送审；原初始化脚本已退役，历史批次 `entity-review-submissions.json` 只供追溯，不重复导入。

Codex 读取意见后，通过 `production-import` 新建相应 ENTITY、STATE 或 ASSET 修订，带上 `expected_version` 及必要的 `expected_heads`，不得覆盖原稿与历史锚点。用户点击“采纳”才记录基础信息、关系、全部完整状态及生成方案的范围，Codex 不代替用户操作；新评论不改变已有采纳。详细字段、并发和恢复契约见系统 `docs/production.md`。

## 状态与生成方案维护

`production_forms.py` 和 `production_inventory.py` 保存抽取规则；初始完整状态迁移已完成，不重复运行初始批次覆盖当前制作描述。今后按用户评论修改准确当前版本，生成方案维护使用 [本轮操作说明](generation-preparation.md#维护与恢复)中的预演、增量应用与重新快照流程。

以下路径均相对于保留的任务工作区 `.codex-project/worktrees/task-20260929-0003`。本轮生产重放恢复在 `.runtime/production/review-simplification/replayed`：2,048 个生产对象、4,503 个修订、14 个文件组成和基础故事 264 条评论。完整库恢复在同目录 `task-restored`：2,171 个对象、4,635 个修订、266 条评论、295 条评论事件，8 张表一致、71 个清单文件通过；关系显示配置也由清单恢复。`technical` 中的测试意见和取消采纳不属于真实制作决定，不导入任务库。最新恢复证据见 [验证说明](verification.md)。

正式发布前的最新正式库备份在 `.runtime/production/closeout/formal-before-publication.sqlite3`，发布后完整复导出在同目录 `formal-export/`；8 张表与交付恢复实例一致，全部旧行保持。发布时临时只读挂载候选 `config/`、`content/`、`export/` 供正式回读，受控集成前撤掉这些挂载，最终仅使用主项目根目录。

数据迁移前任务快照在 `.runtime/production/review-simplification/before`。最新剧情依据弹窗修复没有数据迁移；更新前容器为 `snakeslayingrecord-production-task-0003-before-reference-popup`。它与更早的 `-before-simplification`、`-before-materials`、`-before-region-scale` 等旧容器保持停止；旧版与当前容器共享数据库路径，不能同时启动，也不能直接用快照覆盖用户后来新增的数据。需要回滚时先停服务并重新导出最新库，核对代码对新增关系契约的兼容性；数据回退须逐项设计增量，不把旧快照作为恢复活库的捷径。

## 下一次制作交接

先解决图像实际尺寸与要求的冲突，补齐首轮代表基准并完成实际听审。基准获认可后，按 33 镜需求生产和选用图像、音色与旋律参考，核对 Seedance 2.0 执行平台和现有额度。对白、演唱与环境动作声随画面生成有声视听预演，再剪辑为 16:9 动态分镜，保存逐镜实际输入与可编辑工程。第二轮审阅意见处理后，再在空实例打开工程、播放完整动态分镜并核对全部依赖。以上未完成制作工作由用户另行发布任务。本任务仅按当前成果结项；用户已明确授权双仓主干集成、推送及 3000 切换，后续任务从正式库与新主干继续。任务完成、技术验证、正式发布和作品接受分别记录。
