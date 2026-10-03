# 全剧非歌曲素材：当前交付与继续执行

本任务已准备并登记 255 个图像状态、76 个音色状态关联的方案。当前有 14 张新图、4 份新录音和 18 次真实调用；合格新图覆盖 10/255 个状态，另 245 个状态未调用。声音锁定为 40 个基础身份加 2 项变化，共 42 份新录音；已生成 4 份均获用户听审认可，另 38 个基础身份未生成。任务尚未完成。

用户已认可阿蘅图、旧灯图，以及阿蘅、周掌柜基础音色和阿蘅两份变化音色。六份结论各指向准确原件，见[首批母版认可](master-approvals.json)和[补充音色认可](supplement-approvals.json)。认可不扩大到其他身份、派生候选或镜头采用；Codex 未代点实体采纳。

## 当前待审阅的两张母版

| 准确候选 | 正式入口 | 原件 | 结论 |
| --- | --- | --- | --- |
| 河街·浅滩与对街竹摊修订 | [素材版本 2](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-river-street-day-overall&material_target=e2d88198dac8d2ba0e93293945da858fa0234454dcec88e48583ffb18a8fe02f&material_round=2) | [3584×2016 PNG](../../export/assets/c4ce81f63a44f3cf2880a41661d07fd614021455239d9555c918ab805c8e924d.png) | 浅水河床、缓坡、对街竹摊与门朝河通过目视自检，待用户认可 |
| 李寄·整体返工候选二 | [素材版本 1](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-li-ji-paste-overall&material_target=239727e0849309944d86de9ddd2f4606bda9ef149b6d32001ce3b695e3625b3e&material_round=1) | [2016×2688 PNG](../../export/assets/b84208dd362f2bf0d5668384b5104da3de348619efa3b64e75ffcf3dd7ccb8cd.png) | 减少浆糊／纤维、显出肩颈红印、去掉多余道具，通过目视自检，待用户认可 |

同一版本可有多个真实候选，请按标题与准确原件识别，不以排序或“最新”推定采用。正式系统“实际素材”入口仍有同轮候选 CALL 上下文串用缺陷，以上使用已核对的“需求”入口。修复在隔离系统提交 a6a9e9bbfa2cae97b27dd23b5e49398c69e24a70，尚未部署。

## 已生成与认可的范围

