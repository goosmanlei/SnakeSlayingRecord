> 证据出处：`independent-stage-release-review.md`；原始 SHA-256：`84ae0045f35c49a651323b65f0f21acb2bdb5ce97edbcb65455a0eba5059308d`。正文保留该批次当时结论；当前去向见 [状态补充](../status-addenda.json) 与 [发现索引](../finding-index.json)。正文内未作为链接的 runtime 路径是本机留存证据，不承诺随包交付。

# 三字段正式增量包独立复核

结论：根代理本次将手动阶段加入发布包的修改通过独立核对。仅新增用户明确选择的 `current_stage=MATERIAL_PREPARATION`，与原两段背景合为一次三字段 PATCH；正式库尚未应用。

本审查者曾编写原两字段封装，本次审查的是根代理的新字段范围、候选 JSON、对应 guard 与补偿行为，不能作为原整个发布系统的独立总审。原 Docker、镜像身份、服务所有权、历史连续性与受控完成等未改区域沿用此前他人独审及隔离演练证据。

准确候选

- 受管脚本 SHA：`05fd5a0b53d2dd79222f486eeddaee8344414240bbfbacab40a844c184fe0637`。本次差异只有授权字段集合从二变三及阶段值必须等于用户选择的显式校验。
- 六份 JSON 彼此一致，`before-project.json` 与首次完整 v14 记录逐值相同，完整旧记录／正文哈希不变。更新差集恰为 story_background、creative_background、current_stage，预期正文与请求合成结果一致；630 字故事设定前缀、受众、风格、载体保留。
- `manifest` 的候选正文／updates 哈希、字段清单、阶段事实与用户选择依据同步。原 prepared 时间与未正式应用状态保留，不把后来预览写入冒充正式发布。
- README 将先前两字段预览与阶段选择后的三字段验收区分，正式候选仍从原 v14 一次更新至 v15；补偿为 v15→16 三字段恢复，仍保留两个事件。根代理新回执另外记录主预览阶段单字段 v15→16，不与正式版本号混用。

独立执行

复用原隔离验证的数据与构建方式，在新临时实例中使用真实 ReviewServer 和真实发布封装 `update_package`／`update_project`／`http`／`verify_history`。只将 Request 的地址从正式端口重定向到该实例随机环回端口，没有替身配置结果或调用正式服务。

1. 原 v14 经真实单次 PATCH 变为 v15，完整正文精确等于三字段候选；背景与素材准备阶段一同生效。
2. 同一 expected_version=14 再提交返回 409，不添配置事件。封装重入准确 v15 只回读，不重复 PATCH；记录已推进后再次正向更新也在写入前拒绝。
3. 将候选阶段改回另一个合法枚举 STORY_OUTLINE，封装在任何 HTTP 前按用户选择 guard 拒绝。
4. 真实 SOURCE、结构、剧本三类只读润色参考均读到两段新背景与项目阶段。剧本保留既有 `creative_stage=SCRIPT_DRAFT`，并以 `project_stage=MATERIAL_PREPARATION` 表示项目配置；未调用模型或保存评论。
5. 真实补偿 PATCH 形成 v16，仅恢复原三个字段，完整正文回到原值。再次补偿只回读，不重复写。原 16 条配置事件全部保留，新事件仅精确 v15／v16 两条；其余 11 个业务表逐行哈希一致，SYSTEM 配置不变。基准数据库文件哈希前后相同。

临时服务已停止、目录已删除。结果与所有受管输入哈希见 `independent-stage-release/results.json`，可复现脚本为同目录 `verify.py`。没有重跑原 21 项封装测试，也没有 Docker、集成、推送、正式数据库或浏览器操作。

已回读根代理 `project-stage-history-check.json`：主预览阶段单字段 v15→16，最终完整 body 与本候选一致；其原 19 事件保持并新增一条，其他业务表保持。真实 Chrome 属根代理执行，不归为本审查者执行。

交付文字尚需根代理归并：当前 STATE 与运行报告检查点仍有“阶段未答复／原值保留／正式仅两字段”等先前状态，应改为用户已选择、预览阶段已验、正式三字段待最终确认。旧两字段过程证据保留为当时记录，不改写原验证历史。最终 release 包和批准摘要须按新脚本／JSON 哈希重新准备，不能沿用旧两字段 bundle 的审核摘要。
