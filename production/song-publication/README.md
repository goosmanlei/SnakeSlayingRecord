# 四首歌曲正式入口增量入库

2026-10-05 已完成正式 3000 增量入库，将已归档的歌曲制作成果适配当前正式审阅台的完整素材版本结构。范围是四首歌的全部既有录音及其准确历史：76 个歌曲对象（16 个更新、60 个新增）、142 个修订、640 条依赖、14 条真实评论、89 份受管文件。没有再次生成，也没有接受音频质量或修改正式剧本。

## 从正式入口试听

在正式 3000 的“制作设定 → 实体管理”中选择“歌曲”，打开曲名后选择“独立歌手完整演唱”状态，再使用“素材版本”切换录音。最新草稿与真实调用的完整定义不同，保留为尚未生成的独立版本；要试听请选择下表有录音的版本。

| 歌曲 | 已有录音版本与时长 | 最新未生成草稿 |
| --- | --- | --- |
| 三道滩 | 1：115 秒；2：123.533 秒；3：113.13625 秒 | 4 |
| 送青篷 | 1：118 秒（早期缺词候选）；2：90 秒；3：144.06525 秒 | 4 |
| 四邻安 | 1：88 秒；2：113.005667 秒 | 3 |
| 明月还乡 | 1：114 秒；2：170.370542 秒 | 3 |

共保留 10 份独立整曲录音。原词稿、真实用户意见、旧 Seed 参考片段、另演与纠词短样也沿准确修订保留。以上是当前完整素材版本编号；旧阶段文档中的 ASSET 修订编号属于原件记录，不等同于当前素材版本编号。[制作缺口与原件](../songs-review.md)保留详细范围。

## 数据与验证入口

系统准确提交由 `config/instance.json` 固定为 `b874b959af9c918a482e8488dc25cb0204ab5772`。本次只发布业务数据，沿用正式系统与服务。

- [准确增量包](../publications/songs-current-model-v2.json)由最新正式库的隔离基线与候选计算，不覆盖活跃数据库。
- `scripts/prepare_song_publication.py`仅在独立工作区中适配历史增量，注册完整版本、候选与评论归属。历史修订的原始逻辑字节及身份保持不变。
- `scripts/verify_song_publication.py`核对原有数据、历史修订、评论与媒体，使用副本验证冲突拒绝、事务回滚、并发评论保留及幂等。[校验结果](verification.json)记录实际结果。
- Schema 6 导出包含同一候选及完整历史，受管 JSON 使用引用容器保存原始逻辑字节，音频原件不转码。空实例恢复单独验证。

旧阿蘅 WAV 的结束时间来自真实 PCM 帧数，早期组件时长仅记录六位小数，两者相差约 0.167 微秒。准备时先核对 PCM 实际时长，仅在校验视图中处理这一舍入差，不改历史录音、调用范围或修订哈希；准确记录在增量包的 `origin` 中。

## 正式执行与恢复

准确包与受管文件先提交并合入主干，再从独立工作区调用 `scripts/publish_generation.py --instance 正式目录 --package production/publications/songs-current-model-v2.json --run-name 唯一运行名 --source-commit 完整提交SHA --apply`。发布器核对主目录干净、已合并提交、准确依赖及原件，持有正式发布锁，先一致备份和演练，再单事务追加数据。

执行回执和恢复备份留在本次独立工作区 `.runtime/generation/publications/`。包的事务记录位于正式库 `generation_publications`；外部回执丢失可使用同一准确包与新运行名恢复，不能把旧备份覆盖正式库。输入发生冲突时重新构建增量，保留其他任务的新数据。

[正式执行回执](applied.json)与[正式数据回读](formal-verification.json)确认候选与正式库全部业务表一致，原有271条评论、300条事件及无关数据保持不变，入库后共285条评论、314条事件。[真实 Chrome 验收](browser-verification.json)已在3000歌曲分类中切换全部10个录音版本，确认播放器和时长，实际静音播放《三道滩》版本3并暂停；回读《明月还乡》的3条历史评论，没有创建测试意见。播放与页面检查不构成音质接受。

