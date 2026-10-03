# 给歌曲创作会话的交接话术

目标会话：`01a0fd62-c36c-73a0-bed8-9cb2fdc66d67`，歌曲任务 `task-20261002-0004`。下面正文可直接复制给该会话。本轮准备程序并经 Clash 实际试生成，没有自动发送消息。

---

本项目已准备好 Lyria 完整歌曲调用程序，并经 Clash 成功生成一首《三道滩》候选。请在当前四首歌曲任务中承接准确原件并继续听审。Key 从本机环境变量 `GOOGLE_API_KEY` 读取，不要询问或回显 Key，也不要写入项目文件。

程序、操作说明和测试位于主项目。以你的歌曲 task worktree 根目录为基准，入口是：

- `../../../scripts/lyria_music.py`
- `../../../production/lyria-music.md`
- `../../../tests/test_lyria_music.py`

先回读当前歌词、音乐方案、最新评论及 `.runtime/songs/lyrics-approval.json`，沿用已经取得的歌词／方向确认，不重复索要该确认。该工具没有修改你的歌词、方案或候选库。主项目 `../../../.runtime/lyria-preparation/boat-v1-mp3-a03.json` 引用了获确认的《三道滩》歌词及哈希，是成功候选的准确规格；a01、a02 对应此前拒绝的尝试，a03 已成功，均不得复用 ID。

本机能读到 `GOOGLE_API_KEY`，`ffprobe` 可用。2026-10-03 用户完成 VPS 路由配置后，经 Clash `http://127.0.0.1:7897` 的模型查询及《三道滩》整曲生成均成功。原件为主项目 `../../../.runtime/lyria/boat-lyria-v1-a03/audio-01.mp3`：108.695458 秒（约 1 分 49 秒）、44.1 kHz、双声道，2,614,769 字节。SHA-256 为 `b60925b5e5d07d52eaca435c688838463dc7026c3475ff3475cffc9b5eea6df9`，已回读原件确认与回执一致。

同目录保留 `request.json`、`response.json`、`receipt.json`、`provider-text.txt` 和 `text-comparison.json`。服务端返回的 16 行歌词与已确认输入逐行一致；这是文本核对，不代表实际演唱准确。当前 `audio_accepted=false`、歌词听辨与听审均 pending；账单未查询。先承接此准确候选，不重发请求或无故重生成。

链路为 Clash → 香港 VPS → Xray → 后续代理，香港节点本身不代表最终出口。SSH 回读 `vps` 的运行中 Xray 配置已含 `domain:googleapis.com` → `brightdata-isp-claude`，服务已重启且 active；不要再应用准备会话的旧候选，它已失效并删除。本会话没有改运行配置。直接通过 Clash 调用，不需要额外认证参数。运行：

```bash
python3 ../../../scripts/lyria_music.py --check
python3 ../../../scripts/lyria_music.py --check-api --proxy http://127.0.0.1:7897
```

只读查询不生成歌曲；本次生成成功的证据是 a03 的真实响应和原件。不回显凭据，也不擅自改变全局 Clash 节点。继续核对当前歌词、方案及准确输入。

用户已授权本轮经 Clash 的一首试生成，已成功产出；不据此扩大为全部歌曲或不限次数尝试。模型为 `lyria-3.5`，默认 MP3、省略通用 `response_format` 已实测通过；显式 WAV 按音乐专用文档仅设置 `{"type":"audio"}`，实际支持仍待验证。后续确有授权范围内的新请求时，将规格放在你的 `.runtime/songs/requests/`，另开唯一 ID（例如 `boat-lyria-v1-a04`），默认运行只预览；实际提交需要 `--submit --max-cost-usd 0.08 --proxy http://127.0.0.1:7897`。$0.08 是截至 2026-10-03 的每请求官方估价，参数仅做单次成本预检查，不是平台硬限额或总预算。

候选自动保存到运行工作区 `.runtime/lyria/<id>/`，保留实际请求、原始响应、真实音频和回执。每个尝试 ID 唯一，不自动重试；超时／不确定结果先核账和查结果，禁止删除目录或换 ID 自动重发。服务端已返回但本地处理失败，可用 `--recover` 离线恢复。主项目与歌曲 worktree 共用账户锁。

Lyria API 当前只接收文字／图片，不接收阿蘅声音参考，也不支持对已有曲目多轮编辑。完整歌手版与阿蘅、歌娘、母亲等剧中演法分开，固定旋律换声线需另行验证。程序保留真实原件；显式请求 WAV 但收到其他格式时报告格式不符，不把 MP3 转码冒充无损母版。歌词准确、声音质量和用户接受仍需实际听审；该程序不自动登记正式素材、改剧本、生成镜头或完成歌曲任务。

12 条 Lyria 测试及 4 条 Seed Audio 回归通过；经 Clash 的 MP3 整曲生成已成功，实际账单、实际演唱和歌曲听感仍待核验。详见 `production/lyria-music.md`。承接准确候选后按既有流程听审、处理采用；该试生成不代表四首歌已完成或正式素材已接受。如需将工具纳入任务提交，只承接上述脚本、测试和说明及必要交接，保留你工作区现有修改；不要复制主项目 STATE 或覆写歌曲任务状态。
