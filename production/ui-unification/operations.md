# UI 统一候选的正式应用

本文供负责 `task-20261004-0008` 交付的主代理使用。目标是把已确认的界面与只读 API 投影应用到正式服务，保留全部业务数据，再完成双仓推送。本文是执行说明，不是发布回执；准确候选、发布包摘要和正式页面结果以本轮最终确认及运行回执为准。

本轮不导入制作数据、不迁移 Schema、不重建公开导出、不生成媒体。采用现有代码发布器的顺序：**固定候选 → 用户确认 → 系统本地集成及服务应用 → 正式页面回读 → 系统推送 → 故事 `_complete` 集成、推送及完成**。所有正式动作由同一主代理串行执行。`_complete` 成功后只读回执并报告，不再写文件、提交、部署或重复推送。

## 已核对的入口与基线

2026-10-04 本次只读核对得到以下结果；仅查询 Git 和源码，未操作正式容器或数据库。

| 对象 | 本地与远端 |
|---|---|
| 故事主仓 | `main` 为 `46b70f7abfba5b0c915006fceeb536a633506213`；上游 `origin/main`，实时 `refs/heads/main` 相同；工作区干净。远端：`git@github.com:goosmanlei/SnakeSlayingRecord.git`。 |
| 系统主仓 | 故事主仓同级 `../story-review-desk-python`；`main` 为 `9a1e68507b0be4219c119efb59076f59fd4bca24`；受管文件干净，有既存未跟踪 `.worktrees/`，不得清理。远端：`git@github.com:goosmanlei/story-review-desk.git`。 |
| 系统远端 | 上游为 `origin/main`；本地跟踪引用与实时 `refs/heads/main` 均为 `d6fe329de5b335b0a9afd2084987b09d0fa72e6a`。本地比远端多一个已集成的前置提交 `9a1e685`；本次系统推送会一并发布，最终确认必须展示完整范围。 |
| 系统任务工作区 | 相对故事任务根为 `.runtime/ui-unification/system`，分支 `task-20261004-0008`。故事候选的 `config/instance.json` 必须固定最终系统候选的完整 SHA。 |

[代码发布器](../../scripts/material_review_release.py) 复用 [正式服务守卫](../../scripts/autonomous_optimization_release.py) 和 [系统快进工具](../../scripts/integrate_generation_review_system.py)。它将系统候选打入固定镜像，把候选 `config/instance.json` 与现行相同的制作思路内容挂载为永久只读文件；数据库与媒体继续来自故事主仓 `/instance`。发布器要求 Nginx 环回入口 `3000`、`64401` 和已有 CA 挂载，实际运行态须由 `prepare`、`preflight` 重新核对，不能从本说明推定当前服务已经符合要求。

发布器已登记 `task-20261004-0008`，唯一发布前缀为 `ui-unification-20261004-0008`。任务识别、准确包回读和故事目标守卫已由 [发布器测试](../../tests/test_material_review_release.py) 覆盖：应用前故事 `main` 必须仍等于批准的旧目标，不接受本候选提前合入。现有发布器和任务 CLI 已具备本轮所需的顺序，无须新增交付包装脚本，也无须调用任务运行器内部 Python API。

前置 [制作拆解操作说明](../breakdown/operations.md) 的 `--allow-internal-task-api` 和 `integrate(..., complete=False)` 例外仅属于前置任务。本次不调用 `production_breakdown_release.py`，不继承那次授权。

## 确认前固定候选

以下命令均从故事任务 worktree 根目录执行，须使用原任务执行会话与租约。变量采用本任务前缀，不覆盖用户环境变量。先完成系统提交，把其完整 SHA 固定到故事 `config/instance.json`，再提交故事文档、脚本、测试和已完成的验证证据。本文中的最终 SHA 保留参数占位；实际值写入本机发布包与最终确认消息，不为回填本文再造一轮候选提交。随后准备故事集成候选：

