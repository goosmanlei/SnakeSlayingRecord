# 四首歌曲：整曲试听与恢复

本轮已按用户要求用 Lyria 重制四首独立歌曲，交付原生 MP3 试听。用户在首曲请求 WAV 却返回 MP3 后明确回复：“先完成四首 MP3 试听，WAV 母版保持待解决”。四次调用额度已用完；没有追加重试、充值或自动接受音频。完整任务范围见[任务说明](../planning/complete-songs-task.md)。

## 当前试听

打开[隔离歌曲审阅台](http://127.0.0.1:39114/?workspace=settings.workspace&production_entity=entity-boat-song)，选择歌曲的“独立整曲演唱”和“素材版本 2 · 当前”。作品基础信息保留已确认完整歌词与音乐方向；版本一中的 Seed Audio 候选及旧评论仍可查。独立歌手的演唱不自动代表阿蘅、母亲或歌娘。

以下路径以本任务 worktree 根目录为基准。四份原件位于 `.runtime/lyria/<尝试 ID>/audio-01.mp3`：

| 歌曲／稳定实体 | 尝试 ID | 实际时长 | 原件 SHA-256 |
| --- | --- | --- | --- |
| 三道滩 `entity-boat-song` | `songs-boat-lyria-wav-v1-a01` | 123.533 秒 | `47a045195be06b3769197529fbd5d36bbfb017f12e0570215f4143b37dfe6f0a` |
| 送青篷 `entity-blue-awning-song` | `songs-blue-awning-lyria-mp3-v1-a01` | 144.065250 秒 | `c72e629b2268ab48893c7df6e5e097c5e58e4da066f5d1ee2bbcf64bdd0ad703` |
| 四邻安 `entity-snake-welcome-song` | `songs-welcome-lyria-mp3-v1-a01` | 113.005667 秒 | `1523befb2c386401d7689a091f9a54476835e39c85387055a921050c7a0db64d` |
| 明月还乡 `entity-blessing-stage-song` | `songs-blessing-lyria-mp3-v1-a01` | 170.370542 秒 | `ebad1c3e2a0c104397d072cf725c5d117675f7fae1ec6368115b7ce8c72058d0` |

四首均为接口原始返回的 44.1 kHz、双声道 MP3，合计 13,247,699 字节；没有转码或升采样。首曲 ID 中的 `wav` 表示当时的请求，其回执仍为 `completed_format_mismatch`，实际格式未改写。其余三首按补充授权请求 MP3，回执为 `completed`。

独立试听包为 `.runtime/songs/song-lyria-review-v1.zip`，含四首 MP3、完整干净歌词、音乐方案、原文同步范围、30 项剧中用法、四次原始请求／响应／回执、逐行文本核对与校验清单。准确文件数、大小和 SHA-256 保存在 `.runtime/songs/lyria-review/packet-receipt.json`。候选及制作过程留在 `.runtime/`，未放入公开 `export/` 或 Git。

## 听审重点与未完成项

**用户已实际试听，反馈四首唱腔曲调更好听，但约每一两句就有词音不对应；四首均未接受。** 本会话不能直接听辨这些音频。文件解码、播放器自然到达结尾和返回文本核对，只证明相应技术事实，不能证明中文咬字、音准、节奏、声线、情绪、噪声或自然收尾合格。音乐方案中的调式、节拍、音域与编配是生成输入，实际旋律由录音承载，尚无听辨核定的曲谱。

- 《三道滩》和《明月还乡》：返回歌词文本与确认词稿的逐行顺序一致，实际演唱待核。
- 《送青篷》：返回文本覆盖全部 14 行，但把全词顺序重复两遍；与输入要求的两段自然收束不同，是否可用须听审，不能仅因时长完整而通过。
- 《四邻安》：返回文本覆盖全部 14 行，开头额外有“啊”的衬声；领唱与众声应和是否实际成立、衬声是否合适待听审。庙方祈安是人物说辞，不是故事的客观事实。
- 四首原生无损 WAV 仍缺。旧 Seed WAV 属于不同录音，不能补作本轮 Lyria 母版；MP3 解码为 WAV 也不满足原生无损要求。

本批请求数已到四次，估价合计 $0.32，实际账单未查询。本批不再追加调用。随后获得并用完一次豆包短样纠词授权，具体见下一节；没有四首再次重制或最终任务完成确认。

## 词音核对与两句纠词短样

四次 Lyria 真实请求均完整保留已确认词稿，未修改歌词。用户报告的频繁不对应已分别锚定四首准确素材，作品与审阅判断以新修订记录；原 ASSET、原件、旧评论和创作词稿未改。输入核验、意见登记和逐份自动转写在 `.runtime/songs/lyric-alignment/`。

对全部四首运行两轮本地 Whisper 和一轮已开通的豆包录音识别 2.0，均未输入原词或生成返回歌词。识别结果大量偏离原稿，部分彼此不一致或不成句，不能采纳为完整演唱歌词。结合用户实际听审，当前需处理演唱字音和歌词遵循问题，不能仅调整分行、延音记号或重复顺序后宣称一致。

用户随后明确回复“允许一次短样纠词”。尝试 `songs-boat-lyria-diction-pilot-v1` 使用《三道滩》准确 Lyria 原件的 0—11 秒作参考，用现有豆包音频额度重唱“一道险滩水急，船头慢慢行。”，只发起一次请求，实际返回并计费 12 秒。原生 48 kHz、PCM 16-bit、双声道 WAV 的 SHA-256 为 `ba18bdd6a65bf798f84a08e17890ca68789fb6bf0e4f8552e2e7328738285abb`。现有四首 MP3 未替换。

短样位于原歌曲“独立整曲演唱”下的“两句纠词短样（12秒）”素材卡，参考按钮可试听原 11 秒。用户实际对比后明确反馈：“曲调是保留的，但是发音仍然是不准的”。这份短样保住了曲调，但未达到纠词目标，未接受；不再要求用户重听同一版本。真实意见与 `changes_requested` 判断锚定短样修订 `e0641f6c5abaf2782d4e93369fd24587ac13b65dff22f587a8316026fc49677d`，恢复入口为 `.runtime/songs/lyric-alignment/pilot-feedback/receipt.json`。一次生成授权已用完，不自动追加或扩为四首重制。

### 后续纠词方法

此次提示词已经给出目标汉字、部分拼音，并要求只参考曲调；实际听审仍未通过。参考音频可能同时带入原有字音，但这只是对失败原因的推测。已知结论仅是这次参考重唱没有修准发音，不能把接口字幕或提示词中的拼音当作精确发音控制。

当前项目的 Lyria 与 Seed Audio 接口没有暴露逐音符、逐音素编辑参数；[Lyria 官方文档](https://ai.google.dev/gemini-api/docs/music-generation#limitations)也明确当前版本不支持对生成歌曲进行多轮编辑。因此不继续用同样参考及提示词扩做四首。

下一条待验证路线是先把这两句旋律整理成音符与时值，将“一道险滩水急／船头慢慢行”逐字对应，延音只延长该字的韵母，再用可编辑字音的歌声合成引擎重唱。[OpenUtau 的 DiffSinger 支持](https://github.com/openutau/OpenUtau/wiki/DiffSinger-support)和[中文声库的音符／音素控制说明](https://github.com/yqzhishen/qixuan-diffsinger/blob/main/multilingual_usage_guidance/Multilingual_Usage_Guidance.zh-CN.md)证明有这种控制方式；不代表本机已完成部署或这两句已修好。

本机应用目录未发现已安装的 OpenUtau 或 Synthesizer V。尚须准备准确曲谱、选择与角色相符的声库，核对实际组件许可，再验证字音、旋律和自然度。已查“绮萱”声库允许按条款发布合成作品，但对题材、署名和再利用另有约束；不能仅凭“免费”认定适合本剧所有歌曲。[声库使用条款](https://github.com/yqzhishen/qixuan-diffsinger/blob/main/terms_of_use/Terms_of_Use.zh-CN.md) 此路线会更换歌声音色，仍需另定试唱范围；本轮只核查方法，没有安装声库或发起新生成。

[本轮核对说明](../.runtime/songs/lyric-alignment/核对说明.md)列出原段、短样 WAV／MP3、真实授权、实际调用及校验清单。原 11 秒由 MP3 解码裁切，不能称原生无损母版；12 秒另演 WAV 也不补足四首整曲 WAV 要求。原四首试听包保持原样，本轮补充包为 `.runtime/songs/lyric-alignment-review-v1.zip`，文件清单和校验值见 `.runtime/songs/lyric-alignment/packet-receipt.json`。

## 剧中用法与片段

`.runtime/songs/lyria-review/uses-with-audio.json` 保留全部 30 项准确原文用法：20 项发声呈现、10 项提及或可见歌页等非音频事项。每项指向准确 Lyria 整曲修订和原件，保留角色、唱法、歌词行及既有镜头。接口没有返回逐句时间戳，当前逐句范围为空，新旋律的短参考、角色另演与片段尚未产出。不能把旧时间或旧阿蘅清唱套到新旋律。

第一集仍只对接既有 `shot-e01-001 / e01-line-001` 与 `shot-e01-003 / e01-line-002`，分别为舟行起句和省去中间两滩后的归家句；其他集按准确场次交接。缺词停唱、歌娘核字、母亲哼唱、集体领唱和庙戏需要相应表演，不能由同一独立歌手混音强行代替。

历史 Seed Audio 阶段保留八个 6.82—11.74 秒旋律参考、阿蘅 17.686979 秒另演及两段 6.96／10.026979 秒清唱。全部旧片段仅绑定原 Seed 母版，历史用法表为 `.runtime/songs/audio-review/uses-with-audio.json`。阿蘅基础声线引用已获认可原件 `a7d678681c2e490de0a7dc8aca163131f68e196ceda703dc9c9282418c589272`；新演唱不继承认可。未产出人声／伴奏分轨，不把含伴奏片段称为干净配音。

后续先核定新曲调与逐句边界，再裁切短参考，必要时按角色声线另演。Seedance 2.0 已核对的音频参考限制为单段 2—15 秒、同次请求总长不超过 15 秒；制作时还需回查目标平台当前限制。[视频生成接口](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)

## 歌词与剧情依据

用户“好，继续整曲创作”已确认四首曲名、完整词稿、音乐方向与局部剧本同步范围；准确输入在 `.runtime/songs/lyrics-approval.json`。四首共 60 行，原唱词全部保留。此次 Lyria 请求没有改词，独立作品与剧情呈现分别管理。

基线仍为版本四 `7287b25a34d4b0db242ec5688f33349fa6d449874a3c6acb30033e2260cd2686`，17 集、42 场、1,114 个正文块。唯一已确认正文扩写是 E17/s041 b009《送青篷》第一段末新增衣物叮咛与隔水相望四行，完整改后场次在 `.runtime/songs/s041-proposed.md`，其余 21 块不改。第二段受损位置、“过／认旧桥”核字对白、舟行曲省掉两道滩仍成立。E04/s007 母亲选用《送青篷》起句无词旋律属于已确认制作选择，原文未指明曲名的事实保留。

正式剧本版本五、输入锁定及镜头计划尚未发布。歌词同步范围认可不代表新版正式制作输入已发布，原版本四认可不自动转给新版。正式发布须读取最新数据增量同步，不能覆盖并行任务的新方案、母版或评论。

## 实际调用与用途依据

本轮使用 `scripts/lyria_music.py`、Google Gemini Interactions API 的 `lyria-3.5`，从本机环境读取 `GOOGLE_API_KEY`，经既有 Clash `http://127.0.0.1:7897` 串行调用；未改代理配置。工具、前提及离线恢复见 [Lyria 操作说明](lyria-music.md)。每次保留完整 prompt、模型、参数、原始响应、返回文本、文件规格和使用量；凭据不入包。四首无音频参考输入，不冒充已接受人物声线。

首曲按[官方音乐文档](https://ai.google.dev/gemini-api/docs/music-generation)设置 `response_format={"type":"audio"}` 仍返回 MP3，停止后才取得用户补充授权。初始批次快照在 `.runtime/songs/lyria-review/batch.json`，补充决定在 `mp3-continuation.json`；保留初始未提交规格，不改写为已调用。当前[官方价格](https://ai.google.dev/gemini-api/docs/pricing)是每首 $0.08，工具的单次预算预检查不代表平台硬限额。

[Gemini API 条款](https://ai.google.dev/gemini-api/terms)说明 Google 不主张生成内容所有权；使用者仍须遵守合法使用及适用署名要求，输出可能与他人相似，不保证排他性。包注明 AI 生成，原始字节及其中的 SynthID 保留。核验摘要为 `.runtime/songs/lyria-review/use-basis.json`。未代用户向外部平台上架。

## 技术验证与恢复

`.runtime/songs/lyria-review/four-songs-verification.json` 核对四份文件与响应内音频逐字节一致、SHA-256、完整解码、登记原件和历史保存。旧修订、原 264 条评论及 293 条评论事件全部保留；四首各追加一条真实用户重制指令，未伪造听审或接受，也没有自动采用到镜头。

隔离实例导出后，在 `.runtime/songs/lyria-restored-four-songs/` 从空库恢复并复导出，12 张业务表、146 个清单文件完全一致，包含新旧歌曲、完整歌词、旧片段、评论及准确引用。该副本只用于恢复验证，不能覆盖活跃库。

词音反馈与短样登记后另在 `.runtime/songs/lyric-alignment/pilot-restored-review/` 从空库恢复，12 张表、154 个清单文件一致；272 条评论及既有事件保留，四份原整曲素材未变。增量证据为 `pilot-verification.json`；Chrome 已实际打开新增短样、原唱参考及真实用户意见，两段自然播放到尾，见同目录 `browser-verification.json`。播放验证不证明字音修正或保曲调成功。

随后登记用户对短样的实际听审，评论增至 273 条。新的 `pilot-feedback-restored-review/` 空实例与活跃库的 12 张表、154 个清单文件一致；旧评论、事件、原件和实际调用保留。证据为 `pilot-feedback-verification.json`；Chrome 已实际回读短样标题下的意见与当前作品结论，见 `pilot-feedback/browser-verification.json`。本次只补验听审反馈变化，没有重复音频识别、播放测试或调用生成。既有试听 ZIP 保留其交付时快照，最新意见以活跃实例及上述回执为准。

真实 Chrome 验证结果见 `.runtime/songs/lyria-review/browser-verification-four-songs.json`。四首当前 MP3 的播放器读取、从头自然到尾与新旧版本切换有实际页面证据；此为静音传输验证，不是听审。既有时间段评论、参考预览机制的验证保留于 `.runtime/songs/audio-review/browser-verification.json`，输入为旧版 WAV，不扩大为新录音的歌词定位或新片段验收。

当前活跃库为 `.runtime/songs/review-instance/.runtime/review.sqlite3`，39114 端口。服务停止时先确认端口空闲、通用系统仍为 `config/instance.json` 锁定的 `15822ae77d9b6c3851852555a677d11d7adc7c10`，再从 worktree 根目录启动：

```bash
PYTHONPATH="$HOME/codex-path/creative/story-review-desk-python" \
  python3 -m review_desk --instance .runtime/songs/review-instance serve --port 39114
```

继续前先读活跃实例最新评论及准确接受记录。不要重跑 `prepare_review.py`、`register_audio_review.py` 或恢复脚本覆盖活库。本轮登记已全部完成，批次和回执在 `.runtime/songs/lyria-review/registration/`；新修改用新修订，旧 CALL 输入和旧素材原件不变。

旧 Seed 阶段独立包 `.runtime/songs/song-audio-review-v1.zip` 保留 64 个文件及十个片段，SHA-256 为 `6d5e891db94fea10b1233a68263d7f7b712f549b6e5f5069c2b78df10a75b096`。首曲格式停点包 `.runtime/songs/lyria-first-attempt-review.zip` 也保留为历史，不作为四首当前交付。旧记录不能继承为 Lyria 的接受或母版证明。

下一步核定逐字配唱路线的实际工具、声库及两句音符对应，再确定新的试唱范围；已失败的短样保留为历史，不扩用同一方法。随后解决完整实唱歌词、WAV、逐句定位、角色演法与片段，再准备正式增量发布和验收。最终候选与交付流程齐备后才请用户确认完成并集成，然后执行 `_complete`。当前没有正式发布、推送或任务完成。保留 worktree 和分支，正常退出会话后才释放运行锁。
