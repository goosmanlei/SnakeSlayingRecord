# 连续制作审阅任务的证据交接

执行正文是 [沿同一制作对象连续审阅当前方案、候选与参考](../continuous-workspace-task.md)。本目录只保存必要文字事实，不是新的运行环境或任务账本。

来源为主项目 `.runtime/system-review/publication/cycle-06/02-continuous-workspace.md` 的完整已定任务及同轮调查。源定义 SHA-256 为 `00d84aeef366e0d57de5f5bf5dccd5182a8036bcfee6aeab73a82a14df986bda`。本次整理保留全部交互、样例及交付终点，补明确故障／恢复、双仓引用、共享资源与后续归属。4小时发现期已结束，自主发布授权以当前用户指令为准，不重启发现期。

<a id="baseline"></a>
## 基线与事实边界

主账本 `task-20261011-0008` 已 completed，完成结果为 `local-formal-publication`。准确成果 primary `6a14c238d7fb344fc12cf284be68a11d6bc0a409`、desk `123e7d00912414d4ca1241a03ad5e91ee9d18622`；发布时本地两仓 main/origin/main 与实例引用已回读相符。这是调查和依赖的准确成果，执行仍从当时最新主干及正式数据起步。

0008 的正式浏览器及运行回执在主项目 `.runtime/task-20261011-0008/formal-browser.json`、`final-runtime.json`。根独立运行回查为 `.runtime/system-review/evidence/cycle-06-0008-final-runtime-readback.json`，记录 2026-10-11T16:21:28Z 的镜像 `sha256:a822cec23abfe4c9f7d81d0fe0f80f550332518fd484a37d3704571cd1686106`，配置与主干一致；根真实跨页、候选及正常对照已完整收敛到下面五份文字。原回执作为历史证据留原位置，不是执行本任务必需的私有输入。

本澄清实际读了定义、五份调查、相关任务及回执，并查看三张原图；没有新开 Chrome、运行产品测试或修改业务数据。附件里的辅助源码推断、根真实操作和建议仍分别成立，不把截图或源码解释当成完整交互验证。附件中调查时的 running 状态、旧版本或“再确定滚读”等措辞按正文当前决定解释。

## 五份必要文字

| 文件 | 用途 | 主项目原始相对位置及原始 SHA-256 |
| --- | --- | --- |
| [跨页镜头与旧素材](cycle-06-crosspage-context.md) | 同场反向选镜、跨集回首集、旧素材污染新镜及正常导航对照 | `.runtime/system-review/findings/cycle-06-crosspage-context.md`；`0fa1fc34de5de59d4538827c76f5699aed669ac0ce5740fa4a9352999f7f87bc` |
| [素材入口、候选比较与参考返回](cycle-06-material-choice-model.md) | M2544 两个内部记录、比较审阅断点、M2857 CALL 焦点清除父候选的准确链路 | `.runtime/system-review/findings/cycle-06-material-choice-model.md`；`a2e95e07b2711678e3efb0cb7bb7048c72c77800ff913548d1ae744cbe25119d` |
| [场说明与性能对照](cycle-06-navigation-performance-control.md) | ASH249 点击被说明浮层阻挡；区分接口耗时与鼠标拦截，不重派性能任务 | `.runtime/system-review/findings/cycle-06-navigation-performance-control.md`；`eb295b0fe84297d1419deb029d8be3d06353671f78e0c6d4362c6b27a6034a44` |
| [自用旧候选与复用方案](cycle-06-own-candidate-and-reuse.md) | M2783/M2784 的真实复用工作、旧原件正常用途及不能误报的自引用边界 | `.runtime/system-review/findings/cycle-06-own-candidate-and-reuse.md`；`18d5e60235ba669924798930a1a8516525ae46d414c6426db1379ba7c2da22ba` |
| [准确评论定位正常对照](cycle-06-candidate-comment-navigation-control.md) | C284 从 M2544 候选2定位候选1并刷新保持；复用已有正确能力 | `.runtime/system-review/findings/cycle-06-candidate-comment-navigation-control.md`；`d831a514a7fa761e2d6730823a7e1d54338300d6d1cc80e3db7b0c60c609c2ab` |

