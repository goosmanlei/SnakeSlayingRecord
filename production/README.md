# 版本四制作准备

本目录保存《把灯带回家》从定稿剧本走向第一集生产的实际材料。用户已确认版本四为本任务终稿；主视觉为二维人物＋轻手绘背景，主画幅 16:9。交付终点是能够开始正式镜头生成的输入、素材和有声动态分镜，正式镜头视频及最终成片由后续任务完成。

当前已完成全剧抽取、第一集逐镜设计、通用系统最小实现和首批实际候选；两轮创作审阅、完整素材、动态分镜及工程仍未完成。此处是成果与操作入口，任务执行及完成状态仍只由主项目任务账本管理。

## 阅读与审阅入口

| 要核对什么 | 实际材料 |
| --- | --- |
| 用户确认、剧本与结构依据 | [输入锁定](source-lock.json)，保留整版、17 个分集、42 场和 1,114 个正文块的准确版本 |
| 全剧身份、别名、状态与出场 | [可读清单](inventory.md)和[完整数据](inventory.json)：133 个实体、267 个完整状态，42 场均有检查记录 |
| 后续各集计划需求 | [集场需求](scene-requirements.md)，其余 40 场登记 786 项；不要求本任务生产后续集媒体 |
| 第一集动作、空间与声音 | [33 镜设计](episode01/shots.md)、[精确数据及 320 个必要槽位](episode01/shots.json)、[37 个对白／演唱单元](episode01/dialogue-cues.json) |
| 实际提示词、输入与调用结果 | [requests](requests/)、[receipts](receipts/)和[登记批次](baseline-records/)；均区分计划与实际制作 |
| 完整生产修订历史及文件清单 | [replay.json](replay.json)，包含 2,139 个生产对象、3,482 个修订、14 个实际文件组成；保留 86 个历史局部状态、此前命名复核及 133 份旧送审记录（仅历史追溯） |
| 系统设计、关系图及 API／CLI | 本任务独立通用系统工作区的 [docs/production.md](../.runtime/review-desk-worktree/docs/production.md)，代码版本以本故事 [config/instance.json](../config/instance.json)为准；未集成到正式系统 |
| 已执行验证与具体限制 | [verification.md](verification.md) |

