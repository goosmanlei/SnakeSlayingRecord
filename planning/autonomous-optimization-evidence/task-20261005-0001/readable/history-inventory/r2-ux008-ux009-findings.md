# AO-UX008 与 AO-UX009 独立调查

两项均成立，修复由主协调实施。本次先固定 `3b20d609448365103ebcf381776e33869913fe8b` 的 Git 对象，再以真实产品方法离线复现；没有修改产品或操作浏览器/数据库/服务。

## AO-UX008：详情切换后，列表仍标选中旧记录

**P2，高置信度。** P2-record2 的准确 URL、正文和修订均为 S002，但 B1/B2/A2 同刻语义保存 S001 pressed=true、S002 pressed=false。A1 原标记恰好已经是 S002，因此那4条没有暴露问题；不能据其否定另外12条原始记录（包含1条工具等待超时保留样本，不作为性能样本）。

`production.js:276` 通过真实 `reviewSmallCard` 设置初始 aria-pressed，`openProductionRecord:359` 只更新 active class；`unified-review.css:19` 的 `[aria-pressed=true]` 带!important并控制底色/边框。因此视觉选中与辅助技术均不准确，用户容易把右侧 S002 误当作左侧突出显示的 S001。准确详情和评论目标仍跟随 S002，尚无串写证据。

离线夹具运行真实 loadProductionWorkspace/openProductionRecord/reviewSmallCard，技术A/B记录模拟HTTP、读者内容渲染替代。A→B后state和URL为B，A属性仍true、B仍false；返回A恰好又一致。测试不得把 `document.querySelectorAll('#production-index button')` 固定为空。

最小修复是在原成功响应与epoch检查之后，用同一个 selected 值同时更新 active 和 aria-pressed。无需重载索引、移动路由或改变版本/过滤。测试至少覆盖初次读入、A→B→A、同对象旧准确revision，以及迟到响应不能改新选择。真实页面补验仍由根完成；带错误标记的旧测量不得标为“完整界面正确可用”，可明确收窄到准确详情语义时间。

## AO-UX009：本机存储失败后，定位原文覆盖仅DOM草稿

**P1，高置信度的真实方法复现。** 用户先输入 `  unique unsaved opinion\n`；setItem抛quota，界面提示“当前输入仍保留”。同上下文定位却将它替换为 `old durable text`。故事采编、故事结构、剧本三个入口均复现，0次网络请求。

原因是 renderComments 先清空 comment-body，再从localStorage给新textarea赋值。三个定位函数都会调用它，剧本同集跨场还会在chooseScript中间重绘。因此新定位的最后一行做保护仍不够。

| 条件 | 实际结果 | 正确解释 |
|---|---|---|
| 正常get/set，同准确上下文定位 | 正文保留，textarea重建，原选区字段未恢复 | 不是正文丢失；选择连续性仍未保留 |
| set失败，get正常 | 仅DOM新正文被旧持久文本替换 | 已证实输入丢失 |
| get失败，之前set成功 | body先清空，读异常，当前编辑器消失 | 持久文本仍在；恢复get后可读回最新正文，不能称永久丢失 |
| 同剧本集跨场，set失败 | 相同draftKey/target也丢新正文 | chooseScript的中间重绘必须覆盖 |
| 跨结构稿/跨集，已保存meta后set失败 | 离开清anchor，返回恢复旧正文 | 原意见丢失；没有把它写入新稿 |
| 原toggle入口、同上下文且无scope筛选 | set/get失败均保留同node及逐字正文、3–9 backward选区 | 既有保护有效，不能把定位风险推广为所有开关都失败 |

源资料定位不同source/revision本来先拒绝，本次没有将它推成跨源问题。跨稿测试预先调用真实rememberStoryDraft/rememberScriptDraft保存meta后才制造写失败，避免人工缺失meta的混杂。JSON中selectionAfter的null是简化DOM的新textarea未设置该字段，不是声称真实Chrome caret最终为null或0；既测范围选区，也测单caret 7–7，真实布局与焦点仍待浏览器。

最小方案宜在实际renderComments提供明确的“保留当前编辑器”选项，按DOM中的draftKey和draftTarget与当前准确身份共同校验，且state.anchor仍存在；定位与同集视图重绘启用。复用同DOM能绕过存储旧值/读取异常；若重建，则必须在异常前保全逐字文本、选区和方向。跨准确稿/集不能把旧DOM直接恢复进新稿：需要离开前安全保存，失败则保留原上下文并提示复制，或另作按准确身份留存的内存保护。

集中保护仍须识别新的作者意图：startDraft即使同anchor，也可能是新建；AI采用到草稿和显式恢复草稿会合法改变同key正文；取消/提交成功不得复活旧编辑器。commentAction在定位按钮也会增加，不是稳定的草稿代次。源资料草稿key本身不含revision，必须同时比较commentTarget，防止同source不同revision串文。

具体测试清单在JSON。建议重点采用真实renderer而非只检查“调用了renderComments”；保持UX007窄屏定位、准确原文、取消/提交/草稿新意图、正常无editor路径与迟到响应等既有契约，不扩大到全局重构。

## 证据与复现边界

- 冻结源：`r2-ux008-ux009-baseline/manifest.json`，11文件来自准确Git对象，提取时与live逐字一致；产品未修改。
- 执行：`r2-ux008-draft-repro.cjs` 只读取冻结树，采用既有production_change与polish_draft夹具前缀及真实共享helper。
- 原第一轮仅缺VM的URL全局，失败日志保留为 `r2-ux008-draft-repro-first.log`；补充宿主URL/URLSearchParams后成功。未更改产品或业务断言。
- 初始、扩展、冻结复现日志均保留；最新 `r2-ux008-draft-repro-expanded.json` 包含15个草稿情形和P2前后状态，执行约数十毫秒；不是页面性能。
- 本报告只确认发现与修复建议，不把后续修复或真实页面验收提前写为通过。源码行号以冻结3b20d60为准。

## 建议的最小完整兜底（方案，尚未实施）

采用一个仅作会话内故障保护的Map，身份是draftKey加完整commentTarget（包含准确revision）。entry记录准确作用域、anchor、editing、逐字正文、选区/方向和独立代次。input写失败时记录；元信息remember写失败也要在切换前从准确DOM补记。已有entry遇到后来成功input仍须更新或作废，不能让旧缓存压过新成功正文。

renderComments在清空body前保全同身份live editor，优先级为live输入、准确有效fallback、安全读取storage、现有编辑正文默认值。restore沿现有故事/剧本入口按准确作用域恢复anchor/editing；dirty内存必须优先，因为quota故障后get通常仍成功读出旧值。源资料同id的不同revision不能串稿，也不能为恢复而取消已有评论身份校验。

清理沿现有行为：取消清理成功才清entry；取消失败继续保护。提交只清理本次准确entry实例/代次并遵循ownDraft/stillHere，迟到回执不能清新输入。AI采用和显式恢复成功时更新/作废旧fallback，使明确新值优先；失败仍保留原意见。startDraft维持现有同key草稿恢复语义，不重新定义所有同范围新建都必须清空；取消后同anchor不可复活。commentAction包含定位行为，不能直接拿它当草稿代次。

这样可在现有remember/restore与renderer中处理，不改变导航/返回契约，也不添加第二套界面。它只能保护会话内输入，不能承诺浏览器刷新/崩溃后恢复。实现后的关键反例及清理测试已列JSON的minimum_complete_fallback_plan。
