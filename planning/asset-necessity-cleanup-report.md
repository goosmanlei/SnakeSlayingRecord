# 双项目资产必要性审视与清理报告

本轮已完成两仓内部冗余清理、资产用途审视与隔离验证。未删除作品、媒体、评论、修订、真实调用、准确依赖、采纳或镜头采用记录；没有取消现有功能、HTTP 接口、CLI 或恢复契约。正式集成、双仓推送、服务切换及 **4 个已退役预览容器**的删除仍待本轮最终确认，不能将候选视作已正式应用。

用户在执行会话中明确选择“执行完整资产审视与清理，最终集成前确认”。完整要求见 [任务说明](asset-necessity-cleanup-task.md)。主协调者维护此报告和[唯一覆盖清单](../production/evidence/asset-cleanup/README.md)，故事、系统、数据运行三个领域分工调查并交叉复核；没有启动旧自主优化实验或持续 Goal。

## 基线、范围与可定位清单

上游冲突已在本 worktree 保留双方有效状态后提交 `6a09eb6994614d195dde64bee1c0b91cdd990e11`，随后 `_prepare_integration` 成功同步。执行基线为故事主干 `fd08a2cefe80a723950dbfcb5d9ac8bc09775116`、系统主干 `236433072b1629c197e3685cb5b7e305b53e3285`；前置任务 `task-20261004-0004` 已完成集成和推送。当前配置锁定新系统候选 `709ae260dc84c0b9f2818a44010a7ebc0fc10c42`。故事最终候选以本报告所在提交和交付时 `_prepare_integration --push` 的回执为准，避免在文件中写自身提交号。

正式 Docker 的 43 个受管 `review_desk` 文件与系统基线逐文件 SHA 一致，Nginx 配置一致；旧镜像标签中的版本落后，不能用标签或 `/api/instance` 代替实际源码。[运行版本证据](../production/evidence/asset-cleanup/runtime-live-baseline.json)同时记录挂载：活库和原件位于主故事实例，配置与制作思路使用永久发布目录，只读 CA 挂载保留。正式入口为本机 `3000` 和 `64401`，没有本任务临时 worktree 挂载。

| 清单层次 | 分母与定位方式 | 处置 |
| --- | --- | --- |
| 物理文件系统 | 冻结前扫描 **70,332** 个路径成员：67,172 文件、3,153 目录、7 符号链接；[逐项 gzip JSONL](../production/evidence/asset-cleanup/inventory/files.jsonl.gz)按 `root + path` 定位 | 每项连接用途规则；未匹配 0，读取错误 0 |
| 故事受管资产 | 基线 3,132 成员；48 脚本、23 测试、8 配置/内容/部署条目分别说明，其余 3,053 成员按可展开路径分组；[story.json](../production/evidence/asset-cleanup/story.json) | 原件和有效历史保留；1 项脚本内部合并；本轮新增交付工具/测试另见下文 |
| 系统受管资产与接口 | 130 文件、58 HTTP/静态入口、32 CLI、15 测试/设计入口、11 公共配置字段、11 兼容路径族；[system.json](../production/evidence/asset-cleanup/system.json) | 保留入口与功能，合并/清理内部实现 |
| 全部本地数据库 | 113 个 SQLite 文件、10 种结构签名；[逐库清单](../production/evidence/asset-cleanup/db-all-instances.json)连接[表/列/索引列/外键](../production/evidence/asset-cleanup/db-schema-groups.json) | 保留正式业务、创作检查点、历史发布/恢复和本轮验证副本；无表结构删除 |
| 正式数据 | 14 表（含 SQLite 内部序列表）、13 索引、0 视图/触发器、58,698 行；逐表用途、字段与关系见[数据库审计](../production/evidence/asset-cleanup/db-audit.json) | 全部保留 |
| 运行资产 | 扫描时本机24容器中项目21个；32镜像中项目29个、共享 Nginx 基底1个、外部2个；14卷中项目独占0；7网络中项目1个。逐实例见[运行处置](../production/evidence/asset-cleanup/runtime-decisions.json) | 2个正式容器保留；19旧容器中4个待批准清理、15个保留；映像/卷/网络不清理 |
| 构建与本机运行 | 207条构建缓存元数据，73条有显式项目引用，其余共享或归属不独占；[缓存清单](../production/evidence/asset-cleanup/runtime-build-cache.json)、[进程/端口/调度](../production/evidence/asset-cleanup/runtime-processes-schedulers.json)、[38个运行目录成员](../production/evidence/asset-cleanup/runtime-directory-decisions.json) | 不全局 prune，不停止他人进程；本轮预演新增资产另有准确回执 |

