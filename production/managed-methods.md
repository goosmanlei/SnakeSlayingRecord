# 受管工作方法与实际执行

系统配置中的“工作方法”决定新工作取得哪一版方法。它保存方法文件、共用章节和环节绑定；本故事的写作、读者与媒体工具取得准确快照后，才继续相应步骤。系统负责通用管理和校验，故事工具负责本项目的创作流程，两仓不反向导入。

本页说明已经实现的契约与操作。正式启用身份、写入窗口及验收以 task-20261009-0020 的任务账本和发布回执为准；候选通过不等于已正式生效。验证范围见 [实际验收](managed-methods/VERIFICATION.md)。

## 正文在哪里维护

| 内容 | 有效正文与同步方向 |
| --- | --- |
| 方法 SKILL、连续性知识、环节绑定 | 启用后在实例“系统配置 → 工作方法”维护。保存追加新版本，绑定显式选择准确版本。 |
| 视频手册与影视知识 | 项目 Markdown 是唯一正文。`method-source` 把选定章节及来源摘要追加为只读资源投影；已有阅读页也沿原正文派生。不能在配置页反向改一份正文。 |
| `content/managed-methods.json`、`managed-media-method.json` | 初始化定义，安装到空实例；不覆盖已编辑的活库。媒体初始化同时读取本项目 Markdown。 |
| `content/managed-method-registry.json` | 本次候选的准确配置历史，用于增量迁移与空实例恢复；不是启用后的编辑副本。后续导出必须来自当时有效实例。 |
| 执行包、阶段产物 | 本步骤已取得的不可改写快照；方法升级不改过去。私有写作和读者记录留本机，公开作品导出不携带这些候选。 |

当前只用评论润色、小说检查点、读者请求和单项媒体方案验证基础。视频方法按条件加载手册的模板、参考规则和五类离线案例，评论润色只加载适用的连续性章节。共用专业方法库、全剧重做和新一轮 Prompt 制作继续由后续任务负责。

投影保存所选正文；原文的专业来源、延伸章节和图示仍可从项目原阅读入口查阅，不声称把外部文献或整套影视图文都交给模型。执行需要额外材料时，应显式加入准确资源或保持未满足条件，不能凭链接名称补全事实。

## 外部小说作者

沿 [逐步创作流程](../planning/incremental-writing-workflow.md) 使用 `scripts/novel_writing.py`。新建步骤须指定本任务隔离审阅实例的 `--method-url`：

```bash
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT begin step.json
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT save-candidate step-id candidate.json
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT read-candidate step-id
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT accept step-id acceptance.json
```

`begin` 返回 `method_execution`：完整方法、适用共用章节、种子材料、当前检查点和本步范围。作者实际读取后工作；保存候选、回读候选和采用分别登记真实阶段产物，再形成原有检查点。方法接收的种子不包含用于发布保全的整库 `formal_baseline`。工具不会调用作者模型，也不会把候选当正式小说发布。

同一运行和步骤恢复时校验原输入及方法，当前绑定改变不影响旧步骤；新步骤取得新绑定。没有方法的历史检查点可只读，不能伪装为采用了新方法。当前 SQLite 小说历史无待继续的旧候选；新写作须用新步骤。`screenplay_writing.py` 仍是既有剧本持久检查点工具，本次没有声称它已接入自动创作服务。

## 评论润色与独立读者

评论润色请求实际装入当前绑定的方法全文、适用资料和准确原文上下文，共用既有字符预算。方法过长或条件不匹配会给出修正原因，不回退到硬编码自由 Prompt。建议仍由人手动采用；方法保存不改评论或作品。

`reader_review.py` 新运行在初始化时固定普通逐段、摘要后阅读、摘要整理、有限回看和意见核对五种方法选择。每个实际请求再登记自己的阅读位置和准确输入，结果与该请求关联。它不通过润色接口读整稿，也不把方法管理当成向读者泄露后文的通道。

