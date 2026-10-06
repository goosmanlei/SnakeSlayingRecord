# 制作拆解页阅读优化交付

本包交付分集卡、场镜目录、完整剧情定位、精简正文和紧凑素材分区。依据是[完整任务说明](../../planning/production-breakdown-page-optimization-task.md)及[三张原图与校验清单](input-manifest.json)。任务 `task-20261005-0004` 的两个依赖已完成：大卡任务 0002、小卡任务 0003。系统基线为 `2f2b70d9447d4d0b5e4db90c2a7ea6b6f1a59f5c`；本任务在独立系统 worktree 和两个隔离数据库中实现与验收，没有生成媒体、改写剧本或把测试评论发布到正式库。

本包记录最终候选前的实际验收。唯一系统候选见[双仓交付计划](system-delivery.json)，故事候选由主项目任务账本的 `git_delivery` 记录；正式服务切换、双仓推送及最终资源清理结果读取本任务 `.runtime/breakdown-page/release-final/run/` 实际回执和主项目任务完成说明，不从预览或 Git 提交推断正式成功。首次发布后的补验发现旧共享素材别名的版本被主素材轮次替代；最终候选已修复，并补验旧别名版本 1 与主素材版本 2 各自保持准确成员。

## 七项实现与实际证据

以下系统路径相对审阅台仓库；故事证据路径相对此目录。

| 要求 | 实现 | 已完成验证 |
| --- | --- | --- |
| 1. 统一分集菜单 | `static/screenplay.js` 的 `renderEpisodeCard` 同时供剧本与拆解使用；`production_breakdown.py` 返回准确场镜评论目标，前端按评论 ID 去重并包含已关闭记录 | Chrome 对照两页结构、150×96px、选中态及真实集场范围；逐集操作 17 集。隔离评论新增 2→3，编辑／关闭／重开均保持 2，移除具名测试评论后 3→2；历史视图为 0。[逐集读数](evidence/episodes-browser.json)、[浏览器记录](evidence/browser.json) |
| 2. 场／镜目录 | `production-breakdown.js` 两级目录及准确路由，`scene_shots` 按不可变父级读取，目录与正文共用准确镜集合 | 全部 42 场、297 镜均可在本集目录找到，初次展开；跨场 SH016 的标题在固定顶栏下方。前后退、刷新、连续切集及旧镜头链接通过；旧 SH001 不跟随新镜序 SH999。迟到响应与工作区切换有自动回归 |
| 3. 精简正文 | 场头仅保留场编号标题与剧情依据；删除场景／时段、过程说明渲染；旧说明评论经 `openBreakdownSceneNotes` 读准确原文 | DOM 没有旧行或说明空框；隔离说明上的文字评论定位到原修订 `fixture-note`，没有转绑；删除界面不修改数据库。[前图](evidence/before.jpg)、[后图](evidence/after.jpg) |
| 4. 移除归属筛选 | 删除归属标签及按钮生成，载入清除旧内存条件；素材来源仍是准确镜头关联投影 | 页面无归属筛选节点；旧条件不影响分组函数。全剧准确修订上对照原全选集合，5,067 条逐镜关联无增、漏、重；不向每镜扩展全剧或整场素材。[集合审计](evidence/material-set-audit.json) |
| 5. 完整准确剧情 | 镜头标题旁与场头共用 `openMaterialReference`；`full_scene=1` 返回锁定版本完整场，只用准确正文块高亮；其他接口默认仍读片段 | 真实 SH003 完整 32 块，b004、b006 不连续高亮；夹具首／末块 b001、b032 高亮，中间正文保留。失效块报错，缺少块 ID 时提示且高亮数为 0；旧镜头仍用旧引用。关闭／Esc 保留草稿。[完整场](evidence/full-scene.jpg)、[首末夹具](evidence/fixture-discontinuous.jpg)、[历史](evidence/history.jpg) |
| 6. 共用收窄小卡 | 直接调用 `unified-cards.js` 的 `materialSmallCard`，右栏 300px；共用大卡按真实身份优先选择，旧共享别名使用其准确历史轮次与候选；准确素材链接支持刷新恢复 | 同一 1440×900 视口右栏 411.5→300px，正文 411.5→523px，小卡 370.5→271px，高度仍 84px。长名、无预览、未生成、多素材及空态可读；390px 无横向溢出。M1003 精确 MV004／MC001，M1105 主素材精确 MV002／MC001、旧别名精确 MV001／MC001，刷新不变；大卡及图片返回保持 SH016、滚动 2241 和草稿。[栏宽前后](evidence/after.json)、[窄屏](evidence/narrow.jpg)、[准确音频](evidence/exact-audio.jpg)、[旧别名补验](evidence/legacy-alias.json) |
| 7. 实际类型分区 | `ui_projection.material_classification` 使用准确范围、实体、状态、原件覆盖与制作位置关系；同一素材按真实身份去重，多实体归共有，未知类型归其他 | 真实数据覆盖图像场景／道具／角色／镜头、音频歌曲／角色／镜头、视频镜头。隔离数据补验共有图像、其他文档、长名与无预览；空分区不出现。多实体引用和使用证据继续在读取数据保留。[夹具分区](evidence/fixture-groups.jpg) |

代码仅增加读取投影与展示，不迁移业务数据。原片段接口、真实 CALL 输入、原件、采用、采纳、修订和评论事件保留。场、镜的历史目录还会寻找各对象绑定旧剧本的最近准确修订，避免当前头换到新剧本后旧场消失。

