# 在任务工作区生成和审阅，合并后发布

图像、音色和歌曲的生成原件、请求、回执、登记数据及导出文件先保存在自己的 Git worktree。任务审阅使用自己的数据库和端口。完成审阅后，将交付文件提交任务分支并合入 `main`，再在共享写入窗口向正式库应用增量；Git 合并不会自动发布数据库。

本流程由故事仓库工具实现，复用通用审阅台已有的数据、预览、评论和审阅接口。没有修改 `codex.project`、自动部署钩子或正式服务配置。历史素材保持原有身份与引用；新规则从已同步这些工具的任务开始执行。

## 目录与写入边界

以下路径均相对任务 worktree 根目录。脚本默认使用自身所在的仓库根目录，显式 `--workspace` 可选择另一任务 worktree；不要把它设为主目录。相对的实例、发布包和输出路径均按所选工作区解析。请求规格、外部响应文件及 `--system` 等输入文件参数按命令当前目录解析；Lyria 规格内的歌词和方向文件按规格所在目录解析。

| 内容 | 位置 | 如何进入主干 |
| --- | --- | --- |
| 临时候选、原始模型响应、私有备份和调试材料 | `.runtime/` | 不提交；结项保留必要记录，清理无效副本 |
| 独立审阅库、初始化基线、私有导出 | `.runtime/generation/review/` | 数据经审阅后制作增量包 |
| 交付原件与必要元数据组件 | `export/assets/<sha256>.<后缀>` | 提交任务分支，随 Git 合并 |
| 公开请求、实际回执、登记批次 | `production/requests/`、`production/receipts/` 及相应制作目录 | 脱敏核对后提交任务分支 |
| 审阅后的准确增量 | `production/publications/<名称>.json` | 与原件一起提交、合并；正式入库时逐字节核对 |
| 可恢复导出 | `export/` 与匹配的 `production/replay.json` | 在工作区生成并核验，再提交、合并 |
| 发布备份与执行回执 | `.runtime/generation/publications/<运行名>/` | 仅保留本机；有效恢复与追溯记录保留，失效副本结项清理 |

生成、登记、恢复及导出入口拒绝主目录、`main` 分支、游离提交和越出工作区的输出；写入路径不得包含工作区内的符号链接。只读检查和离线请求预览仍可在主目录运行。这是项目脚本的路径约束，不接管手工 shell 操作或通用系统 CLI，因此后者也须遵守本页约定。

账号互斥是共享例外：Lyria 保留主目录 `.runtime/lyria/account.lock`，Seed Audio 使用主目录 `.runtime/production/seed-audio.lock`。这里仅协调调用，不保存新素材。Seed Audio 汇总已登记 worktree 的配额回执，按请求 ID 去重；状态不一致时保留较大的扣减或预留。未归档的调用回执不能随意删除，不能通过换 worktree、删目录或换尝试 ID 释放已用额度。历史额度观察不代表当前余额，生成范围和费用仍按当次授权核对。

## 初始化与恢复审阅

先创建或进入自己的任务 worktree，并同步最新主干。无正式任务记录的独立工程工作也可以使用独立分支；不要为了使用这些工具另建任务账本。下列命令从 worktree 根目录执行：

```bash
generation_main=$(python3 -c 'from pathlib import Path; from scripts.generation_workspace import primary_root; print(primary_root(Path.cwd()))')
generation_system="$generation_main/../story-review-desk-python"

python3 scripts/generation_review.py --system "$generation_system" \
  --instance .runtime/generation/review init
python3 scripts/generation_review.py --system "$generation_system" \
  --instance .runtime/generation/review serve
```

`generation_system` 可改为任务自己的通用系统工作区，执行前核对它与 `config/instance.json` 的系统提交一致。`init` 用 SQLite 一致性备份读取当前正式库，保留为不可重置的初始化基线，再建立独立活跃库并复制原件。它不迁移或修改正式库。页面标题追加“任务预览”；`serve` 只监听 `127.0.0.1`，默认自动选择空闲端口，使用终端实际打印的地址。

