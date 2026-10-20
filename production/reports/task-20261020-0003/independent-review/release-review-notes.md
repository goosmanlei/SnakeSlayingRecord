# 数据保留发布脚本：独立补充复核

本次新增 `--task` 未发现 P0／P1／P2 缺陷；`release-review.jsonl` 为空。参数正确传递后，现有 prepare／apply／finalize 流程能够使用 `task-20261020-0003` 的身份。这个结论只覆盖代码与以下只读检查，不代表正式发布或发布验收已经完成。

## 范围与测试

复核 `scripts/oss_runtime_release.py` 的本次 diff、全部直接使用 `TASK` 的函数，以及 `vps_experience_remote.preflight`、旧全量发布保护、`resource_bundle.closure`／`database_identity` 和已有发布契约。Python 没有 bits-code-guard 列出的额外语言专项；按新旧代码方向及逻辑、业务语义、安全、并发、健壮性、性能维度检查，未把旧实现的适用边界误报为本次新增缺陷。

本次脚本 diff SHA256：`be888960dfa6cdcab3cc3c43d556d0a9074943d9d5e0480a8541d21a27582e72`。

通过内存载入脚本、替换子命令处理函数的方式验证参数解析，没有执行真实 prepare／apply／rollback／resume／finalize：

- 5 个子命令分别测试默认和显式身份，共 10 项通过：默认仍为 `task-20261019-0004`，显式值为 `task-20261020-0003`。
- 路径穿越前缀、编号长度错误、末尾换行、全角数字共 4 类输入在派发前以退出码 2 拒绝。
- 新 `TASK` 拒绝旧任务的 manifest，错误为 `wrong release ownership`。
- 参数测试没有调用 Docker／SSH。另做了两端 Docker 元数据和配置摘要的只读回查，未访问凭据正文、正式库或云端原件。

## 身份链路

`main` 在合法正则验证后、派发前更新全局 `TASK`。后续链路一致：

| 环节 | 身份依据 |
| --- | --- |
| prepare | `manifest.task=TASK`；同时绑定双仓提交、镜像身份和文件摘要 |
| apply | `verify_bundle` 要求任务相等；receipt、HTTP 写入锁容器、应用 `org.leiguoguo.task` 标签使用同一 TASK |
| rollback | receipt 任务检查；新容器的任务、镜像、desk 提交、manifest 摘要和实例挂载共同核对后才移除；旧容器原身份保留 |
| resume／finalize | receipt 任务和阶段检查；准确活动容器 ID、镜像及 release 摘要复验 |
| VPS 长期入口 | `storage_upgrade.task` 使用 TASK；`storage-runtime.json` 通过 release 路径和 manifest 摘要关联任务 |

**本轮每个命令都必须显式携带全局参数，并放在子命令之前**，例如 `python3 scripts/oss_runtime_release.py --task task-20261020-0003 prepare ...`。bundle 内及 release 内脚本的默认值同样保留旧任务；apply、finalize、rollback、resume 不能遗漏该参数。遗漏会在 manifest／receipt 所有权检查处拒绝，不应为继续执行而改旧回执或绕过检查。

## 当前实际挂载和目录

只读回查时，正式本机容器为 `4f9af2d5cf29e8d61af31b754acdb86a1a2f9e3fc61665b3e02b24493eaf132d`，desk 标签为 `254d509cbe644f75e90344bc1ae40b7279aa418f`；VPS 容器为 `a5b382d64590cd2a937fcba1c174349f2609f9e1b73524adffbdd4cdc9418d59`，desk 为 `816f728329453cf3c15c234920f879bdb67aa991`。两端旧 task 标签均为 `task-20261019-0004`，所以旧标签不能单独代表当前源码版本。

两端实际生效的资源配置和当前候选逐字节相同：

