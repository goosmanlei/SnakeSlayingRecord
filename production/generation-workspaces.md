# 在任务工作区生成和审阅，合并后发布

图像、音色和歌曲的生成原件、请求、回执、登记数据及导出文件先保存在自己的 Git worktree。任务审阅使用自己的数据库和端口。完成审阅后，将交付文件提交任务分支并合入 `main`，再在共享写入窗口向正式库应用增量；Git 合并不会自动发布数据库。

本流程由故事仓库工具实现，复用通用审阅台已有的数据、预览、评论和审阅接口。多仓 Git 工作区和交付由 `codex.task` 管理，项目继续管理业务发布。历史素材保持原有身份与引用；新规则从已同步这些工具的任务开始执行。

## 一项任务管理两个仓库

以下流程要求 `codex.task` v0.2.0 或更新版本，并已将本项目适配合入；本机切换及历史接入情况见 [STATE.md](../STATE.md)。用户从故事主目录沿用 `add/mod/run/mrun`，无需填写仓库配置或执行登记命令。Agent 读取项目规则，核验主目录同级的 `../story-review-desk` 及其 Git 身份，通过当前任务的内部回调声明用途与目标分支。

故事 worktree 仍为主目录下 `.codex-task/worktrees/<任务 ID>`；新系统 worktree 为 `.codex-task/linked-worktrees/<任务 ID>/<仓库别名>`。这些路径由账本返回，不按相邻关系猜测。澄清阶段只记录计划；执行时统一加锁后创建并授权目录。执行中发现还需修改系统时，先登记计划、保存当前成果，再通过原 `run/mrun` 恢复同一会话，不在尚未启用的系统目录提前工作。

Agent 在执行会话内登记提交引用约束：主仓 `config/instance.json` 的 JSON 字段 `/review_desk_commit` 必须等于系统仓库候选。内部回调接收的对象为 `{"commit_references":[{"repository":"primary","file":"config/instance.json","pointer":"/review_desk_commit","equals_repository":"desk"}]}`，其中 `desk` 替换为本任务实际别名，文件路径相对故事 Git 根目录。先提交系统成果，再更新故事配置并提交，最后准备整组候选；上游集成使系统提交变化时须重新更新引用及准备。

同时登记清理检查器 `scripts/task_workspace_guard.py` 和其实际 SHA-256；路径相对故事主目录。检查器只读核对包括已停止容器在内的挂载，以及 `.runtime/service-releases/` 中发布 Compose 和恢复配置实际使用的目录；冻结发布包中的任务编号和来源路径保留原始字节，仅作追溯，不要求原工作区继续存在。Docker 查询失败、配置无法核验、脚本摘要变化或实际依赖未解除时保留现场；正式容器对整个故事根目录的普通 `/instance` 挂载不单独认定为每个任务的依赖，直接指向任务目录的其他挂载仍阻断。

新原生任务先 `_prepare_integration`（需要推送时加 `--push`）冻结全部候选，再准备现有项目发布包。`integrate_generation_review_system.py` 从包内的原生标记调用任务 `_deliver`，任务按依赖顺序完成系统和故事的集成与必要推送；项目脚本读取回执，不再自行重复合并或推送。正式库／服务发布、真实页面验收和资源收尾完成后再 `_complete`。中途失败使用同一冻结包和任务恢复；候选变化则重新准备和验证。

已执行旧任务及旧冻结包沿原发布后端恢复。历史嵌套路径只在旧启动器与写入者退出后核验、原地接入，不移动、不改会话或完成历史；新后端失败不能回退旧脚本重复写入。清理前先归档必要材料、结束保留用途并释放运行资源，再由任务工具迁移各仓会话、按内外关系清理整组 worktree。参考或实验分支不因主任务完成而自动丢弃。

## 执行基线与主干同步

任务草稿的创建提交和前置任务的完成提交只记录来源，不固定后续开发版本。开始或恢复执行时，读取主项目当前规则及任务账本，核对每个交付仓库的本地目标分支、远端 upstream 和任务工作区实际提交。启动器会按适用流程获取并合并远端 upstream；仍须检查本地主干上尚未推送的有效成果及实际合并结果，不能把旧工作区或历史报告当作当前状态。

在阶段成果已保存、准备依赖其他任务新成果，以及准备最终候选前，将已前进的主干 merge 回各自任务分支，处理冲突并复验受影响功能。没有主干变化时无需重复合并；有未保存修改、冲突或发布恢复现场时先处理现场。双仓同步后，重新核对故事配置对系统准确提交的引用。冻结候选发生变化时重新准备发布包；部分交付先沿原回执核对，不混用新旧候选。

开发代码的持续同步与准确证据各有用途：性能比较仍保留同条件的对照记录，制作输入锁仍绑定已确认作品和素材，任务数据库的初始化快照仍用于计算增量，不能在 merge 时重置或替换。新任务从执行时有效正式数据初始化；已有任务遇到正式数据变化时按准确版本和增量冲突规则重整候选。已完成任务的工作区不承担后续任务基线，必要历史依据收敛后按结项流程退役。

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

四类内容完成 V1 收敛后，以 [版本收敛交付](version-consolidation/README.md) 的 Schema 8 完整导出与发布幂等回执作为有效恢复入口。旧制作包、旧回放和其他任务的旧库只供历史追溯，不能恢复到当前实例。新的普通创作从最新正式基线初始化，原有历史保留和冻结规则继续生效。

先创建或进入自己的任务 worktree，并同步最新主干。无正式任务记录的独立工程工作也可以使用独立分支；不要为了使用这些工具另建任务账本。下列命令从 worktree 根目录执行：

