# AO-UX008：选中记录标记同步的独立审查

**局部代码、离线契约和主协调保存的真实浏览器修复证据均通过独立复核；受影响 P2 性能补验仍待完成。** 本结论对应过程提交 `04bf6bfaa237f973fd921f14afaefff8636056fe` 的两份修改文件；其字节 SHA 与先前独审完全相同，不把根随后处理的 UX009、新性能对照或发布算入通过。本人没有重新操作浏览器，而是审阅下述原件与截图。

实现者为主协调，独立审查者为 `/root/reset_supervisor`。开始前守卫为 armed、新 T0 `1791177710`，watcher PID20556、锁与监督有效、无错误。按授权仅只读上述两文件、现有夹具及必要共享 helper；自有脚本、报告和回执写入 `reviews/`，未修改产品、未操作浏览器、服务、数据库或重新测性能。

## 问题与修复是否对应

先前真实浏览器原件已证明，P2 详情的准确对象/revision 已切换，但卡片仍保留旧 `aria-pressed`；CSS 又根据该属性确定选中背景。基线也有该问题，不能算本轮引入。准确源见 `../history-inventory/r2-ux008-ux009-findings.md` 与 [final-action-independent-evidence.json](final-action-independent-evidence.json) 中15条标准错误记录及特殊预热。

本次只在 `openProductionRecord` 原有成功读取路径，把原先更新 `.active` 的同一个 selected 判断同时用于 `aria-pressed`。只有带非空 `data-object-id` 的记录按钮才获得属性，不给索引内无关按钮添加切换语义。没有重载索引、改动路由、覆盖准确历史版本、改变评论目标或扩展界面。

新增语句在原读取 epoch/工作区及异步归属检查之后。迟到读取、读取失败、工作区已切换，均到不了标记更新；原实体 owner 判定不变。settings 下旧子记录仍按拥有者实体标选中，同时详情保持准确子记录/revision；现代统一实体路径继续先委派 `openEntityReview` 并返回，不错误进入通用卡片循环。

两个新增持久测试覆盖 A→B→同 B 旧准确版→A、非记录按钮，以及慢 A 不能覆盖新 B。原来较简化的测试夹具只替换按钮集合，本次独审另运行真实 `production_change` 的 load/open 和真实 `reviewSmallCard`，避免只验证改动形状或把选择器固定为空。

## 独立验证

| 验证 | 实际结果 | 范围 |
| --- | --- | --- |
| 自有实际生产夹具检查 | 8/8，13.55ms | 真实 loadProductionWorkspace / openProductionRecord / reviewSmallCard / focusProductionReview；技术 API 记录、无网络 |
| 原 production_navigation | 14/14，70.21ms | 包括新增2项，准确旧状态/归属、过时读取等原契约 |
| 原 production_change 精选 history | 4/4，67.15ms | 准确历史按钮、从镜头进入历史、既有材料/实体归属、离开后迟到历史读取 |

自有8项的实际检查为：

1. 初次真实列表与详情加载后，唯一当前卡片的 active/pressed 都正确。
2. 点击真实 `reviewSmallCard` 的 A→B→A，两个标记、详情和 URL 一致；索引内另加无 objectId 按钮始终没有 `aria-pressed`。
3. 同一 B 对象显式读取旧 revision，卡片仍选 B，详情及 URL 保留准确旧版，未默默切回当前头。
4. A 慢响应在 B 成功后返回，不能改变新 B 的对象、revision、URL 或任一标记。
5. 详情读取失败，原准确记录和标记保留。
6. 读取期间离开工作区，迟到成功不能改写原记录和标记。
7. legacy settings 的准确旧 STATE 仍显示旧 STATE，列表选中拥有者 ENTITY，非拥有者及子对象按钮不误选。
8. 定义 `openEntityReview` 的现代实体路径仍按原 owner 和准确 revision 委派，通用循环未介入。

实际夹具仅替代技术数据、读者内容排版和 DOM 几何；active 的 classList 被记录以核对属性一致性。没有加载完整浏览器 CSS，故13.55ms是测试执行时间，**不是页面性能数据**。0次 POST、0次外部 fetch。执行前后7份相关文件 SHA 全部不变，详见 [AO-UX008-independent-fixture.json](AO-UX008-independent-fixture.json)。

## 保存的真实浏览器证据

主协调在 Chrome、隔离服务62608、1440×900执行 S001→S002→S002准确版本4→S001。独审读取三份保存状态，并实际查看 S002 截图：

| 原件 | UTC时间 | 独立核对 |
| --- | --- | --- |
| [S002当前版本](../browser/R2-UX008-S002-selected.json) | 09:27:52.180 | 只有S002 pressed；正文标题01-02；URL和精确版本控件同为cab284f5…，版本5当前 |
| [S002准确版本4](../browser/R2-UX008-S002-exact-version4.json) | 09:28:07.142 | S002保持唯一pressed；同一对象准确revision为8289f9c5…；控件明确版本4并显示历史修订提示 |
| [返回S001](../browser/R2-UX008-return-S001.json) | 09:28:07.310 | 只有S001 pressed；正文标题01-01；URL和精确版本控件回到dd7e0739…，版本5当前 |

[实际S002截图](../browser/R2-UX008-selected-S002.png)显示左侧S002卡片带选中底色和边框，S001没有同样选中底色；右侧标题为河街上的邀请、版本5当前。这支持修复所针对的视觉与辅助技术一致性，未用接口代替页面。三份JSON都记录1440×900；Chrome选择和操作链由主协调说明，JSON本身不含浏览器UA或服务代码摘要。独审另从准确过程提交读取两份文件并核对先前SHA，未把DOM原件误称为自带运行代码证明。

起始S001没有这批单独的“操作前”文件；返回S001有完整原件，因此本独审直接确认的是三个保存后态，并结合根的真实操作链。没有因此伪造开始快照、操作耗时或评论写入验证。所有全文revision与原件SHA见独立JSON的browser_evidence。

## 证据与结论边界

- 独立脚本：[AO-UX008-independent.cjs](AO-UX008-independent.cjs)；真实夹具回执：[AO-UX008-independent-fixture.json](AO-UX008-independent-fixture.json)；运行日志：[AO-UX008-independent-fixture.log](AO-UX008-independent-fixture.log)。
- 原测试日志：[AO-UX008-navigation-tests.log](AO-UX008-navigation-tests.log)、[AO-UX008-history-tests.log](AO-UX008-history-tests.log)。准确文件 SHA、diff 和整体回执见 [AO-UX008-independent.json](AO-UX008-independent.json)。
- 不涉及存储/API 写入及导出格式，未发现需要新增数据库迁移或重跑先前 Schema6 保全的变化。此次真实保存状态支持唯一选中与准确版本/正文，未提交或验证评论写入；受影响 P2 的同条件性能仍须另行复验。
- 已测 `3b20d609` 的错误 pressed 原件与旧耗时继续留存；本次修复后正确状态不能把旧样本回写为正确，也不能当作修复后性能数据。按准确差异复用无关已通过记录，无需重跑全部页面。

未发现本次修复新增的高影响缺口，当前功能缺陷已获得实际页面后态支持。该结论不包含性能收益、集成、推送或正式切换授权。