文件枚举含 `.git`、`.codex-project`、隐藏/未跟踪文件、全部注册的现存 worktree、`.runtime/` 及系统外置任务 worktree。按路径计成员，逻辑字节不等于独占磁盘空间；硬链接、APFS 克隆和工作区副本不当作可回收体积。所有目录均实际枚举到成员，不以顶层目录数冒充文件覆盖。用途可以分组，成员不能省略。

明确的扫描限制与排除：

- 清单自己的 `inventory/` 子目录内容排除，目录本身计入；该子树只有两个输出文件，由 Git 与 `summary.json` 中清单 SHA 保存，避免自指。冻结后产生的 Git 对象和运行回执属于明确保留的 Git/任务证据类别；不是新发现的业务资产。
- 符号链接只记录链接及目标，不越界读取；凭据/环境文件只核对路径和调用用途，不公开内容。SQLite magic 检查覆盖非秘密普通文件，符号链接等另列。历史数据库逐结构审视并保留恢复意义，没有宣称逐行重新审阅每份旧快照正文。
- 系统调度扫描遇到 `/Library/LaunchDaemons/com.microsoft.teams.TeamsUpdaterDaemon.plist` 权限错误，属于外部 Teams 更新服务，本任务不读取/清理，不影响这4项项目容器的删除判断；未宣称审视整机资源。
- 15个旧容器的准确 Image SHA 已不可读取，仍有唯一历史容器层，保留其潜在恢复能力；不把它们记为已清理，也不宣称能重建其旧服务。没有其他影响本次删除安全的未解决归属项。

## 实际合并与清理

| 项目 | 冗余或废弃证据、调用承接 | 实际结果与验证 |
| --- | --- | --- |
| 歌曲发布重复实现 | `652f7b5` 已把真实入口迁到 `publish_generation.run_publication`；7个旧辅助函数和重复 `KEYS` 无动态调用，保留完整 CLI/歌曲范围/事务发布函数 | 故事过程提交 `a914e23`，脚本减3,471字节；真实临时库预演→应用→幂等重试与共享发布24项通过，独立复核通过 |
| 参数文本投影 | 制作详情与评论锚点各自实现同一 JSON 字符串化；集中到现有 `review_text`，两调用方复用，不新增管理层 | 系统 `709ae26`；6,998修订的24,248文本块逐字一致，包括1,075生成参数与840真实调用参数，准确锚点不变 |
| 来源转发壳及无用导入 | `showProductionSource` 的历史调用在 `1c41907` 已迁到准确素材参考入口；`mimetypes` 无调用 | 删除转发壳及导入，现有参考按钮/旧链接兼容保留；没有删除HTTP入口 |
| 退役 CSS | 23个独有类、81个 selector 出现点；逐项连接 `0b8e7ad`、`1d0877b`、`3411203`、`e482189` 的DOM迁移，检查静态/动态类名及测试/夹具 | 五个CSS净减5,927字节；保留部分的selector顺序和声明等价，桌面/窄屏实际验证；证据不足的 `eyebrow` 保留 |
| 现行说明与发布入口 | README/production旧状态把已应用候选写成待应用、把初始目标与有效范围混用；歌曲旧清单中的脚本哈希属于归档版本 | 直接修正现行入口；歌曲 `df0bbcd` 原始清单保持，说明后续公共脚本已演进；复用既有 code-only 发布工具支持0005，不复制另一套发布实现 |

新交付资产均有具体用途：[文件枚举器](../scripts/asset_cleanup_inventory.py)只读收集元数据与用途映射；[运行清理器](../scripts/asset_cleanup_runtime.py)只对确认清单执行漂移检查、归档及精确容器删除；其测试验证拒绝误删和中断恢复；报告/压缩清单/哈希/页面证据用于复核。本轮不增加审阅界面、通用调度框架或新的业务存储。

### 4 个正式运行清理候选

它们属于已受控退役的 `task-20260929-0003`，均已停止；原实例绑定路径已不存在，账本记录该工作区已清理，Git不再登记。可写层变化仅Python缓存与空目录，原精确镜像仍存在，没有作品或业务数据仅存其中。正式运行使用另一组容器、网络及永久挂载，彼此独立。

| 容器名 | 精确 ID 前缀 |
| --- | --- |
| `snakeslayingrecord-production-task-0003` | `4819129011e7` |
| `snakeslayingrecord-production-task-0003-before-reference-popup` | `962f992fca8f` |
| `snakeslayingrecord-production-task-0003-before-simplification` | `31b49f8b6479` |
| `snakeslayingrecord-production-task-0003-before-materials` | `188a696e6f83` |

