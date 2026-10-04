> 证据出处：`final-release-process-normalization-review.md`；原始 SHA-256：`22cc8f26892491c75352f5c028b22c3d223dc3ae27821a8c6c0ed0999f57454a`。本项接续 AO044 发布护栏，当前去向见 [状态补充](../status-addenda.json)。产品综合终审与 c1da4cd 源码保持不变。

# AO044 最终发布准备：空 User 比较独立补验

窄修通过独立复核，未发现阻断项。它只允许 Docker 元数据中未指定 User 的 `null` 与空字符串等价；非空用户差异和其他启动字段仍被拒绝。系统产品候选 `c1da4cdce8c98bd52beafed1dc0a7b70887d8653` 不变，本补验不代表真实发布准备、构建或切换成功。

根首次实际只读 prepare 返回 `ValueError: nondefault service process configuration; revise plan`。两容器均只存在 container User 空字符串与 image User null 的差异，其余受检字段相同。没有生成发布包，也没有正式写入。随后 shell 的 cat 成功不能当作 prepare 成功；原失败回执（本机原证据：final-release-prepare-first-failure.json；按 source-index.json 查询是否收入）与字段差异（本机原证据：final-release-prepare-process-difference.json；按 source-index.json 查询是否收入）保留。

修后脚本 SHA-256 为 `b7f437bfddb864f4d347046c38a74e75e1d4ec21c30a0f786e3176e69c5224df`。相对已审 `05fd5a0b…`，唯一源码变化在 prepare 的四字段比较：复制 Cmd、Entrypoint、User、WorkingDir，只将复制件中 `User is None` 转为空字符串，再严格比较整个字典。没有使用会放过 False 或 0 的宽松真值转换，也不修改原始 inspect 数据或 safe_container 快照。镜像本来明确指定用户且容器完全相同时，沿用原先允许行为；未把全部非空用户一律禁用。

独立探针调用实际 prepare，使用不同于作者测试的合成容器与镜像元数据；前置 Git/inspect 以本地替身隔离，在两个服务的进程比较均结束后立即停止，禁止进入真实 HTTP、子进程或发布包写入。38 个分支全部通过：

- app 与 nginx 分别覆盖 null／空字符串双向、两边均空，以及原本同一个明确镜像用户。
- root、字符串 0、UID:GID、空格、不同明确用户、镜像非空但容器为空均继续拒绝；非法布尔 False 与数字 0 也不被规范化接受。
- Cmd 变化或移除、Entrypoint 的列表／空列表与 null 差异、WorkingDir 改变或置空均继续拒绝。
- 每个允许和拒绝分支结束后，原始 inspect 数据与 safe_container.user 均保持原值。

旧源码执行同一比较场景时，10 个应允许的场景被拒绝、28 个应拒绝场景正常拒绝；修后 38／38 通过。探针结果（本机原证据：final-release-process-normalization-review/after-results.json；按 source-index.json 查询是否收入）与来源哈希（本机原证据：final-release-process-normalization-review.json；按 source-index.json 查询是否收入）保存了准确输入。作者 24 项发布封装测试结果已阅读，此处未重复整套。

RestartPolicy、环境、挂载、端口、CA、PROJECT 版本、准确候选及 build/apply/recover 的护栏未改。这个离线实际函数补验不能代替根重新执行最终候选的只读 prepare、构建与 preflight；更不能当作正式服务写入或验收。综合终审的核心产品结论保持，本补验仅接续其中发布脚本 05fd 的准确字节绑定；最终故事提交与后续运行回执仍由根绑定。