## 联合验收与复现

Chrome 实际操作了制作拆解主流程，回归剧本卡、素材管理三列分页和音频卡、实体及状态大卡、镜头制作提示词／准确输入／视频右栏、嵌套参考输入、图像放大、音频播放、采编评论定位与编辑 Esc，以及结构图弹窗和整体草稿。发现的窄屏当前位置、共享素材别名两项问题已修复并补验。实际记录与边界见[浏览器记录](evidence/browser.json)；没有把自动测试代替真实浏览器验收。

当前自动检查：系统 Python 279 项、JavaScript 636 项、故事发布守卫 61 项均通过，`git diff --check` 无错误。最后修复只改动共享素材前端选择与回归测试，Python、集合与发布守卫沿用未变化的检查，JavaScript 全量重跑。完整命令与输出摘要见[测试证据](evidence/test-results.json)。在系统 worktree 执行 `python3 -m unittest discover -s tests`、`node --test tests/*.test.cjs`；在故事 worktree 执行 `python3 -m unittest discover -s tests -p '*release*.py'`。

需要重建预览时，在本故事任务 worktree 执行：

```sh
python3 scripts/generation_review.py --system .runtime/breakdown-page/system --instance .runtime/breakdown-page/review init
python3 scripts/generation_review.py --system .runtime/breakdown-page/system --instance .runtime/breakdown-page/review serve --port 62340
python3 scripts/breakdown_page_audit.py --system .runtime/breakdown-page/system --instance .runtime/breakdown-page/review --baseline production/breakdown-page/evidence/before-set.json --output .runtime/breakdown-page/recheck.json
```

`init` 只建立独立预览，不连接正式库；重跑集合审计前核对正式数据仍对应基准准确修订。隔离夹具只用于首末、不连续、无引用、失效引用、镜序改变、旧说明评论、共有／其他及空态；不会计作真实业务覆盖。未生成视频的播放器未冒充验证；实际验证音频 8.5 秒可播放及图像 3584×2016 原件可读。这些技术结果不表示用户接受作品或素材质量。

## 受控发布与恢复

用户以 `--auto` 授权本任务内按序交付，最终确认由实际候选验收代替，不能伪造用户逐项接受。两仓目标均为 main，upstream 在准备回执中冻结，禁止强推；实现、暂存和提交均在任务 worktree，主目录操作由已有受控脚本完成。

1. 提交系统候选，故事配置 pin 与本包指向同一 SHA；故事提交后执行 `_prepare_integration -g creative -p SnakeSlayingRecord --task task-20261005-0004 --push`。冲突只在当前任务工作区解决并提交，重新准备，按影响补验。
2. `scripts/material_review_release.py prepare --task task-20261005-0004 --push-system --system-worktree .runtime/breakdown-page/system --bundle .runtime/breakdown-page/release-final --story-candidate <准备候选> --story-target <目标头> --system-candidate <计划候选> --system-target <计划目标>`。冻结源码、配置、现有正式镜像／挂载和辅助脚本；`build` 离线构建，`preflight` 校验准确摘要并预演系统 fast-forward，不写正式数据库。
3. 候选验收通过后 `_deliver --note '候选与实际验收依据'` 集成、推送故事。再 `material_review_release.py apply` 带 bundle、`--manifest-sha256`、`--image-receipt-sha256` 与 `--apply`，持共享锁核对未漂移，备份正式库，系统受控 fast-forward，切换不可变配置挂载和镜像，回读健康、源码与全库保全。业务增量 0，不覆盖正式库，不导入夹具。
4. Chrome 在正式 3000 实际核验分集、目录跳镜、完整剧情高亮、素材小卡／准确大卡、返回及受影响入口；正式浏览器结果写冻结包 `run/formal-browser.json`。用真实回执核对正式运行 SHA、镜像与保全，成功的发布不重复执行。
5. `publish-system` 带同包与两个摘要及 `--apply`，向冻结 upstream 普通 fast-forward 推送并读回远端。远端分叉即停，重新准备补验，不强推。
6. 停止本任务两个预览服务，移除失效隔离库、夹具、缓存和重复日志，按准确路径回读；全部完成标准满足后 `_complete`。此后不再修改交付文件，保留工作区、分支与 TUI。

正式不可变挂载与恢复入口为主项目 `.runtime/service-releases/breakdown-page-20261005-0004-<故事短SHA>-<系统短SHA>/`。切换失败时同包 `recover` 带同样摘要及 `--apply`，只恢复旧镜像与配置挂载，不恢复数据库、不 reset Git；真实评论与历史保留。冻结包、正式前后备份、旧镜像和回执用于发布追溯与恢复，较新恢复基线替代且无追溯需要后再核对移除。

## 资源收尾

提交前已验证受管原图与任务附件逐字节一致，删除 3 份重复原图和 1 份临时文档脚本，回读均不存在，见[记录](evidence/cleanup-before.json)。首轮已停止两个预览并删除 2,833 个文件，见 `.runtime/breakdown-page/release/run/cleanup-final.json`。补验预览及重复日志在最终正式验收后清理；精确数量、路径、停止及删除回读写 `.runtime/breakdown-page/release-final/run/cleanup-final.json` 和任务完成说明，不修改已交付候选补日志。系统嵌套 worktree、分支、原图、验收证据和有效冻结恢复包保留；工作区待 TUI 退出、锁释放后用各仓 Git 与 `codex.project task cleanup` 正确退役。其他活跃任务和正式资源不进入清理范围。
