# 全剧非歌曲素材：代表母版审阅与执行交接

本目录交付 `task-20261002-0003` 的逐项方案和首批六份真实候选。255 个图像状态的方案已准备，音色已准备 40 个基础身份、2 项声音变化补充；又发现两处实际发声漏项，正在请用户确认范围增量。四张图、两份音色已增量登记到正式素材库，原件与调用可追溯。全剧生成、母版认可和最终交付尚未完成。

用户先审代表母版，再推进对应派生。当前没有认可的图像或音色母版，不把生成成功、页面可播放、方案采纳或 Codex 自检当作用户认可。

## 先审阅这些准确原件

正式入口使用需求卡，选择“版本 1”，识别标题含“首轮候选”的新原件。同轮旧候选保留，不以排序或“最新”推定采用。点击原图可放大，声音可播放和按区间评论；直接在会话反馈也可，但需指明具体原件。

| 本轮候选 | 正式需求入口 | 原件与规格 | 自检及当前处理 |
| --- | --- | --- | --- |
| 阿蘅整体图 | [日常洗旧青衣](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-a-heng-blue-overall&material_target=e0e3e576207967838b531d30c69e5aa2841d44b7312818bc107c8f06d1ee7145&material_round=1) | [PNG](../../export/assets/6f9cb6a1cabddd8ce34630709e0993ef66c69a66429a330f7cf943107b6c890f.png)，2016×2688 | 全身、衣着、书和米袋可辨；水彩布纹需用户决定是否简化，待认可 |
| 李家旧灯 | [未点灯的基础形态](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-old-lantern-base-overall&material_target=c04b3877a5421432067f5bb24be40d19bf1af4b1e2325462de2f884df4e2c3af&material_round=1) | [PNG](../../export/assets/db9bd8e4707d2533180622e8d44c50b16c171c3518b9da6772247861666e4b26.png)，2688×2016 | 轮廓、提梁、灯芯和补纸可辨；纸纹偏明显，待认可 |
| 李寄整体图 | [劳作后未擦手](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-li-ji-paste-overall&material_target=88d580f065b9fc5f24718b42308df0cb490b90fd0cc083c6687efa85a99c5927&material_round=1) | [PNG](../../export/assets/bdcf59f03528e763188d87d46a9fe6134363634aa6256cadc1dc364d505fb6b0.png)，2016×2688 | 自检不通过：浆糊／羊毛过量、肩红印被遮、多余桌桶和纸堆；须修订 |
| 河街整体图 | [日间河街](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-river-street-day-overall&material_target=c571a20461c9fefb7a8a7c2c62c1d4bb74329bcfeb075007d484b8195fb64421&material_round=1) | [PNG](../../export/assets/9ea910cbdf141babe3b87f7054b84701de70721c0889977cdf0a6c52358f44f0.png)，3584×2016 | 自检不通过：道具屋门朝街而非河、额外招牌、瓦片墙纹偏密；须修订 |
| 阿蘅基础音色 | [基础音色](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-a-heng-blue-voice&material_target=e522f05e989232e8323608cc74addd94b5e542c15c2d69692109c5fdd3e78ecb&material_round=1) | [WAV](../../export/assets/a7d678681c2e490de0a7dc8aca163131f68e196ceda703dc9c9282418c589272.wav)，14.50 秒 | 待实际听辨及用户认可 |
| 周掌柜基础音色 | [基础音色](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-zhou-base-voice&material_target=19c210a047952c1e82036d6ba68c987a2dca01e25802b4b8b1ed7ea78425e00c&material_round=1) | [WAV](../../export/assets/78869528db4fbac5d5f8ff3d747317c3fabd7c69d96494029c9967600083c2ec.wav)，19.78 秒 | 待实际听辨及用户认可 |

两份新声音都是 48 kHz、双声道、PCM 16-bit。回执字幕与试读原句一致，浏览器已操作播放至结尾、无媒体错误；这些检查不能确认实际发音或角色声线。`representative-review.json` 的听辨者仍为空。听审后记录听辨者、准确文件、问题与结论，不用播放器计时替代。

