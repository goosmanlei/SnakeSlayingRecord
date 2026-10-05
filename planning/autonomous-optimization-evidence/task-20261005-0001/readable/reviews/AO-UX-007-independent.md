# AO-UX-007：窄屏评论定位独立审查

最终小改动可保留，在本次审查范围内没有未解决的阻断项。SOURCE、故事结构、剧本普通与结尾定位都在找到有效目标后，才收起窄屏评论面板；普通页面把焦点返回现有评论按钮，不增加额外滚动。根的 390 像素真实页面记录支持 S1 文本、S2 圈选图像、S3 文本定位后内容可见、焦点可用；1200 像素记录支持宽屏仍保留面板。跨场结尾和错误路径不能据此扩大为已完成真实浏览器验收。

审查者 `/root/reset_supervisor` 独立于产品实施者主协调及测试 worker。此次仅读取代码、diff、测试源码和已保存浏览器证据，并查看三张 PNG；没有操作浏览器、执行测试、读取数据库或修改产品。基准 HEAD 为 `2ffe4c3382d3bb4ef94f4310a4609f6cd9daa835`，准确未提交 diff、源码及证据 SHA 在同名 `.json`。最终入口守卫 armed，T0 `1791177710`，锁、心跳和监督有效；这次检查未重置计时。

## 独立发现及修正

| 发现 | 最终处理 | 复核结论 |
| --- | --- | --- |
| 第一版在所有窄屏定位之前直接收起；invalid anchor、缺准确修订/场次、目标不存在时也会隐藏评论上下文 | 通用入口恢复原 unified-dialog 条件；新增调用移到 SOURCE/structure 有效 target 与 script 有效 block 之后 | 已静态消除本轮新增的失败路径退化；原校验、准确版本与错误提示保留 |
| “定位引用结尾”直接调用 locateScriptComment(comment,true)，绕过通用入口 | 在 locateScriptComment 的成功 block 分支统一处理 | 两个入口都执行；此项是发现并补齐既有遮挡覆盖，不记为初版新引入缺陷 |
| 普通页面重建评论按钮后，成功定位时焦点落 BODY | revealLocatedComment 在 `<1200` 收起后，面板直接属于 body 才 focus 现有 comments-toggle，使用 preventScroll:true | S1/S2/S3 最终记录焦点均为 comments-toggle；modal 返回焦点规则未被改写 |

`revealLocatedComment` 最终使用正向 `if(window.innerWidth<1200)` 包裹收起与聚焦，宽屏直接跳过整个动作；窄屏聚焦后各路径继续执行原目标 scrollIntoView，因此不会先滚向底部评论按钮再拉回正文。真实浏览器的有限数值宽度下，这与前次所验的 `>=1200` 提前返回等价，故最终语法调整可复用已完成浏览器证据。helper 不改变目标、准确引用或选中评论；非 body 的 modal 不会把焦点移出弹窗。现有 production、entity、material、reference 与嵌套 dialog 的定位和面板搬移没有本轮新增变化。

## 真实页面记录回读

以下路径相对 `../browser/`。这是根的真实浏览器证据经过独立文件复核，不是审查者重新操作页面。

| 场景与记录 | 可确认结果 | 结论边界 |
| --- | --- | --- |
| S1，390×844：`R2-UX007-final-S1-draft.json`、`location.json`、`geometry.json`、`draft-restored.json`、`390.png` | 定位后 panelHidden=true，焦点 comments-toggle；评论 39e0f723-3ac6-4ce4-ad9b-01e4f6813a1a 的“能”在 y550.234–574.234，命中检查 visibleTarget=true；截图中高亮未遮挡。重开后输入与定位前逐字相同：“未提交定位回归草稿：最终成功路径与准确原文。” | 直接证明这次正常存储的未提交草稿保留和目标可见；不能推广到 localStorage 失败 |
| S2，390×844：`R2-UX007-final-S2-location.json`、`geometry.json`、`390.png` | panelHidden=true、焦点 comments-toggle；准确 visual id 为 site，图像 y421.656–621.656；圈选区域几何 y510.296–556.456 均在视口内，截图中原图未被面板覆盖 | 此组没有 S1/S3 的 elementFromPoint 字段；依据几何与实际截图判断图像可见，不虚构命中结果 |
| S3，390×844：`R2-UX007-S3-keyboard-located-390.json`、`geometry.json`、`390.png` | panelHidden=true，焦点 comments-toggle；评论 d5fdd7dc-4102-49ed-b109-527ffc771813 的“挑柴老汉原本跟着打拍子，手停在半空。”在 y479.828–503.828，visibleTarget=true；截图高亮可见 | 为普通键盘定位，不能当作跨场结尾按钮的真实页面证据 |
| S1，1200×900：`R2-UX007-final-S1-1200.json` | 查看评论按钮仍 expanded，审阅评论区域仍存在 | 支持 1200 边界不触发窄屏收起；不替代所有宽屏/场景验证 |

S1/S3 记录时间为 UTC 07:55:22–07:56:14，S2 为 UTC 07:57:48–07:58:00，均为本次最终焦点处理后由根提供的记录。原问题由根在 390×844 发现，前证据 `R2-S1-native-narrow-located.png/json` 保留。新正文、评论内容、锚点、正式数据或媒体原件均不在本次产品 diff 中。

## 测试与剩余边界

独立阅读了 worker 对 `tests/comment_outside_click.test.cjs` 的新增覆盖：390/1199/1200/1440，SOURCE/structure/script 开头和结尾，错误修订/目标/锚点，不同 SOURCE、缺末端，以及 renderComments 后焦点已成为 BODY 的情况。fixture 执行实际定位入口和 helper，但桩替换了部分 reader、版本选择和评论渲染；因此它能验证关闭顺序、原始路由参数和焦点调用，不能独自证明完整重建下的草稿/焦点生命周期。最终 `../backend-investigation/ux007-comment-location-tests-reset-01/final-focused.log` 回读为 138/138 通过、失败/取消/跳过均 0、109.020084 ms；这是根执行五套聚焦回归的日志，本独审未重跑。该目录 `receipt.json` 只记录首次单文件 `node --test tests/comment_outside_click.test.cjs` 的命令与前后 SHA，不能写成最终五套统一回执；最终命令以根的真实工具记录为准，当前最终源码 SHA 单独保存在本独审 JSON。

最终语法调整源于旧三套导航 fixture 未提供 innerWidth：反向提前返回会把 undefined 错当作窄屏而触发缺少的面板/几何 mock。尝试在旧 fixture 补 1440 又暴露已有宽屏几何 mock 缺口，该临时改动已撤销；最终只采用正向 `<1200` 产品谓词，新四断点测试继续显式设置真实数值宽度。`navigation-run.log` 与 `navigation-rerun.log` 失败记录保留，不写成从未失败，也不把 mock 错误当成真实浏览器故障。最后对照只改变谓词写法，没有改既有导航断言来获得通过。

closePanel/setPanelOpen 不删除草稿存储、anchor、编辑 ID 或媒体节点。S1 真机记录补足正常存储下的实际输入回读；结构/剧本版本切换仍走原 remember/restore，准确版本选择未改。既有定位器会重建评论，localStorage 写失败导致仅存 DOM 的输入无法完整恢复属于已有风险，本次没有修复，不写成新增 closePanel 导致，也不记为已通过。

本次性能和页面耗时不在此项结论中。未对 production、嵌套弹窗、所有历史版本或 invalid anchor 重做浏览器验收；可按真实改动范围复用已通过且输入未变的证据。后续若继续改变这两个 JS 文件或定位契约，应核对实际差异后决定补验范围。
