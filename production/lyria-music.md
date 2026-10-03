# Lyria 完整歌曲生成

本工具供歌曲创作任务在自己的工作区生成完整歌曲候选，继续使用已有歌词、音乐方案、听审和素材登记流程。它不写正式数据库，也不更新剧本或自动接受音频。程序为 `scripts/lyria_music.py`，仅使用 Python 标准库；提交前需要可用的 `ffprobe`。

## 凭据与当前验证

凭据从当前进程的 `GOOGLE_API_KEY` 读取，不写入请求、回执或日志。不要在聊天中提供 Key，不要写进规格文件。2026-10-03 本机已确认变量存在、`ffprobe` 可用。

用户提供的认证 HTTP 代理 `http://brd.superproxy.io:44445` 已通过 curl 和本程序分别查询 Google 模型元数据，均返回 HTTP 200，模型名为 `models/lyria-3.5`；该入口尚未验证歌曲生成。

2026-10-03 用户补充 VPS 路由后，SSH 回读运行中 Xray 配置已有 `domain:googleapis.com` → `brightdata-isp-claude`，服务已重启且 active。链路为 Clash → 香港 VPS → Xray → 后续代理；不能凭 Clash 节点名称判断最终出口。本会话没有改运行配置，先前远端临时候选已删除，无需再应用。

经 Clash `http://127.0.0.1:7897` 的模型查询和《三道滩》整曲生成均成功。候选在主项目 `.runtime/lyria/boat-lyria-v1-a03/audio-01.mp3`：108.695458 秒、44.1 kHz、双声道、原始 MP3，哈希与回执一致。服务端返回的 16 行歌词与输入逐行相同，证据为同目录 `text-comparison.json`；实际演唱和听感仍待听审，账单未查询。先前 a01 因显式 WAV MIME 不支持、a02 因地区限制被拒绝，所有已提交 ID 均不可复用。

本机通过 Clash 调用不需要额外代理认证。若直接使用认证代理，用户名与密码通过私有环境变量 `LYRIA_PROXY_USER`，值为 `用户名:密码`，再用 `--proxy-user-env LYRIA_PROXY_USER` 选择它；不要把值放在命令行、规格或回执中。本会话只曾临时注入直接代理检查进程，未永久配置或写入项目。本工具不设置全局代理。