中断后直接重启同一实例的 `serve`。`init` 遇到已有目录会拒绝；不要删除活跃库重新初始化。需要从已提交导出恢复时，使用新的目标：

```bash
python3 scripts/production_review.py --system "$generation_system" recover \
  --destination .runtime/generation/recovered
python3 scripts/generation_review.py --system "$generation_system" \
  --instance .runtime/generation/recovered serve
```

恢复实例没有生成任务的初始化基线，不能直接用 `prepare` 推断正式增量。已有旧任务继续使用自己的准确登记包和相应发布入口；不能把旧恢复副本冒充最新正式基线。

## 生成、登记与审阅

1. 使用本工作区的 `seed_audio.py`、`lyria_music.py` 或图像工具。外部图像工具返回到其原生缓存时，`record_builtin_image.py` 将准确原件与真实回执收敛到本 worktree，不复制到主目录。Lyria 原始响应与候选先留在 `.runtime/lyria/<id>/`，整理交付时再登记内容寻址原件。
2. `register_production_candidates.py`、`register_full_generation.py`、`register_generation_batch.py` 的 `--instance` 必须指向本工作区 `.runtime/` 下的实例。通用系统的 `production-file`、`production-import` 也只针对该实例调用；不使用正式主目录作为日常生成目标。既有准确输入、母版认可、谱系和预期版本校验继续生效。
3. 在任务页面查看图像、播放音频、评论、修订和记录实际审阅结论。真实用户认可与工具检查分别记录。执行本流程不代表授权新增付费调用，也不代表接受任何作品。
4. 自检完成后冻结包；不要把测试评论、测试采纳或无关创作变更放进交付数据。

```bash
python3 scripts/generation_review.py --instance .runtime/generation/review prepare \
  --output production/publications/素材批次-v1.json
python3 scripts/publish_generation.py --instance "$generation_main" \
  --package production/publications/素材批次-v1.json --run-name materials-preflight-01
```

`prepare` 比较初始化基线与当前任务库，收集对象修订、准确依赖、素材轮次、评论、锚点及编辑／关闭历史，并核对原件哈希和字节数。它拒绝删除或重写不可变历史，也拒绝借此发布剧本、资料或系统配置修改。预演默认只在本 worktree 的备份上应用增量；正式库不变。正式输入已变更、同一对象已前进或同一评论被改动时会停止，须读取最新数据重新整理候选。

## 合并与正式发布

先核对工作区 diff、原件清单、预演结果和授权范围，提交准确包与原件。正式任务沿既有 `_prepare_integration`／`_complete` 流程集成；没有任务记录的工作按已获授权的 Git 合并流程办理。发布和恢复所需资料收敛前保留原任务分支及 worktree；结项按下节清理，不把工作区永久保留当作归档方式。

`generation_source_commit` 填入包含已审发布包及全部原件的完整提交 SHA。该提交必须已合入主目录当前 `main`；主目录必须干净。回到保留的任务 worktree，在已协调的正式写入窗口执行：

```bash
generation_source_commit=填写已合入主干的完整提交SHA
python3 scripts/publish_generation.py --instance "$generation_main" \
  --package production/publications/素材批次-v1.json --run-name materials-apply-01 \
  --source-commit "$generation_source_commit" --apply
```

发布器检查提交祖先关系，以及包和原件在任务目录、该提交、主目录文件与主干 HEAD 中的字节一致性。正式发布不再从 worktree 补拷原件；未跟踪、未合并、被修改或缺失的文件必须先通过 Git 修复。`--apply` 是实际写入开关，源码提交并不等于数据库已发布。

现有两种登记格式保留兼容入口，沿用同样的工作区、合并检查、锁、备份和回执规则：

| 输入 | 命令 |
| --- | --- |
| 歌曲准确增量 `production/song-stage/publication-plan.json` | `scripts/publish_song_stage.py --instance ... --run-name ... [--source-commit ... --apply]` |
| 全剧素材登记批次 | `scripts/publish_full_generation.py --system ... --instance ... --registration ... --run-name ... [--source-commit ... --apply]` |

