# 歌曲任务恢复入口

用户已明确要求按四首当前制作成果提交、集成并结束任务，同时确认最新《三道滩》的唱词仍不准确。继续执行的是现状交付，不是再次生成或等待同一录音重听；质量问题与任务阶段收尾分别记录。任务账本及完成回执决定是否已受控完成。

## 交付材料

- [production/song-stage/README.md](../production/song-stage/README.md)：当前四首原件、完整歌词、用法、缺口、证据及已准备的发布／恢复顺序。
- [production/songs-review.md](../production/songs-review.md)：当前音频与历史制作的完整交接。新《三道滩》为 113.13625 秒素材版本 3；其他三首仍为首批 Lyria 版本 2。
- [production/song-stage/songs-current-stage.zip](../production/song-stage/songs-current-stage.zip)：可独立试听的 32 文件包。四首 MP3、60 行词稿与实际回执不依赖平台临时链接。
- `production/song-stage/publication-plan.json` 与 `scripts/publish_song_stage.py`：76 个歌曲对象的精确增量，89 个文件在 `export/assets/`；只在本任务工作区归档，不静默覆盖正式导出快照。
- 原活跃歌曲库：`.runtime/songs/review-instance/.runtime/review.sqlite3`，39114 端口。合并正式数据副本的交付验证库：`.runtime/songs/current-state-closeout/release-instance/.runtime/review.sqlite3`，39115 端口。

## 当前恢复顺序

先读 [STATE](../STATE.md)，核对主项目任务账本与最新目标。主目录未提交素材属于 `task-20261002-0003`，由它处理；不要删除、移动、暂存它们来绕过集成检查。歌曲正式增量尚未写入，共享正式库、导出和服务切换等其结束写入后串行操作。

正式库已存在四项撤回包布需求，旧通用系统 `15822ae` 的空库恢复失败；并行任务已提交的 `335168e` 能完整恢复。本任务只将该准确提交归档到 `.runtime/songs/current-state-closeout/system-335168e/` 验证副本，没有代其集成或部署。兼容提交交接后按交付目录中的已准备命令预演并复核输入变化，再继续受控 `_prepare_integration`／`_complete`；旧候选不能充当新候选确认。

六项发布保护测试、正式副本增量演练、12 张表／805 个文件完整恢复、Chrome 四首词稿与意见回读已通过。音频未变的播放测试复用原证据，不重复全套回归。用户没有认可唱词准确，音质仍不标通过；没有歌曲被自动采纳到镜头。完成时间、用户确认和集成／推送结果只写账本及运行回执，确认后不为日志补交代码或文档。

## 不可重发的既有调用

五次 Lyria（首批四次和追加《三道滩》一次）及一次豆包纠词短样的授权均已用完。最新录音、首批录音、12 秒短样都已保存完整原件，无须离线恢复或重发。不要因新的 worktree、会话或任务收尾更换尝试 ID 自动重试。

`GOOGLE_API_KEY` 从本机环境读取，沿已有 Clash 代理调用，不回显或复制凭据。Lyria 工具实际契约见 [production/lyria-music.md](../production/lyria-music.md)。本工作流没有人物参考或逐字音素编辑控制；返回歌词不是实唱转写，MP3 不能转码冒充原生 WAV。OpenUtau／DiffSinger 仅是此前核查的备选路线，未部署。

纠词、原生 WAV、逐句时间和新曲调片段、全部角色演法，以及剧本／制作锁定正式同步仍是后续工作。原始依据、调用、素材、评论、锚点和采用不改写；旧 Seed 片段不能当作新 Lyria 成果。保留任务分支和 worktree，正常退出会话才释放运行锁。
