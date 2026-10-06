# 全站视觉与系统配置候选

本候选已实现十三个子页的共同页头、浅色菜单与控件，以及系统与 AI 的两个配置分区。剧本页固定菜单下缘至介绍首行的距离，在相同 1280×900 视口下由 70 像素收敛至 24 像素。桌面、390×844 窄屏逐页检查及必要回归已完成；图标文件上传的真实浏览器验收被 Chrome 扩展文件权限阻断，因此任务尚未完成，未集成、应用、推送或切换正式服务。

可审阅入口是本任务的隔离实例 `http://127.0.0.1:62660/`。其中包含验证用配置、已关闭的测试评论和采纳事件，只用于验收，绝不作为正式业务数据发布。视觉候选可供用户审阅，技术检查不代表用户对视觉或既有素材的接受。

## 版本与边界

- 故事工作区先解决启动时的 `STATE.md` 合并冲突，提交 `98fc8dab515714aec06797b40d48e6b7c26abdcd`，再成功执行受控准备命令同步基线。没有把未解决的合并当作同步成功。
- 直接前置任务 `task-20261005-0004`、`task-20261005-0005` 已完成并正式应用；后续实体大卡第二版也已在实际系统基线中。系统基线为 `bb1c9a952e27c3b5eb26bba6d81a3627996d8841`。
- 系统候选为 `166b766560273e9cdab533da22fc5636f60ec94a`，工作区为 `.runtime/system-page-style/system`。准确交接见 [system-delivery.json](system-delivery.json)，故事实例通过 `config/instance.json.review_desk_commit` 固定该提交。
- 最终故事候选由 `codex.project task _prepare_integration` 生成并写入主项目任务账本。不得由本文的 Git 基线推断当前主干或正式运行版本；准备与推送回执留在任务本机运行记录。
- 本次业务增量为 0。未改小说、剧本、制作思路正文、媒体、历史修订、评论原文、采用或真实调用；不生成媒体，也不调用评论润色模型。

## 需求与八张原件的对应

完整任务依据是 [需求全文](../../planning/system-page-style-task.md)。八张 PNG 按原字节保存于 `inputs/`，文件名、字节数与 SHA-256 在 [原件清单](input-manifest.json) 中；均与主项目账本输入一致，未缩放、转码或重绘。下表的系统路径以系统仓库根为基准。

| 依据 | 实现位置与实际结果 | 验收证据 |
|---|---|---|
| 01：三层页头与剧本留白 | `review_desk/static/index.html` 唯一页头；`review_desk/static/navigation.js` 按当前路由提供标识、标题、用途；`review_desk/static/desk-theme.css` 统一间距。清除旧页头，资料／章节目录不重复介绍页 | [之前](evidence/before-screenplay.jpg)、[之后](evidence/after-screenplay-desktop.jpg)、[测量](evidence/after-spacing.json)、[全部页](evidence/pages.json) |
| 02：采编资料菜单与正文标题 | 资料目录、资料分组、章节及正文标题改浅色纸面；选中有边线与字重，小说评论高亮仍可读 | [采编页](evidence/after-sources-desktop.jpg)、[旧小说高亮](evidence/sources-existing-highlights.jpg) |
| 03：结构稿次、章节与正文标题 | 稿次横向可达、章节统一浅色选中；长作品标题换行，具体稿次与来源保留 | [结构页](evidence/after-structure-desktop.jpg)、[窄屏](evidence/after-structure-narrow.jpg)、[图示](evidence/structure-diagram-preview.jpg) |
| 04：剧本版本、分集、场次与正文标题 | 四类区域统一浅色；版号、评论数、场次估时和单场完整正文保留 | [剧本页](evidence/after-screenplay-desktop.jpg)、[窄屏](evidence/after-screenplay-narrow.jpg) |
| 05：拆解分集与场镜菜单 | 复用分集卡及两级目录，浅色选中有侧边线，末集／末镜可达 | [拆解页](evidence/after-breakdown-desktop.jpg)、[末镜](evidence/breakdown-last-shot.jpg)、[窄屏页首](evidence/after-breakdown-narrow-top.jpg) |
| 06：镜头制作分集与场镜菜单 | 同一导航风格；保留逐镜方案、右侧视频、小卡及显式上游参考选择 | [镜头页](evidence/after-shots-desktop.jpg)、[窄屏页首](evidence/after-shots-narrow-top.jpg)、[参考空态](evidence/shot-reference-empty.jpg) |
| 07：模型／强度与两个输入项 | `review_desk/static/app.js` 分区仍是同一表单；实际目录联动、帮助与字段错误；`review_desk/configuration.py` 将原 1000—30000 约束公开给前端，未扩大范围 | [配置页](evidence/after-system-desktop.jpg)、[错误](evidence/config-invalid.jpg)、[焦点](evidence/model-keyboard-focus.jpg) |
| 08：站点图标操作 | 当前图标与待保存预览分开；已有选择、上传、恢复默认与结果文案清楚；上传只登记，保存才应用 | [配置页](evidence/after-system-wide.jpg)、[交互结果](evidence/config-interactions.json)、[上传阻断](evidence/upload-blocker.json) |
| 全站菜单和控件 | 公共主题统一字体、行高、内边距、边框、圆角；默认／悬停／选中／焦点／禁用／错误可分辨，模型勾选、筛选与版本边线补充颜色识别 | [真实状态结果](evidence/config-interactions.json)、[键盘焦点](evidence/model-keyboard-focus.jpg)、[空态](evidence/entities-empty.jpg) |
| 双仓交付与过程收尾 | 准确系统提交、实例 pin、代码发布入口及下述恢复步骤；未把隔离库变成发布包 | [系统交接](system-delivery.json)、[自动检查](evidence/tests.json)、[资源清单](evidence/cleanup-pending.json) |