全剧批次先在最新正式备份中逐批使用通用系统校验，再将完整增量在一个事务中提交；后一批失败不会留下前一批。正式发布保持共享 `.runtime/publication.lock`，事务再次核对原对象和准确输入；无关任务新增的评论、采用与修订继续保留。页面写入不使用该发布锁，因此发布前仍须协调审阅写入窗口，版本冲突不能靠强制覆盖解决。

## 发布后的导出与失败恢复

成功事务同时写入数据库 `generation_publications` 执行记录，再写本机 `transaction.json`、`after.sqlite3` 和 `applied.json`。执行记录是运行元数据，不进入公开业务导出。若事务已提交而外部回执落盘失败，保持同一个包，以新的 `--run-name` 重跑；发布器从库内记录识别已发布状态并补出回执，不重复追加对象或评论事件。

每次运行名只用一次。失败目录保留，不删除已有原件，不回灌 `before.sqlite3`。数据库事务失败会回滚；隔离目标在事务前复制的无引用原件可以保留供排查。没有库内提交记录时，修复问题后先预演再重试。不要把曾发布的旧包用于重建一个丢失执行记录的非空正式库；恢复后先核对业务记录。

正式入库后，从最新正式库初始化一个新的本机实例，使用它生成可恢复导出；不要从旧任务快照覆盖正式数据：

```bash
python3 scripts/generation_review.py --system "$generation_system" \
  --instance .runtime/generation/published-snapshot init
python3 scripts/generation_review.py --system "$generation_system" \
  --instance .runtime/generation/published-snapshot export
python3 scripts/production_review.py --system "$generation_system" snapshot \
  --instance .runtime/generation/published-snapshot
python3 scripts/production_review.py --system "$generation_system" recover \
  --destination .runtime/generation/published-recovery --historical-pcm-precision
```

`export` 和 `snapshot` 只改当前 worktree 的受管交付文件；核对恢复后的准确版本、历史评论和文件哈希，再提交导出并合入主干。Schema 6 及以上完整导出已经保存全部修订，`snapshot` 写出 `production-export-index-v1` 索引，绑定准确历史身份、原件和导出清单，不再生成重复的正文重放批次；旧格式恢复仍兼容。索引与清单或历史不一致时拒绝恢复。

`export/material-content.json` 使用 Git LFS 保存实际文件。新克隆先执行 `git lfs pull --include=export/material-content.json`，再核验清单和恢复；不能把 Git 中的 LFS 指针当作内容图。交付时核对实际文件与指针的 SHA256、大小及远端原件回读。受控 Git 交付与 LFS 原件上传均须成功，不能只确认分支指针。

正式库发布、导出合并、服务部署和远端推送分别回读，不能用其中一步的成功替代其他结果。纯故事工具更新通常无需重建通用审阅台或切换 3000。

本次实施的验证范围、正式库前后比较和复用来源见 [验收证据](evidence/generation-workspace-verification.json)。0003、0004 的既有素材不迁移、不删改；它们的实际制作与正式入库状态继续见 [STATE.md](../STATE.md)。

## 结项清理

执行 [任务结项清理规则](../AGENTS.md#任务结项清理)。准备最终候选时，先将真实调用、额度、用户意见、准确原件和必要验收记录收敛到既有交付位置，清除无效试写、测试夹具、临时脚本／文档及重复导出；仍用于发布、验收或恢复的实例与镜像暂时保留，并列明用途。

集成、正式发布和验收完成后，按进程、容器、镜像和路径的准确身份停止任务预览，清理无效测试库、缓存、重复副本、临时容器与历史过程镜像。核对正式服务及其他未完成任务的依赖，保留实际挂载的发布目录、正式库、原件和必要恢复／追溯记录。失败现场只有在问题解决且有效信息已收敛后才可清理；旧发布目录和镜像不因曾经发布就永久保留，也不因已被替换就自动认定失效。

清理后回读删除结果，在结项报告说明删除范围、必要保留项及尚未清理项的下一步。`_complete` 后不补改受管交付；工作区退出会话并释放锁后使用 `codex.project task cleanup`，跨仓库嵌套 worktree 使用所属仓库的管理入口处理。分支、提交和会话历史保留。
