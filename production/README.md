# 版本四制作准备与审阅

《把灯带回家》版本四已获用户确认，17 集、42 场、1,114 个正文块；主视觉为二维人物与轻手绘背景，16:9。当前完成全剧实体／状态抽取、第一集 33 镜设计、逐素材方案及首批实际候选。基准尚未全部补齐或接受，第一集未就绪；完整素材、有声动态分镜、成片和工程在后续制作范围。

本轮制作审阅改进已在隔离实例联合验证，系统候选 `131eb81` 已吸收并行素材轮次任务 `8cf4852`；正式发布顺序仍待协调。正式 3000 当前保留原系统 `4c0cc62` 和真实业务库；下述新交互指本轮候选，正式版本与最终验证以 [STATE.md](../STATE.md)和[本轮验证](review-ui-verification.md)为准。本任务不生成媒体、不自动推送。

## 内容入口

| 要核对什么 | 材料 |
| --- | --- |
| 定稿、用户确认与准确来源 | [source-lock.json](source-lock.json) |
| 全剧身份、别名、完整状态和出场 | [inventory.md](inventory.md)及[inventory.json](inventory.json)：133 个实体、267 个完整状态 |
| 直接关系、集场原文和修正范围 | [entity-relationships.md](entity-relationships.md)、[准确增量与全部证据](entity-relationships.json)、[33 条修正前后对应](relationship-review.md) |
| 第一集镜头、空间和定稿声音 | [33 镜设计](episode01/shots.md)、[准确数据](episode01/shots.json)、[37 个对白／演唱单元](episode01/dialogue-cues.json) |
| 实体描述与生成方案 | [generation-preparation.md](generation-preparation.md)：33 个实体的 77 个状态、122 项方案，区分计划与实际调用 |
| 现有候选的实体与状态归属 | [baseline-associations.md](baseline-associations.md)、[requests](requests/)、[receipts](receipts/)及[baseline-records](baseline-records/) |
| 原生有声预演计划 | [声音契约](native-audio-workflow.md)、[33 镜计划](episode01/seedance/manifest.json)，尚未执行 |
| 完整恢复与历史 | 最新正式 `export/` 与匹配的 [replay.json](replay.json)；历史制作准备验证见 [verification.md](verification.md) |

## 用户如何审阅