正式系统目前有一处候选卡缺陷：从“实际素材”进入、同轮有多个素材身份时，其他候选可能显示入口素材的实际提示词；原件和数据库调用没有被改写。上表的“需求”入口已实测分别显示准确调用。修复已在隔离系统工作区完成并验证，尚未部署，见下文。

## 范围、依据和待绑定输入

以执行时正式库为准，未用初始抽取批次覆盖当前内容。[source-lock.json](source-lock.json) 保存准确剧本／分集修订、所有对象头、评论校验、与初始抽取的 602 项当前记录差异及排除项。整版仍是版本四 `7287b25a…2686`，17 集、42 场、1,114 块；正文未改写。

| 交付内容 | 数量与含义 | 当前可执行边界 |
| --- | --- | --- |
| 图像基础状态 | 126 份，覆盖 126 个需要图像的实体 | 独立文字生成，无虚构图片参考；逐个生成并审阅基准 |
| 图像派生状态 | 129 份，与基础合计 255 个状态 | 每份写明完整形态及差异；获认可母版原件和准确修订尚待绑定，不能直接调用 |
| 基础音色 | 40 个实际说话身份 | 30 个明确发声标签、10 个在叙述／集体身份内区分的发声者；独立音色先审基准 |
| 声音变化 | 阿蘅嗓哑、泪后哽咽，共 2 份 | 依赖认可后的阿蘅音色；嗓哑覆盖嗓哑、劳累湿鞋两个状态 |
| 音色状态关联 | 76 条，其中 34 条复用 | 不是 76 次录音；每条指明准确角色／状态和复用原因 |
| 待确认漏项 | 第 8 场问月亮的孩子、第 35 场屋内唤程差役的人 | 建议各增一基础音色，变为 42 基础＋2 补充；后者需新建仅声音身份／状态，图像保持 255 |

从 133 实体、267 完整状态中排除四首歌曲的八个状态，再排除窗外唤李寄归家者、台鼓只闻声、小满和许家女儿四个无图像状态，得到 255 个目标。基础状态已覆盖实体，不另增实体图。旧素材、裁切、放大、失败调用和关联补全均不计本轮新图。

[recipes.json](recipes.json) 是逐项方案，包含身份、完整状态、制作造型、构图比例、连续性、参数、来源及参考约定；[音色范围表](voice-scope.md)便于逐身份核对，准确修订与完整样句仍在方案中。年龄、颜色等制作选择与定稿事实分开，未新增剧情状态。`form-paste-wool-paste` 的既有制作描述误写成手上残留物，本轮方案依第 3 场第 5—6 块改为碗／刷中的湿浆糊；没有改写旧状态历史。

七个只有间接发声叙述、没有逐字台词的身份，明确借用有出处的定稿短句作试读，并标原说话人；不冒充该角色新增对白。未说话的集体成员不拆独立声线。李寄第 33 场的无词哭声、孩子哭叫、动物声、环境动作声及歌曲均不另制本轮音色；孙六的短暂咳嗽和普通喘息属于表演，阿蘅母亲持续虚弱已在基础音色描述中，不另造固定声音身份。最终声音范围仍待两处漏项答复。

参考绑定规则如下：

1. 本轮四张图和两份基础声音均是独立生成，没有提交图像／声音参考。真实输入锁保存在 [call-input-lock.json](call-input-lock.json)；李寄请求中的 `source_lock_sha256=2c9c4bec…7832` 是 JSON 按键排序、紧凑序列化后的 UTF-8 内容校验，计算约定为 `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))`。含缩进的文件本身 SHA-256 为 `9e46295b6850b62ee76eef0efcb452ae2fe9684e50f47de0940e4e7b657c22c5`，二者用途不同。后续发现声音漏项更新了方案输入锁，但没有倒改已发生的请求。
2. 图像派生的方案输入先指向准确基础需求，标记 `pending_approved_master`。取得用户认可后换成准确 ASSET 修订、原件组成、校验值与实际区域；OpenArt 实际传 `params.visualReferences`，按顺序提供 `type: image`、真实 `id`、`url`、`label`。不把需求引用或文件名占位当已上传图片。
3. 音色补充的 `@音频1` 指向用户认可的基础 WAV 全段（不超过 30 秒）；超长时记录裁取范围、原件校验及实际片段。按已核对的豆包接口提交音频数据，不只写一段“参考母版”。同声线复用保留准确原件，不伪造新调用。
4. 图像以干净母版为起点，优先一代，最深输入累计不超过两代。多参考按最深谱系计数，换名或加入母版不重置。渠道改变时重新核对参数、实际输入约定、身份和风格，再调用。