历史读者运行继续已冻结的 instructions、源、摘要与回看策略，方法历史未知。恢复不会用当前常量重写历史请求。操作和费用授权沿 [读者流程](../planning/reader-review-workflow.md)；本任务只构建新请求并核验已保存旧运行，没有发起新的付费读者调用。

## 单项媒体方案

先在隔离实例取得准确 REQUIREMENT（素材需求）记录；`record.json` 保留 `object_id`、`kind`、当前 `expected_version` 和完整 `payload`。以下命令均只准备或登记，不生成媒体：

```bash
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step begin --record record.json --run-id my-run --step-id shot-01
# 实际读取目录中的 SKILL.md、references/、shared/、request.json 和 record.json 后创作
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step draft --record draft-record.json
# 保存后实际重读，再写发现、依据和修订判断
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step review --assessment review.md
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step finish --record final-record.json --output registered.json
```

`finish` 生成待 `production-import` 的准确包，只有并发版本、现有制作规则和方法产物同时通过才成为受管方案。目标前进时不要手改 `expected_version` 继续提交；回读新目标并开始新步骤。已冻结阶段不能覆盖，进一步修订显式新建步骤。

生成准备包把方法快照与模型 Prompt 分开。模型只得到方案 Prompt、准确媒体和实际参数；手册不会被拼成最终视频 Prompt。新调用登记必须来自同一准备包，仍检查认可、原词、输入锁、渠道、原件与局部范围。已有候选／片段／路线选择记录准确父方案与确定性操作；不补造作者方法历史，也不能夹带 Prompt 修订。

本任务未向 OpenArt、Seedance、Seed Audio 或 Lyria 发起生成。`seed_audio.py`、`lyria_music.py` 的独立实验入口仍保留原账号、费用和恢复边界；它们不自动变成合格生产方案。进入受管制作必须通过准备和 CALL 登记校验。图像／视频 CLI 是外部执行通道，不存在自动生成全剧的服务。

## 正式切换与恢复

沿 [生成工作区流程](generation-workspaces.md) 准备准确双仓候选。在途盘点须覆盖具体工作类型、运行／步骤、冻结输入、待交付内容及后续新步骤，不能按任务创建时间或任务编号永久豁免。

本次采用先完成相关旧交付、再启用媒体约束的切点。`scripts/material_review_release.py prepare` 可接受项目内的 `--method-registry` 和 `--method-audit`。审计的 `wait_for_delivery` 逐项检查任务真实完成；正式 apply 同时持有既有发布锁，停止核验过身份的准确 app 容器，检查 3000 与 64401 的评论、认可、配置和内容写入口停止后才取得切点快照。停机前已接受的新写入包含在快照中，不用旧任务库覆盖活库。新服务同时提供 API 写入锁，单独持有发布锁仍不足以排除页面写入。

`method_migration.py` 只追加配置历史，并记录启用时库中已有方案的准确修订及摘要。它不新增表、索引或触发器；迁移前后逐表比较所有无关数据，只有方法记录与可重建读取代号可以变化。作品、评论、认可、原件索引和准确历史不能减少或改写。媒体新步骤启用后必须采用相应方法；未知旧历史仍保持未知。

恢复分三件事：

1. 方法定义包可在空实例恢复同样的正文、版本和引用；目标已经更新时不能覆盖。
2. 完整 Schema 9 导出恢复作品、评论、认可、原件索引和公开方法／制作关联；实际原件按哈希保全。私有执行另外显式导出，不能靠公开作品包恢复私有候选。
3. 服务回退只恢复运行镜像，**不恢复数据库**。配置迁移沿现有结构追加，不回灌旧快照；如后续需要数据修正，应在保全新写入的前提下作新的准确变更。

执行记录证明读取入口交付了具体内容与阶段结果，不能证明模型内部理解。受控请求、独立会话实践、真实页面与付费外部调用分别验收，不互相代替。
