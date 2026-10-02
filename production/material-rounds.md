# 素材轮次承接与验证

素材按修订轮次审阅，初始方案和首轮产出属于版本一。现有 6 份素材的 24 个内部修订并非 24 次生成：已登记 7 个真实调用对象（14 条提交／完成状态修订）。目前没有针对素材、需求或调用的正式评论，不能据内部修订次数虚构用户修订轮次。

阿蘅声线重点样例：需求有两条记录修订，素材有四条记录修订；原件与原始提交 CALL 始终相同。后续修订补充状态覆盖及需求关联，需求第二条修订来自全局声音制作流程调整。因此归为同一素材版本一，四条旧修订、原件、调用与链接全部保留。

李寄两次图像调用均属于首轮基准尝试，第二次核对原生 4K。库内没有区分独立用户修订轮次的触发证据，按已证实首轮保留两个候选。这个缺口在对应表的 `gaps` 中明示；本任务不重新生产图像，也不把已有低于 4K 的图像写成合格母版。

## 完整对应与原始证据

[完整对应表](material-round-mapping.json) 覆盖 1,126 个需求／素材身份、3,235 条精确记录归属；每条保留完整修订 SHA 与依据。下表列出全部 24 条素材修订，短 SHA 仅帮助阅读，完整原件与引用仍在导出数据中。

| 素材对象 | 旧记录修订 | 新素材版 | 原始调用 | 原件 SHA 开头 |
| --- | --- | --- | --- | --- |
| asset-aheng-song-01 | 1 / 8c147c51ab76 | 1 | call-aheng-song-01 | 9edcf64a1d34 |
| asset-aheng-song-01 | 2 / be00f5517102 | 1 | call-aheng-song-01 | 9edcf64a1d34 |
| asset-aheng-song-01 | 3 / 408103789e12 | 1 | call-aheng-song-01 | 9edcf64a1d34 |
| asset-aheng-song-01 | 4 / 4be31a852deb | 1 | call-aheng-song-01 | 9edcf64a1d34 |
| asset-aheng-voice-01 | 1 / d4ca874bc9cd | 1 | call-aheng-voice-01 | a041a61f5f37 |
| asset-aheng-voice-01 | 2 / b735232027ce | 1 | call-aheng-voice-01 | a041a61f5f37 |
| asset-aheng-voice-01 | 3 / 1abe5a7cb526 | 1 | call-aheng-voice-01 | a041a61f5f37 |
| asset-aheng-voice-01 | 4 / f69bbbcbb808 | 1 | call-aheng-voice-01 | a041a61f5f37 |
| asset-liji-image | 1 / 3bc05d920d34 | 1 | call-liji-baseline-01 | 82a51fcd6319 |
| asset-liji-image | 2 / 79dca6a288e1 | 1 | call-liji-baseline-02 | cd50ecc53c05 |
| asset-liji-image | 3 / 959ae058abe5 | 1 | call-liji-baseline-02 | cd50ecc53c05 |
| asset-liji-image | 4 / 8db9e0dad451 | 1 | call-liji-baseline-02 | cd50ecc53c05 |
| asset-liji-voice-01 | 1 / 62ad84f264f8 | 1 | call-liji-voice-01 | 902279032693 |
| asset-liji-voice-01 | 2 / ea9d952f21f5 | 1 | call-liji-voice-01 | 902279032693 |
| asset-liji-voice-01 | 3 / dd05e939dbbe | 1 | call-liji-voice-01 | 902279032693 |
| asset-liji-voice-01 | 4 / b342bb1e0e8f | 1 | call-liji-voice-01 | 902279032693 |
| asset-zhao-voice-01 | 1 / 7e2022fe18f3 | 1 | call-zhao-voice-01 | 842ecea98a02 |
| asset-zhao-voice-01 | 2 / ece1129863da | 1 | call-zhao-voice-01 | 842ecea98a02 |
| asset-zhao-voice-01 | 3 / 809e921f303e | 1 | call-zhao-voice-01 | 842ecea98a02 |
| asset-zhao-voice-01 | 4 / 5d901dafe51a | 1 | call-zhao-voice-01 | 842ecea98a02 |
| asset-zhou-voice-01 | 1 / 902dcc4327b1 | 1 | call-zhou-voice-01 | d242aeb9c0b0 |
| asset-zhou-voice-01 | 2 / 99150b20b507 | 1 | call-zhou-voice-01 | d242aeb9c0b0 |
| asset-zhou-voice-01 | 3 / f86be556070b | 1 | call-zhou-voice-01 | d242aeb9c0b0 |
| asset-zhou-voice-01 | 4 / 885e25702347 | 1 | call-zhou-voice-01 | d242aeb9c0b0 |

