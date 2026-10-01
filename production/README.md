# 版本四制作准备

本目录保存《把灯带回家》从定稿剧本走向第一集生产的实际材料。用户已确认版本四为本任务终稿；主视觉为二维人物＋轻手绘背景，主画幅 16:9。交付终点是能够开始正式镜头生成的输入、素材和有声动态分镜，正式镜头视频及最终成片由后续任务完成。

当前已完成全剧抽取、第一集逐镜设计、通用系统最小实现和首批实际候选；两轮创作审阅、完整素材、动态分镜及工程仍未完成。此处是成果与操作入口，任务执行及完成状态仍只由主项目任务账本管理。

## 阅读与审阅入口

| 要核对什么 | 实际材料 |
| --- | --- |
| 用户确认、剧本与结构依据 | [输入锁定](source-lock.json)，保留整版、17 个分集、42 场和 1,114 个正文块的准确版本 |
| 全剧身份、别名、状态与出场 | [可读清单](inventory.md)和[完整数据](inventory.json)：133 个实体、86 个必要状态，42 场均有检查记录 |
| 后续各集计划需求 | [集场需求](scene-requirements.md)，其余 40 场登记 782 项；不要求本任务生产后续集媒体 |
| 第一集动作、空间与声音 | [33 镜设计](episode01/shots.md)、[精确数据及 320 个必要槽位](episode01/shots.json)、[37 个对白／演唱单元](episode01/dialogue-cues.json) |
| 实际提示词、输入与调用结果 | [requests](requests/)、[receipts](receipts/)和[登记批次](baseline-records/)；均区分计划与实际制作 |
| 完整生产修订历史及文件清单 | [replay.json](replay.json)，包含 1,466 个生产对象、1,626 个修订、14 个实际文件组成；包括本轮 49 个技术命名复核对象 |
| 系统设计、关系图及 API／CLI | 本任务独立通用系统工作区的 [docs/production.md](../.runtime/review-desk-worktree/docs/production.md)，代码版本以本故事 [config/instance.json](../config/instance.json)为准；未集成到正式系统 |
| 已执行验证与具体限制 | [verification.md](verification.md) |

本机隔离审阅入口为 [制作设定](http://127.0.0.1:39103/?workspace=settings.workspace)、[素材管理](http://127.0.0.1:39103/?workspace=materials.workspace)、[全剧制作](http://127.0.0.1:39103/?workspace=production.workspace)。39103 由独立 Docker 后台容器运行，不依赖代理会话；需要本机 Docker 保持运行。正式 3000 服务、正式数据库和导出未被替换。39104 是操作测试曾使用的端口，当前未启动；其恢复实例中的技术审阅和采用不属于真实制作决定，不应作为交付数据导出。

制作设定按“记录类型”和“内容分类”平铺选项，每项直接显示数量。先选“实体”可查看角色 51、场景 16、道具 62、歌曲 4；选“实体状态”则查看状态数。每项数量保留其他筛选和搜索条件后计算，不重复累计历史版本；零数量项仍可见。再次点选已选项可取消该组限制，“清除筛选”同时清除搜索和筛选。

实体状态统一命名为“实体完整名称·状态说明”，例如“阿蘅米袋·装有当日工米”。状态的所属实体、剧情内容和素材版本分别管理；同一实体可以有多个状态，不因此必须制作同样数量的图像。当前 86 个状态均有所属实体，本轮优化其中 49 个标题；旧版本名称与精确引用保留，技术命名复核不代表用户接受制作内容。

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

只有该容器尚不存在时，才从故事任务工作区根目录执行以下创建命令。先确认实例数据库已经存在，并核对本地镜像版本。当前镜像的 29 个系统文件与 `392dead589cca5ac5e49f88d9dce04d64c100ca1` 一致，镜像摘要及本次更新验证见 [state-naming.json](evidence/state-naming.json)，此前跨会话服务修复见 [service-restored.json](evidence/service-restored.json)。这一步只启动现有实例，不初始化或覆盖数据。

```bash
test -f .runtime/production/review-instance/.runtime/review.sqlite3 && \
docker run -d --name snakeslayingrecord-production-task-0003 \
  --restart unless-stopped --label codex.task=task-20260929-0003 \
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

当前实际制作实例没有正式素材采用，第一集 320 个必要槽位均未就绪。`production-package ID --output directory` 只有在必要输入满足时才复制精确文件目录；页面下载的是同一清单。当前不把缺项清单冒充可执行生成包。

继续整理时，`scripts/episode01_shots.py` 与 `scripts/scene_requirements.py` 接受 `--system`、`--instance`，默认只比较并校验，显式 `--import-records` 才写入变化。`production/inventory.json` 是抽取的当前编写数据，历史恢复必须使用 `replay.json`，不能重复按初始版本导入或用编写数据覆盖真实审阅。`scripts/register_production_candidates.py` 用于本轮真实调用首次登记，不应对已有对象重复执行。

新调用音频前，用 `python3 scripts/seed_audio.py production/requests/aheng-song-01.json` 这类具体单个请求文件检查参数；默认只输出预览，不提交。`--submit --quota <最新额度记录>` 才调用服务；使用已有 `VOLCENGINE_SPEECH_API_KEY` 环境变量。未知结果按最长 120 秒保留额度，不自动重复调用。新增请求应使用新 ID，保留旧回执及原件。

整理完成后，从真实制作实例执行 `production_review.py ... snapshot --instance ...` 保存新的精确重放；不要从 39104 的操作测试实例保存。正式发布前仍须读取最新正式数据与代码，合并候选后复验，不以本次启动快照覆盖用户新增评论。

仅优化状态名称时，在 `scripts/production_inventory.py` 的状态说明中维护短名，实体前缀自动取自实体清单；重新生成 `inventory.json` 与 `inventory.md` 后，运行 `python3 scripts/rename_state_titles.py --system "$production_system" --instance .runtime/production/review-instance` 预演。工具要求除名称和编写数据的引用占位符外，现有状态内容与清单一致，先列出影响范围，再准备准确的新修订及命名复核；显式 `--apply` 才原子写入，版本冲突则拒绝。镜头、需求、实际制作输入和旧素材引用保持原值，随后按上文保存重放。当前已完成此批更新，重复运行会返回无需改名。

## 下一次制作交接

先解决图像实际尺寸与要求的冲突，补齐首轮代表基准并完成实际听审。基准获认可后，按 33 镜需求生产和选用素材，生成逐镜完整目录包与 16:9 有声动态分镜，保存可编辑工程。第二轮审阅意见处理后，再在空实例打开工程、播放完整动态分镜并核对全部依赖。最终任务完成与本地集成须另行展示候选提交、验证证据并获得用户明确确认；当前没有进入该步骤。
