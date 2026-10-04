# 自主审阅台优化的本地交付与恢复

本目录服务于 `task-20261004-0002` 的最终审查与确认后执行。当前仅准备候选，未集成、推送或切换正式服务。运行进展、准确候选及限制以 [运行报告](../../planning/autonomous-optimization-run-report.md) 为准。本流程默认只集成本地两个 `main`，不包含远端推送。

交付包含通用审阅台代码、故事制作思路正文，以及 PROJECT 配置中的两段背景更新。评论、不可变修订、实际调用、原件、素材轮次和采用关系沿当前正式数据库保留，不用任务预览快照覆盖活库。正式页面使用 3000 和 64401 两个现有环回端口；开发验收使用独立预览。

## 配置内容及保护

[两个更新字段](project-context/updates.json) 是可直接阅读的完整新正文；[精确改动](project-context/edits.json) 说明替换范围。更新吸收已确认的版本四、17 集／42 场、411 份已发布非歌曲原件及歌曲仅阶段归档等事实。创作背景的 630 字故事设定前缀保持，原生尺寸例外仅按已有明确授权表述，不改变故事设定或认可作品。

[原记录](project-context/before-project.json)、[请求](project-context/request.json)、[预期完整字段](project-context/expected-body.json) 与 [来源及校验清单](project-context/manifest.json) 一起受管。仅修改 `story_background`、`creative_background`；`current_stage`、受众、风格、目标载体均保留。原 PROJECT 是版本 14、存储格式 3；正常保存将成为版本 15、存储格式 4，后者是既有系统能力，不是本轮新增迁移。阶段判断尚未答复，不能据新背景自行改变阶段。 清单中的执行状态保留最初准备时记录，后续预览验证以运行报告为准。

封装会检查原完整记录（含更新时间）、原字段值和准确请求，不自动提高 `expected_version`。正式记录已变时应停止，核对差异并重新准备。只发一次 PATCH；响应丢失后核对准确版本、完整正文和事件，不盲目重试。预览中已完成两字段更新与历史保留验收，正式库未应用。

## 确认前准备

执行入口为 [autonomous_optimization_release.py](../../scripts/autonomous_optimization_release.py)。路径以故事任务 worktree 根为基准。它不请求或伪造用户确认，不执行 `_complete`，也不推送。`--apply` 只是防误触开关，不能代替用户的最终明确确认。

1. 冻结系统候选；故事 `config/instance.json` 的 `review_desk_commit` 必须准确指向该系统提交。把实现、必要文档、报告、证据和本目录一起提交；保留过程提交。
2. 在当前故事 worktree 运行 `codex.project task _prepare_integration -g creative -p SnakeSlayingRecord --task task-20261004-0002`。对返回的最新目标合并候选补验实际变化范围；系统仓的目标变化也先在独立系统 worktree 合并、解决、验证。准备不代表用户确认或质量通过。
3. 用两仓完整 40 位候选与目标准备一个新的、不可覆写的运行包。参数模板如下，最终实际参数与摘要记录在运行报告及本机包回执，不从旧例子猜值：

   ```bash
   python3 scripts/autonomous_optimization_release.py prepare \
     --story-worktree . \
     --system-worktree .runtime/autonomous-optimization/system-worktree \
     --project-update production/autonomous-optimization-release/project-context \
     --output .runtime/autonomous-optimization/final-release \
     --story-candidate STORY_CANDIDATE --story-target STORY_TARGET \
     --system-candidate SYSTEM_CANDIDATE --system-target SYSTEM_TARGET
   python3 scripts/autonomous_optimization_release.py build \
     --bundle .runtime/autonomous-optimization/final-release
   python3 scripts/autonomous_optimization_release.py preflight \
     --bundle .runtime/autonomous-optimization/final-release
   ```

`prepare` 从准确 Git 提交取系统完整包及两个故事文件，检查正式服务结构和原 PROJECT，只读正式实例。`build` 仅构建本地镜像：从已存在的正式镜像 ID 建任务唯一基础标签，拒绝标签被其他镜像占用，构建前后再次核对；完全替换 `/app/review_desk`，逐文件核对候选，避免遗留已删除文件。`preflight` 再只读检查准确输入，不能替代真实页面验收。

运行包包含不可变 manifest、镜像回执和准确发布文件。候选或部署输入变化时使用新包，不修改已经审查的包。向用户展示两仓分支／提交、两个本地 main、镜像与包摘要、运行报告、预览和剩余限制，并明确请求完成、集成及下述正式写入的确认。确认等待不延长本轮优化。

## 确认后的固定顺序