## 渠道、尺寸和真实用量

OpenArt 项目为“李寄斩蛇 · 把灯带回家”，显式项目 ID 见 `../../config/openart.json`。CLI v0.1.1（`85fa0ad`）返回 `unknown flag: --quality`，无法按要求提交 high；已向用户说明并使用同一平台连接器，模型实际标识为 `gpt-image-2-5-sunburst`。参数为 high、最高暴露档位 `4k`、单张 PNG、关闭自动改写，宽高比按人物 3:4、道具 4:3、河街 16:9。平台链接只用于下载与追溯，原件已本地受管。

请求档位不等于像素尺寸，本轮按用户已确认的最高原生返回尺寸验收，不放大。四次调用前后余额 9,979→8,914，批次差值 1,065 credits；单次 250／250／250／315 是调用前报价，完成回执没有逐次实扣字段，不把报价编造为独立结算。未切换内置图像渠道，也未新增付费渠道或购买。工具实际参数表、额度观察与估算边界见 [渠道证据](../evidence/full-generation-channels.json)。

豆包 `seed-audio-1.0` 登录后页面显示 43.81 分钟；保守按 2,628 秒安排本轮，实际两个 WAV 合计 34.28 秒。2,593.72 秒只是保守扣减估算，不是平台刷新余额。用户已安排本任务先生成代表音色，歌曲任务暂不调用；后续重新核对共享余量和互斥安排，不复制或回显凭据。请求未知时先恢复回执，禁止盲重试扣费。

| 调用 | 平台调用／历史 ID |
| --- | --- |
| 李寄图 | `lkiNeGMdUC2PJzagAyLv` |
| 阿蘅图 | `T7CTclFPkd5ELP0e21RY` |
| 旧灯图 | `3gZjythbNQxCL4aSUXur` |
| 河街图 | `kicl0xvZlCGnhODCLkph` |
| 阿蘅声音 | `68f2cc50-b240-47b9-9ace-d8b01bdbd003` |
| 周掌柜声音 | `dbebf701-d121-470e-90ac-8eeeee0f2259` |

真实请求在 [requests](../requests/)、回执在 [receipts](../receipts/)；六份原件与各自请求／回执共 18 个受管文件，其 SHA-256、准确实体／状态／需求、实际参数、谱系、用量与自检均在 [registration.json](registration.json) 及正式 CALL／ASSET 中。

## 已登记和实际验证

先在隔离库校验三批增量，再在共享发布锁内核对正式全部旧对象头，顺序登记方案、真实调用／候选、完成回执。没有写采纳或用户审阅结论；自检说明不冒充用户意见。新增 60 个对象、349 个修订，全部旧 4,671 修订和 264 评论保留；新增 48 个首轮需求，不把方案内部修订伪造为新的素材轮次。