本工具按当前官方 `lyria-3.5` 与 Interactions API 契约准备，默认 MP3 已真实生成验证；WAV 请求按音乐文档只设置 `response_format={"type":"audio"}`，歌曲任务本轮首曲按此参数实际返回 MP3，回执为 `completed_format_mismatch`，原生 WAV 尚未取得；不添加被实测拒绝的通用 MIME／delivery 字段。真实费用尚待核账。官方入口：[音乐生成](https://ai.google.dev/gemini-api/docs/music-generation)、[接口字段](https://ai.google.dev/api/interactions-api)、[价格](https://ai.google.dev/gemini-api/docs/pricing)。

## 工作区与输入

以下命令从已合入工具的歌曲任务 worktree 根目录执行：

```bash
python3 scripts/lyria_music.py --check
python3 scripts/lyria_music.py --check-api --proxy http://127.0.0.1:7897
# 已验证的认证代理；LYRIA_PROXY_USER 必须已在执行进程中配置。
python3 scripts/lyria_music.py --check-api \
  --proxy http://brd.superproxy.io:44445 --proxy-user-env LYRIA_PROXY_USER
```

`--check` 只查本机前提；`--check-api` 只 GET 模型元数据，不生成、不计音乐生成费用。成功查询也不等于已验证付费生成。未指定 `--proxy` 时使用 Python 的系统／环境代理设置；显式参数支持 HTTP 代理，认证只能通过 `--proxy-user-env` 指定环境变量，不允许把凭据嵌入 URL。不修改 Clash 配置或全局节点；不要传 SOCKS URL。

每个实际尝试使用独立 JSON 规格。候选规格、方向文本、请求、回执和输出均留在本机 `.runtime/`。示例：

```json
{
  "id": "boat-lyria-v1-a04",
  "song_entity_id": "entity-boat-song",
  "model": "lyria-3.5",
  "lyrics_file": "../lyrics/boat.txt",
  "lyrics_sha256": "填写该准确歌词文件的SHA-256",
  "directions_file": "boat-directions.txt",
  "output_format": "mp3"
}
```

`lyrics_file` 和 `directions_file` 以规格文件所在目录为基准；哈希是原文件字节的 SHA-256，可分别指定 `lyrics_sha256`、`directions_sha256`，不匹配则拒绝请求。程序自动在音乐指令后附完整歌词。方向文本包含语言、段落、节拍／速度、声乐、编配、情绪与目标时长，按已确认方案编制；目标时间写入提示词，不伪装成有保证的 API 时长参数。未知字段会被拒绝，不能夹带音频参考。

主项目 `.runtime/lyria-preparation/boat-v1-mp3-a03.json` 记录成功候选的准确规格，引用歌曲任务获确认的歌词及哈希；`boat-v1.json` 和 `boat-v1-mp3.json` 对应此前拒绝的两次尝试。不要复用已提交的尝试 ID。另开尝试前核对最新评论、当前方案及实际范围；规格和候选不公开跟踪。

## 预览、提交与输出

```bash
# 默认离线预览完整输入，不创建调用目录，不读取 Key，不联网。
python3 scripts/lyria_music.py .runtime/songs/requests/boat-lyria-v1-a04.json

# 只有实际生成范围和预算已明确时，才执行这一条。
python3 scripts/lyria_music.py .runtime/songs/requests/boat-lyria-v1-a04.json \
  --submit --max-cost-usd 0.08 \
  --proxy http://127.0.0.1:7897
```

`--workspace` 默认当前工作目录，必须指向歌曲 task worktree 根目录；即使程序从主项目调用，输出也在该工作区的 `.runtime/lyria/<id>/`。各 worktree 通过共同 Git 仓库下的 `.runtime/lyria/account.lock` 串行提交；占用时直接退出，不等待或抢占。

`--max-cost-usd` 必须明确提供，至少覆盖本工具按 2026-10-03 官方价格记录的每请求 $0.08 估算。它只是本次单请求的预检查，不是平台侧硬限额或批次累计预算；实际价格、账单及总尝试次数由执行会话核对。歌曲任务后来获得四首重制授权，已完成四次调用；首曲格式不符后又获补充 MP3 授权。此批额度已用完，不据此追加尝试。当前四首、准确原件及待听审项见 [整曲交接](songs-review.md)。

每次只 POST 一次，不做自动重试，也不自动换模型。尝试目录已存在时拒绝再次提交；超时、连接中断或不确定服务错误记录 `unknown`，不能通过删除目录或换 ID 自动重发。先核对服务端／账单和已有结果，再决定是否另开尝试。

调用目录保存：

- `request.json`：实际完整模型输入，不含 Key；准确来源文件与哈希在回执中。
- `response.json`：原始完整响应，保留歌词、结构、音频数据及实际模型信息。
- `audio-01.wav` 或实际格式后缀：服务端返回的原始音频字节，不转码、不升采样、不混接多个块。
- `provider-text.txt`：服务端返回的歌词／结构文本（若有）；不能代替对实际演唱的听辨。
- `receipt.json`：实际状态、文件哈希、容器、编码、采样率、声道、时长、使用量及待听审状态。

默认请求 MP3，保留原始 MP3 字节。显式选择 WAV 时，用 `ffprobe` 核对实际 PCM WAV；若服务端返回其他格式，保留真实原件并以 `completed_format_mismatch` 退出，不将 MP3 转码冒充无损母版。返回多个音频块分别保存，不擅自假设是连续片段或分轨。使用 `store=false`，不维护服务端多轮会话；长请求默认超时 600 秒。

服务端成功但本地解码／探测失败时，可在原响应仍在的条件下离线恢复，不再次计费：

```bash
python3 scripts/lyria_music.py \
  --recover .runtime/lyria/boat-lyria-v1-a03
```

恢复只处理本工作区对应目录中的 `response.json`。HTTP 拒绝时保存脱敏错误；没有响应的 `unknown` 不可通过恢复编造产出。

## 后续制作与验收

歌曲会话先核对已经确认的歌词和当前意见，不重复索要已取得的歌词认可。Lyria API 当前不支持音频参考与多轮编辑；不能承诺固定同一旋律只换角色声音，不能把短曲试唱与整曲重生成视为同一旋律，也不能把返回的文本当成实际歌词核对通过。

音频实际产出后逐句听辨中文歌词、咬字、旋律、结构、开头结尾和噪声；完整歌手版本与阿蘅、歌娘、母亲等剧中演法分别管理。原生格式验证不替代听审。接受的整曲与短片段按既有后台接口登记，引用准确母版与时间范围；本工具不自动发布正式素材或生成镜头。

离线验证：`python3 -m unittest tests.test_lyria_music -v`，覆盖无网络预览、准确歌词哈希、原件保留、格式不符、超时防重发、离线恢复和跨 worktree 共用锁。