当前基线的采编、结构、拆解、镜头和配置另有 `before-*.jpg`。这些截图视口为 2166×872，用于配色与结构对照，不据此比较像素间距；只有剧本的前后截图使用同一 1280×900 视口进行距离测量。用户八张问题截图也保留为原件，截图中的旧模型、版号和计数没有写成默认值。

## 逐页覆盖

桌面检查为 1280×900，窄屏为 390×844；实际尺寸和路由用途记录在 [pages.json](evidence/pages.json)。十三页都只有一个可见页面级标题，正文和用途完整；页面宽度无横向溢出。横向目录本身仍可滚动，并不计作页面溢出。

| 主入口／子页 | 桌面 | 窄屏 |
|---|---|---|
| 制作思路／故事创作 | [页面](evidence/after-approach-story-desktop.jpg) | [页面](evidence/after-approach-story-narrow.jpg) |
| 制作思路／生产制作 | [页面](evidence/after-approach-production-desktop.jpg) | [页面](evidence/after-approach-production-narrow.jpg) |
| 故事创作／故事采编 | [页面](evidence/after-sources-desktop.jpg) | [页面](evidence/after-sources-narrow.jpg) |
| 故事创作／故事结构 | [页面](evidence/after-structure-desktop.jpg) | [页面](evidence/after-structure-narrow.jpg) |
| 故事创作／剧本创作 | [页面](evidence/after-screenplay-desktop.jpg) | [页面](evidence/after-screenplay-narrow.jpg) |
| 制作设定／制作拆解 | [页面](evidence/after-breakdown-desktop.jpg) | [页面](evidence/after-breakdown-narrow-top.jpg) |
| 制作设定／实体管理 | [页面](evidence/after-entities-desktop.jpg) | [页面](evidence/after-entities-narrow.jpg) |
| 制作设定／素材管理 | [页面](evidence/after-materials-desktop.jpg) | [页面](evidence/after-materials-narrow.jpg) |
| 全剧制作／镜头制作 | [页面](evidence/after-shots-desktop.jpg) | [页面](evidence/after-shots-narrow-top.jpg) |
| 全剧制作／组合与历史 | [页面](evidence/after-history-desktop.jpg) | [页面](evidence/after-history-narrow.jpg) |
| 系统管理／故事项目 | [页面](evidence/after-project-desktop.jpg) | [页面](evidence/after-project-narrow.jpg) |
| 系统管理／系统与 AI | [页面](evidence/after-system-desktop.jpg) | [页面](evidence/after-system-narrow.jpg) |
| 系统管理／编号前缀 | [页面](evidence/after-codes-desktop.jpg) | [页面](evidence/after-codes-narrow.jpg) |

页头间距为桌面 24 像素、窄屏 18 像素。拆解／镜头窄屏初始沿既有逻辑定位到首镜，`pages.json` 的屏幕间距因此为负数；该值不是页首测量。记录中的文档间距和另存的页首截图确认同为 18 像素，保留了原定位行为。宽屏 1920×1080 抽查了配置、结构和素材，均无页面溢出；十个结构稿次、长标题与三列素材卡可用。

## 交互结果与未验收项

已在隔离实例真实执行以下动作，详见 [配置结果](evidence/config-interactions.json) 和 [关键行为结果](evidence/regressions.json)：

- 已有图标选择与预览、恢复默认、与润色两块同时编辑、保存及刷新回读；当前图标与待保存预览保持区别。
- 环境变量名 `9BAD`、字数 `999` 拒绝并显示字段错误；改为有效值可保存，模型与推理强度联动，刷新和跨配置子页保留草稿。测试值只有变量名，没有真实密钥。
- 故障代理返回保存前 503、提交后响应丢失并阻断回读；界面分别显示“尚未确认保存”和“结果待确认”。恢复后先回读识别准确已保存版本，不重复 PATCH。
- 两个标签真实并发造成 409。旧版本草稿、图标选择和另一块输入保留；刷新仍使用原版本基线，不擅自覆盖最新配置。
- 默认、实际指针悬停、选中和键盘焦点有实测状态；模型 ArrowRight 联动可选强度，Tab 可到输入，保存后禁用态和字段错误有截图。
- 实体小卡打开大卡、版本 1／2 切换、采纳→取消→重采纳→取消；放大图、Escape 关闭、返回大卡与列表的阅读位置保持。实体筛选无匹配空态、分页、每页行数及浏览器前进后退可用。
- 末集 E17／S042／SH018 可达且 URL 保留准确修订；上游 M2507 无真实候选时，“选为本镜参考”禁用，浏览不写入选择。
- 剧本圈选、评论草稿收起／恢复、Enter 换行、⌘+Enter 提交、定位、Esc 放弃编辑及关闭后历史保留可用。旧小说 D037 的十六条评论、高亮和定位保持可读。
- 实体图像原件 2016×2688 可放大；真实 M1212／MV001／MC001 音频可播放、暂停和键盘操作时间轴。未评定媒体质量，也未生成测试视频替代既有素材。