附件只适配交接说明及链接，调查事实、准确编号、源提交、限制和发生顺序保留。源码路径按原文所指 desk 仓库解析；故事 planning 引用改为本目录可访问的相对链接。

<a id="media"></a>
## 三张媒体原件

`_media --draft acb47808-b45a-4bcc-b55a-37722f962832` 返回空清单，本会话无内嵌用户媒体需要选择或跳过。下列三项是用户指定的已有本地图片，发布时逐项使用 `--input-file` 与 `--input-name` 登记；不能把 Markdown 当媒体，也不能只在正文中提到图片而不保存原件。

三份源文件后缀均为 `.png`，实际文件签名均为 **JPEG，2192×1359**。为保留给定原图及原文件身份，沿工具按原文件名登记、逐字节保存，不转码、不修图；工具的扩展名推定类型不作为实际编码证据。阅读时按真实图像编码打开。SHA-256 与字节数以下表为准。

<a id="media-1"></a>
### 原图1：旧素材使视听页不可读

- 文件：`cycle-06-crosspage-invalid-material.png`，119408 字节。
- SHA-256：`0c0b4f7392a275ff1d11b2ba078f10b20105545e4ed1d529ac725d8ecba5e647`。
- 用途：查看“准确镜头素材不属于此镜头”及集场目录消失的页面状态；完整触发顺序由跨页文字证据补足。

<a id="media-2"></a>
### 原图2：内部记录修订选择

- 文件：`cycle-06-material-revision-choice.png`，175638 字节。
- SHA-256：`1daa415b3303d66da455b228150ee96e61bbbe5092c4625981b216c100533814`。
- 用途：核对 M2544 普通素材入口的多余弹窗、两个记录修订按钮及原集场范围，验收直接进入当前方案的变化。

<a id="media-3"></a>
### 原图3：旧灯候选原件现场

- 文件：`cycle-06-lantern-candidate-after0008.png`，158448 字节。
- SHA-256：`d215977cf95228c1bdb72e37b718ee5bee15f6318766c50e0a7fa0bdb033d151`。
- 用途：准确识别本次旧灯候选原件与预览现场；图片本身不证明关闭／刷新时地址丢失，须结合 M2857 操作和焦点证据验收。

原始来源均为主项目 `.runtime/system-review/evidence/` 下的同名文件，只读使用，不改动或删除。发布后的受管位置由主项目 `.codex-task/tasks.json` 中本任务 `inputs[].path` 给出，预期位于 `.codex-task/task-inputs/task-20261012-0002/`。这些路径相对**主项目**，不是相对草稿 worktree；执行时从账本取得，不拼接临时实例路径。媒体不重复提交到 planning 或 export。

<a id="evidence-boundary"></a>
## 未另带入的历史材料

没有会话媒体被跳过。原调查另提到 `cycle-06-context-return-ash010.png`、`cycle-06-reuse-plan-reading.png`、`cycle-06-formal-navigation-network.json`、`cycle-06-own-candidate-reference.json`：前两项的必要页面与操作事实已在完整文字证据中，后两项分别是一次网络样本和共同解析正常边界的辅助明细。本项不承接全站性能或36条引用的主数据清查，正文已给正常对照及重新实测要求，因此不复制这些重复／相邻范围资料。它们不作为执行者必须取得的附件，不把其中一次耗时当性能预算、36条结构校验当制作质量验收。

三张被选原图需要保留错误页、弹窗及准确图像的可见细节，已列为必要输入。核心执行与验收无需根私有聊天、51673 等旧隔离环境或其浏览器标签，所有目标和重走步骤都在正文与五份文字中。共享正式资源、恢复和收尾按项目唯一流程及正文分工执行。
