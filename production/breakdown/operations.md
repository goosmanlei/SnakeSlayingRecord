# 候选准备、正式应用与恢复

所有实现、设计、测试与提交在任务隔离工作区完成。故事主仓和通用系统主仓都以 `main` 为本地集成目标；故事远端为 `origin` 的 `refs/heads/main`，由本次 task run 的 `_complete` 推送并回读。系统仓库本轮只进行本地受控集成，不擅自远端推送。正式资源按下述顺序串行使用。

## 确认前准备

1. 系统候选提交后，在故事 `config/instance.json` 固定系统提交；故事把完整首稿、增量、导出、操作说明和验证证据一起提交。保留合并恢复及过程提交。
2. 运行 `codex.project task _prepare_integration -g creative -p SnakeSlayingRecord --task task-20261004-0007`。它只准备候选，不等于验收或用户确认；冲突在任务 worktree 解决、提交，再准备。候选或输入变化仅补验受影响范围。
3. 以下命令使用准备回执中的实际 SHA，创建新的本机未跟踪发布目录。构建固定系统镜像，预演最新正式库的准确增量；不写正式业务数据，不切服务。

```bash
python3 scripts/production_breakdown_release.py prepare \
  --bundle .runtime/breakdown/release \
  --system-worktree .runtime/breakdown/system \
  --story-candidate STORY_CANDIDATE --story-target STORY_TARGET \
  --system-candidate SYSTEM_CANDIDATE --system-target SYSTEM_TARGET
python3 scripts/material_review_release.py build --bundle .runtime/breakdown/release/service
python3 scripts/production_breakdown_release.py preflight --bundle .runtime/breakdown/release
```

`STORY_*`、`SYSTEM_*` 为参数占位，不是可直接执行的提交名。发布包固定两仓提交、正式运行基线、配置和制作思路挂载、CA 哈希、准确增量、全部原件哈希、脚本及任务运行器源码哈希。构建回执另固定镜像内容与镜像回执哈希。最终展示这些候选与回执，再请求用户确认。

## 需要明确确认的一处分阶段例外

用户要求先合并两仓代码，再迁移正式数据和应用服务，正式重点页面验收后才办理完成。当前任务 CLI 的 `_complete` 把故事集成、推送和完成合在一起，没有公开“只集成、暂不完成”的命令；同时本次 task run 又限定只能通过内部命令更新任务账本。

因此候选提供了待批准的 `production_breakdown_release.py`：调用现有任务运行器的认证、加锁集成实现 `task_worktree.integrate(..., complete=False)`，暂不推送或标记完成；不手工编辑账本。**这偏离“只通过内部命令”的限制，必须在最终确认中单独明确允许，不能由脚本参数冒充授权。** 未获该例外许可时只保留候选及发布包，不能提前 `_complete` 来假装正式验收已完成。

## 确认后的固定顺序

使用最终展示的外层 manifest 和镜像回执哈希，只有收到真实用户确认才执行：

```bash
python3 scripts/production_breakdown_release.py apply \
  --bundle .runtime/breakdown/release --apply --allow-internal-task-api \
  --manifest-sha256 APPROVED_MANIFEST_SHA \
  --image-receipt-sha256 APPROVED_IMAGE_RECEIPT_SHA \
  --note '用户确认的双仓候选、正式增量与服务应用；页面验收后办理完成'
```

脚本依次执行：确认提交、脚本、原件、CA、服务镜像与挂载未漂移；对最新正式库预演；通过认证的任务集成路径合入故事；用既有系统集成工具快进系统；备份最新正式库并事务式应用准确增量；安装固定镜像与永久配置挂载并验证健康及历史保存。任何阶段失败就停止，不调用 `_complete`，不推送，不覆盖活库。

随后只做一次正式重点浏览器回读：制作拆解 E01 与 E17；E17-002 念读状态和准确正文；实体李寄的已有原件与历史；E17/s042 素材筛选；镜头制作未生成和输入缺项；故事、剧本及共用播放器关键路径。正式回读不新增测试评论或采用。通过后执行：

```bash
codex.project task _complete -g creative -p SnakeSlayingRecord \
  --task task-20261004-0007 --note '经确认的候选、增量迁移、正式页面和测试证据；方案交付不等于媒体完成'
```

`_complete` 回查候选与目标、推送故事 `origin/main` 并回读，成功回执是完成依据。必要的实际 SHA、时间和正式验收记录保存在任务账本或本机发布包，确认后不为补日志修改已确认候选。成功后不再写任务文件，不清理工作区、不领下一任务；正常退出会话才释放运行锁。

## 中断和恢复

外层发布包保存分阶段回执。只有候选、目标、脚本、原件、配置和任务运行器哈希未变化，且当前服务仍是批准前或本候选运行态时，才可按同一真实授权重试。故事部分集成使用运行器原有恢复路径；系统快进和增量发布可幂等重试。并发业务评论保留，受影响头变化则整批拒绝；涉及原确认的变化必须重新准备、补验、确认。

服务应用失败时，内层 `material_review_release.py recover` 可以恢复批准前镜像和挂载，仍需原批准哈希与 `--apply`；它不还原数据库、不重置 Git。旧程序若暂不识别新索引，仅用于旧入口应急，不用它导出覆盖 Schema 5 交付。已迁移数据的修复采用新受控增量；`before.sqlite3` 只作审计与空实例恢复资料，禁止复制覆盖活库。

新服务的常规重启入口会固定在主项目 `.runtime/service-releases/breakdown-20261004-0007-…/`；使用该发布目录内 `material_review_release.py restart --release . --apply`，不要运行普通 compose 重建覆盖准确镜像。永久发布挂载不依赖任务预览目录；未撤除的临时挂载会在 preflight 阶段报告，不能留到确认后临时设计。