可执行清单保存完整 ID、镜像、命令、状态、挂载、重启策略和可写层摘要：[manifest](../production/evidence/asset-cleanup/runtime-cleanup-manifest.json)，SHA-256 `58f125142f3bb6514657555d29e6da4ede690e27afc3a326d8d4c8e111803168`。默认真实预检4/4通过；14个模拟安全/恢复测试及独立复核通过。最终确认后先再核对全部待删项、归档日志与身份，再逐个核对并 `docker rm <完整ID>`；不带force/volume/image选项，不删除主机目录。中断重试承接有哈希的原回执，保留不完整归档，不用容器消失推定成功。

审计期间 `docker cp` 对停止容器的只读意图探测导致Docker Desktop创建了原本不存在的空绑定目录。首次扫描、账本退役状态、目录创建时间和空目录检查确认来源后，只用逐层 `rmdir` 撤销这次探测生成的4层空链，已恢复原来的missing状态；[副作用及恢复回执](../production/evidence/asset-cleanup/runtime-probe-side-effect-recovery.json)完整保留。最终工具已移除此操作。其他15个旧容器因缺少准确原镜像而保留，不扩展清理权限。

## 保留资产及历史完整性

全部1,398个受管资源均有用途：正式完整导出引用1,307份，歌曲独立阶段89份，可选图标派生2份。可读作品与对应导入JSON承担不同职责，不合并删除；原生媒体、撤回/未采纳候选、失败或付费调用回执、旧方案及其精确引用均保留。`.runtime/novel-writing`、精修/冷读检查点、歌曲尝试、账号/发布锁、永久服务发布包、前序任务证据与工作区也分别有创作、计费、幂等或恢复用途。仅搜索不到引用、文件陈旧或备份内容相似，不足以删除。

正式一致性快照 SHA-256 为 `bf09386e9bd1c7b04fc262ad39a811b37c0246af1b9849d5deb8f7aa179ba4d1`。核验包括58,698行的准确身份与全内容哈希、6,998修订哈希、41,139载荷内精确引用、6,866制作修订依赖集合、271评论锚点，以及1,307媒体文件共1,036,571,531逻辑字节的哈希；数据库完整性/外键检查无错误。逐项证据见覆盖清单，不仅比较总行数。

没有发现可以安全删除的业务表。`generation_publications` 的1条本地发布回执支持幂等与故障恢复，继续保留；它按既有公开契约不导出，不能因完整导出未包含而判垃圾。当前完整导出→空实例恢复比对12个公开业务表的58,695行逐身份/全内容哈希与1,307媒体哈希全部一致，关系显示配置语义一致，FK/integrity通过。差额是本地发布回执1行及SQLite内部序列2行，不是业务历史丢失。`config/` 和 `content/` 仍随Git保留；方法文档不靠数据库恢复。

本轮没有表结构、导出格式或旧格式读取契约变化，因此不制造数据库迁移。现有兼容/恢复自动检查照常执行，另外完成当前全量恢复预演以证明清理后仍可使用。正式应用仅换代码/准确配置覆盖层，使用当时最新活库备份并核对不可变历史、稳定身份及准确锚点，允许用户并发追加意见或更新当前头；不把本任务快照导回正式库。

## 验证与实际边界

- 故事自动检查：全量230项通过（673.641秒）；全套含枚举器最初4项；枚举器最终5项安全用例单独补验通过，修复外部父子worktree枚举顺序导致的重复计数；运行清理14项含中断重试通过；发布工具8项含旧任务兼容及真实prepare→load通过。
- 系统自动检查：Python151项、Node388项通过。跨领域独立复核覆盖实际diff、动态引用与清理证据。日志见[证据目录](../production/evidence/asset-cleanup/README.md)，不把模拟用例当正式删除回执。
- 真实Chrome在隔离端口62614回归故事采编、结构第10/8稿、原图放大/关闭、旧评论定位、剧本3/4切版、实体旧版/当前版、准确参考、素材筛选、共用音频播放/选段/定位、全剧镜头原文和素材选择。仅在隔离库新建1条测试音频评论，实际关闭/重开后总数与待处理/历史口径正确。390×844窄屏通过，默认视口已恢复。截图与逐动作结果见[页面证据](../production/evidence/asset-cleanup/browser-observations.json)。未替用户接受素材，也未把播放计时称为声音质量听审；正式页面尚待切换后一次重点验收。
- 镜像启动、挂载、健康、重启与旧镜像回退后再应用见[隔离Docker预演](../production/evidence/asset-cleanup/docker-rehearsal.json)。专用克隆库与62616端口不依赖正式挂载；原镜像回退只换代码，不恢复数据库。正式发布包另用已提交候选准备、构建和默认preflight核对，回执留本任务 `.runtime/asset-cleanup/release/`。

性能使用同台macOS、Python3.9.6、同一端口62615、单进程环回HTTP、完全相同数据库SHA与请求参数；每类首次单列、预热5次后完整读取50次响应，P95为排序第48个样本。结果不是生产容量承诺。

