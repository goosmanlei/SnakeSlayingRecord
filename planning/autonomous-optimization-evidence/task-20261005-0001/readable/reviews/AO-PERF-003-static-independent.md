# AO-PERF003 评论 SOURCE 请求内缓存静态独审

审查者 `/root/reset_supervisor`，未实施本批。按根的性能窗口约束，只读代码与既有测试；没有运行测试、数据库、HTTP、浏览器或后台负载。

**结论：当前最小 diff 未见必须修复的问题，可以进入有界验证。** 这不是已通过兼容性测试、性能测量或页面验收的结论。

## 已确认的兼容性

1. GET `/api/comments` 的筛选、排序和 material scopes 仍由原 `store.comments` 完成；新 helper 仅添加原有 anchor_state 字段，保留原 comments 顺序与字段。`/api/comments/context` 和写请求路径没有切到批处理。
2. SOURCE 缓存按 object_id 保存 `source()` 解析出的完整文档及从该文档重算的 canonical digest，没有把 sources.revision 列当作内容真实性证明。每条评论仍查询 object/revision 并核对 revision.object_id；缓存命中后仍比较准确 payload.source_revision。
3. 缓存的是文档，不是整个 anchor_state。首次错 revision、错引用或错范围只影响本条结果，不应污染同源下一条正确评论。原 `_validate_blocks` 构造独立 pieces 字符串列表，并不改写源 blocks；缓存对象没有随 anchor_state 返回给前端。
4. STORY、生产记录、global/time/visual/region 路径照旧。time 和生产视觉的原件校验、SOURCE 视觉文件存在检查均仍逐条执行，不会因上一条通过而跳过。异常捕获种类和失败 reason 逻辑未改。
5. HTTPServer 的 Store 实例持续存在，因此不能把此缓存挂到 Store 上；当前实际代码在每次 helper 调用中创建局部 dict，满足这一要求。默认 `_source_cache=None` 的直接 validate_target/anchor_state、create_comment、润色、bundle.restore 继续每次读取。
6. keyword-only 私有参数保留原三位置参数调用方式。仓库内未发现必须接受新四位置参数的调用，或覆盖这两个方法且拒绝新 keyword 的现有产品子类。

## 必须由针对性测试闭合的边界

- 同一 SOURCE 的正确、错误 quote/越界/错块评论混排；每条结果与旧逐条 anchor_state 完全相同，source/digest 只做一次。
- 相同 SOURCE 的错误 revision 与准确 revision 混排，及他对象的 revision；不能用当前头替换被评论历史，也不能跳过归属检查。
- document 实际字节/内容改变而 sources.revision 列维持旧值时，仍按实际解析内容重新计算 digest 并拒绝不匹配；不要仅用列值做缓存命中。
- 同一 Store 上连续两个批处理调用，第二次必须重新读 SOURCE；缺失、损坏或修复不应留下跨调用的失败/成功缓存。
- 直接写/润色/restore 使用默认参数，不因先前 GET 命中绕过校验；建议明确 source 调用次数和结果，避免只测代码内分支。
- 不同媒体评论之间的原件变化仍会被逐条检查。即便同一 SOURCE 文档命中缓存，也不能缓存 visual 文件存在性；生产 time/region 应保留真实 component SHA/范围检查。
- GET 的空结果、source/object/revision 筛选、混合 SOURCE/STORY/生产评论和 scopes 字段的完整 JSON 等价。

此代码没有让整个 GET 成为数据库事务快照，不能宣传为一次请求内所有查询的原子快照。现有 API 禁止替换已有评论的 SOURCE，当前最小优化可以继续保持这个既有业务边界；不要顺手扩大为跨请求对象缓存、修改正式 SOURCE 规则或改写写事务。

## 验证输入

读取时 HEAD：`ddb602e3cd084f0420d16e67eb03a6a6fd25ca5c`，两文件为未提交 diff；指纹如下。

```json
{
  "review_desk/store.py": "f4890ff6c941884b0b772006f8e9625201f3f8682cefdb49597e32b83a897896",
  "review_desk/server.py": "757d2f0f5f660adbfe44531e7150ff1f2623f35d252bb723f4fe9cdee617dbd8"
}
```
