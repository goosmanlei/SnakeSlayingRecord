# 视听三部分任务：证据与样例

先读 [完整任务规格](../audiovisual-three-part-review-task.md)。本包交接用户已定的产品终态、父会话调查与拟定样例，不代表视听模块已改造、设计已采纳或正式数据已迁移。

## 文件与证据边界

- [调查正文](av-simplify-20261010.md) 和 [准确数据](av-simplify-20261010.json) 从主项目 `.runtime/system-review/findings/` 同名文件按原始字节复制；其中“当前”、评论数量及旧认可数量只属于调查时点，执行时重新核对最新准确数据和写入者。原记录中的相对源码和输入路径以故事主项目或已注明的 desk 仓库为基准。
- [可操作拟定样例](av.html) 来自主项目 `.runtime/system-review/findings/simplification-samples/av.html`，只扩充顶部边界说明，内嵌准确数据、Prompt 与原交互保持不变。可直接用浏览器打开，不访问业务接口；它不是产品实现或迁移程序。原调查正文提到的 `simplification-samples/av.html` 在本包对应此文件。
- 父会话已实操 ASH001 首帧／视频 Tab 与 ASH080 状态对照，并独立审读规格。本轮引用该已有证据，不冒充本澄清会话重新完成这些操作。
- 本澄清会话已逐张查看三张用户原始截图、核对 PNG 头、实际尺寸及 SHA-256；读回样例源码和证据。尝试在 Chrome 打开本 worktree 的 `file://` 样例被浏览器策略拒绝：仅允许 HTTP／HTTPS，且禁止绕过。没有改换通道重试；本轮文件一致性检查不算浏览器验收。
- ASH001 和 ASH015 的叙事目的、ASH080 的状态分组均为拟定方案，不冒充已采纳稿；有效范围最终须逐集理解和回读，不能按样例句式批量填充。
- ASH001 样例展示首帧 M2974 → 视频 M2975，主机位 M2973 仅是上游参考；JSON 记录调查时视频五项输入。ASH080 只演示两项既有需求按关键状态分组，不展示完整生成流程；按钮没有真实共用素材卡、保存和数据迁移能力。样例提示层也未完成可移入阅读要求。完整返回、保存、键盘与提示层、准确多入口及恢复仍是执行任务的验收，不因原型存在而视为已完成。
- 本轮未观看／生成镜头视频、未试听音频、未验证全剧声画，未改正式库或运行服务。旧源码／数据调查和浏览器样例路线不能替代执行者的迁移、内容与实际页面验收。

## 三张原始媒体

三张 PNG 均需要原件：布局、控件、图中文字和折叠／下拉位置是问题证据，文字转述不能代替。通过受管 `_publish --input-file` 保存到主项目唯一任务媒体目录，按下列描述性名称登记，不缩放、不转码、不写入正式素材库。原始来源均在主项目 `.runtime/system-review/findings/simplification-publication-20261010/`，登记后的真实路径和身份以主账本 `inputs` 回读为准。

| 原始文件 | 登记文件名 | 实际像素 | 用途 |
| --- | --- | --- | --- |
| user-shot-card-1.png | audiovisual-old-shot-description.png | 1055 × 523 | 旧“叙事目的与表演”实际复述动作，以及起始／结束／承接、共同条件与声音等重复说明 |
| user-shot-card-2.png | audiovisual-old-state-dropdown.png | 1037 × 365 | 状态依据折叠、产物下拉、设计采纳与独立动作对白块 |
| user-shot-card-3.png | audiovisual-old-generation-details.png | 1057 × 1279 | 生成详情折叠、用途与意见及重复解释；截图实际显示 ASH002 的 M2977 首帧引用，不作为 ASH001 当前五项输入的依据 |

本会话 `_media --draft` 未列出媒体；上述三张是用户已从原会话提取的本地原件，全部保留，没有遗漏或跳过的媒体。Markdown、JSON、HTML 为受管规划文件，不作为图像附件。

## 来源与完整性

正文的源规格为主项目 `.runtime/system-review/findings/simplification-publication-20261010/av-task.md`，完整保留在任务正文开头，后接登记与交接、可验证完成标准。调查绑定的故事提交为 `73ec023a968dd6a74d1afaf61db795e6a9628899`，desk 为 `59fbaa39b117e8a6bb6d92b094ca582e0d718f4d`；本轮已回读两仓 main 与本机 origin/main 均为这些提交，执行基线不冻结在此。

以下 SHA-256 用于核对原件字节，不代表浏览器、叙事或声画质量验收：

| 文件 | SHA-256 |
| --- | --- |
| av-simplify-20261010.md | `20364d840e1d33faec353404386d6bcdbe291eff0e9f163cc28037801ad5fdc0` |
| av-simplify-20261010.json | `4a4fcdeeaacde9e5a2a7fd500dc2fad70b63865d076f3bc3d7cadfd3a5cde83b` |
| 原始 av.html | `9f0f8afe14f493a939ae593d340a174a5f6232afbcdb42de452b3bbf5a2b337d` |
| 交付 av.html（仅补边界说明） | `d6c3a72ed56448b3a593828bba6121df70c625dd06df7398b86488f984c6759a` |
| 原始 av-task.md | `be00dfc368202fee27a6e47d03301fd25c9c63f60f49a0ba176978dbc1cf5c77` |
| user-shot-card-1.png | `45cd5992cf3b2126f04abe76ef97296b432666caabfe9485f1d6556ad366ea62` |
| user-shot-card-2.png | `6d8fae03b6e4e9c667ffd0eff2670a09de79274b33bede2caa25b4826a71a918` |
| user-shot-card-3.png | `5daf11b9d7c47a49f80cbc42d714e0de3297aa2838c00757a96f95c93a9199a5` |

本澄清没有创建预览服务、容器、镜像、测试数据库、缓存目录或附属 worktree，无此类过程资源待清除。保留当前受管草稿 worktree 与上述交付文件供任务承接；执行后的资源收尾沿项目规则及实际引用办理，不能在发布会话中提前退役。
