# 取消逐项审批任务的依据

先读任务正文 `../comment-led-review-retirement-task.md`。本目录支撑已定产品目标和迁移边界，不是已完成实现报告。

- [dependencies.md](dependencies.md)：当前未完成任务范围及直接依赖 0018 的理由；0018 传递依赖 0015/0016。任务状态以主账本实时值为准。
- [model-evidence.md](model-evidence.md)：RV/DC 的实际用途、评论去重、不可变 CALL 和可复用退出机制。
- [model-evidence.json](model-evidence.json)：正式库只读一致查询的准确身份、计数与必要历史意见原文。仅用于分类和核对，不是可覆盖正式库的数据包。
- [sample.html](sample.html)：本机可操作评论样例，非正式产品、未加载声音、无 AI 调用；以正常浏览器打开即可查看。测试留言仅本机存储。
- [browser-observations.md](browser-observations.md)：根代理正式页面只读与样例保存／重开／刷新的实际观察及边界。

调查时 Git 基础为 primary 93ce2df、desk 8d7a04cf1935ec166afa68ef7711405ae4e74510，正式服务页面另行只读观察，二者不能混称。执行以实际开始时最新双仓主干和有效正式数据为准。

用户已确认：清理 RV 及旧实体送审包，取消独立审阅决定及逐项审批，由评论表达意见并由 AI 整改；准确版本／候选选择只保留底层支持，本次不做新 UI 或自动策略。用户要求将整个目标发布为一项任务，并按未完成任务安排依赖。本次不是恢复持续 Review 的授权。
