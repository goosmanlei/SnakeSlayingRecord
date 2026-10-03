# 四首歌曲：整曲试听与恢复

用户已回复“好，继续整曲创作”，确认上一轮完整歌词、曲名、音乐方向及局部剧本同步范围。本轮已制作四首整曲候选、八个旋律短参考，以及阿蘅声线另演的第一集两段清唱。当前交付用于听审，尚不是已接受的发行终版；完整任务范围以[任务说明](../planning/complete-songs-task.md)为准。

## 试听与准确版本

在[隔离歌曲审阅台](http://127.0.0.1:39114/?workspace=settings.workspace&production_entity=entity-boat-song)选择歌曲，再选“独立整曲演唱”。歌词在作品基础信息中；播放器可选段评论。独立歌手不自动代表阿蘅、母亲或歌娘。《送青篷》同轮保留两次真实结果，本轮请听 **90 秒第二稿**；118 秒第一稿的返回字幕缺四行，未作为完整试听版本。

| 稳定实体 | 曲名／本轮录音 | 实际时长 | 原始 WAV SHA-256 |
| --- | --- | --- | --- |
| `entity-boat-song` | 三道滩 · full-v1 | 115 秒 | `4b46af94ab4760d03c1b3acc56708fcc107cfcbfa1141a8077fa57879dec6b07` |
| `entity-blue-awning-song` | 送青篷 · full-v2 | 90 秒 | `e2c298a4a82b42114389032374abd0f108746efef898e40fe13f83d5ecc261fe` |
| `entity-snake-welcome-song` | 四邻安 · full-v1 | 88 秒 | `2fdccee2ac168192522ad56ddc3d95f63bb0aa350a9f30bfdefbdd4f976817bd` |
| `entity-blessing-stage-song` | 明月还乡 · full-v1 | 114 秒 | `627f35f9e98206fb6a34a1d96a437bfeca724cab92fad2bddfb3560f00145fe7` |

四份母文件均为接口原始返回的 48 kHz、双声道、PCM 16-bit WAV，未本地转码或升采样；另有 256 kbps MP3 试听副本。旋律目前由录音承载，尚无经听辨核定的曲谱。音乐方案中的调式、节拍、音域及编配是实际生成输入，不能反过来证明输出准确遵从。

以下路径以本任务 worktree 根目录为基准。完整试听包为 `.runtime/songs/song-audio-review-v1.zip`，64 个文件，118,793,905 字节，SHA-256 为 `6d5e891db94fea10b1233a68263d7f7b712f549b6e5f5069c2b78df10a75b096`。包内含四首 WAV／MP3、完整歌词、原文同步提案、实际请求与回执、角色另演、十个片段及校验清单；旧缺词候选单独保存在 `history/`。候选与过程只存 `.runtime/`，不会随文档提交上传 Git。

## 剧中片段与待补演法

- 八个旋律参考为 6.82—11.74 秒，分别覆盖舟行起句／归家、《送青篷》开头／断句／相照／认旧桥、领唱应和及庙戏“米饵献上，明月还乡”。文件真实存在、可定位到准确母版，但仍含独立版伴奏，不能冒充干净角色配音。
- 阿蘅清唱另演原件为 17.686979 秒，SHA-256 `dcd331048e40bb4bf5ed6b4aaa96e86852f80339094ce4bc6512c57d03476e4c`。实际引用用户已认可的阿蘅基础音色 `a7d678681c2e490de0a7dc8aca163131f68e196ceda703dc9c9282418c589272`，认可原记录为 `review-master-fg3-aheng-voice-01 / 144216df3855deb325e7663a78a5a43dbce23e1d43a0498193b726236f1a5305`；此次清唱不继承该认可。
- 两段清唱片段长 6.96 秒与 10.026979 秒，分别对应 E01/s001 b002、b004，既有 `shot-e01-001 / e01-line-001` 与 `shot-e01-003 / e01-line-002`。按返回时间标记，字音范围落在原预计唱词窗口内；归家片段完整尾部比原 10 秒镜头多约 0.027 秒，听审尾腔后再决定剪尾或延镜，未抢词变速或自动采用。
- 其余《送青篷》角色清唱、两次缺词停唱、阿蘅和母亲哼唱、歌娘核字慢唱、集体及庙戏场面演法尚未全部制作。后续须沿准确听审意见修订曲调，再引用相应已认可角色声线另演，保留母亲、歌娘与阿蘅的身份差别。没有声源分轨产出，不把混音片段称为分轨。

`.runtime/songs/audio-review/uses-with-audio.json` 保留 30 项全剧用法的准确版本四原文、完整歌曲逐行时间、片段关系、角色及未完成项；提及和可见歌页不算音频义务。时间来自接口逐字标记加裁切余量，实际拖腔与边界仍待听审。八个参考文件都符合 Seedance 2.0 单段 2—15 秒的长度范围；同一请求多段音频总长仍不得超过 15 秒，不能把两个合规文件直接当成合规组合。接口依据见[视频生成接口](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)。

## 已确认的歌词与剧情边界

基线仍是版本四 `7287b25a34d4b0db242ec5688f33349fa6d449874a3c6acb30033e2260cd2686`，17 集、42 场、1,114 个正文块。`.runtime/songs/lyrics-approval.json` 锁定上一轮四个实体修订、全部词稿／方案校验值及用户原话。四首共 60 行；原唱词全部保留。第一轮文字包 SHA-256 `6d8675161b00b90bdec513d6a1cc70b0754b7e3646401dc8509953f02d4c538e` 保持原样。

唯一已确认正文扩写为 E17/s041 b009 的《送青篷》第一段，新增衣物叮咛与隔水相望四行。完整改后场次在 `.runtime/songs/s041-proposed.md`；其余 21 块不改。第二段受损位置、“过／认旧桥”核字对白、舟行曲省掉两道滩仍成立。E04/s007 母亲选用《送青篷》起句无词旋律是已确认的制作选择，原文没有指定曲名的事实保留。

正式剧本、输入锁定及镜头计划尚未换版。现行接口须新增完整版本五及分集旧新引用对照；歌词同步范围认可不等于新版正式制作输入已发布。后续在最新正式数据上增量同步，不能用启动快照覆盖并行任务已登记的方案、母版或评论。

## 工具、额度与用途依据

实际使用现有 `scripts/seed_audio.py` 的 Seed Audio 1.0 HTTP 客户端，通过任务内适配器将全部文件写入 `.runtime/songs/audio-production/`。六次调用均有 completed 回执：四首本轮候选、《送青篷》第一次缺词候选、阿蘅省段清唱；回执计费时长合计 542.686975 秒。无新增购买或充值，也没有使用其他音乐平台订阅。

调用前现场核对开通状态和剩余额度；任务适配器同时获取已发现的各 worktree 调用锁，按 request ID 去重既有回执，扣除观察后用量，为未知请求按 120 秒预留，并另外保留 600 秒供并行任务。遇到其他调用占锁时未提交；金额／额度不采用旧快照推断当前余额。实际请求、模型参数、参考校验、平台日志号与扣减记录见 `.runtime/songs/audio-production/production/receipts/`；声线认可原记录及七条依赖修订只读引入隔离实例，正式库未写。

[音频生成接口](https://docs.volcengine.com/docs/DoubaoVoice/audio-generation-http?lang=zh)支持单次最长 120 秒、最多三份各不超过 30 秒／10 MB 的参考；这些是接口限制，不能代替歌曲质量核验。[生成模型服务专用条款](https://docs.volcengine.com/docs/DoubaoVoice/Generativemodelservicespecificterms-1?lang=zh)第 3.5 条规定生成内容的合法使用及演唱作品授权，第 3.9、3.11 条约束合成标识。交付保留原始返回字节并注明 AI 生成；不宣称作品排他性或适用于其他产品条款。核验摘要在 `.runtime/songs/audio-use-basis.json`，平台整页文档没有放入交付包。

## 已验与未验

`.runtime/songs/audio-review/verification.json` 已核对四首选定候选的真实格式、MP3 解码、全部 60 行的返回时间标记、十个片段与母版的逐样本一致性，以及试听包全部校验值。历史修订、264 条评论、293 条评论事件和既有采用保留；只追加新记录及四个实体的头修订。此轮调用登记与最终听审接受分别保存。

隔离实例导出后在 `.runtime/songs/audio-restored/` 空实例恢复，12 张业务表、120 个清单文件一致。恢复范围包含歌词、音频、片段、旧意见、原实际调用和准确引用。真实 Chrome 的播放、时间评论、参考预览证据另存 `.runtime/songs/audio-review/browser-verification.json`；测试评论只写 `.runtime/songs/audio-browser-qa/`，不进入用户审阅库、干净恢复实例或正式库。

**本会话没有直接听辨这些音频。** 字幕覆盖、零满幅样本或播放器到达结尾，不能证明实际咬字、音准、节奏、音色、乐句连贯、情绪、噪声或尾腔合格。四首整曲与全部片段都保持待真实听审、待用户接受；没有完成判定或镜头自动采用。

## 恢复与下一步

活跃审阅库是 `.runtime/songs/review-instance/.runtime/review.sqlite3`，39114 端口。恢复副本及浏览器测试库不得作为发布输入。服务停止时先确认端口空闲、系统提交仍为 `config/instance.json` 所锁定的 `15822ae77d9b6c3851852555a677d11d7adc7c10`，再从 worktree 根目录启动：

```bash
PYTHONPATH="$HOME/codex-path/creative/story-review-desk-python" \
  python3 -m review_desk --instance .runtime/songs/review-instance serve --port 39114
```

继续时先读活跃实例最新评论及准确接受记录。不要重跑 `prepare_review.py`、`register_audio_review.py` 或恢复脚本覆盖活跃实例；`.runtime/songs/audio-review/registration/` 保存本轮批次与回执，登记完成。新的歌词或音频修改使用新修订，实际旧 CALL 输入不变。

先收集四首整曲、短参考与阿蘅清唱的实际听审意见，修订到准确版本获认可；再完成其余角色演法、场面处理、剧本版本五和全部引用同步，准备正式增量发布包。最终候选、部署顺序、目标分支和实际验收证据齐备后再请用户确认完成并集成，随后才运行 `_complete`。当前没有正式发布、推送或任务完成确认。冲突恢复提交为 `1e75c514091538fda2bf09d5739b05788fbab8aa`；后续候选以重新 `_prepare_integration` 的回执为准。保留 worktree 和分支，正常退出会话后才释放运行锁。