## 操作与恢复

路径以本故事任务 worktree 为基准。共享系统代码位于本任务独立的 `.runtime/review-desk-worktree`；具体 CLI 和评论意图契约见系统 `docs/material-versions.md`。

1. 从最新正式数据库做 SQLite 一致性备份，复制到新的隔离实例；复制受管 config/content/export，不复制密钥或依赖目录。
2. `scripts/material_round_audit.py --system SYSTEM --instance ISOLATED --output production/material-round-mapping.json` 读取全部准确历史并构建对应表。它针对已核实的首轮批次，有新素材评论或调用身份变化时拒绝自动归组，须重新审阅证据。
3. 使用系统 `material-round-migrate ... --validate-only` 预演，再在隔离副本应用。正式发布时在写入前重新读取最新库指纹；变化即失败，不覆盖用户后来写入的数据。
4. `scripts/verify_material_rounds.py` 比较旧 8 张表，并在空实例恢复后再导出；校验原件、调用、评论、事件、依赖和准确采用全部一致。
5. 双仓正式应用、3000 与集成由单个会话串行协调。任务完成须对最终候选复验并取得用户确认；不自动推送。

迁移新增四张索引表，不更新／删除原业务行。Schema 4 导出携带轮次与评论显示归属；旧原件、历史链接及准确采用仍指向原记录。重复应用为无操作，冲突和错误回滚，不用数据库快照替换正式库。

## 已完成验证与边界

- 自动验证：通用系统 98 项 Python、40 项前端测试及故事工具 75 项测试通过，覆盖初版登记、修订轮次、同轮多条意见、元数据补全、并发首条意见、过期拒绝、事务回滚、历史兼容和恢复回滚。延迟提交的首次执行归当前轮；历史候选不会覆盖同轮的另一真实调用。
- 隔离迁移：原有 8 张业务表逐行不变；空实例恢复后 12 张表一致，71 个清单文件（含 66 个受管资源）校验一致。见 [恢复证据](evidence/material-round-recovery.json)。
- 两个可执行隔离准备包：GPT Image 双图按“图片1／图片2”自然语言指代，Seedance 图／音频／图按“@图片1／@音频1／@图片2”指代，准确裁切与片段保留；没有付费生成。见 [准备包证据](evidence/material-input-contracts.json)及 [OpenArt 原始表单](evidence/gpt-image-form.json)。
- Chrome：横／竖／方图的桌面框均为 548×300，430 像素窄屏均为 322×300，图幅保持原比例、页面无横向溢出；键盘放大关闭、圈选归一化、同块开放／关闭评论、历史轮次、零评论、新增／关闭／重开和三层参考弹窗返回及草稿保留已操作。音频波形、播放、静音与键盘选段已操作；切版后旧结果不重复成卡，回到历史版本恢复原图及未提交草稿、焦点。全剧制作的准确剧情依据与需求弹窗关闭后回到触发按钮。观察与截图见 [浏览器记录](evidence/material-browser-observations.json)；这不代表实际听审。
- 共用创作回归：采编／结构圈选 17 项、剧本集场与评论 42 项、创作导航与评论 78 项通过。原始结果保存于 `evidence/material-*-browser.json`。

正式 3000 已应用系统 `4a8d18b`，42 个文件与提交一致；原八张业务表逐行不变，十二张表恢复及 71 文件核验通过。阿蘅单层素材版本、舟行曲原始声线输入及共享轮次、评论空列表、图片放大和全剧剧情依据已在 Chrome 回读，正式库没有测试写入。见 [迁移证据](evidence/material-formal-publication.json)、[运行版本](evidence/material-formal-system.json)和 [正式浏览器记录](evidence/material-formal-browser.json)。

当前正式数据库仍在主项目，候选 config/content/export 只读挂载自任务工作区。用户确认最终候选后，先核对双仓目标，撤除候选挂载，再按受控流程集成；不自动推送。主干和任务完成状态见 `STATE.md` 及主项目账本，媒体内容接受、4K 基准及动态分镜仍由后续制作任务完成。

首次 Compose 重建自动移除了九个已停止、具有同服务标签的旧容器。旧镜像、挂载文件和一致性备份保留；后续切换仅按准确名称替换当前应用容器，避免再次触发归档容器清理。
