# 版本四制作准备与审阅

《把灯带回家》版本四已获用户确认，17 集、42 场、1,114 个正文块；主视觉为二维人物与轻手绘背景，16:9。当前完成全剧实体／状态抽取、第一集 33 镜设计、逐素材方案及首批实际候选。基准尚未全部补齐或接受，第一集未就绪；完整素材、有声动态分镜、成片和工程在后续制作范围。

全剧非歌曲首轮生成已交付 369 张新图、42 份新声音，共 411 份原件，并由前序任务增量发布正式库；探索、返工和撤回版本一并保留。有效图像目标为 251 项，四份声音获用户听审认可，其余 38 份待听审。准确身份、原件、谱系和接受范围见 [全剧生成交接](full-generation/README.md)及[范围归并](full-generation/scope-amendment.json)。素材卡、筛选、评论计数、共用音频播放器和实体读取由 `task-20261004-0004` 更新；使用与证据见[素材审阅交付说明](../planning/material-review-streamlining-delivery.md)。当前候选与实际运行状态沿 [STATE.md](../STATE.md)核对，旧阶段记录不代表新的验收或授权。

## 内容入口

当前全剧逐镜首稿与新素材版本／候选交付见 [制作拆解交付](breakdown/README.md)：17 集、42 场、297 镜；正式应用以任务账本和发布回执为准。

| 要核对什么 | 材料 |
| --- | --- |
| 定稿、用户确认与准确来源 | [source-lock.json](source-lock.json) |
| 全剧身份、别名、完整状态和出场 | [inventory.md](inventory.md)及[inventory.json](inventory.json)：原始抽取为 133 个实体、267 个完整状态；按[归并说明](full-generation/scope-amendment.json)撤回重复包布后，有效范围为 132 个实体、263 个完整状态 |
| 直接关系、集场原文和修正范围 | [entity-relationships.md](entity-relationships.md)、[准确增量与全部证据](entity-relationships.json)、[33 条修正前后对应](relationship-review.md) |
| 第一集镜头、空间和定稿声音 | [33 镜设计](episode01/shots.md)、[准确数据](episode01/shots.json)、[37 个对白／演唱单元](episode01/dialogue-cues.json) |
| 实体描述与生成方案 | [generation-preparation.md](generation-preparation.md)：33 个实体的 77 个状态、122 项方案，区分计划与实际调用 |
| 全剧非歌曲首轮方案与新原件 | [交接与审阅入口](full-generation/README.md)、[逐项方案及历史目标](full-generation/recipes.json)、[音色范围](full-generation/voice-scope.md)，包含准确方案、待绑定输入和用户锁定的 40 基础＋2 变化音色范围 |
| 素材轮次、历史对应及 0001 验证 | [material-rounds.md](material-rounds.md)、[准确对应](material-round-mapping.json)与[编制工具](../scripts/material_round_audit.py) |
| 历史场级计划需求 | [scene-requirements.md](scene-requirements.md)：其余 40 场 566 项镜头用途需求，不等于 251 个有效图像状态生成目标 |
| 现有候选的实体与状态归属 | [baseline-associations.md](baseline-associations.md)、[requests](requests/)、[receipts](receipts/)及[baseline-records](baseline-records/) |
| 原生有声预演计划 | [声音契约](native-audio-workflow.md)、[33 镜计划](episode01/seedance/manifest.json)，尚未执行 |
| 完整恢复与历史 | 完整 `export/` 交付快照与匹配的 [replay.json](replay.json)；历史制作准备验证见 [verification.md](verification.md) |
| 生成、独立预览与合并后发布 | [任务工作区流程](generation-workspaces.md)：所有新产物先留在任务分支，正式库显式增量发布 |

## 用户如何审阅