```bash
generation_main=$(python3 -c 'from pathlib import Path; from scripts.generation_workspace import primary_root; print(primary_root(Path.cwd()))')
generation_system="$generation_main/../story-review-desk"

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

先核对工作区 diff、原件清单、预演结果和授权范围，提交准确包与原件。多仓任务按上节的准备、Git 交付、正式发布与最终完成顺序推进；单仓与已执行旧任务沿其既有受控流程集成。没有任务记录的工作按已获授权的 Git 合并流程办理。发布和恢复所需资料收敛前保留原任务分支及 worktree；结项按下节清理，不把工作区永久保留当作归档方式。

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

### 审阅台镜像的固定名称

正式审阅台发布使用三个固定 Docker 标签，不再按任务或提交增加正式标签。任务中的独立构建和隔离预览允许使用临时镜像及任务标签，结项时按下方清理流程处理。

| 标签 | 用途 |
| --- | --- |
| `story-review-desk:current` | 已完成服务和数据核验的当前发布 |
| `story-review-desk:previous` | 上一次发布，供准确回退 |
| `story-review-desk:base` | 固定构建基底，不随每次发布移动 |

候选构建默认不加标签，每个发布包用自己的 `build-image-id` 接收构建结果，再将准确镜像 ID 冻结到 `image.json`。并行任务不会覆盖彼此的候选；构建成功后回执中断时，重试先核验已有 ID 和源码，不重复构建。正式 Compose、发布清单和回退入口始终使用准确镜像 ID；固定标签用于识别当前、上一版和构建基底，不能代替准确版本校验。发布成功后才更新 `current` 和 `previous`，回退成功后同步反向更新；标签操作可安全重试。

首次构建可从当时正式镜像初始化 `base`；已有实例也可使用下方入口从当前镜像的本机祖先初始化。以后各版均从同一基底替换审阅台源码，不再沿着上一版逐次追加历史层。初始化不会压平既有历史层；需要升级 Python、FFmpeg 或运行配置时，另行准备和核验新基底，不能直接移动标签绕过冻结包的 ID 校验。

从故事主目录执行以下入口，默认只展示计划；`--apply` 将当前及回退镜像加上固定标签，并移除指向同一镜像的旧 `ao-task-…-base`、`materials-…`、`autonomous-…` 标签。它先核验正式容器和发布包，在发布锁内操作，不删除镜像、不重启服务、不修改数据库：

```bash
python3 scripts/normalize_review_images.py
python3 scripts/normalize_review_images.py --apply
```

新发布包的构建与标签操作使用主目录 `.runtime/docker-image-tags.lock` 串行保护。旧冻结包继续使用其中的原辅助脚本及准确 ID；未开始的任务同步新主干后再准备发布包。固定标签不自动删除无标签镜像：候选、失败构建和被替换的回退镜像仍须按任务结项规则核对用途后精确清理，不使用全局 prune。构建缓存与镜像标签分别管理。

成功事务同时写入数据库 `generation_publications` 执行记录，再写本机 `transaction.json`、`after.sqlite3` 和 `applied.json`。执行记录是运行元数据，不进入通用业务导出；V1 收敛后的故事导出另同步最小发布回执及其配置哈希，空库恢复一并还原，避免丢失幂等身份。若事务已提交而外部回执落盘失败，保持同一个包，以新的 `--run-name` 重跑；发布器从库内记录识别已发布状态并补出回执，不重复追加对象或评论事件。

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

`codex.project task` 管理任务工作区、会话和 Git 交付，不会因为启动任务就自动构建 Docker 镜像。镜像和容器由项目构建、验证或预览命令按需创建；相同构建也可能复用已有镜像 ID。执行 Agent 须把准确 ID、创建／复用情况和用途记录到任务 `.runtime/` 的现有回执中；使用临时标签时应包含任务身份，且不得在验证阶段移动正式 `current`、`previous` 标签。

正式交付与验收完成后，执行 Agent 在结项阶段完成 Docker 收尾：

1. 核对本任务记录、全部容器（含已停止容器）、准确镜像 ID，以及正式服务、其他活跃任务和有效恢复入口的引用。
2. 停止并删除已无用途的本任务过程容器，再删除不再被使用的任务镜像。复用镜像不能仅凭本任务结束就删除；已转为正式当前版、回退版或构建基底的镜像保留。
3. 按准确 ID 回读容器和镜像已不存在。只删除临时标签而留下无标签镜像，不算完成镜像清理。尚需保留的过程资源须写明实际用途、责任和解除条件，不能把全部过程镜像永久作为证据。
4. 在完成报告中给出实际删除数量及保留项，再按既有顺序完成任务；退出会话并释放锁后，另用 `codex.project task cleanup` 退役工作区。

`task cleanup` 及本项目 `scripts/task_workspace_guard.py` 检查工作区占用、Docker 挂载，以及保留发布包的 Compose 和恢复配置中实际使用的目录。发布清单中的任务编号、故事／系统工作区路径仅记录构建来源，不要求原工作区继续存在；清单和冻结包保留原始内容，清理工作区无需先删除清单。实际挂载、恢复所需的配置文件或工作目录仍指向任务工作区时，检查器给出具体引用并阻止删除。检查器不自动删除过程容器或镜像，因此 Docker 收尾仍由执行 Agent 实际执行；不能用工作区已删除替代清理回执。异常或中断任务先保留恢复现场，恢复后继续收尾。

`_complete` 后不补改受管交付文件。工作区退役须先退出会话并释放锁，再使用 `codex.project task cleanup`；多仓任务按账本纳管范围整组检查、逐仓迁移会话并清理。尚未接入的历史嵌套 worktree 先核验归属，不能直接递归删除；分支、提交和会话历史保留。
