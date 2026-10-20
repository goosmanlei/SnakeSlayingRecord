# 跨组独立复核

截至本报告记录的候选源码，未发现仍开放的 P0–P2 引入缺陷，`cross_group.jsonl` 为空。三组报告中的已修复问题与跨文件契约没有发现直接冲突。该结论是独立代码及私有行为复核，不代签正式 UI、性能、部署或恢复验收。

## 范围与方法

读取 `group_1-notes.md`、`group_2-notes.md`、`group_3-notes.md` 及相关证据，回看修复后的 `resources.py`、`read_cache.py`、`server.py`、`editing_api.py`、`editing_review.py`、`editing.py`、实体投影和前端读取链。按 bits-code-guard Step 3.1–3.4，先读取新旧 diff、完整函数和直接调用方，再检查逻辑、业务语义、安全、并发、健壮性、资源释放和明确性能回归；JavaScript 参照该技能的 TypeScript 专项。仅报告本次新增且触发条件明确的缺陷，不报告风格问题。

基线为 desk `254d509cbe644f75e90344bc1ae40b7279aa418f`，候选仍为工作区修改。复核时各实现文件的准确身份见 `cross_group-source-hashes.json`；此后文件改变需按影响复核。本次未修改实现或正式测试。

## 已复验的交叉边界

- **浏览器取消到服务端释放。** 前端成片摘要、准确 get/review 及实体大卡读取携带所属页面或对话框的 AbortSignal，替换请求与销毁会取消旧请求；原有 epoch、对象身份校验仍保留。服务端只给 catalog/get/status/review 安装读取取消检查，资源读取作用域包含相应 POST。真实私有 HTTP 探针覆盖 GET 和 POST 的这四个 action，共 8 个组合：客户端在受控读取期间断开，实际 handler 中的生产读取或资源读取检查观察到取消；请求结束后数据库事务、请求读取缓存、资源租约和取消回调均释放。探针用受控 `_dispatch` 读取体，验证实际路由、连接和作用域，不把它当作完整真实成片渲染。
- **写入和只读事务分界。** 源码确认写 action 继续原提交路径；独立 dispatch 探针用 save 替身确认不调用传入的读取消检查，也不创建读取事务/缓存作用域。未执行真实写业务请求。review 的每个元素和 binding 检查前设取消点，dispatch 结束前再次检查；因此底层取消若被现有媒体不可用分支捕获，仍会在后续边界停止请求。
- **内容缓存与评论新鲜度。** `content` 域只排除 comments/comment_events，其他表代际仍参与失效；HTTP 路径只对明确的内容列表使用此域。只缓存不含选中详情、候选修订或直接 ASSET 原件上下文的 deferred workspace，之后每次补当前评论目标。私有 SQLite 探针通过真实 CLOSE 评论动作确认：评论域重建、内容域复用；随后真实源记录变更同时使两个域重建。内容域与完整域的读取次数分别为评论关闭后 1/2、内容变更后 2/3。
- **准确版本与原件可用性。** summary catalog 返回准确 object/revision，前端补全和 review 使用同一对身份；默认 catalog 保持旧完整返回。私有 HTTP 用合成不可变成片记录验证 GET summary → POST get 的准确正文，故意错配 object/revision 返回 400。组 2 可重放探针再次确认已选原件删除立即暴露、候选实际选择拒绝、摘要不读取云原件、字层缓存命中仍验证每个 entry 和实时归属及物理文件身份。
- **容量、版本与生命周期组合。** 复读组 1 的并发预留修复、准确云版本每次 HEAD、同对象锁与租约退出顺序，没有发现其与取消传播或只读事务冲突。前端评论索引依赖数组替换，波形/Worker 按消费者释放，图片销毁允许缺少 pause/load；复用了组 3 已完成的实际函数 Node VM 证据。本次未重新执行这些既有组内探针，也未将 Node VM 当作浏览器验收。

## 独立执行结果与重放

`cross_group_probe.py` 共 **4/4 通过，1.389 秒**，日志为 `cross_group-tests.txt`；其中断线用例包含上述 8 个 HTTP 组合。另将组 2 既有探针整理为 `group_2_probe.py` 并执行 **5/5 通过，1.156 秒**，日志为 `group_2-replay-tests.txt`。脚本全部使用自动清理的临时实例和合成文件；HTTP 仅绑定本机回环临时端口。

从 desk 工作区运行，`$STORY_WT` 为主任务工作区：

```sh
PYTHONPATH=. python3 "$STORY_WT/.runtime/performance/independent-review/group/cross_group_probe.py" -v
PYTHONPATH=.:tests python3 "$STORY_WT/.runtime/performance/independent-review/group/group_2_probe.py" -v
```

前两次跨组探针未通过是探针自身装配问题：评论文字锚点缺少必填字段，以及将 socket FIN 的异步抵达误写为立即可见。随后补齐锚点，并在有 2 秒上限的安全读取边界重查连接，未改生产实现。原始日志 `cross_group-tests-initial.txt`、`cross_group-tests-second.txt` 保留，不将这些失败记为产品缺陷或通过证据。

## 未验边界

未访问正式实例、正式数据库、OSS、凭据或付费生成；未操作浏览器或发布服务。真实 UI、20 轮生命周期/GC、音视频与多轨拖动、生产规模性能收益、本机/VPS 发布、空实例恢复和用户验收仍由主任务分别取证。组内既有测试失败及其 HEAD 对照以各组报告为准，本报告没有把它们计为全量通过。