| 实体请求 | 清理前 P95 ms | 清理后 P95 ms | 完整响应 |
| --- | ---: | ---: | --- |
| 典型阿禾 | 116.88 | 114.81 | SHA一致 |
| 素材最多李寄 | 251.29 | 255.68 | SHA一致 |
| 历史阿禾准确修订 | 124.48 | 126.25 | SHA一致 |

最大波动约+1.75%；三类仍满足既定P95≤300ms且≤task0004优化前同类基线50%。本任务无需再把已优化结果减半；比较、全部样本和首次/中位数见[性能证据](../production/evidence/asset-cleanup/performance-comparison.json)。

## 最终批准后的准确操作与恢复

两个目标分支均为 `main`；故事推送到 `origin` 的 `goosmanlei/SnakeSlayingRecord`，系统推送到 `origin` 的 `goosmanlei/story-review-desk`。最终候选、upstream、不可变发布包摘要和预检结果须在用户确认前展示。故事受控集成只通过 `codex.project task _complete`，不在主目录手工合并或暂存。

确认前准备步骤（已提交候选为输入；不是正式应用授权）：

```bash
codex.project task _prepare_integration -g creative -p SnakeSlayingRecord --task task-20261004-0005 --push
# 将该次回执candidate/target填入prepare；system候选及目标固定如下。
python3 scripts/material_review_release.py prepare --task task-20261004-0005 \
  --system-worktree .runtime/asset-cleanup/system --bundle .runtime/asset-cleanup/release \
  --story-candidate "$approved_story_candidate" --story-target "$prepared_story_target" \
  --system-candidate 709ae260dc84c0b9f2818a44010a7ebc0fc10c42 \
  --system-target 236433072b1629c197e3685cb5b7e305b53e3285
python3 scripts/material_review_release.py build --bundle .runtime/asset-cleanup/release
python3 scripts/material_review_release.py preflight --bundle .runtime/asset-cleanup/release
python3 scripts/asset_cleanup_runtime.py --manifest production/evidence/asset-cleanup/runtime-cleanup-manifest.json
```

正式顺序固定为以下串行动作；确认后的回执只存唯一任务账本或本机未跟踪运行目录，不追加候选文档提交：

1. 用已展示的发布包manifest/image回执SHA调用 `material_review_release.py apply --bundle .runtime/asset-cleanup/release --apply --manifest-sha256 <已确认摘要> --image-receipt-sha256 <已确认摘要>`。它重新核对候选/目标/正式挂载/镜像/CA和内容，备份最新活库，受锁保护地快进系统main，安装永久配置层、应用已验证镜像并检查健康/源码/挂载与有效历史保留。业务导入和迁移为0。
2. 从任务系统worktree执行 `git push origin 709ae260dc84c0b9f2818a44010a7ebc0fc10c42:refs/heads/main`，禁止force；用 `git ls-remote origin refs/heads/main` 核对准确提交。若远端或本地主干已变化，先比较，不覆盖、不继续完成。
3. 对本次永久release执行既有 `material_review_release.py restart --release <该发布目录> --apply`，核对健康、准确镜像和挂载。正式3000真实Chrome只做一次重点回归：阿蘅音频/参数/原件、已有评论、素材筛选和镜头原文。正式库不新增测试评论，开发期完整套不重跑。
4. 执行 `python3 scripts/asset_cleanup_runtime.py --manifest production/evidence/asset-cleanup/runtime-cleanup-manifest.json --manifest-sha256 58f125142f3bb6514657555d29e6da4ede690e27afc3a326d8d4c8e111803168 --run-name approved --apply`，仅删除4精确旧容器；回读它们已不存在、15保留容器与原镜像仍在、正式两服务及挂载未变。若漂移/归档失败即停止，不跳过守卫。
5. 成功后运行 `codex.project task _complete -g creative -p SnakeSlayingRecord --task task-20261004-0005 --note '<实际验收与双仓推送证据>'`。复用其候选、目标、故事远端核对和完成回执。未成功不能宣称任务完成；不在完成后另行push。

如服务应用失败，使用同一包与两个准确SHA调用 `material_review_release.py recover ... --apply`，恢复先前镜像/挂载，保留当时最新活库和已快进Git，不reset、不restore旧DB。容器清理失败使用同一manifest、run-name与归档回执续跑；旧容器本来已缺实例挂载，不承诺恢复旧服务。必要镜像、日志、发布包和失败现场保留。

15个缺原镜像的旧容器、全部有效恢复资料和受管工作区本轮保留，既没有得到放弃恢复能力的逐项决定，也不需要为完成本任务强行删除。任务完成后不再改文件、补提交或清理工作区；保留分支，正常退出会话后才释放运行锁。