1. 根协调在共享写入窗口执行 `apply`。封装按“系统 Git 发布锁 → 故事 publication 锁”获取互斥；现有系统快进器另有自己的集成锁。页面和其他 CLI 写连接不自动遵守这些锁，尤其要保证配置更新不与另一配置写入并发。
2. 封装复查可能变化的准确输入，对当前正式库做一致备份以比较历史；备份不能回灌。随后复用已有 `integrate_generation_review_system.py` 快进系统本地 main，保留幂等回执，不重置主干。
3. 安装主项目 `.runtime/service-releases/` 中的独立不可变发布目录，用预构建镜像重建 app 与 Nginx。保留正常 `/instance`、可信 CA、现有环境和两端口。环境值只在子进程内存传递，不输出、不落盘；发布文件内只含变量占位。
4. 新发布永久只读挂载准确 `config/instance.json` 和 `content/production-approach.json`，不覆盖其父目录或数据库。核对容器包文件、两挂载文件和健康，再沿同一个正式 HTTP 服务一次更新两段背景。比较全部旧业务行仍在、SYSTEM 未改、PROJECT 仅新增一条准确事件。
5. `apply` 的成功状态是 `formal_browser_acceptance_pending`，尚不表示完成。根协调只做一次必要的正式 Chrome 验收：新制作思路、两段背景及保留阶段、一个旧评论与准确历史原件、相关工作区入口；不在正式库写技术评论、采纳或判断。已通过的隔离异常检查继续复用。
6. 正式必要验收通过后，执行用户指定的 `_complete`，作为本任务最后一次受控代码／账本写入。成功后只回读完成回执及文件一致性，不再改文档、提交、推送、撤挂载、重启或补写配置。保留任务 worktree 和分支，正常退出会话后才释放运行锁。

确认后的参数模板：

```bash
python3 scripts/autonomous_optimization_release.py apply \
  --bundle .runtime/autonomous-optimization/final-release \
  --manifest-sha256 REVIEWED_MANIFEST_SHA256 \
  --image-receipt-sha256 REVIEWED_IMAGE_RECEIPT_SHA256 --apply
# 完成一次必要正式页面验收后：
codex.project task _complete -g creative -p SnakeSlayingRecord \
  --task task-20261004-0002 --note '实际候选与验证证据摘要'
```

若后来要求推送，须在最终确认前通过任务 `_prepare_integration --push` 纳入唯一 upstream 并展示推送目标，不能在本地完成后另行推送。

## 失败、恢复与长期维护

| 情况 | 处理 |
| --- | --- |
| 候选、目标、正式服务或 PROJECT 漂移 | 停止相关写入；核对差异，必要时重新准备、补验并确认，不能抬版本绕过冲突 |
| 系统已快进，故事未完成 | 保留真实双仓状态；同准确候选可恢复原流程，不 reset 系统 main |
| 服务切换失败或部分完成 | `_complete` 前可执行同包 `recover --action service`。逐服务核对所有权，拒绝其他发布；用旧 app 和 Nginx 的固定镜像 ID 恢复，保留最新正式数据库 |
| 配置已准确应用但需补偿 | 仅在无人改动的准确 v15 下用 `recover --action config` 形成 v16 的两字段补偿事件；保留 v15/v16 历史。若先前已完成准确补偿，核对完整事件链后只回读，不再写一次 |
| 配置结果未知或与预期不符 | 停止完成；读准确记录和事件，不盲重试，不用快照覆盖 |
| `_complete` 失败 | 保持任务未完成及已有真实服务状态，按工具返回原因恢复。是否回退服务按已确认的方案判断，不补造用户确认 |
| `_complete` 成功后发现问题 | 只读记录并报告；新的修改另行准备、验证、交付 |

恢复命令沿相同 `--bundle`、两个已审摘要和 `--apply`，增加 `recover --action service` 或 `recover --action config`；先确认当前状态符合对应条件，不把两种恢复盲目串联。

永久挂载意味着只修改故事主目录并不会更新运行中的这两个文件。未来变更必须建立新发布目录并切换挂载。发布目录自带 `release.py restart --release . --apply`，只重启仍属于该准确发布的现有容器；容器已删除时拒绝，不尝试从不存在的凭据重建。此入口用于以后独立维护，不在本任务 `_complete` 后追加执行。

## 已有验证及边界

封装作者检查、独立故障检查及真实隔离 Docker 演练的准确证据见运行报告。提升到本目录时，脚本字节 SHA-256 为 `c4ddc127bb004c1f8484870c02b9e5635fc128905b258013a6b027311d61953d`，与已审和已实际构建的版本相同；迁移后的 20 项离线测试通过。独立审查曾纠正恢复覆盖其他发布、旧镜像标签漂移、补偿中断恢复和本地基础标签等问题，原失败证据保留。

真实 Docker 演练使用独立项目、端口和技术库，验证候选包、两文件只读挂载、服务切换和回滚后新旧技术评论保留。它没有完整执行硬绑定正式端口的 `apply`／`recover`，不能写成正式发布已通过。最终准确候选包及正式必要验收仍须按上述顺序完成。