```bash
~/bin/codex.project task _prepare_integration \
  -g creative -p SnakeSlayingRecord --task task-20261004-0008 --push
```

该命令会同步故事上游并记录后续集成、推送计划，此时不执行正式集成、推送或完成。若出现冲突，由主代理在任务工作区解决、提交，再准备；候选改变后补验受影响内容。回执须明确故事目标 `main`、远端 `origin`、`refs/heads/main` 和最终候选。此后到 `_complete` 之间保持双仓候选受管文件不变；发布包和正式回读结果写在未跟踪 `.runtime/` 中。

在同一 shell 设置以下参数。两个 `PENDING_...` 必须替换为主代理最终候选的 40 位 SHA；不得用当时 `HEAD` 自动替代已确认的值。目标基线若已变化，应重新准备并审阅变化，不能直接改变量继续旧发布包。

```bash
set -euo pipefail
UI_STORY_ROOT="$PWD"
UI_SYSTEM_WORKTREE="$UI_STORY_ROOT/.runtime/ui-unification/system"
UI_STORY_MAIN="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
UI_SYSTEM_MAIN="$(dirname "$(git -C "$UI_SYSTEM_WORKTREE" rev-parse --path-format=absolute --git-common-dir)")"
UI_STORY_CANDIDATE='PENDING_STORY_CANDIDATE'
UI_SYSTEM_CANDIDATE='PENDING_SYSTEM_CANDIDATE'
UI_STORY_TARGET='46b70f7abfba5b0c915006fceeb536a633506213'
UI_SYSTEM_TARGET='9a1e68507b0be4219c119efb59076f59fd4bca24'
UI_SYSTEM_REMOTE_TARGET='d6fe329de5b335b0a9afd2084987b09d0fa72e6a'
UI_BUNDLE="$UI_STORY_ROOT/.runtime/ui-unification/release"
if ! [[ "$UI_STORY_CANDIDATE" =~ ^[0-9a-f]{40}$ ]] || ! [[ "$UI_SYSTEM_CANDIDATE" =~ ^[0-9a-f]{40}$ ]]; then
  printf '请先填写已审阅的双仓候选 SHA。\n' >&2
  exit 1
fi
```

只有最后一条检查成功才继续。`UI_BUNDLE` 必须是尚不存在的新目录；重新准备使用新目录名，不覆盖旧包。下列命令使用现有 CLI 参数：

```bash
python3 scripts/material_review_release.py prepare \
  --task task-20261004-0008 \
  --story-worktree "$UI_STORY_ROOT" \
  --system-worktree "$UI_SYSTEM_WORKTREE" --bundle "$UI_BUNDLE" \
  --story-candidate "$UI_STORY_CANDIDATE" --story-target "$UI_STORY_TARGET" \
  --system-candidate "$UI_SYSTEM_CANDIDATE" --system-target "$UI_SYSTEM_TARGET"
python3 scripts/material_review_release.py build --bundle "$UI_BUNDLE"
python3 scripts/material_review_release.py preflight --bundle "$UI_BUNDLE"
git -C "$UI_SYSTEM_WORKTREE" log --oneline "$UI_SYSTEM_REMOTE_TARGET..$UI_SYSTEM_CANDIDATE"
```

`prepare` 固定双仓提交、运行镜像和挂载、配置、CA 摘要、系统源文件与发布脚本；`build` 只创建本地镜像，沿用已核验基础镜像并禁用网络拉取；`preflight` 只读复核正式资源及系统快进条件。这些命令不导入正式数据、不切服务、不推送。

向用户展示双仓完整候选及改动范围、40 项检查的实际结果、未验项、manifest 与镜像回执 SHA-256、上述系统远端到候选的完整提交范围，以及下面的固定顺序。明确此次服务应用先于故事主仓集成：运行代码与只读实例文件均取自已确认候选，故事主仓最后由 `_complete` 快进。取得对候选、顺序、双仓目标和正式服务应用的明确确认后才能进入下一节。

