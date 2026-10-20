# 独立前端复核

最终未发现尚未修复的 P0–P2 新缺陷。复核者未修改实现或正式测试；实现者根据即时反馈完成修复后，本组回读并复验。此结论不替代真实浏览器、压力与发布验收。

## 范围与方法

读取 HEAD 到工作区差异：`review_desk/static/{app,editing,management-cards,production,review-ui,unified-cards,entity-relations}.js`（初始 7 文件、132 行新增/50 行删除），并阅读相关完整函数和一层直接调用方。共享边界覆盖 `editing.py`、`editing_api.py`、`server.py`；取消补丁后补读 `editing_review.py`。最终文件身份在 `group_3-source-identities.json`，包含当时的 HEAD。

依 bits-code-guard 通用工作流 Step 3.1–3.4，已读 review-dimensions、review-rule 与 lang-typescript，检查逻辑/业务语义、信息与鉴权边界、并发、资源销毁、明确性能回归；未报告风格或仅旧代码已有的问题。文档上下文包括 README、成片剪辑契约；评论来源和草稿行为以 app.js、production-breakdown.js、material-review.js 等一层调用方为准。

## 已发现并复验的修复

1. **P1，置信度 10：同身份轻记录补全被聚焦去重跳过。** 原 `production.js` 早退只更新 detail，未更新 selected。`unified-cards.js` 异步补全素材后（约 485–492 行）会对同一需求调用 focus；因此 selected 留在没有完整正文的轻记录。独立 VM 从实际观察源码提取函数，结果 selectedIsHydrated=false、detailIsHydrated=true；记录在 `group_3-focus-observed.js/json`。修复把 row 对象、edit_token 和 content_sha256 纳入判等；`group_3-focus-fixed.js/json` 回归为两者均 true、准确 prompt 可读。
2. **P1，置信度 10：图片销毁调用不存在的 pause/load，打断其他组件清理。** `reviewRefreshMedia` 也由 `methods.js` 给 IMG 调用；新增无条件 pause/load 在图片销毁时会抛错。修复改为可选调用，并隔离各个 cleanup 的异常。独立 Node 探针在修复后的实际源码上验证 IMG 销毁完成且后续组件 cleanup 运行；见 `group_3-probes-fixed.json`。未将修复后运行伪称为修复前失败实验；原缺陷由实际 diff 和直接调用方确定。
3. **取消覆盖缺口，已补齐。** 最初浏览器为成片 get/review POST 添加 abort，但服务端 lease 仅检查 GET/HEAD，POST 不安装只读 cancel_check。实现者补齐四种只读 editing action 的 lease 检查、dispatch 读前/读后检查，以及 review 元素循环 try 外检查。逐处回读确认调用边界，写 action 仍不走取消路径；此项未单独执行真实断线 HTTP，留给后端回归。

## 独立行为证据

`group_3-probes.cjs` 在 Node VM 中执行实际函数；`group_3-probes-fixed.json` 的四项均通过：

- 图片销毁不阻断其他组件；
- comments 数组替换后索引更新，并区分精确 revision；
- 同波形两个消费者只发一次请求，一个取消不取消另一个；
- Worker 相同输入只发一条消息，一个消费者取消不终止另一个消费者的计算。

聚焦补全另见上述前后探针。轻目录逐项读取以准确 object/revision 调用 get，原有不属于该集/准确版本缺失的拒绝路径仍存在。代码检查未发现本次新引入的错开其他成片或任意回退行为。RAF 手势的 pointerup 会先应用 pendingMove，cancel 恢复原 range；scroll/layout 使几何失效，dispose 取消 RAF、刷位置并移除监听，真实拖动仍需浏览器确认。

独立运行 7 个既有 Node 测试文件，共 99 项：87 通过、12 失败。完整通过的文件为 editing_draft、entity_graph_drawing、entity_graph_layout、production_page_lifecycle、material_source_loading、comment_storage_failure。ui_unification_compatibility 中 10 项因 fixture 未提供新增 reviewLifetime（含一个继发 release 未定义）失败，已通知实现者更新测试装配，不能作为产品失败或通过；另 2 项旧候选默认语义断言在同一 HEAD 私有快照重跑仍失败，见 `group_3-head-existing-failures.txt`，故未列为新缺陷。构建基线快照只读取 Git HEAD；用后已移除本组创建的 head-fixture，保留结果。

命令：`node --test tests/editing_draft.test.cjs tests/entity_graph_drawing.test.cjs tests/entity_graph_layout.test.cjs tests/production_page_lifecycle.test.cjs tests/material_source_loading.test.cjs tests/comment_storage_failure.test.cjs tests/ui_unification_compatibility.test.cjs`。

## 未验边界

本组未操作正式页面、写入业务数据或执行部署；未用非 CUA 浏览器自动化。未自行宣称 20 轮真实 GC、DOM/listener/Worker 不增长、中文字体/窗口 resize、真实多轨拖动、音视频听感、网络断线或本机/VPS性能验收通过。上述行为需要主执行者的隔离浏览器与发布后证据。新增 mock 装配及全量测试结果由主执行者汇总。
