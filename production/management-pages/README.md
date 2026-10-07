# 实体与素材管理四列交付

本包对应 `task-20261006-0004`，依据 Notebook 第 1010 章完整三条要求。原文、来源摘要及范围见[任务说明](../../planning/management-pages-optimization-task.md)。本章与会话没有输入媒体；本包图片均为真实浏览器验收截图。

## 当前用法

实体管理按类型、素材管理按真实集场及特殊归属分组。正文在 1440×900 桌面为四列，850×900 为两列，390×844 为一列；大卡内部和逐镜侧栏沿各自容器布局。每组独立起行，组末不足四项仍占一个基准行，标题不计行。默认每页 10 行，最多 40 个展示项；支持 5／10／20／50 行。窄屏只重排当前页，不改变页内对象集合。

所属集／所属场与其他条件一样使用平铺单选按钮，可换行。只显示准确 E／S 编号，不显示标题和重复计数。Tab 聚焦，Enter／空格选择；“全部集／全部场”取消相应选择，切集清理旧场，清除筛选恢复全部。实体的类型、采纳与搜索，以及素材的媒体类型、生成结果与搜索仍可组合。筛选或行数变更回首页，结果收缩钳制页码，空结果保留禁用的第 1／1 页。

两页共用底部分页。首页、上一页、页码、下一页、末页及行数选择保留，纸色背景、边框、字体、圆角与页面按钮一致；可操作悬停为浅绿，键盘焦点有边线，禁用状态变淡。普通小卡打开准确对象及版本；关闭大卡恢复筛选、页码、位置和触发卡焦点，版本与候选不被最新指针替换。

## 已完成的隔离验收

Chrome 使用独立库及 62404 预览，真实尺寸由 DOM 回读；未操作正式采纳、评论或生成。代码包含前置 1008 的标题／总量小卡和 1009 的逐镜改动，本轮已补验组合版本的四列可读性。长名沿共用小卡单行省略及完整名称提示，编号和底部信息保留。

| 要求 | 实际结果与证据 |
| --- | --- |
| 两页四列和窄屏 | 桌面网格四列；850 两列、390 单列，无页面横向溢出，三种视口当前页身份集合相同。[实体桌面](evidence/entities-desktop-cards.png)、[实体850](evidence/entities-850.png)、[实体390](evidence/entities-page2-390.png)、[素材桌面](evidence/materials-desktop.png)、[素材850](evidence/materials-850.png)、[素材390](evidence/materials-390.png)。 |
| 逐页完整性 | 实体4页分别40／39／38／16项，共133个有效实体，保留已撤回实体排除规则；素材74页共2,882个分组展示项、2,073个唯一素材。真实逐页集合与未分页接口一致，素材按组＋身份无额外重复；实体按身份无遗漏。[集合核对](evidence/collection-check.json)、[逐页DOM记录](evidence/browser.json)。 |
| 分组与分页边界 | 实体跨页续组、组末不足四张和多组独立起行实际核对；首末页、单页和空结果禁用正确。两页四种行数实际切换均回首页。自动测试另验证大组续页、5／10／20／50 行完整遍历和越界钳制。 |
| 平铺组合筛选 | 实体 E01／S001＋角色＋未采纳＋“李寄”得到2个实体；素材 E01／S001＋图像＋有结果＋“李寄”得到 M945 一项。切 E02 清理旧场，只显示 S003／S004；全部、清空、无匹配搜索、Enter／空格实际操作。全部集下素材场选项也从准确集场编号索引读取 S 编号，关联范围没有变化。 |
| 返回及草稿 | 第二页实体 EN088 关闭回原卡焦点及页码；圈选同一正文后，未提交草稿恢复，随后取消，没有入库。[草稿返回](evidence/entity-draft-return.png)。素材第二页 M1131 切 V1，后退回列表、前进重开同一准确修订／V1／C1，页码保留。[浏览器记录](evidence/browser.json)。 |
| 分页风格与旧版对照 | 共用分页、禁用和键盘焦点真实检视。[分页](evidence/pagination-desktop.png)、[旧实体三列／下拉](evidence/before-entities.png)、[旧素材](evidence/before-materials.png)。 |
| 必要自动回归 | JavaScript 660项、相关 Python 44项、原生双仓交付适配7项通过；覆盖准确对象／版本、上下文、分组、筛选及迟到响应。[检查摘要](evidence/tests.json)。 |
| 数据边界 | 隔离库32张业务表与初始化基线的逐行摘要完全相同。[数据保全](evidence/preview-conservation.json)。业务数据增量为0，无媒体生成、业务迁移、夹具或测试评论发布。 |

自动检查与真实页面验收分别记录，不将接口成功当成浏览器验收。正式3000的实际版本、正式验收、Git推送及清理结果保存在本任务账本和下方本机回执，不在冻结交付后补改本文件。

## 双仓发布与恢复

用户 `--auto` 已授权范围内双仓集成、普通推送与正式服务切换。系统准确提交由[交付引用](system-delivery.json)及故事 `config/instance.json.review_desk_commit`锁定；主项目内部回调校验它与系统候选相等。系统候选先提交、故事随后提交，再准备整组候选；候选发生变化时更新 pin，重新准备并补验受影响范围。

以下从故事任务 worktree 执行，`desk`为任务工具返回的 `../../linked-worktrees/task-20261006-0004/desk`。任务回调始终使用主项目入口、唯一 `.codex-task` 数据目录，Git集成与推送只由 `_deliver`完成。

1. 双仓提交后，经主项目任务回调 `_prepare_integration --task task-20261006-0004 --push`冻结候选，核对两仓 main及上游。候选验收输入变化须补验；不手工在主目录合并或推送。
2. 用 `python3 scripts/material_review_release.py prepare --task task-20261006-0004 --push-system --system-worktree ../../linked-worktrees/task-20261006-0004/desk --bundle .runtime/management-pages/release --story-candidate <故事候选SHA> --story-target <故事目标SHA> --system-candidate <系统候选SHA> --system-target <系统目标SHA>`冻结代码包，再对同包执行 `build`、`preflight`。包核验正式容器、挂载、源码与准确配置，不导入隔离库。
3. 候选验收通过后由 `_deliver`执行两仓受控Git交付及普通推送，再执行 `material_review_release.py apply --bundle .runtime/management-pages/release --apply --manifest-sha256 <摘要> --image-receipt-sha256 <摘要>`。发布在共享锁内串行进行，正式活库和原件保持原挂载，不用快照覆盖。
4. Chrome在正式3000核对两页四列、集场筛选、分页及大卡返回；回读实际镜像、配置pin与远端。正式检查和32表保全依据保存在 `.runtime/management-pages/release/run/`。原生后端已由 `_deliver`负责系统推送，项目 `publish-system`仅验证同包回执。
5. 正式验收后停止本任务62404进程，按准确路径清除预览库／原件副本、失效缓存及重复日志。保留双仓worktree、分支、冻结发布包、验收截图和正式一致性备份，用于追溯与代码恢复；TUI退出释放锁后再走受管worktree退役。实际数量和回读见本机 `release/run/cleanup-final.json`。
6. 全部完成后才 `_complete`；成功后停止文件写入，保持当前TUI，不领取其他任务。

切换异常时先查同包 `run/`及实际容器，再恢复或续用。`recover`带相同两个摘要及 `--apply`仅恢复原镜像／配置挂载，不重置Git或覆盖数据库。不可变服务重启入口在主项目 `.runtime/service-releases/<本任务release_name>/`。历史数据恢复沿项目当前净化导出基线，不能回灌测试或旧快照。