## 确认后串行执行

先把用户已确认的两个包摘要填入变量；不是临执行时重新计算一个变化后的摘要来替代原确认。

```bash
UI_MANIFEST_SHA='PENDING_APPROVED_MANIFEST_SHA256'
UI_IMAGE_RECEIPT_SHA='PENDING_APPROVED_IMAGE_RECEIPT_SHA256'
if ! [[ "$UI_MANIFEST_SHA" =~ ^[0-9a-f]{64}$ ]] || ! [[ "$UI_IMAGE_RECEIPT_SHA" =~ ^[0-9a-f]{64}$ ]]; then
  printf '请先填写用户已确认的准确包摘要。\n' >&2
  exit 1
fi
python3 scripts/material_review_release.py apply \
  --bundle "$UI_BUNDLE" --apply \
  --manifest-sha256 "$UI_MANIFEST_SHA" \
  --image-receipt-sha256 "$UI_IMAGE_RECEIPT_SHA"
```

发布器在共享锁内重新检查候选和目标，备份此刻最新正式库供核查，快进系统主仓，应用固定镜像与永久文件挂载，再核对健康、运行源文件、实例文件和原有业务身份及不可变历史。`business_delta: 0` 表示本包没有业务导入，不能解释为用户并发评论数必须完全不变。`before.sqlite3` 只作审计与隔离恢复资料，禁止复制覆盖活库。此时故事主仓尚未集成，返回 `formal_browser_pending` 也不是任务完成。

随后由主代理在正式入口进行一次重点只读浏览器回读：采编阅读基准；结构版本常驻及章节滚动；剧本版本／集／场；制作设定和全剧制作页签；实体／素材共用大卡及准确历史链接；制作拆解与镜头制作的集场切换、逐镜归属、提示词参考与既有媒体。正式库不写测试评论、采纳或采用。记录实际视口、对象／修订、操作与结果；浏览器受阻按项目规则处理，未验项不计通过。

正式回读和服务证据在 `_complete` 前保存到 `UI_BUNDLE/run/`，受管文档不为补日志改动；这些事实通过最终完成说明与包路径交接。若正式页面需要代码修复，停止收尾，修复后重建候选和发布包、补验并重新确认。

正式回读通过后推送系统仓库。先确认系统本地 `main`、任务工作区均为已批准候选，并检查远端基线是候选祖先。远端须仍为批准基线；若它已经是相同候选，则只回读，不重复推送。下列任一检查不符即停。推送不用强推，也不改远端配置。

```bash
test "$(git -C "$UI_SYSTEM_MAIN" branch --show-current)" = main
test "$(git -C "$UI_SYSTEM_MAIN" rev-parse HEAD)" = "$UI_SYSTEM_CANDIDATE"
test "$(git -C "$UI_SYSTEM_WORKTREE" rev-parse HEAD)" = "$UI_SYSTEM_CANDIDATE"
test -z "$(git -C "$UI_SYSTEM_MAIN" status --porcelain --untracked-files=no)"
test -z "$(git -C "$UI_SYSTEM_WORKTREE" status --porcelain --untracked-files=no)"
git -C "$UI_SYSTEM_MAIN" merge-base --is-ancestor "$UI_SYSTEM_REMOTE_TARGET" "$UI_SYSTEM_CANDIDATE"
UI_SYSTEM_REMOTE_NOW="$(git -C "$UI_SYSTEM_MAIN" ls-remote --heads origin refs/heads/main | cut -f1)"
if [ "$UI_SYSTEM_REMOTE_NOW" = "$UI_SYSTEM_REMOTE_TARGET" ]; then
  git -C "$UI_SYSTEM_MAIN" push origin "$UI_SYSTEM_CANDIDATE:refs/heads/main"
elif [ "$UI_SYSTEM_REMOTE_NOW" != "$UI_SYSTEM_CANDIDATE" ]; then
  printf '系统远端已偏离批准基线或候选，停止交付。\n' >&2
  exit 1
fi
test "$(git -C "$UI_SYSTEM_MAIN" ls-remote --heads origin refs/heads/main | cut -f1)" = "$UI_SYSTEM_CANDIDATE"
```