| 内容 | 新原件与用途 | 状态 |
| --- | --- | --- |
| 阿蘅基础图 | [2016×2688 PNG](../../export/assets/6f9cb6a1cabddd8ce34630709e0993ef66c69a66429a330f7cf943107b6c890f.png) | 用户认可，保留现有轻水彩质感 |
| 旧灯基础图 | [2688×2016 PNG](../../export/assets/db9bd8e4707d2533180622e8d44c50b16c171c3518b9da6772247861666e4b26.png) | 用户认可 |
| 阿蘅五种派生形态 | 嗓哑、点名后日常、泪痕、湿衣、湿鞋，各一张新图 | 直接引用认可基础原件，深度 1；自检通过，未逐张获用户认可 |
| 旧灯点亮 | 一张 2688×2016 新图 | 直接引用认可基础原件，深度 1；自检通过 |
| 阿蘅基础音色 | [14.50 秒 WAV](../../export/assets/a7d678681c2e490de0a7dc8aca163131f68e196ceda703dc9c9282418c589272.wav) | 用户听审认可；日常、湿衣等同声线状态准确复用 |
| 周掌柜基础音色 | [19.78 秒 WAV](../../export/assets/78869528db4fbac5d5f8ff3d747317c3fabd7c69d96494029c9967600083c2ec.wav) | 用户听审认可；门外状态准确复用 |
| 阿蘅嗓哑补充 | [9.88 秒 WAV](../../export/assets/1c03d8d5efa4320e75086932bd28489ec714c8eaaa87bbe84daf57c6aafb1c16.wav)；[正式入口](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-a-heng-hoarse-voice&material_target=d1ffb26facaa914964afdca0794ec2c4e492131a85305ed80382729a7e933450&material_round=1) | 用户回复“两份均认可”；湿鞋状态复用完整 0–9.88 秒，不新增调用 |
| 阿蘅泪后哽咽补充 | [4.58 秒 WAV](../../export/assets/190e628c7cac1e564192f5afe87227585d18a9af88d7aaea923bfc7b1c37856d.wav)；[正式入口](http://127.0.0.1:3000/?workspace=materials.workspace&production_object=need-form-a-heng-tears-voice&material_target=d3bfd0187d05a98bb511ee2d8bf865da545214feeba865d32a8446f3e5dbd51e&material_round=1) | 用户回复“两份均认可” |

四份录音均为原始 48 kHz、双声道、PCM 16-bit WAV，合计 48.74 秒。字幕原句与完整播放已核对；听审结论来自用户答复，Codex 未独立听辨，也不把播放器计时或字幕当成听审。

[逐原件自检](representative-review.json)保存全部 18 份原件、SHA-256、规格、用量与问题。14 次图像调用中，李寄首次与河街前三次共 4 张自检未通过，保留记录，不计合格。旧素材、裁切、放大和仅补关联均不计本轮新图。

## 河街浅滩修订与谱系

用户指出门前河水应更多表现为浅滩。意见原文已通过既有评论契约关联首轮准确原图并开启素材版本 2，见[意见与输入](river-feedback.json)和[正式保护证据](../evidence/full-generation-river-feedback-publication.json)。原 264 条评论全部保留，新增一条真实用户意见转录，没有正式测试评论。

第二次河街调用在意见到达前提交，仍为深水、高石岸，未通过。第三次独立文字生成修正水深与缓坡，但竹摊画到米铺同侧。第四次仅以第三次完整原图修正竹摊位置，深度为 1。第三次未获用户认可，该输入只允许修正同一身份、同一完整状态，不允许供其他状态派生。

河街清晨／日间／夜间、道具屋日间／夜间、晾布处、浅滩日间／暮色八份方案已同步此连续性。保留剧本中的下游局部石缝暗水，不扩大成整条深水河道；不改写定稿。若第四次获认可，其后派生深度最多为 2，不能因重新命名或认可而重置谱系。

## 范围、提示词与参考

[source-lock.json](source-lock.json)保存执行入口的正式剧本、对象头、评论与排除项。版本四整版仍为 7287b25a34d4b0db242ec5688f33349fa6d449874a3c6acb30033e2260cd2686，17 集、42 场、1,114 块。133 实体、267 状态中排除四首歌的八个状态，以及两项仅声音、两项仅提及状态，得到 255 个图像目标：126 个基础状态覆盖实体，129 个派生状态，不重复另生实体图。

[recipes.json](recipes.json)逐项保存身份、完整形态、差异、构图、制作选择、来源、参数和引用。当前索引已回读正式准确方案修订，76 条声音关联也逐项指向准确需求；原请求与历史输入锁未改写。见[索引核对](../evidence/full-generation-plan-revision-sync.json)和[首批调用输入锁](call-input-lock.json)。年龄、配色等制作选择与剧本事实分开。

[音色范围](voice-scope.md)锁定 40 基础＋2 变化，76 条状态关联中 34 条复用。用户明确不补问月亮的孩子与屋内唤程差役者，不新增后者实体／状态。七个只有叙述发声、没有逐字台词的身份借用有出处的定稿短句作试读，标明原说话人，不冒充新增对白。未说话成员不拆独立声线。

未获认可的独立身份先生成并审阅基础原件；未绑定的派生保持待绑定。调用时提供准确素材修订、文件组成、SHA-256、区域／片段；OpenArt 实际提交有序 visualReferences 的真实资源 ID 和 URL，豆包两项补充实际提交阿蘅基础 WAV 的 0–14.50 秒，以“@音频1”指代。需求引用不冒充已上传媒体，复用不伪造新调用。

所有 I2I 按最深参考谱系累计、最多两代，换名或加入母版不重置。歌曲、动物声、环境动作声、逐句配音、视频、动态分镜和成片不在本轮范围。

## 渠道与用量

OpenArt CLI 0.1.1 不接受质量参数，原始错误为 unknown flag: --quality，因此使用同一账户和故事项目的连接器提交 high。两次 CLI 结果查询还遇到 error: not authenticated — run openart login，已按原调用 ID 用连接器恢复回执，没有重复生成。项目固定 8K6WcbrPLghSBJXBtWAE，实际模型为 gpt-image-2-5-sunburst。

14 次图片调用余额从 9,979 到 6,168，累计差值 3,811 credits。最高原生尺寸档返回 2016×2688、2688×2016 或 3584×2016，均保存原件，没有放大或声称实际达到 4K。没有切换内置渠道、购买或充值。

豆包补充前实查 43.24 分钟，之后刷新为 33.95 分钟。这是共享余量：本任务两项补充 14.46 秒；歌曲任务记录六次调用 542.686975 秒，合计约 9.29 分钟，与页面变化相符，歌曲用量不算本任务调用。继续前重查余额、调用状态与共享锁。计算和来源见[本批渠道证据](../evidence/full-generation-continuation-channels.json)。

## 正式登记、页面与恢复

每个增量先在隔离库预演核对，再在主项目 publication.lock 内重读全部对象头并登记。旧修订、原件、评论、采用与关系保留。各批次登记包和正式增量证据保存精确写入；存在 applied.json 的批次不得盲重跑。

当前完整 export 与 [replay.json](../replay.json)匹配同一正式快照。空实例恢复核对十二张表、125 个清单文件、54 个本任务受管组成、18 份新原件；快照为 2,262 对象、5,085 修订、265 评论、294 评论事件和 1,175 素材轮次，不能据此覆盖下次活库。

正式 Chrome 已核对六张派生图、李寄返工、河街新旧轮次和意见、准确参考、两份补充完整播放及湿鞋复用。空实例恢复后又实际打开浅滩原图并播放复用声音，见[页面证据](../evidence/full-generation-continuation-browser.json)和[恢复证据](../evidence/full-generation-continuation-recovery.json)。历史参考弹窗保留创建时说明；后来用户认可单独登记为审阅结论，不改写历史素材。

## 继续执行与恢复入口

路径以本任务 worktree 为基准。正式库仍在故事主项目 .runtime/review.sqlite3，唯一任务账本在主项目 .codex-project。通用系统从故事主项目定位同级 story-review-desk-python；本任务隔离系统为 .runtime/review-desk-worktree，分支 codex/task-20261002-0003-material-context。

- .runtime/full-generation/continuation-export：最新正式一致性快照与完整导出。
- .runtime/full-generation/continuation-restored：本批空实例恢复，实际端口 64396，不写正式数据。
- 各 *-publication 目录：before／after、批次回执与 applied.json。结果未知时先恢复回执，不删标记后重复扣费或登记。
- [register_generation_batch.py](../../scripts/register_generation_batch.py)：将真实已完成调用与核对过的原件登记到隔离实例，检查准确方案、提示词、认可或同状态返工依据、谱系和 SHA；不发模型请求。
- [publish_full_generation.py](../../scripts/publish_full_generation.py)：用 --registration 显式选增量、--run-name 选唯一执行窗口，--apply 才写正式库；全部对象头变化即拒绝，不能用旧快照覆盖。
- [verify_full_generation.py](../../scripts/verify_full_generation.py)：用 --before、--after、--registration、--report 只读复核某个已完成增量，不重发生成。

完整空实例恢复沿用 production_review.py 的 recover 命令，目标必须是新的任务 .runtime 目录。服务使用 --port 0 后核对真实监听地址。8 项全剧生成验证、3 项参考授权／谱系验证已通过；未变更的系统修复沿用此前 18 项测试与页面证据。

下一步记录两张新母版的用户审阅并绑定对应派生，其他身份逐个取得基准认可。245 张图与 38 份声音的缺口未标完成。全部任务工作完成后再准备双仓候选、必要正式切换和验收顺序，取得明确完成确认后执行 _complete。当前只做本地阶段提交，不推送、不切换正式服务、不领取其他任务。
