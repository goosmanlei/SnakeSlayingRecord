# 故事创作导航与评论数量交付

三个子页面的一级导航持续选中“故事创作”，当前 Tab 准确标识采编、结构或剧本。采编右上搜索框、资料总数、相关状态及事件和正文重复“审阅意见”按钮已移除；完整资料列表通过浮动“查看评论”、正文高亮和圈选继续审阅。实现已应用到本机 3000，两个仓库的 Git 本地集成及任务完成仍待用户确认；本任务不推送。

## 数量与交互

- 资料条目把标题保留在主行，次行显示“评论 N”；精修版本的箭头、选中态及章节展开／收起保持。分类区分“资料 N 项”和所属条目的评论合计。章节只作导航。
- 结构每个“第 N 稿”显示自身精确修订的评论总数；文字、整篇、整图和区域评论均计入。零评论显示“评论 0”。页面说明和计数提示明确包含已关闭评论。
- 总数读取现存评论并按 UUID 去重；不同资料、修订和稿次分别统计，删除记录与编辑／状态事件不计入。新增增加，编辑、关闭和重开不改变；重新取得数据及刷新后同步。共用面板原有“未关闭／历史待决”继续使用原口径。
- 页面通过 `/api/sources?with_revision=1` 取得展示资料的当前对象修订。默认 `/api/sources` 保留原始文档格式，避免破坏后台冷读工具的完整文档比对。字段不写入资料或公开导出，不改正文、锚点和数据结构。

## 双仓版本与合并

系统根目录按故事主项目定位 `../story-review-desk-python`，本任务系统 checkout 在当前故事 worktree 的 `.runtime/review-desk-worktree/`；不从嵌套目录拼接相邻系统路径。系统分支为 `codex/task-20260930-0003-creation-ui`，从已完成 favicon 的系统 main `d7646d8` 建立，过程提交 `bbc9c2c`，兼容修正 `7d36e6d`；按用户追加要求移除采编页头资料总数后的最终提交 `e48218947a6cf74e48bad7a0b4909ae334562a81`。系统 `main` 已核对，无新代码需合并；目标仍为本地 `main`。

故事复用 `codex-project/task-5d617876a40f/task-20260930-0003`，通过 `_prepare_integration` 吸收最新 main `1845701`。冲突只在 STATE 和系统版本引用，已在本 worktree 解决：保留当前界面候选，吸收 favicon 图样、使用说明及 HTTP 测试路径适配，把已完成 favicon 的旧待确认表述收敛为当前状态。没有恢复旧快照、覆盖最新作品或领取其他任务。最终故事候选以最近准备回执为准；实例系统版本引用固定为上述 `e482189`。

## 实际验证

| 范围 | 结果和边界 |
| --- | --- |
| 自动测试 | 系统 35 项、故事 60 项全部通过，无跳过。包含默认资料 API 格式、可选修订字段、评论精确归属及后台冷读 HTTP 集成。 |
| Chrome 界面统一 | 78 项通过：三页直接链接／刷新／切换／前进后退、移除搜索、页头资料总数与重复按钮、零／多／关闭评论、分类合计、历史资料修订隔离、两稿和四类结构锚点、计数刷新及 UUID 去重，1400／390 像素边界、菜单操作与选中态。 |
| 共用评论和剧本 | 快捷键 76 项、剧本集场 42 项、圈选／定位与阅读状态 17 项通过。覆盖草稿、编辑、关闭／重开、定位、快捷键、保存限制和新版稿次／集场隔离；组合输入保护是测试事件模拟。 |
| 真实交互与布局 | 在隔离端口真实拖到正文外松手，添加正确引用；真实 Enter 换行、⌘+Enter 新增保存、Esc 取消编辑后原评论保持。同任务前轮完整最新实例检查桌面及 390 像素三页，本轮补查采编去除页头总数后的桌面及窄屏，标题、计数、精修和分类展开／收起以及结构版本选中均可使用。 |
| 正式 3000 只读 | 45 资料、10 稿、三个剧本版本与最新 17 集可阅读；三页一级导航和 Tab、浏览器历史／刷新及共用面板开关正常，无控制台错误。全部资料／分类和结构版本的浏览器数量逐一与正式库精确修订核对一致。民间小故事评论 0、扩写方向评论 19、故事精修评论 108。 |
| 数据与运行保护 | 正式候选应用及浏览器回查前后，全部数据库表行数与行哈希一致，保留本轮最新基线的 193 评论、105 对象及全部用户配置。25 份实际 Python／静态文件与候选逐文件 SHA-256 一致；默认资料 API 格式兼容。未导出覆盖正式数据或改正文，测试评论只在临时夹具。 |

