# Lyria 歌曲任务恢复入口

歌曲任务 `task-20261002-0004` 已合入主干 `ebda293d674410b1d483e7fdaae1781c181662e1` 的 Lyria 工具，在自己的工作区完成首批四首 MP3，并按新的单次授权追加《三道滩》吐字调整整曲。当前交付、准确版本及恢复步骤以 [四首歌曲交接](../production/songs-review.md) 和 [STATE](../STATE.md) 为准；不能按早期接入或生成授权重新发起调用。

## 当前材料

以歌曲任务 worktree 根目录为基准：

- 工具及使用方法：`scripts/lyria_music.py`、`production/lyria-music.md`；12 条 Lyria 与 4 条 Seed Audio 回归在合并后的代码通过。
- 首批四次真实调用：`.runtime/lyria/songs-boat-lyria-wav-v1-a01/`，以及 `songs-blue-awning-lyria-mp3-v1-a01/`、`songs-welcome-lyria-mp3-v1-a01/`、`songs-blessing-lyria-mp3-v1-a01/`。
- 授权快照、原件核验、登记修订、空实例恢复和浏览器证据：`.runtime/songs/lyria-review/`。
- 可独立试听的交付包：`.runtime/songs/song-lyria-review-v1.zip`。
- 最新《三道滩》：`.runtime/lyria/songs-boat-lyria-diction-v2-a01/audio-01.mp3`，113.13625 秒，素材版本 3；记录与恢复在 `.runtime/songs/lyria-boat-diction-v2/`，独立单曲包为 `.runtime/songs/boat-lyria-diction-v2-review.zip`。首批包中的舟行曲仍为旧录音。
- 活跃隔离库：`.runtime/songs/review-instance/.runtime/review.sqlite3`，39114 端口。不要用恢复实例或旧导出覆盖活跃库；继续前先读取新评论。

用户已确认词稿、曲名、音乐方向及局部剧本同步范围，随后授权四次 Lyria 重制。首曲请求 WAV 却返回 MP3 后，用户确认“先完成四首 MP3 试听，WAV 母版保持待解决”。首批四次估价 $0.32，账单未查询；用户试听后报告四首频繁词音不对应，均未接受。随后一次豆包两句纠词短样实际生成 12 秒，用户确认曲调保留、发音仍不准确。

用户之后另行授权“先追加生成一首试一下”，明确选择“继续用 Lyria 重生成《三道滩》”。已完成这一次，估价 $0.08，无重试；输入十六行歌词未改，加入逐句拼音与较少拖腔要求。接口返回第九句少“险”，无提示词的本地识别也有多处差异，不能据此宣称纠词成功。最新录音待实际听审，原生 WAV 整曲与剧中片段仍未完成。歌曲任务五次 Lyria 和这次豆包短样的授权均已用完。

## 工具与保护边界

本机环境读取 `GOOGLE_API_KEY`，不询问、回显或写入 Key。沿用户已经准备的 Clash `http://127.0.0.1:7897` 调用，不改全局节点、VPS 路由或代理配置。模型为 `lyria-3.5`；只读 `--check-api` 成功不能代替真实生成证据。

每个尝试 ID 唯一。保留完整请求、原始响应、真实文件编码、歌词文本和回执；不删除目录或换 ID 自动重试。跨 worktree 共用账户锁。服务端已返回而本地处理失败才考虑工具的离线 `--recover`，首批四首和最新追加整曲均已保存完整原件，无须恢复或重发。

主项目早期试曲 `../../../.runtime/lyria/boat-lyria-v1-a03/audio-01.mp3` 为另一准确录音：108.695458 秒，SHA-256 `b60925b5e5d07d52eaca435c688838463dc7026c3475ff3475cffc9b5eea6df9`；此前 a01、a02 是被拒请求。以上历史不改写、不复用 ID，不与本任务素材版本 2 的 123.533 秒或版本 3 的 113.13625 秒《三道滩》混淆。

Lyria 本工作流不支持人物音频参考或同一录音多轮编辑。原生 MP3 不转为 WAV 冒充无损；旧 Seed WAV 不替代新曲母版；返回歌词不是实际音频转写，更不能代替听审。首批四次与最新追加请求的歌词均未改动；机器转写仍无法形成可靠实唱词稿，不能用机器误识别更新正式歌词。

原 11 秒与纠词 12 秒短样的听审已完成，失败意见及判断在 `.runtime/songs/lyric-alignment/pilot-feedback/`；不要再请求用户听同一版本，不重新提交或扩用这次参考重唱。OpenUtau／DiffSinger 是此前查过的备选路线，本次用户明确选择继续 Lyria，没有部署它。

下一步听审素材版本 3 的新《三道滩》。最新登记、空库恢复及实际 Chrome 播放证据均在 `.runtime/songs/lyria-boat-diction-v2/`；12 张表、163 个清单文件和 274 条评论核对一致，未写测试意见。已完成的准备、登记、恢复和打包脚本不得重跑覆盖活库或旧证据。后续再解决无损母版、逐句定位、角色演法和剧本同步。正式库、公开导出、3000 服务与最终集成仍需串行协调；当前阶段不写正式数据、不推送、不运行 `_complete`。