本机隔离审阅入口为 [制作设定](http://127.0.0.1:39103/?workspace=settings.workspace)、[素材管理](http://127.0.0.1:39103/?workspace=materials.workspace)、[全剧制作](http://127.0.0.1:39103/?workspace=production.workspace)。39103 由独立 Docker 后台容器运行，不依赖代理会话；需要本机 Docker 保持运行。正式 3000 服务、正式数据库和导出未被替换。39104 是操作测试曾使用的端口，当前未启动；其恢复实例中的技术审阅和采用不属于真实制作决定，不应作为交付数据导出。

制作设定按实体浏览，筛选区平铺全部 133 个实体及角色 51、场景 16、道具 62、歌曲 4。列表每个实体只出现一次，并标出完整状态数；例如“阿蘅米袋 · 5 个完整状态”。打开实体即显示上方的身份、别名、基础说明和其他基础信息，下方平铺状态及制作设定；默认选择按剧情来源排序的首个完整状态并标为“基础状态”，切换时上方信息保持显示。搜索别名、状态或设定描述也能找到所属实体。分类数量保留搜索条件后计算，不重复累计历史版本，零数量项仍可见；“清除筛选”同时清除搜索与分类。状态的旧链接、准确版本与评论保留，镜头引用仍打开当时指定的状态版本。

实体卡常驻基础信息，下方平铺完整状态并默认基础状态；关联参考素材和完整描述并列展示。用户直接评论 AI 的当前产出，Codex 根据准确版本的意见修订，保存后即可继续审阅，无送审步骤。页面没有内容修改入口。

“采纳当前版本”可选，覆盖当前基础信息、全部完整状态和关联素材；采纳后仍可评论。新内容不继承旧采纳，历史意见与采纳保留。李寄、阿蘅等已有图像／声音候选直接显示；尚未核对具体完整状态的素材标为实体参考，不算满足状态要求。此前 133 份旧送审记录仅保留历史，不显示于状态选项或实体筛选，不再生成新记录。本次没有代替用户采纳真实内容。

“正式输入”不列入制作设定；267 个完整状态在所属实体内部展示，不计入实体数量。全剧制作顶部只显示“剧本依据：版本四 · 已确认 · 17 集”，没有确认说明入口；底层记录与历史引用保留。默认打开第一集 33 镜，切换分集和场次后可点击“检查本集／本场素材缺项”，每页最多显示 20 项。单镜详情显示该镜需求，进入页面不自动展开全剧缺项。这里的剧本确认不代表制作基准或第一集素材已被接受。

状态表示实体在某一时刻的完整形态。李寄的衣着、掌心包布和额角旧伤同时成立时，在一个状态内完整说明；阿蘅米袋从空袋、工米入袋、追加预付米到退米后扎袋、清账接退粮，共五种形态。阿禾和船家各有一个完整状态；普通走动、表情变化或素材候选换版不额外制造状态。

每次实际呈现或发声都绑定准确状态，同场、同镜的变化有先后顺序、动作和正文依据。全剧 618 次场内实体使用与第一集 206 次镜内使用均已检查，没有缺失或错属。小满、许家女儿仅被提及，保留已知事实状态，不要求生产媒体。

每个需要呈现的状态保留一项整体参考，再按需增加局部、角度或声音；当前共 265 项整体参考需求。Codex 按审阅意见通过工具增加补充需求；素材管理可把同一文件组成关联多个准确状态，并说明整体或细节覆盖。新增关联保存为素材的新候选修订，实际调用和已有采用不改写。未选整体参考时，细节不能使状态就绪。当前候选尚未完成与新状态的逐份适配核对，也未获用户接受。

旧 86 个局部状态不计入当前完整状态数量，仍保留修订、来源、评论及实际制作引用。完整状态的对应与影响清单见 [迁移核对](evidence/complete-state-migration.json)；它仅供复核，不代表旧素材自动兼容或已经换版。技术验证见 [verification.md](verification.md)。

## 当前实际候选

下面列的是候选原件，不是已经接受的基准。精确修订、SHA-256、制作调用与歌词依据可在素材详情及重放清单核对。

| 素材 | 版本／原件 | 核查结果 |
| --- | --- | --- |
| 李寄造型 | `asset-liji-image` 版本 1、2；[第一张](../export/assets/82a51fcd631931e43bc0ed5535a1c80827a072fb37dd9a2e8b366d5d13258458.png)、[第二张](../export/assets/cd50ecc53c05dd06c2f592adf164b12f2711ef44538479cd3b55a711590dae33.png) | 均为文字生成根候选，2016×2688，未达到原生 4K；已回看，尚未接受母版 |
| 阿蘅对白 | [17 秒 WAV](../export/assets/a041a61f5f37de8086eba7de160804c785587d1ae1ce024ef67246f846c69e84.wav) | 48 kHz、双声道、PCM 16-bit，待实际听审 |
| 李寄对白 | [12.38 秒 WAV](../export/assets/90227903269315a0fde6b66cdcb91698d0c7737c2e1f6dddf593e6fe7fc8f014.wav) | 同上，待实际听审 |
| 周掌柜对白 | [17 秒 WAV](../export/assets/d242aeb9c0b0069f18a252f62a6a2aedc4625522033aa92c5a5ab03f8da1f76f.wav) | 同上，待实际听审 |
| 赵执事对白 | [11.5 秒 WAV](../export/assets/842ecea98a028fa105e0f30a4f5a6085d412d3c40aecf24516f5a7a10b19ab92.wav) | 同上，待实际听审 |
| 阿蘅舟行曲 | [17.0534 秒 WAV](../export/assets/9edcf64a1d34914d1d406a01aff9617f3759eb51ed699e1380fde6f96993c953.wav) | 实际引用上述阿蘅对白作为声线参考；原歌词未另写，录音是否准确仍需听辨 |

OpenArt CLI 0.1.1 没有暴露所需质量及分辨率参数，两次实际改由 OpenArt 连接器提交明确项目 `8K6WcbrPLghSBJXBtWAE`、GPT Image 2.5、high、4K。第二次还指定 3072×4096，原件仍为 2016×2688。两次共用 500 Credit，最后回读 9,979；没有重复提交相同失败设置。保持 4K、接受该模型实际尺寸或改用其他模型的取舍仍待用户决定，不能将这两张候选标记达标。

豆包音频使用 `seed-audio-1.0`。控制台核对时剩余免费量 45.06 分钟（2,703.6 秒），五次调用共计费 74.9334 秒。该观察值减去本任务调用得到 2,628.6666 秒的本任务保守余量，不代表账户其他会话未发生消费；下次付费制作前应重新核对。模型在当前会话不能直接听辨音频，字幕核查和播放器计时推进均不能代替实际听审。没有充值或新增购买。

首轮基准审阅还缺其他必要人物、代表背景与道具等视觉材料，以及实际声线／演唱听辨。完整基准获得用户对确切版本的认可后才批量派生。24 fps、1080p 动态分镜及 48 kHz 声音是待审制作规格；227 秒是镜头设计估时，不是成片实测。

## 隔离恢复与运行

日常审阅使用现有后台容器 `snakeslayingrecord-production-task-0003`，挂载本任务 `.runtime/production/review-instance` 中的现有数据，仅监听 `127.0.0.1:39103`。容器采用 `unless-stopped` 重启策略；退出代理会话不会停止它，手工停止后可用以下命令恢复。不要为页面打不开重新恢复或导入数据库。

```bash
docker start snakeslayingrecord-production-task-0003
docker logs --tail 40 snakeslayingrecord-production-task-0003
```

只有该容器尚不存在时，才从故事任务工作区根目录执行以下创建命令。先确认实例数据库已经存在，并核对本地镜像版本。当前镜像的 32 个系统文件与 `6bca5a8b89600a1f5d40187d85cbc0978607b985` 一致，镜像摘要及本次更新验证见 [direct-entity-review-runtime.json](evidence/direct-entity-review-runtime.json)。服务设有两秒套接字空闲超时，避免浏览器空预连接无限阻塞页面；业务操作仍在同一数据库线程执行。这一步只启动现有实例，不初始化或覆盖数据。

```bash
test -f .runtime/production/review-instance/.runtime/review.sqlite3 && \
docker run -d --name snakeslayingrecord-production-task-0003 \
 --restart unless-stopped --label codex.task=task-20260929-0003 \
  --label codex.system-revision=6bca5a8b89600a1f5d40187d85cbc0978607b985 \
  -p 127.0.0.1:39103:8765 \
  --mount "type=bind,source=$PWD/.runtime/production/review-instance,target=/instance" \
  story-review-desk:task-20260929-0003-production
```

以下空实例恢复命令也从故事任务工作区根目录执行。Python、FFmpeg／ffprobe 和对应版本通用系统需先可用；不复制 `.env` 或凭据。当前系统工作区仅是本机路径，重新检出时可用通用仓库中 `config/instance.json` 固定的提交替代它。最后的 Python 命令是前台临时检查服务，不能作为需要跨会话保留的交付入口。

```bash
production_system=.runtime/review-desk-worktree
python3 scripts/production_review.py --system "$production_system" recover \
  --destination .runtime/production/fresh-review
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance .runtime/production/fresh-review serve --port 39105
```

目标必须是当前 worktree `.runtime/` 内尚不存在的目录。工具先核对既有故事导出摘要和 14 个受管文件，再恢复基础故事数据并通过通用业务操作重放生产修订，最后比较全部生产修订 ID、当前采用的记录头和文件校验值。不会覆盖已有数据库；失败的目标保留供检查，换新的空目录重试。重放保留修订内容与顺序，不复写首次导入时间；完整数据库导出恢复同时保存数据库元数据、评论和事件。

仅使用现有 39103 实例继续工作时不要重新恢复。查看实际缺项：

```bash
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance .runtime/production/review-instance production-ready shot-e01-001
```

当前实际制作实例没有正式素材采用，第一集 320 项镜头用途与 41 项共用状态整体参考，合计 361 项必要输入均未就绪。`production-package ID --output directory` 只有在必要输入满足时才复制精确文件目录；页面下载的是同一清单。当前不把缺项清单冒充可执行生成包。

继续整理时，`scripts/episode01_shots.py` 与 `scripts/scene_requirements.py` 接受 `--system`、`--instance`，默认只比较并校验，显式 `--import-records` 才写入变化。`production/inventory.json` 是抽取的当前编写数据，历史恢复必须使用 `replay.json`，不能重复按初始版本导入或用编写数据覆盖真实审阅。`scripts/register_production_candidates.py` 用于本轮真实调用首次登记，不应对已有对象重复执行。

新调用音频前，用 `python3 scripts/seed_audio.py production/requests/aheng-song-01.json` 这类具体单个请求文件检查参数；默认只输出预览，不提交。`--submit --quota <最新额度记录>` 才调用服务；使用已有 `VOLCENGINE_SPEECH_API_KEY` 环境变量。未知结果按最长 120 秒保留额度，不自动重复调用。新增请求应使用新 ID，保留旧回执及原件。

整理完成后，从真实制作实例执行 `production_review.py ... snapshot --instance ...` 保存新的精确重放；不要从操作测试实例保存。正式发布前仍须读取最新正式数据与代码，合并候选后复验，不以本次启动快照覆盖用户新增评论。

## 直接审阅与后续修订

内容由 AI 通过共用业务接口新增修订，用户打开实体即可审阅。读取整份实体内容：

```bash
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance .runtime/production/review-instance \
  production-entity-review entity-li-ji
```

HTTP 对应 `/api/production/entity-review?entity_id=entity-li-ji`，查询不写数据库。读取过去采纳的准确内容时，CLI 追加 `--revision 采纳判断的修订`，HTTP 追加 `revision_id`。无需执行初始化或准备送审；原初始化脚本已退役，历史批次 `entity-review-submissions.json` 只供追溯，不重复导入。

Codex 读取意见后，通过 `production-import` 新建相应 ENTITY、STATE 或 ASSET 修订，带上 `expected_version` 及必要的 `expected_heads`，不得覆盖原稿与历史锚点。用户点击“采纳当前版本”才记录具体内容范围，Codex 不代替用户操作；新评论不改变已有采纳。详细字段、并发和恢复契约见系统 `docs/production.md`。

## 完整状态整理与迁移

`scripts/production_forms.py` 维护完整形态及按剧情发生的顺序；`scripts/production_inventory.py` 维护实体与逐场检查；镜头与需求工具从准确场次状态取用。状态的未知细节仍需审阅，编写数据不是用户已接受的母版。先核对源数据与页面的新编辑，再在任务实例预演；以下路径均相对故事工作区根目录：

```bash
python3 scripts/migrate_complete_states.py plan \
  --system "$production_system" --instance .runtime/production/review-instance \
  --file .runtime/production/next-state-plan.json --write-artifacts
```

计划文件含准确旧记录头、拟新增修订、旧状态对应、受影响位置及内容校验值。回读差异，确认没有覆盖页面上的新编辑，才执行同一文件：

```bash
python3 scripts/migrate_complete_states.py apply \
  --system "$production_system" --instance .runtime/production/review-instance \
  --file .runtime/production/next-state-plan.json
```

提交在同一事务中检查所有读取依赖和每项记录版本；并发变化会使整批回滚，应重新预演和核对。相同源数据重新预演返回零变化。迁移不改旧局部状态、素材、实际调用、采用或审阅结论；不再适用的计划需求以撤回修订保留理由。当前批次已完成，不需再次导入初始 JSON；后续整理同样通过受控增量修订与快照交接。

本轮真实生产重放在 `.runtime/production/recovered-direct-review-final`，含 2,139 个生产对象、3,482 个修订、14 个文件组成与基础故事 264 条评论；完整库恢复在 `.runtime/production/bundle-direct-review-real`，含 2,262 个总对象、3,614 个修订、266 条评论、295 条评论事件和 70 个清单文件，8 张表逐项一致。已有 133 份旧送审记录只供历史恢复，正常页面直接读取实体内容。另用 `.runtime/production/direct-review-test` 验证采纳后继续评论、新修订及历史定位，并分别完成完整库与生产重放恢复；这些技术决定与三条新测试意见没有进入真实任务库。详见 [恢复证据](evidence/direct-entity-review-recovery.json)。恢复副本不覆盖最新运行数据。

## 下一次制作交接

先解决图像实际尺寸与要求的冲突，补齐首轮代表基准并完成实际听审。基准获认可后，按 33 镜需求生产和选用素材，生成逐镜完整目录包与 16:9 有声动态分镜，保存可编辑工程。第二轮审阅意见处理后，再在空实例打开工程、播放完整动态分镜并核对全部依赖。最终任务完成与本地集成须另行展示候选提交、验证证据并获得用户明确确认；当前没有进入该步骤。
