# AO-UX009 独立实现审查

结论：主协调补齐活动草稿身份后，**35项独立反例全部通过，真实 Chrome 的代表性故障流程证据也通过独立复核**；初稿引入的5项恢复优先级回归已经关闭。本次复核未发现剩余阻断项。浏览器操作由主协调完成，审查者读取了27份原始 JSON、2张实际截图、故障注入代码、只读服务包装和首尾回执；没有把浏览器结果计作自己执行。

审查者为已登记 coverage_reviewer，未实施产品。脚本只写本机 reviews/，没有启动服务、操作浏览器、访问数据库或调用外部API。实际最终执行约46.99毫秒，不是页面性能结果。

## 修复覆盖

脚本从固定3b20d60的polish_draft夹具取DOM/HTTP外壳，实际 app.js/structure.js/screenplay.js 由 --system 指定；没有把 renderComments、定位、choose、草稿恢复或提交清理替换为成功stub。读者布局/面板几何及HTTP响应使用纯技术替代，评论刷新在提交清理用例中stub，不能据此声称真实写入或刷新已验证。

已验证：
- 同source、结构稿、剧本集定位在set失败和get失败时保留逐字正文；正常持久化及失败时保留范围方向/单caret。同集跨场的中间重绘也保留。
- 跨准确结构稿/集，在正文失败或仅meta失败时恢复正确anchor/正文；后续成功input覆盖旧fallback；source同id换revision不继承旧内存意见。
- 取消成功不复活，取消失败仍保留；编辑另一条评论不串旧稿；AI显式采用成功/失败，以及legacy非空保护、空fallback下显式恢复均保持各自意图。
- 成功提交只清本次；迟到回执不能清另一新草稿，也不能清同key后来记录的失败输入。后一项是防御性回调排序夹具，不声称浏览器允许在提交锁定期间直接键入。
- 被编辑的原评论已缺失或已换准确revision时，恢复逻辑仍拒绝重开；无editor时普通列表正常。

## 独立发现并关闭的初稿回归

初稿按“任意该目标fallback优先于持久meta”恢复，导致早先失败的锚点A压过后来成功持久化的锚点B。B取消或提交后，A还会自动复活。五个反例在冻结原基线全部通过，在初稿全部失败，确认属于新增回归。

主协调将准确作用域到当前活跃identity的指针独立维护。每次remember成功/失败都更新当前身份；取消和ownDraft清理只撤销匹配活动资格。A的失败正文仍可供未来明确选择A时恢复，但不能自动冒作当前稿。静态核对该指针更新没有无故替换fallback entry实例；save仍用捕获entry实例判断迟到回执是否有资格清理。

复验记录依次为：
- 首次26项：冻结9过17失败，初稿25过1失败。唯一初稿失败来自本审查错误地要求legacy覆盖非空live草稿；既有文案明确“已有本轮内容时不会覆盖”，因此原日志保留，测试纠正为非空保护/空草稿合法恢复，未改产品适配错误断言。
- 新增真实恢复反例后32项：冻结14过18失败，初稿27过5失败；上述5项在冻结均通过。
- 活动identity修复后32/32通过；再补迟到同key与原编辑评论校验，最终35/35通过。

## 真实浏览器证据复核

浏览器窗口为 2026-10-05 17:34:33—17:39:54（+0800），只读隔离端口62611，桌面1440×900、窄屏390×844。启动时 HEAD 为04bf6bf，app.js和screenplay.js已有未提交修复；首尾产品树哈希一致。当前提交204c469的三份被审产品源码SHA与离线独审完全相同，因此复用35项通过，无须重跑。不能把浏览器当时的 HEAD 写成204c469。