**未通过的浏览器项：** Chrome 的 `fileChooser.setFiles` 报告 ChatGPT 扩展未启用“允许访问文件网址”；原生 Chrome 选择器替代入口返回 `Computer Use server error -10005: cgWindowNotFound`。有效文件上传、取消选择、无效文件、超限及上传失败的完整 UI 路径尚未实测，不能用自动测试或接口结果替代。工具要求的处理入口是 `chrome://extensions` → ChatGPT 扩展 → 详情 → Allow access to file URLs，见 [扩展说明](https://developers.openai.com/codex/app/chrome-extension#upload-files)。该权限由用户处理，开启后继续本任务补验。

自动检查：系统 Python 297 项、前端 Node 648 项、故事发布脚本 61 项通过；系统与故事 `git diff --check` 通过。前端检查覆盖无效字段拒绝前保留全部输入、文件取消／无效／超限错误、原有配置草稿、失败、未知结果与冲突契约；这些只算自动检查。既有图标导出、损坏及空库恢复沿系统 Python 回归验证，未把标签栏缓存或浏览器上传记为已通过。

## 正式交付与恢复顺序

以下是继续执行步骤，不是已经完成的发布回执。当前自动授权涵盖本任务的正式交付，但验收阻断必须先解决。冻结包准备、镜像构建与预检可以先独立完成；其最新结果和准确候选读取本机 `.runtime/system-page-style/release-final/run/delivery-preparation.json`，不据此推断已应用。

1. 在保留的隔离实例补齐文件上传路径，更新受影响证据并重新确认候选。新增改动必须先提交，再运行 `codex.project task _prepare_integration -g creative -p SnakeSlayingRecord --task task-20261005-0006 --push`。准确故事候选和目标从其回执读取，系统候选按 `system-delivery.json` 核对；候选变化补验相应范围。
2. 从本故事 worktree 执行 `scripts/material_review_release.py prepare`，传入本任务、系统 worktree、准确双仓候选／目标、`--push-system` 和本机 `.runtime/system-page-style/release` 包目录。沿既有构建及预检入口生成镜像和冻结清单，核对清单与镜像回执哈希。
3. 候选验收通过后用 `codex.project task _deliver` 受控交付故事 Git，再通过 `material_review_release.py apply --apply` 以准确清单及镜像回执哈希串行应用系统代码和正式服务。发布器保持正式活库与导出，本任务不导入隔离测试库或修改正式配置。
4. 从实际镜像、挂载和实例 pin 核对系统提交；真实浏览器检查 3000 全部子页与受影响关键路径，确认正文、评论和媒体引用。随后沿 `publish-system --apply` 正常推送系统并回读远端；失败、远端分叉或未知结果须按原入口核查，禁止强推或盲目重放。
5. 完成正式验收和过程清理后，把运行证据写入本机冻结包或任务完成说明，再调用 `_complete`。不修改已交付候选来追加运行日志。

代码故障优先依据冻结包保留的旧镜像与运行描述向前恢复服务，保全期间新增的评论、采纳及配置事件；不能回灌旧任务数据库。若尚未正式应用，只需保留任务候选和当前正式服务，不执行恢复。具体发布检查与恢复入口沿 [制作工作区规则](../generation-workspaces.md) 和发布脚本自身的冻结回执。

## 过程资源

首次收尾核对删除 1 份被最终检查替代的前端日志，66,799 字节；回读确认不存在。当时尚未构建发布镜像，Docker 删除数为 0。该阶段准确范围与回读在 [cleanup-pending.json](evidence/cleanup-pending.json)；后续冻结包与镜像的保留或清理以本机 `release-final/run/` 最新回执为准。

隔离预览 62660、故障代理 62661、预览库及基线副本、三份上传夹具、双仓 worktree 和必要测试日志保留，用于剩余浏览器验收与恢复；准备后的冻结包和候选镜像用于继续部署预检，不能替代上传验收或正式验收。它们仍有用途，当前不声称清理完成。责任为本任务执行者：上传权限恢复后补验，正式应用并验收后停止两个服务，再按准确路径删除无效库、夹具、代理和重复副本；有效提交与必要证据保留。嵌套系统 worktree 和故事 worktree 须待 TUI 退出、锁和挂载释放后走各自受管清理入口，不递归强删。
