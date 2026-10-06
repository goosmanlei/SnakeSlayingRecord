# 镜头制作页交付

本包交付镜头制作页的分集／场镜导航、平铺视频制作版本、独立 Prompt、共用素材小卡，以及准确上游参考的选择、持久化和生产前校验。依据为[完整任务说明](../../planning/shot-production-page-task.md)和[三张原图清单](input-manifest.json)。原件逐字节、哈希和实际像素一致；Notebook 全章与八项目标逐项对应如下。前置大卡0002、小卡0003和拆解0004的正式交付已回读，复用其组件，不重复发布。

系统基线是 `aa5d2422f87bd63d300fd93fc975c0f519d35a9b`。唯一系统候选和目标见[双仓交付计划](system-delivery.json)；故事候选、受控推送和结项查主项目任务账本。本包记录候选验收事实，正式切换、远端回读和最终清理查本任务 `.runtime/shot-production/release/run/` 实际回执。Git 交付不替代正式页面验收。隔离库的选择、评论和离线视频不发布，本次正式业务增量为0，不调用收费媒体生成。

## 八项实现与验收

以下系统路径相对审阅台仓库；故事入口和证据相对本包。

| 全章要求 | 实现位置 | 实际验证与证据 |
| --- | --- | --- |
| 1. 分集导航 | `static/screenplay.js` 共用卡、`production_breakdown.py` 的镜头页评论范围、`production-breakdown.js` 去重计数 | Chrome对照剧本卡150×96px，17集编号、标题、准确场范围一致；隔离视频／剧本／上游各新增1条评论后，镜头E01只计视频1条。含已关闭、不含删除或编辑事件，统计对象在导航说明中。[剧本对照](evidence/screenplay.png)、[镜头页](evidence/wide.png) |
| 2. 场→镜导航 | 复用0004的准确二级目录、阅读位置与路由，镜头页显式 `production_tab=shots` | 默认展开，多场顺序正确；390px切到E17后点击SH018定位S042，刷新与前进后退保持准确地址。全剧42场297镜集合一致。空场、长名、滚动、旧镜序与历史场依赖复用未变化的[0004实际验收](../breakdown-page/evidence/browser.json)，本任务补验镜头页与版本路由。 |
| 3. 场头与筛选清理 | 当前DOM不生成通用说明／空框／归属筛选；`scripts/production_inventory.py`、`scripts/production_breakdown.py`、`production/inventory.json` 移除生成来源 | 保留场名、地点、日夜、剧情依据；42项当前编制源物理删除通用说明。新PREPARATION允许无重复文字块；不可变旧修订、评论、检查覆盖和归档不重写。[集合审计](evidence/material-set-audit.json)核对5,067条关联，无增、漏、重；旧筛选状态不参与分组。 |
| 4. 视频版本与Prompt | `breakdownPrompt` 默认最新视频制作版、平铺版本／候选与准确地址；`renderLinkedPrompt`独立标题和原文锚点 | 单V1、多V1/V2、旧V1有离线候选而最新V2无结果均实测；V2不串入V1结果。手动与准确链接优先，刷新保持；参数和Prompt分开，历史读取真实CALL。[新版本](evidence/locked-new-version.png) |
| 5. 准确参考统一入口 | `shot_references.py` 准确逐槽投影，`renderShotInputs`共用小卡，`openShotReference`共用大卡 | V3 C_、V1 C_、V_ C_和V3 C2如实显示；同素材两个用途分别选V3 C2/V1 C1，同名另一身份不误改。卡片及两个重复@图片1都到M2528/MV003/MC002；未选仍可打开，无候选不冒充已选。[准确目标](evidence/exact-reference.png)、[逐槽状态](evidence/saved-slots.png) |
| 6. 选择与保存 | `POST /api/production/shot-reference` 同事务核对当前修订、槽指纹、身份、候选、组成和原件；修订中保存选择及幂等收据 | 浏览后关闭不写；明确保存、关闭、刷新、重开一致。并发409和缺原件失败均无部分写入；原件恢复后回读失败前后修订一致。双层图像弹窗及成功保存后，原文草稿、焦点与位置保留；4秒延迟适配器真实操作“保存→立即关闭”，迟到成功只刷新仍有效页面，不重开弹窗。[冲突](evidence/conflict.png)、[失败](evidence/missing-original.png) |
| 7. 锁定与生产阻断 | `shot_references.select`、`material_plans.version`、`generation.readiness/package/validate_call`共用守卫，Store新CALL也校验 | 已提交V1改选建立V2；submitted/failed/unknown及同输入改选自动验证锁定，旧CALL、候选、评论和范围保留。HTTP直接调用生成包拒绝缺项，导入新CALL不能用prepared_plan绕过。缺版本／候选、错配、失效引用、缺原件、组成及范围不合法均拒绝；完整输入仍需认可准确新方案。未发起生成。 |
| 8. 共用小卡与较窄右栏 | 共用 `materialSmallCard`/`openUnifiedMaterial`；右栏300px，窄屏逐镜排列 | 2192px宽屏正文1019px、右栏300px；1280px正文363px、右栏300px；390px两区346px，页面横向溢出0。右侧仅本镜视频。阿蘅普通大卡仍默认有结果V1（最新V2未生成），无本镜操作；离线1秒片可播放。采编、结构放大、剧本、实体／素材管理、拆解与普通大卡回归。[桌面](evidence/desktop.png)、[窄屏](evidence/narrow.png) |