| 场景 | 独立核得结果与范围 | 原始证据（均在 `../browser/`） |
| --- | --- | --- |
| 故事来源定位与切版 | 正文写入抛 QuotaExceededError 后，含首尾空格及换行的全文、准确source/revision、27–33 forward选区在同上下文定位前后完全一致。v8→v9不带出editor，返回v8恢复原正文和身份；跨版本返回选区为33–33，未承诺保留27–33。 | `R2-UX009-SOURCE-before-locate.json`、`SOURCE-after-locate`、`SOURCE-other-revision`、`SOURCE-return` 同前缀文件 |
| 结构稿与剧本定位元信息单独写失败 | 结构第8稿（5cec42…）→另一准确稿（73e1de…）→原稿，第一集be410…→第二集→第一集，非本目标无editor，返回后编辑对象、锚点key和正文精确相同。 | `R2-UX009-STRUCTURE-meta-before/other-revision/meta-return.json`；`SCRIPT-meta-before/other-episode/meta-return` 同前缀文件 |
| 三页正文写失败、读取失败模式下定位 | SOURCE、结构、剧本均逐字保留正文。剧本同集由01-01换到01-02保留，定位回01-01仍准确。实际 getItem 的4次异常均发生在`:submission`读取；正文由live/fallback短路，未发生正文读取异常，不能夸大为每个正文读取路径均抛错。 | `R2-UX009-SOURCE-read-failure-locate.json`；`STRUCTURE-body-after-locate/read-after-locate`；`SCRIPT-other-scene/body-after-locate/read-after-locate` 同前缀文件 |
| 窄屏定位与重开 | 定位后panelHidden=true、焦点comments-toggle；原指针点击记录仍hidden，不算重开成功。后续键盘Enter记录panelHidden=false、同一准确意见正文不变、焦点仍在toggle。 | `R2-UX009-SCRIPT-narrow-after-locate/reopen/keyboard-reopen.json`、`R2-UX009-script-narrow-retained.png` |
| 恢复正常与取消 | SOURCE和剧本另录正常模式新输入；结构恢复normal后取消。三页再次回来editor均null，失败草稿未复活。此轮没有提交或保存到服务器。 | `R2-UX009-SOURCE-storage-restored/cancelled/cancelled-return.json`、`STRUCTURE-cancelled/cancelled-return`、`SCRIPT-normal-restored/cancelled-no-resurrection` 同前缀文件 |

注入脚本只代理62611页面的localStorage方法；没有修改Storage.prototype、sessionStorage或浏览器真实安全策略。24条事件由12次模式控制、8次QuotaExceededError、4次SecurityError组成，**不是24次故障**。本轮只读包装以immutable/query_only打开冻结库并拒绝写方法；102条实际HTTP全为GET、状态200、无error。首尾数据库SHA均为5c6d00…，产品树、实例配置和1411项输入的名字/大小/mtime一致；后者不等于重新校验每份媒体字节。服务已收到SIGTERM正常结束，无错误。

失败和混杂输入原样保留。SOURCE最初等待不存在的整体按钮失败来自主协调说明，现有本批文件未独立记录该次失败；之后使用真实“编辑”路线。结构首次点击的JSON实际出现图像dialog、没有editor，故障序列停在模式控制6，直到之后Enter才有元信息异常7；不能把这次无editor归因为存储修复失败，也没有足够证据断言产品点击根因。390像素截图可见测试浮层占据底部；原指针重开样本未成功，键盘样本才通过。两张截图用于核对布局与测试浮层，精确正文及选区来自原始DOM属性；截图内编辑框可能处于滚动区域外，不以截图文件名证明文字可见。

故障包装与浏览器原件及其SHA列于同名JSON的browser_evidence_manifest。包装README中的“尚未启动”属于初版准备说明，由上述运行回执和真实证据取代；本审查没有修改主协调的包装文件。

## 精确证据与边界

- 可切换源码的脚本：`ux009-independent-counterexamples.cjs`。
- 最终结果及源码SHA：`ux009-independent-live-final.json`；完整失败stack与历次结果保留在同名前缀的 baseline/first/second/third/fourth 文件。
- 冻结基线：`../history-inventory/r2-ux008-ux009-baseline/manifest.json`，Git对象3b20d609448365103ebcf381776e33869913fe8b。
- 本报告同名JSON记录脚本、结果、产品三文件与初稿/基线SHA；后续源码变化不能自动沿用本次通过。

会话内fallback不承诺刷新或崩溃后的恢复；不改历史/原件/数据库，不增加第二套评论UI。此轮浏览器补齐代表性故障定位、切版及窄屏重开，未重演全部35个离线反例，也没有真实服务写入。成功提交、迟到回执和原评论revision校验的本项证据仍为离线行为；不冒作浏览器提交。全量Node由主协调另行报告616/616，本审查未重跑或将其计作独立执行。以上均为功能正确性证据，不形成性能收益结论。