正式已有录音的直接链接：

- [三道滩 · 版本3](http://127.0.0.1:3000/?workspace=settings.workspace&production_tab=entities&breakdown_episode=screenplay-04-lantern-home-e01&breakdown_scene=preparation-s001&production_entity=entity-boat-song&entity_state=form-boat-song-independent&production_object=asset-songs-boat-full&production_revision=72894b94e4ae68720ae08df802fa0c13843dfafa07fc8c2d0ab400fe0fb94ced&material_id=need-form-boat-song-independent-overall&material_version=3)
- [送青篷 · 版本3](http://127.0.0.1:3000/?workspace=settings.workspace&production_tab=entities&breakdown_episode=screenplay-04-lantern-home-e01&breakdown_scene=preparation-s001&production_entity=entity-blue-awning-song&entity_state=form-blue-awning-song-independent&production_object=asset-songs-blue-awning-full&production_revision=be7f9844f1058839ce2d6853b8d42214df1ab53ce2d1c56d64f5b75c5c9b71b9&material_id=need-form-blue-awning-song-independent-overall&material_version=3)
- [四邻安 · 版本2](http://127.0.0.1:3000/?workspace=settings.workspace&production_tab=entities&breakdown_episode=screenplay-04-lantern-home-e01&breakdown_scene=preparation-s001&production_entity=entity-snake-welcome-song&entity_state=form-welcome-song-independent&production_object=asset-songs-welcome-full&production_revision=4c5e0f44701a7b4723a8f56f5b0cdc9864d5e347f0a8ce7ffc080d48a53fd446&material_id=need-form-welcome-song-independent-overall&material_version=2)
- [明月还乡 · 版本2](http://127.0.0.1:3000/?workspace=settings.workspace&production_tab=entities&breakdown_episode=screenplay-04-lantern-home-e01&breakdown_scene=preparation-s001&production_entity=entity-blessing-stage-song&entity_state=form-blessing-song-independent&production_object=asset-songs-blessing-full&production_revision=4e3a28d1f3cf1c5a0ef9a6b57d80346c860a845e5a5a688af43e661131ad8d40&material_id=need-form-blessing-song-independent-overall&material_version=2)


## 完整导出恢复

当前系统的普通恢复器会拒绝两条旧WAV调用约0.167微秒的时间舍入差。使用 `scripts/recover_song_publication.py --system 兼容系统目录 --destination 本工作区.runtime内新目录 --candidate 待比较的准确数据库副本` 恢复本次Schema 6导出；仅核对并处理增量包中两条准确历史调用的校验视图，不改数据或系统代码。校验依据包括原件SHA-256、实际PCM帧数、准确输入组件及完整历史payload。其他输入仍按原恢复器校验。

[恢复结果](recovery-verification.json)确认22张业务表与候选全部一致，含6296个对象、10302个修订、285条评论和314条事件；历史payload没有变化。旧 `production_review.py recover` 先展开历史replay，本轮进程被系统终止，未记为通过；本Schema 6恢复入口直接使用完整导出，避免依赖旧replay。

## 本次过程资源清理

[清理回执](cleanup.json)确认删除本次隔离测试、重复预检、恢复与审阅副本及旧中间包，共9482个文件、8484895354字节逻辑大小；所有指定路径已回读不存在。没有本次仍运行的预览进程或容器，正式服务挂载不指向本次工作区。正式库、原件及其他任务资源没有删除。

本机仅保留 `songs-model-apply-01` 的准确发布前后数据库和事务回执，供发布追溯与向前恢复；较新的有效恢复基线取代后才能移除。少量诊断日志保留用于解释普通恢复器的旧时长兼容问题。当前会话仍使用工作区；退出并先迁移必要发布备份与回执后，可经Git工作区管理清理，分支和提交保留。三份歌曲脚本用于复现准确适配、校验及历史精度恢复，属于交付入口，不是遗留试验脚本。