统一入口为 [生产制作](http://127.0.0.1:3000/?workspace=settings.workspace&production_tab=breakdown)，包含制作拆解、实体管理、素材管理。旧镜头制作链接进入合并后的准确位置，旧素材链接兼容保留；旧组合页面明确不可用。准确运行身份及正式验收以任务账本和发布回执为准，交付说明见 [入口合并](production-unification/README.md)。

制作拆解左选集、中间按场读镜头设计、右侧跟随场／镜查看实体状态与素材；剧情正文由准确来源入口打开。实体管理保留身份、主要关系与完整状态；关系、状态及素材版本在对应控件切换，评论绑定准确修订。

“采纳”认可当前基础信息、关系、全部完整状态和生成方案，通过完整准备校验才允许推进生成；仍可取消和评论。旧内容采纳取消后，原实体／状态／素材范围仍完全一致时可重新认可，页面说明其不授予生成许可。内容修订、真实缺项、历史阅读或版本冲突不会靠启用按钮绕过；Codex 不代替用户采纳。

素材管理按具体需求计一项，在同一条目查看占位、结果和历史；没有需求关联的历史素材独立保留。按未生成／已生成、真实内容类别与搜索组合筛选，只有真实原件计为已生成。类别由完整可浏览数据确定，组合搜索零结果不移除已有类别；清除恢复完整列表。真实调用、审阅结论和镜头采用保留详情与旧链接，不再与需求并列计数。

实体管理和素材管理复用素材卡。未生成时显示真实需求对应的图像、声音或其他媒体占位；声音不借人物封面充当原件。已有准确结果时预览真实文件。未生成时显示待执行方案，已有结果只显示所选结果真实调用中的模型、参数、提示词和参考输入；历史原方案可单独查看，不互相补写；参考在页内弹窗查看，可继续放大原图。关闭、Esc 和键盘返回保留版本、阅读上下文、焦点与未提交评论草稿。图像完整显示，真实音频可播放、选段、试听和评论。

素材代表持续需求；版本固定模型、参数、提示词、准确输入与随机策略，实际调用后固定方案。同方案重复生成产生同版本多个候选；评论、审阅、选择、重复回执和关联补全不自动建版。固定种子变化建新版，随机产生的实际种子只记录调用。旧轮次及评论锚点原样保留，逐项对应见 [迁移说明](breakdown/migration.md)。

制作页面用于审阅与准确采用，数据编辑和生成通过后台工具完成。制作拆解按集场镜阅读设计正文，随后连续显示本镜视频方案、准确输入、版本候选和采用；完整素材区包含视频子集并按稳定身份去重。旧组合与历史页面及其专属契约已退役。素材管理新增集场筛选，每页 40 项。使用说明与完整逐镜稿见 [本轮交付](breakdown/README.md)。

## 现有候选与实际限制

| 原件 | 实际情况 |
| --- | --- |
| [李寄第一张](../export/assets/82a51fcd631931e43bc0ed5535a1c80827a072fb37dd9a2e8b366d5d13258458.png)、[第二张](../export/assets/cd50ecc53c05dd06c2f592adf164b12f2711ef44538479cd3b55a711590dae33.png) | 两次文字生成根候选，2016×2688，未达原生 4K，未接受母版；同一素材身份的旧准确原件保留 |
| [阿蘅对白](../export/assets/a041a61f5f37de8086eba7de160804c785587d1ae1ce024ef67246f846c69e84.wav) | 17 秒，48 kHz、双声道、PCM 16-bit |
| [李寄对白](../export/assets/90227903269315a0fde6b66cdcb91698d0c7737c2e1f6dddf593e6fe7fc8f014.wav) | 12.38 秒，同规格 |
| [周掌柜对白](../export/assets/d242aeb9c0b0069f18a252f62a6a2aedc4625522033aa92c5a5ab03f8da1f76f.wav) | 17 秒，同规格 |
| [赵执事对白](../export/assets/842ecea98a028fa105e0f30a4f5a6085d412d3c40aecf24516f5a7a10b19ab92.wav) | 11.5 秒，同规格 |
| [阿蘅舟行曲](../export/assets/9edcf64a1d34914d1d406a01aff9617f3759eb51ed699e1380fde6f96993c953.wav) | 17.0534 秒，实际引用阿蘅对白作声线参考 |

上表为早期 6 个素材身份、7 次实际调用、两张图和五份 WAV，作为历史样例全部保留，不是当前全剧数量。后续 411 份新原件及准确调用见[全剧交接](full-generation/README.md)。播放或技术自检不代替声音听审；素材有原件和内容采纳也不等于镜头已明确采用。第一集的准确采用、完整有声动态分镜与工程仍待制作，227 秒为设计估时。继续生成须重新核对额度、准确输入、母版认可与当次授权。

## Codex 后台维护与恢复

以下三条只读命令可在真实故事根目录执行；正式业务库为主目录 `.runtime/review.sqlite3`。生成、登记、恢复和导出改在独立任务 worktree 执行，实例选择与变量设置见[任务工作区流程](generation-workspaces.md)。通用系统位于主项目同级 `story-review-desk`，按根 [README](../README.md)核对 [config/instance.json](../config/instance.json)指定版本；任务可选择自己的兼容系统工作区。不要复制密钥、建立第二份任务账本或把旧快照覆盖到活库。

```bash
production_system=../story-review-desk
PYTHONPATH="$production_system" python3 -m review_desk --instance . production-entity-review entity-li-ji
PYTHONPATH="$production_system" python3 -m review_desk --instance . production-get --object asset-liji-image
PYTHONPATH="$production_system" python3 -m review_desk --instance . production-ready shot-e01-001
```

读取历史采纳时，`production-entity-review` 追加 `--revision 准确采纳修订`；读取素材历史时 `production-get` 追加 `--revision 准确修订`。HTTP 对应 `/api/production/entity-review`、`/api/production` 与准确来源的 `/api/production/source`，读取不写内容。

生成任务维护使用 `production-import FILE --validate-only` 预演，再用相同批次导入自己的隔离实例；携带 `expected_version` 和必要的 `expected_heads`，保留原稿与历史锚点。真实文件先用 `production-file FILE` 导入该实例，再通过 `production-import FILE.json` 登记其准确 CALL、ASSET 与需求／状态关联；文件入库本身不创建采用。准确采用沿用系统仓库的 `docs/production.md` 契约。正式生成数据统一经准确包、Git 合并及显式发布处理。关系在本故事 [编制工具](../scripts/entity_relationships.py)中维护，先 `plan` 后 `apply`，正式写前重新准备。

`production_forms.py`、`production_inventory.py`、`episode01_shots.py` 和 `scene_requirements.py` 保存本故事规则；不要重复运行初始批次覆盖已审内容。`register_production_candidates.py` 只用于真实新调用首次登记，不重复登记已有对象。全剧首轮方案与代表项使用 `prepare_full_generation.py`、`register_full_generation.py`，后续真实增量使用 `register_generation_batch.py` 和带准确批次参数的 `publish_full_generation.py`；这些工具不代发模型请求；已经发布的批次不得盲重跑。新媒体请求先检查单个请求、最新额度与准确输入，再按当次授权执行。

恢复只接受任务 worktree 内新的隔离目录，先准备 Python、FFmpeg／ffprobe 和固定版本系统；以下命令均在任务 worktree 根目录执行，`production_system` 指向实际通用系统目录：

```bash
python3 scripts/production_review.py --system "$production_system" recover \
  --destination .runtime/production/fresh-review
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance .runtime/production/fresh-review serve --port 39105
```

完整 `export/` 校验全部资料、对象与修订、依赖、评论／事件、公开配置及原件；恢复后比较准确版本与文件校验，不重复导入已有生产数据。`production-package ID --output directory` 仅在必要输入满足时复制执行文件；缺项清单不作为可执行包。

每次收尾从最新正式库的一致性备份导出完整 `export/`，再执行 `production_review.py ... snapshot --instance ...` 保存与导出匹配的重放。测试意见和测试采纳不得进入正式导出。正式发布增量应用，不用启动快照替换数据库；恢复失败保留隔离目标供检查，不覆盖已有实例。

## 正式运行和集成

3000 由 `snakeslayingrecord-app-1` 与 `snakeslayingrecord-nginx-1` 提供，仅监听本机，使用 `unless-stopped`。正式实例文件由永久发布目录覆盖挂载；应使用当前发布目录内的恢复／重启入口，不能用普通 `docker compose up --build` 覆盖精确镜像与挂载。实际运行版本、当前目录和本轮操作计划见 [STATE.md](../STATE.md)与[资产清理报告](../planning/asset-necessity-cleanup-report.md)。凭据和可信 CA 保持原配置，不复制或公开。

共享正式库、公开导出、系统集成与服务应用串行。发布前核对最新数据与两仓基线，备份后增量应用，再回读重点页面与历史；代码恢复不覆盖活库。旧容器按其实际用途、层内数据、挂载和恢复依赖判断，不因停止就删除，也不同时启动共享正式库的旧实例。

双仓代码、说明和证据先在任务隔离工作区提交，故事用 `_prepare_integration` 固定候选；最终确认覆盖准确候选、推送目标和正式操作方案后才受控应用。任务完成状态只读唯一账本，完成后不追加文件提交。

此前 `0002` 的关系发布复核使用故事工具，只读比较其保留工作区中的发布前后备份；批次限定为逐条审阅的实体关系，不允许其他对象、旧修订、评论、轮次或采用发生变化：

```bash
python3 scripts/verify_production_review.py \
  --before .runtime/review-ui/formal-publication/write-window-before.sqlite3 \
  --after .runtime/review-ui/formal-publication/after-all-browser.sqlite3 \
  --batch .runtime/review-ui/formal-publication/published-batch.json \
  --report .runtime/review-ui/formal-publication/rechecked.json
```

上述 `.runtime/review-ui/` 路径相对保留的 `task-20261002-0002` 工作区，仅用于复核该次关系发布。全剧方案／原件发布核对使用 `verify_full_generation.py`，准确命令见 [全剧交接](full-generation/README.md)。下一次修改必须重新读取正式当前版本并准备增量。