| 文件 | 两端及当前候选 SHA256 | 规模 |
| --- | --- | --- |
| `config/resource-storage.json` | `c4cf173c34fa942837f5a19f6245ada7894abd9841a5bfecccdbb28ad2944683` | 413 B；project／bucket 为 lijizhanshe，region 为 cn-hongkong，cache_bytes 为 16 GiB |
| `config/resource-catalog.json` | `fde3fd17f056883caaa57685164e2cf1ea29730718ea5ed22962a58b610c124b` | 1,161,619 B，817 个逻辑路径 |

两端实例根下 `.runtime/resources/catalog.json` 均不存在。本次现场没有发现 VPS 独有 base catalog 被当前候选覆盖的差异；正式切换时仍须在发布窗口复核，不能把本次只读快照当成永久锁定。

实际配置来自旧发布目录的逐文件挂载。本机来源为 `.runtime/service-releases/task-20261020-0002-08c0b83e00d2-254d509cbe64/instance/config/`；VPS 来源为 `/home/work/lijizhanshe/storage-releases/oss-a21308561feb-816f72832945/config/`。必须按 Docker 生效挂载取配置，不能读取实例目录下被覆盖的占位文件来替代。

## 本次发布仍须核对的具体边界

1. **保留的是当前实际配置，只有 code pin 前进。** apply 第 300–306 行从旧 `instance.json` 挂载源读取，保留原字段，只修改 `review_desk_commit`；这个行为同样适用于本机。如果本次候选改变了其他 instance 配置，不能认为这些字段会随 bundle 生效。本任务应核对实际新挂载文件与旧配置的差异确实只有 pin。
2. **base 资源目录会替换，runtime overlay 才被保留。** resource-storage 和 resource-catalog 来自新 bundle，脚本不自动合并旧 base catalog。停写后复制实例 `.runtime/resources/catalog.json` 到候选位置用于 closure 检查；正式服务仍读取原实例的可写 overlay。若发布前发现新 overlay 或目录差异，须保留所有准确描述和冲突校验。closure 检查业务引用和 SHA／字节数／MIME 的目录一致性，不等于完整远端字节可用性验证。
3. **旧内容挂载仍是新服务依赖。** 除 3 份配置和 OSS 凭据外，apply 第 389–398 行逐个保留旧 bind 的 Source、Destination 和只读状态。本机三份 `content/data-model.json`、`content/production-approach.json`、`content/skill-flow.json` 仍来自 task-20261020-0002 的 service-release；本地 CA 挂载也保留。VPS `/usage` 和 `/instance` 保留。新服务验收后不可仅因旧任务编号而删除这些源目录。
4. **记录实际发布后的配置摘要和运行身份。** release 内 `instance.json` 是以上述真实配置生成的，因此不保证与准备包中同名文件的 manifest 摘要相同。不要只凭候选 manifest 宣称运行文件一致；回读三份配置的真实挂载、实际内容摘要、desk pin、镜像 ID、容器 ID、TASK 和 oss-release 标签。finalize 后两端 `storage-runtime.json` 及 VPS `state.json` 应指向准确新服务，原 `publication_id` 保持。
5. **停写窗口需要覆盖独立写入者。** HTTP 写入锁只约束遵循该锁的请求；发布锁与停掉应用不能自动阻止任意外部 CLI 写库或写 catalog。切换前确认渲染无 queued／running，并协调本任务之外的写入者。保存两端各自的数据库备份与表指纹、usage 摘要，不用本机数据填补 VPS 原有内容差异。
6. **数据库不变证明与索引恢复分开。** 现有 `database_identity` 不包含 read_generations，也不统计索引；新索引不会因此误报业务内容变化，但前后指纹相等不能证明索引完整恢复。本次新增索引仍需主任务的完整导出到新空实例恢复证据。
7. **遵守回退阶段及实际资源边界。** `opening`／`open` 后不能自动退回旧代码；不确定时先核 receipt、准确容器和写入锁，再使用对应任务的 resume／finalize。正式切换前后独立核对原网络、内存／CPU／PIDs、日志限制、共享 Nginx／Xray、凭据挂载和服务健康。清理时以实际活动挂载和恢复责任判定保留项。

本组未执行正式发布、恢复或业务写入；新服务实际页面、性能、资源闭包和完整恢复仍由主任务交付。