本轮新候选重新通过 35／60 项自动测试与四组 78／76／42／17 项浏览器检查；正式部署以应用前最新库为基线，193 条评论逐表保留，没有恢复前轮 191 条评论的旧快照。

未发生浏览器初始化阻断。自动圈选检查与真实手势分别记录，没有把 DOM Range 或接口成功当作真实手势、页面或用户验收。

## 复现与证据

从系统任务 worktree 根启动独立夹具，每轮重启以恢复初始数据：

```bash
PYTHONPATH=.:tests python3 tests/creation_ui_server.py --port 8803 --evidence /tmp/creation-ui.json
PYTHONPATH=.:tests python3 tests/screenplay_server.py --port 8804 --evidence /tmp/shortcuts.json
PYTHONPATH=.:tests python3 tests/screenplay_server.py --port 8805 --evidence /tmp/screenplay.json
PYTHONPATH=. python3 tests/selection_server.py --port 8806
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

分别在浏览器打开 `/creation-ui-tests`、`/comment-shortcut-tests`、`/screenplay-tests`、`/selection-tests`。本次另从执行时最新正式库只读一致备份建立隔离实例，端口 8807；不复制密钥。后台源修订夹具仅用于测试，不改变生产导入的不可变语义。故事根测试需显式指定系统路径：

```bash
REVIEW_DESK_SYSTEM_PATH="$PWD/.runtime/review-desk-worktree" \
PYTHONPATH=".runtime/review-desk-worktree:." \
python3 -m unittest discover -s tests -v
```

本机证据位于当前故事 worktree 的 `.runtime/creation-ui/evidence/`，不入公开 Git：`creation-ui.json`、`shortcuts.json`、`screenplay.json`、`selection-result.txt`；`system-tests.log`、`story-tests.log`；三页 `*-desktop.png`、`*-narrow.png` 及精修收起／选中截图；`native-drag-draft.png`、`native-keyboard-saved.png`（同任务前轮真实交互）；本轮 `sources-narrow-final.png`；`formal-{sources,outline,script}.png`、`formal-source-counts.json`、`formal-structure-counts.json`、`formal-deploy.json`、`final-verification.json`。浏览器截图仅作验收证据，不是新创作媒体。

## 当前候选与确认后的步骤

共享正式资源更新取得系统仓库 `.git/review-desk-integration.lock` 后串行应用，保留原正式运行环境、正常主项目 `/instance` 和可信 CA 挂载；凭据只在内存中继承到 Docker，不写工作区或输出。实际容器为 `story-review-desk-creation-ui:e482189`；先前的 `d7646d8` 及过程候选停止容器保留供回退。发布锁已释放，任务会话运行锁仍保留。

用户确认最终两个候选后，重新核对系统 main、故事准备回执、任务账本及发布锁。系统本地 main 快进到 `e482189`，故事只运行指定 `_complete` 完成受控集成与任务登记；任一目标或候选变化则重新准备、验证并取得新确认。`_prepare_integration`、候选运行和验证均不代表任务完成或用户认可。只做本地集成，不推送。

`_complete` 成功后不补写文件或提交，只回读账本与运行状态。保留工作区和分支，不自动清理、不领取下一任务；正常退出会话后才释放任务运行锁。