系统推送及回读成功、全部必要证据已保存后，最后核对故事仍是原准备状态，再执行本任务最后一条会写入状态的命令。任一核对失败即停，不重新准备或扩大推送范围来绕过批准的候选：

```bash
test "$(git -C "$UI_STORY_MAIN" branch --show-current)" = main
test "$(git -C "$UI_STORY_MAIN" rev-parse HEAD)" = "$UI_STORY_TARGET"
test "$(git -C "$UI_STORY_ROOT" rev-parse HEAD)" = "$UI_STORY_CANDIDATE"
test -z "$(git -C "$UI_STORY_MAIN" status --porcelain --untracked-files=no)"
test -z "$(git -C "$UI_STORY_ROOT" status --porcelain --untracked-files=no)"
test "$(git -C "$UI_STORY_MAIN" ls-remote --heads origin refs/heads/main | cut -f1)" = "$UI_STORY_TARGET"
~/bin/codex.project task _complete \
  -g creative -p SnakeSlayingRecord --task task-20261004-0008 \
  --note '用户已确认双仓准确候选、系统完整推送范围及服务顺序；正式服务与重点页面已回读，系统 origin/main 已核对；执行证据见本任务 .runtime/ui-unification/release/run，故事集成推送由本命令完成。'
```

若实际包目录不是 `release`，须在调用前把完成说明中的路径改为实际目录。`_complete` 根据已准备候选执行故事快进、推送及远端回读，成功回执才是完成依据。命令不重定向到任务文件；成功后只读取该回执、双仓提交和远端引用并报告，不再补写文档／截图／回执文件，不再提交、推送、重启或清理工作区。

## 中断与恢复

- `apply` 失败：保留准确包与回执，先确认仍是原运行态或本候选；只有包、候选和目标都未漂移才按原授权重试。其他任务已应用服务时停止，不接管它。
- 服务需要退回：在 `_complete` 前可使用同一包与原批准摘要执行 `python3 scripts/material_review_release.py recover --bundle "$UI_BUNDLE" --apply --manifest-sha256 "$UI_MANIFEST_SHA" --image-receipt-sha256 "$UI_IMAGE_RECEIPT_SHA"`。它恢复原镜像与挂载，不恢复数据库、不重置 Git；撤回系统提交或业务变更须另行处理。
- 系统推送失败：尚未调用 `_complete`；保留已应用服务与系统本地集成事实，排查远端。如果一次推送已成功但本机中断，先 `ls-remote` 确认已是同一候选，直接进入后续步骤，不重复推送或要求远端退回旧基线。
- `_complete` 失败：按任务账本确认是否“已集成、待推送”，使用受管恢复路径；不手改账本、重置故事主仓或另造提交。只有成功后才适用本任务的终态禁写约束。
- 完成后的常规重启属于后续维护。本轮不在 `_complete` 后运行它；既有发布器的永久 `material_review_release.py restart --release . --apply` 仅重启仍属于同一发布的容器，不能用普通 Compose 重建覆盖固定镜像。

## 本说明的核验范围

按 `document-writing` Skill 以交付主代理为读者走查：能够依本文找到原任务入口、固定双仓与发布包、说明确认范围、执行串行应用、处理失败并在完成后停止写入。命令参数已对照发布器 CLI 和本机 `codex.project` 的 `_prepare_integration`／`_complete` 实现；Git 分支与远端同时用本地引用和只读 `ls-remote` 核对。发布器 9 项离线测试通过，本文的 Bash 命令块已做语法检查、相对文件链接已回读。未执行本文的 prepare、build、preflight、apply、push 或 `_complete`，未核验当前正式容器／数据库；最终候选、真实发布与浏览器验收仍由主代理完成。