完整实际动作与边界见[浏览器记录](evidence/browser.json)。参考版／候选指上游输入，镜头正文版指本镜视频方案，两者不混用。普通大卡的浏览默认值不写入参考；“选为本镜参考”仅修改当前槽位，不改其他镜头、全局采用或素材认可。

场头删除只影响当前展示与当前编制源。正式数据库里的旧说明仍有真实评论依赖，保留准确历史入口；不为了移除冗余文字改写旧哈希，也不为本次代码发布重建父场并改变297镜的绑定。若后续重新编制场，走新PREPARATION修订和增量路径，空blocks合法且来源、覆盖与历史继续校验。

## 数据契约、验证与恢复

完整通用接口和字段见系统 `docs/production-breakdown.md` 的“镜头视频版本与准确参考”。选择保存在当前视频REQUIREMENT的新准确修订；未提交版更新草稿，已提交、失败或未知版改选建立新版。操作ID与请求指纹随修订保存：重复内容只返回原收据，同ID不同请求拒绝；当前修订、槽位或候选冲突整事务回滚。

保存保持原有组件、裁切和时间范围，重新选择原件时同时校验其适用性。旧CALL只在其准确绑定方案与实际输入逐项一致时读取方案中的显式版本选择；历史缺口不自动补最新候选。评论草稿仍绑定原不可变原文，不转绑选择后的新修订。

针对性Python10项包含独立导出→空库恢复后准确引用、完整素材版本索引及幂等收据一致。全量系统Python291项、JavaScript643项、故事发布守卫61项、制作编制6项通过，双仓 `git diff --check` 通过；[测试证据](evidence/test-results.json)给出命令输出摘要与哈希。恢复继续使用既有bundle协议，无新增表或数据迁移。后台通过参考检查仅解除参考阻断，方案认可、范围、其他缺项及模型输入契约仍需满足。

预览必须建在任务隔离目录，不能连接正式库：

```sh
python3 scripts/generation_review.py --system .runtime/shot-production/system --instance .runtime/shot-production/review init
python3 scripts/generation_review.py --system .runtime/shot-production/system --instance .runtime/shot-production/review serve --port 62450
```

系统worktree执行 `python3 -m unittest discover -s tests` 和 `node --test tests/*.test.cjs`；故事worktree执行 `python3 -m unittest discover -s tests -p '*release*.py'` 及 `test_production_forms.py`。新镜头调用按生成包提供准确generation_requirement及认可范围，不能仅登记prepared_plan。旧执行记录只能更新状态，不能改实际输入；恢复历史走现有准确导出恢复，不能用普通导入绕过新执行校验。

## 正式交付与收尾

用户以 `--auto` 授权本任务自行完成验收和按序交付，不伪造用户接受素材。故事和系统实现、暂存、提交只在各自任务worktree；主目录的集成与推送由现有受控命令负责。

1. 系统提交后更新故事配置pin与本包交付计划，故事提交后 `_prepare_integration -g creative -p SnakeSlayingRecord --task task-20261005-0005 --push`；来源或候选变化时补验影响范围。
2. `scripts/material_review_release.py prepare --task task-20261005-0005 --push-system --system-worktree .runtime/shot-production/system --bundle .runtime/shot-production/release --story-candidate <候选> --story-target <目标> --system-candidate <系统候选> --system-target <系统目标>`，再按同包 `build`、`preflight`；冻结准确源码、配置、镜像与upstream，不修改正式库。
3. 候选验收通过后故事 `_deliver --note '候选验收与交付依据'`。然后同包 `apply --apply --manifest-sha256 <摘要> --image-receipt-sha256 <摘要>`，持共享锁回读未漂移、一致性备份、系统受控fast-forward、不可变配置和正式镜像切换；业务增量0，全库保全，不导入隔离副本。
4. Chrome在正式3000操作分集、场镜、Prompt、准确大卡、返回及共用组件；核对实际服务源码、镜像和配置pin，结果写冻结包 `run/formal-browser.json`。再 `publish-system` 带相同包、两摘要与 `--apply`，普通推送冻结upstream并回读；分叉即重新准备，不强推。
5. 按准确进程／路径停止预览、删除无效隔离库、离线夹具、缓存与重复日志，回读并记录 `run/cleanup-final.json`。所有标准满足才 `_complete`；之后不再改候选文件，保留TUI、worktree和分支。

正式恢复目录为主项目 `.runtime/service-releases/shot-production-20261005-0005-<故事短SHA>-<系统短SHA>/`。失败使用同包 `recover`、同摘要与 `--apply` 只恢复旧服务镜像和配置，不恢复数据库或reset Git，真实评论与历史继续保留。冻结包、正式前后备份、镜像和回执用于追溯与恢复，新的有效基线替代且用途结束后再核对清理。

提交前已删除3份重复输入图，原件、字节、哈希回读一致，见[清理记录](evidence/cleanup-before.json)。正式验收后的删除数量、停止结果和保留用途写实际回执；不在候选中预先宣称完成。嵌套系统worktree按自身Git入口退役，故事worktree待TUI退出释放清理锁后走 `codex.project task cleanup`，不递归强删。