长期入口为 [制作设定](http://127.0.0.1:3000/?workspace=settings.workspace)、[素材管理](http://127.0.0.1:3000/?workspace=materials.workspace)与[全剧制作](http://127.0.0.1:3000/?workspace=production.workspace)。主导航与标题提供定位，全剧制作保留必要的“剧本依据：版本四 · 已确认 · 17 集”摘要。

制作设定按实体浏览。基础信息常驻，主要关系先排列，再选择完整状态；关系节点不跳转，连线文字可圈选评论，来源弹窗显示准确剧本版本、集场和原文。关系、状态及素材版本在各自控件旁切换，评论始终绑定当时修订；旧内容与旧引用保留。

“采纳”认可当前基础信息、关系、全部完整状态和生成方案，通过完整准备校验才允许推进生成；仍可取消和评论。旧内容采纳取消后，原实体／状态／素材范围仍完全一致时可重新认可，页面说明其不授予生成许可。内容修订、真实缺项、历史阅读或版本冲突不会靠启用按钮绕过；Codex 不代替用户采纳。

素材管理使用平铺的记录类型与内容分类按钮，可组合搜索，数量随搜索与另一组条件联动。按当前列表对象计数，历史修订不重复累计；真实未生成的需求单独计为需求，不计为实际素材或就绪。全部类别包括零结果均可选择，清除同时重置搜索与筛选。筛选不改变正在阅读的准确版本。

制作设定和素材管理复用素材卡。未生成时显示真实需求对应的图像、声音或其他媒体占位；声音不借人物封面充当原件。已有准确结果时预览真实文件。模型、参数、提示词和参考输入分别来自方案与实际调用，不互相补写；参考在页内弹窗查看，可继续放大原图。关闭、Esc 和键盘返回保留版本、阅读上下文、焦点与未提交评论草稿。图像完整显示，真实音频可播放、选段、试听和评论。

素材版本按修订轮次选择，内部记录修订号不代表生成次数。待产轮次只显示该需求占位，旧结果保留在历史轮次中；同一轮次可以有多次真实调用和候选。跨状态复用按实际关联需求的轮次显示，不从实体身份推断原件适用范围。

三个制作页面没有批量导入、登记原件、编辑说明、添加需求及维护关联的专用表单；内容调整通过评论交给 Codex。准确素材采用、审阅结论、评论、版本、预览及缺项检查仍可用。全剧制作默认第一集 33 镜，按分集／场次筛选后检查缺项，每页最多 20 项；单镜详情展示该镜需求。

## 现有候选与实际限制

| 原件 | 实际情况 |
| --- | --- |
| [李寄第一张](../export/assets/82a51fcd631931e43bc0ed5535a1c80827a072fb37dd9a2e8b366d5d13258458.png)、[第二张](../export/assets/cd50ecc53c05dd06c2f592adf164b12f2711ef44538479cd3b55a711590dae33.png) | 两次文字生成根候选，2016×2688，未达原生 4K，未接受母版；同一素材身份的旧准确原件保留 |
| [阿蘅对白](../export/assets/a041a61f5f37de8086eba7de160804c785587d1ae1ce024ef67246f846c69e84.wav) | 17 秒，48 kHz、双声道、PCM 16-bit |
| [李寄对白](../export/assets/90227903269315a0fde6b66cdcb91698d0c7737c2e1f6dddf593e6fe7fc8f014.wav) | 12.38 秒，同规格 |
| [周掌柜对白](../export/assets/d242aeb9c0b0069f18a252f62a6a2aedc4625522033aa92c5a5ab03f8da1f76f.wav) | 17 秒，同规格 |
| [赵执事对白](../export/assets/842ecea98a028fa105e0f30a4f5a6085d412d3c40aecf24516f5a7a10b19ab92.wav) | 11.5 秒，同规格 |
| [阿蘅舟行曲](../export/assets/9edcf64a1d34914d1d406a01aff9617f3759eb51ed699e1380fde6f96993c953.wav) | 17.0534 秒，实际引用阿蘅对白作声线参考 |

仍为 6 个素材身份、7 次实际调用、两张图和五份 WAV；播放器验证不代替声音听审。第一集 250 项镜头用途与 67 项状态必要需求合计 317 项均未明确采用。原生尺寸、代表背景／道具／人物基准、准确声音和平台额度须在后续制作解决；227 秒为设计估时，非成片实测。之前观察的账户额度不是当前余额，执行前重新查询。

## Codex 后台维护与恢复

日常命令以真实故事根目录为工作目录；正式业务库始终为 `.runtime/review.sqlite3`。通用系统位于同级 `story-review-desk-python`，新克隆按根 [README](../README.md)准备，并使用 [config/instance.json](../config/instance.json)指定版本。任务工作区改用该任务的隔离系统目录。不要复制密钥、建立第二份任务账本或把旧快照覆盖到活库。

```bash
production_system=../story-review-desk-python
PYTHONPATH="$production_system" python3 -m review_desk --instance . production-entity-review entity-li-ji
PYTHONPATH="$production_system" python3 -m review_desk --instance . production-get --object asset-liji-image
PYTHONPATH="$production_system" python3 -m review_desk --instance . production-ready shot-e01-001
```

读取历史采纳时，`production-entity-review` 追加 `--revision 准确采纳修订`；读取素材历史时 `production-get` 追加 `--revision 准确修订`。HTTP 对应 `/api/production/entity-review`、`/api/production` 与准确来源的 `/api/production/source`，读取不写内容。

维护使用 `production-import FILE --validate-only` 预演，再用相同批次导入；携带 `expected_version` 和必要的 `expected_heads`，保留原稿与历史锚点。真实文件先用 `production-file FILE` 导入原件，再通过 `production-import FILE.json` 登记其准确 CALL、ASSET 与需求／状态关联；文件入库本身不创建采用。准确采用沿用系统仓库的 `docs/production.md` 契约。关系在本故事 [编制工具](../scripts/entity_relationships.py)中维护，先 `plan` 后 `apply`，正式写前重新准备。

`production_forms.py`、`production_inventory.py`、`episode01_shots.py` 和 `scene_requirements.py` 保存本故事规则；不要重复运行初始批次覆盖已审内容。`register_production_candidates.py` 只用于真实新调用首次登记，不重复登记已有对象。新媒体请求先检查单个请求、最新额度与准确输入，再按当次授权执行；本任务不调用生成。

恢复只接受新的隔离目录，先准备 Python、FFmpeg／ffprobe 和固定版本系统：

```bash
python3 scripts/production_review.py --system "$production_system" recover \
  --destination .runtime/production/fresh-review
PYTHONPATH="$production_system" python3 -m review_desk \
  --instance .runtime/production/fresh-review serve --port 39105
```

完整 `export/` 校验全部资料、对象与修订、依赖、评论／事件、公开配置及原件；恢复后比较准确版本与文件校验，不重复导入已有生产数据。`production-package ID --output directory` 仅在必要输入满足时复制执行文件；缺项清单不作为可执行包。

每次收尾从最新正式库的一致性备份导出完整 `export/`，再执行 `production_review.py ... snapshot --instance ...` 保存与导出匹配的重放。测试意见和测试采纳不得进入正式导出。正式发布增量应用，不用启动快照替换数据库；恢复失败保留隔离目标供检查，不覆盖已有实例。

## 正式运行和集成

3000 由 `snakeslayingrecord-app-1` 与 `snakeslayingrecord-nginx-1` 提供，仅监听本机，使用 `unless-stopped`。凭据和可信 CA 沿用现有配置；重建使用 `REVIEW_DESK_BUILD_CONTEXT=../story-review-desk-python`。查看／重启用 `docker compose ps`、`docker compose restart`，不要因页面故障重新恢复数据库。

共享正式库、公开导出、系统集成和 3000 部署必须串行。发布前核对最新正式数据与两仓基线，备份并增量应用，再回读三个页面和关键样例。旧容器与旧库保留追溯；共享同一正式库的旧容器不得同时启动，回滚代码前先导出最新数据，不用旧库覆盖新增评论或决定。

双仓修改、说明与证据在本任务工作区提交，故事通过 `_prepare_integration` 生成候选并复验。展示最终候选及实际验证后，由用户明确确认完成并集成，再运行 `_complete`；准备命令不是通过验收。本任务不自动推送，完成后停止写文件与提交，保留工作区与分支。