| 核验 | 证据与边界 |
| --- | --- |
| 输入、范围、声音样句、最高原生尺寸规则与真实请求／原件一致性 | `tests/test_full_generation.py` 5 项通过；声音调用程序原有 4 项通过；[包校验](../evidence/full-generation-package-check.json)核对文件与本地链接 |
| 正式增量保护 | [full-generation-formal-publication.json](../evidence/full-generation-formal-publication.json)，限定需求／实际调用／候选；旧历史、评论、来源、配置和轮次保留 |
| 完整导出与空实例恢复 | [full-generation-formal-recovery.json](../evidence/full-generation-formal-recovery.json)，十二张表相同、89 清单文件及 18 新文件校验通过；没有隔离测试评论 |
| 真实页面 | [full-generation-browser.json](../evidence/full-generation-browser.json)，正式预览与新声音播放、恢复后原图与播放、隔离音频选段／评论和轮次；不代表用户听审或素材认可 |
| 候选卡调用信息修复 | 系统隔离分支 `codex/task-20261002-0003-material-context`、本地提交 `a6a9e9bbfa2cae97b27dd23b5e49398c69e24a70`，18 项材料相关测试通过；实际素材入口的新旧阿蘅音色与三份李寄图各读自己原调用，尚未部署 |

暂存检查仅在四份连接器原始完成回执及其四份导出副本报告文件末尾空行；为保留已正式登记的原始字节和 SHA-256，不清理这些原件。八个准确路径及配对校验见包校验记录，其余暂存文件的空白检查通过。

目前 251 个图像状态尚未调用，另两张不合格、两张待用户认可；已准备的 42 个音色新生成项中 40 个未调用，两份待听审。两处声音漏项尚未计入上述分母。恢复成功与正式登记不等于完成 255 个合格原件，更不等于镜头采用或成片就绪。

## 继续执行与恢复入口

以下路径以本任务工作区为基准；正式业务库始终在故事主项目。通用系统真实主仓从故事主项目定位 `../story-review-desk-python`，不要从嵌套 worktree 套用该相对路径。本任务的隔离系统检出为 `.runtime/review-desk-worktree`，不设第二份任务账本。

- `.runtime/full-generation/formal-input.sqlite3`：本轮生成前只读正式快照。
- `.runtime/full-generation/publication/before.sqlite3`、`after.sqlite3`、`batch-*.json`、`applied.json`：真实正式增量窗口与回执。已经成功发布，不重跑。
- `.runtime/full-generation/formal-export`、`formal-restored`：正式导出与空实例恢复副本。`review` 含测试评论，仅用于技术核验；`isolated-restored` 是更早方案的技术恢复，均不能覆盖正式库。
- `scripts/prepare_full_generation.py --snapshot SNAPSHOT --output DIRECTORY`：只读编制方案。后续先备份最新正式库、展示对象与范围差异；不能覆盖已提交调用所用输入锁。
- `scripts/register_full_generation.py --system SYSTEM --instance ISOLATED_INSTANCE`：本阶段六份代表项的登记编制器，只允许任务 `.runtime` 内隔离实例。它不是任意后续批次的一键生成器，后续须按新原件扩展准确增量；没有真实调用则不创建占位 CALL／ASSET。
- `scripts/publish_full_generation.py --system SYSTEM --instance FORMAL_INSTANCE`：本阶段发布前置检查；`--apply` 才写正式库。检查完整对象头、独占 `publication.lock`、复制校验原件、按批次登记并回读。存在此前尝试或 `applied.json` 即拒绝；中断先看批次回执和正式当前头，不删除回执后盲重跑。

复核已经发生的发布可只读运行：

```bash
python3 scripts/verify_full_generation.py \
  --before .runtime/full-generation/publication/before.sqlite3 \
  --after .runtime/full-generation/publication/after.sqlite3 \
  --registration production/full-generation/registration.json \
  --report .runtime/full-generation/publication/rechecked.json
```

完整恢复沿用 `../README.md` 中的 `production_review.py recover`，目标必须是新隔离目录。服务启动先核对端口，或使用 `--port 0` 由系统分配，再读取实际监听地址；本轮修复版使用 56314。曾尝试的 39114 已被其他任务占用，未停止、修改或测试写入该实例。

下一步先收用户对准确原件的意见、处理两处声音范围漏项，再修订失败图及绑定获认可母版。声音复用、派生图都重查准确输入和共享额度。全部必要工作完成后，双仓各自提交，准备最终受控集成顺序、候选与影响范围验证，再请用户确认完成；当前仅阶段提交，不执行 `_complete` 或推送。正式系统修复部署须另在该受控顺序内串行办理。
