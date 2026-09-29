# 评论输入快捷键交付说明

故事采编、故事结构和剧本分集共用评论编辑器。输入框聚焦时，⌘+Enter 执行“提交评论／保存修改”，Esc 执行“取消本次评论／取消编辑”。取消会放弃当前未提交内容并删除对应本机草稿；已保存评论不变，面板保持打开。普通 Enter 换行。输入框外 Esc 仍收起评论面板并保留草稿，图像弹窗中的 Esc 仍只关闭图像。

空白正文不可提交；保存请求期间输入框只读，提交、取消和草稿操作暂时禁用，重复按键或点击不能重复提交。请求失败保留草稿并解除限制。中文输入法组合期间不触发提交或取消，也不连带收起面板。

## 实现与仓库边界

系统源码从故事主项目根定位 `../story-review-desk-python`。本轮从已集成剧本集场界面的系统 `1c86fb9` 建立独立 worktree，在本任务 `.runtime/review-desk-worktree/` 修改共用 `review_desk/static/app.js`，没有从旧 `../story-review-desk` 继承代码。系统分支为 `codex/task-20260930-0001-comment-shortcuts`，过程提交 `1107f70`、最终提交 `39ff95ef7d2b2dea6bb4fd62fb88fc64b7a01a6e`。

未来新增评论区复用 `bindCommentEditorShortcuts(textarea, {submit, cancel})`，传入实际按钮，由按钮及保存函数共同维护验证、提交锁与取消语义。共用编辑器已统一接入，三个工作区无需各写一份全局键盘处理。系统 README 与 `docs/comment-checklist.md` 包含说明和验收入口。故事实例只更新 `config/instance.json` 的系统版本锁及项目说明、知识、状态和验证记录，故事正文、业务导出未改。

## 复现验收

在系统任务 worktree 根启动一次性夹具，端口可以按需选择：

```bash
PYTHONPATH=.:tests python3 tests/screenplay_server.py --port 8796 --evidence /tmp/comment-shortcut-browser.json
```

用浏览器访问 `http://127.0.0.1:8796/comment-shortcut-tests`，点击“运行快捷键检查”。测试只使用临时资料和数据库。页面还可选择三类“真实键盘页面”并准备草稿，以实际按键核验换行、提交、保存与取消。组合输入通过事件模拟核验，不等于操作系统输入法实测。重新跑完整检查前重启夹具，避免已提交评论污染初始条件。

另以独立端口启动同一服务器，访问 `/screenplay-tests` 运行集场与评论联合回归；用 `PYTHONPATH=. python3 tests/selection_server.py --port 8798` 核验圈选与定位。系统单测为 `PYTHONPATH=. python3 -m unittest discover -s tests -v`。故事任务根用 `PYTHONPATH=.runtime/review-desk-worktree:. python3 -m unittest discover -s tests -v`，系统依赖显式取当前独立 worktree，不复制密钥、数据库或依赖目录。

实际通过：快捷键 76 项、集场 42 项、圈选 17 项、真实键盘 15 项、系统单测 29 项及故事单测 60 项（既有条件跳过 1 项）。具体覆盖和限制见 [VERIFICATION.md](../VERIFICATION.md)，本机证据在 `.runtime/comment-shortcuts/evidence/`。

## 正式运行与待确认集成

本任务验收要求先发布本机正式系统并回读，已在系统仓库 `.git/review-desk-integration.lock` 内串行完成。沿用原容器 Python 环境构建完整代码，不依赖 Docker Hub；替换 app、重启 Nginx，保留运行环境与正式库、可信 CA 挂载。当前 3000 服务使用系统 `39ff95e`，11 份静态文件与候选源码逐字节一致。Chrome 只读实查精修九、结构和两版集场页面；发布前后八类业务表和五组业务 API 一致，191 条正式评论未变。没有写测试评论、恢复旧快照或重新导出。

本机发布不等于任务完成。故事成果提交到 `codex-project/task-20260930-0001` 后，通过 `_prepare_integration` 将最新故事 main 合并到当前任务 worktree，对命令返回的候选复验；系统分支也核对并吸收最新系统 main。用户确认具体候选及验证证据后，按序将系统 main 快进到上述提交，再运行本任务指定 `_complete` 完成故事的受控本地集成。若任一目标变化则重新准备、验证和确认；不自动推送。

`_complete` 成功后不再补写代码或状态，不清理 worktree 和分支，不领取其他任务。任务完成状态以主项目账本为准；正常退出会话后才释放运行锁。
