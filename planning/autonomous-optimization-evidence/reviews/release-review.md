> 证据出处：`independent-release-review.md`；原始 SHA-256：`d757e9fbd52240b8a7515d3a0595a1b739d459fd0adf33f64121f16f80b9020a`。正文保留该批次当时结论；当前去向见 [状态补充](../status-addenda.json) 与 [发现索引](../finding-index.json)。正文内未作为链接的 runtime 路径是本机留存证据，不承诺随包交付。

# 发布封装独立审查

恢复链原 3 项问题已关闭；REL-04 基础镜像引用修订的独立函数审查通过。当前候选 `delivery-plan/release.py` SHA-256 为 `c4ddc127bb004c1f8484870c02b9e5635fc128905b258013a6b027311d61953d`；这份结论只覆盖静态审查、真实封装函数与隔离命令替身、临时 SQLite，不代表实际 Docker／Compose 或正式发布通过。

本代理没有实现封装。先通读初版 581 行、设计、服务只读清单与既有受控快进器，再补 4 项独立探针；作者根据根授权修复后，补验受影响的 7 项。未重复作者 15 项全套，未执行真实 Docker、正式 HTTP/PATCH、集成、推送或 `_complete`。

## 原问题及复验

| 编号 | 原影响 | 当前实现与独立结果 |
|---|---|---|
| REL-01，原 P1 | 故事 main 未变、另一个发布已切正式服务时，恢复仍会 force-recreate 覆盖它。 | 写入前核对两候选/main、CA、旧Compose、本次run身份与原快照哈希；app/nginx只接受准确旧、本轮candidate或固定恢复中间态。独立确认 foreign app 与 foreign nginx 均在任何 compose 调用前拒绝。 |
| REL-02，原 P2 | 旧 image ID 存在不能保证旧 Compose 的可变 tag／隐式 nginx tag 启动该镜像；原实现先启动再报错。 | 不可变恢复覆盖同时固定两个旧 image ID，应用环境仍通过内存占位映射。独立确认 candidate app＋old nginx、old app＋candidate nginx 均正确恢复；已旧或再次恢复不重建。保存文件没有技术测试环境值。 |
| REL-03，原 P2 | 两字段补偿已经写 v16，但回读/回执中断后重入因不再是 v15 而拒绝，无法补确认。 | 准确v16＋完整旧body只回读；恢复前后检查本次旧快照、旧行保留与准确v15/v16完整事件链。独立临时SQLite验证重入和再重入均0 PATCH并完成回执；v16当前值正确但前一v15事件body错误则在写入前拒绝。 |

初版 SHA `7ed31a57fdc404ed6bb1f0f3bbd3d04d902f01bbc77a5f5ff2697e4f3ac76883` 的 3 个反例在 `independent-release/results.json`；4 项通过是“证实缺陷＋验证旧行保护”，不是初版验收通过。修复后 `independent-release/recheck-results.json` 为7/7，`recheck.py` 使用真实 recover／recovery_runtime／update_project／verify_history，仅替代Docker/外部命令边界，配置历史检查使用实际临时SQLite快照。

首次新夹具未把旧 mounts 按实际 safe_container 规则排序，6例在进入目标路径前被正确拒绝；修正本夹具排序后7/7。原始 `recheck-fixture-initial.log` 留存，不将夹具错误称作产品回归。

## REL-04 本地基础镜像标签修订

原 `FROM sha256:…` 在本机真实 Docker 构建失败，依据为 `docker-rehearsal/build-results.json`；`local-tag-results.json` 是另一诊断构建的成功证据，不等于准确新版 wrapper 已执行成功。候选改用包含本任务 ID 与完整基础镜像 ID 的本地 tag，`prepare` 只记录该名称；`build` 检查准确镜像存在，仅在标签确实缺失时创建，遇 foreign tag 或列举失败拒绝。构建显式 `--pull=false --network=none`，完成后再次核对基础 tag，随后核对候选镜像源码并写入绑定 manifest 的回执。

独立 `independent-release/base-tag-probe.py` 执行实际 helper 与 build 函数，Docker 命令边界全部替代，使用真实临时回执文件。8 项通过：同 ID 标签复用且不重写；准确基础镜像缺失拒绝；缺失标签只从准确 ID 创建；foreign tag 拒绝覆盖；列举失败不猜测缺失；创建后标签漂移拒绝；构建中漂移在源码核对和回执前拒绝；正常构建参数、源码检查、镜像及 manifest 回执绑定正确。结果在 `base-tag-results.json`，没有真实 Docker／正式写入。

本次不重复已通过的 7 项恢复探针，修订集中于基础镜像 helper、prepare 的 FROM／manifest 和 build。旧恢复报告的 e981564 SHA 是当时验证输入，不应改写成新版本已跑同一套。随后独立实施代理的实际 `docker-rehearsal/wrapper-build-results.json` 已回读：准确 c4ddc127 wrapper 的 load_bundle／pin／build／source_check 成功，42 文件一致，基础 tag 前后同完整 ID，正式容器 ID、镜像和启动时间不变。输入是 system10a11aa／story5e016a 的技术机制包，尚未运行完整 prepare，也不是最终交付候选包；实际 apply／正式发布未执行。

## 已核对的保护与限制

从准确Git blob导出两份故事文件及完整review_desk树，核对story pin、准确候选/目标、同仓和受管清洁度。正式镜像内源码逐文件比对，不能从 `/api/instance` 单独推断运行代码。

两字段PROJECT请求仍限制完整旧记录/version14和完整新body/version15，未知结果不盲重发；补偿是版本前进到16，不还原旧库。不自动提高expected_version，额外更高版本或其他body仍拒绝。

数据库只读一致backup，不覆盖活库。所有旧业务行哈希多重集合必须保留，SYSTEM精确不变。独立SQLite反例确认新增一条相同内容不能掩盖旧行身份被改写。恢复补偿还核对准确事件body链。共享写窗口仍需协调；本封装不会自动修复外部改写历史。

新Compose定义保留CA只读、正常主实例、两个只读文件覆盖、3000/64401环回端口及完整环境内存占位；子进程输出捕获，不落盘秘密。永久restart已收缩为对准确现有双容器执行docker restart，不重建/重新设计发布；容器缺失或归属不明应停止。

旧 Dockerfile 直接 FROM sha256 已被根实际 Docker 演练证伪；新的本地 tag 机制及准确新版 wrapper 构建已在技术输入包通过；最终候选构建、Compose 真实创建／中断／恢复、两个端口及正式源码落点须以各自独立回执验收。根禁止本代理真实build/apply，故不以mock替代。app已切而nginx尚未完成的已知中间态已由函数探针覆盖；容器缺失等未识别状态停止，不承诺自动恢复任意中断。

`apply`的终点只是formal_browser_acceptance_pending。最终候选、发布输入、镜像回执和演练准备好后，仍须用户明确确认；根执行一次必要正式Chrome及原 `_complete`。本报告不是发布许可，亦未宣称实际服务已经切换。
