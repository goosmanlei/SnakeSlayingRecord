# Lyria 歌曲任务恢复入口

歌曲任务 `task-20261002-0004` 已合入主干 `ebda293d674410b1d483e7fdaae1781c181662e1` 的 Lyria 工具，并在自己的工作区完成四首 MP3 重制候选。当前交付、准确版本及恢复步骤以 [四首歌曲交接](../production/songs-review.md) 和 [STATE](../STATE.md) 为准；不能按早期单曲接入话术重新发起生成。

## 当前材料

以歌曲任务 worktree 根目录为基准：

- 工具及使用方法：`scripts/lyria_music.py`、`production/lyria-music.md`；12 条 Lyria 与 4 条 Seed Audio 回归在合并后的代码通过。
- 四次真实调用：`.runtime/lyria/songs-boat-lyria-wav-v1-a01/`，以及 `songs-blue-awning-lyria-mp3-v1-a01/`、`songs-welcome-lyria-mp3-v1-a01/`、`songs-blessing-lyria-mp3-v1-a01/`。
- 授权快照、原件核验、登记修订、空实例恢复和浏览器证据：`.runtime/songs/lyria-review/`。
- 可独立试听的交付包：`.runtime/songs/song-lyria-review-v1.zip`。
- 活跃隔离库：`.runtime/songs/review-instance/.runtime/review.sqlite3`，39114 端口。不要用恢复实例或旧导出覆盖活跃库；继续前先读取新评论。

用户已确认词稿、曲名、音乐方向及局部剧本同步范围，随后授权四次 Lyria 重制。首曲请求 WAV 却返回 MP3 后，用户确认“先完成四首 MP3 试听，WAV 母版保持待解决”。本批已完成四次，估价 $0.32，账单未查询，无追加重试授权。四首均待听审，原生 WAV 与新旋律对应的剧中片段仍未完成。

## 工具与保护边界

本机环境读取 `GOOGLE_API_KEY`，不询问、回显或写入 Key。沿用户已经准备的 Clash `http://127.0.0.1:7897` 调用，不改全局节点、VPS 路由或代理配置。模型为 `lyria-3.5`；只读 `--check-api` 成功不能代替真实生成证据。

每个尝试 ID 唯一。保留完整请求、原始响应、真实文件编码、歌词文本和回执；不删除目录或换 ID 自动重试。跨 worktree 共用账户锁。服务端已返回而本地处理失败才考虑工具的离线 `--recover`，本轮四首均已保存完整原件，无须恢复或重发。

主项目早期试曲 `../../../.runtime/lyria/boat-lyria-v1-a03/audio-01.mp3` 为另一准确录音：108.695458 秒，SHA-256 `b60925b5e5d07d52eaca435c688838463dc7026c3475ff3475cffc9b5eea6df9`；此前 a01、a02 是被拒请求。以上历史不改写、不复用 ID，也不与本轮 123.533 秒《三道滩》混淆。

Lyria 本工作流不支持人物音频参考或同一录音多轮编辑。原生 MP3 不转为 WAV 冒充无损；旧 Seed WAV 不替代新曲母版；返回歌词不是实际音频转写，更不能代替听审。当前《送青篷》返回文本重复全词两遍，《四邻安》多开头衬声，须随实际录音审阅。

先完成听审与准确旋律确认，解决无损母版和逐句定位，再处理各角色演法、短参考及剧本／制作依赖同步。正式库、公开导出、3000 服务与最终集成仍需串行协调；当前阶段不写正式数据、不推送、不运行 `_complete`。
