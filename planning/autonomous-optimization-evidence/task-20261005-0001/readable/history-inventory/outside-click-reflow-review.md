# AO-UX-001：外点关闭重排吞掉首次点击的独审

主协调真实验证发现：S2评论面板打开时点击“添加整体意见”，pointerdown立即收起评论并重排布局，首击没有打开编辑器；面板关闭后第二击才成功。`browser/AO-UX-001-outside-reflow-click-failure.json`记录首次后editor=false/panelHidden=true，第二次后editor=true/panelHidden=false，准确结构修订URL保持不变。这是本轮避让布局与原有pointerdown关闭时机组合产生的实际回归，不能因此前开合位置稳定而忽略。

本代理只读核对代码和上述文件，未执行浏览器或测试、未修改产品。

## 对最小方案的判断

将文档级外点关闭由pointerdown冒泡移到click捕获，在click目标已经确定后收起面板，方向正确。当前`closePanel → setPanelOpen(false)`只切hidden、更新两个触发器的aria-expanded并恢复阅读位置，不渲染/移除目标节点、不改变评论目标、草稿或Selection。它不会像pointerdown一样在按下到松开之间移动可点击目标；“添加整体意见”的目标onclick随后仍可调用startDraft。

不能改为click冒泡：目标onclick可能先打开草稿，随后文档冒泡处理又将其关闭。捕获是为了在目标业务动作之前完成外点语义，不是为了提前阻断目标事件；不应添加preventDefault或stopPropagation。

必须显式豁免`target.closest('dialog')`，否则捕获处理早于dialog原有冒泡阻止，会把旧有弹窗保护撤掉。既有`.material-reference,[data-review-dialog-trigger]`、panel.contains以及两个全局评论按钮的例外继续保留。

## 需处理或实际验证的风险

1. **区域拖选的pointerup先开草稿，之后仍可能收到click。** `structure.js`在文档pointerup捕获阶段调用startDraft，先打开评论并重绘reader；新的click捕获若随后发生，可能立即收起刚开的区域草稿。拖选后的click是否到达旧元素、共同祖先或重绘节点取决于实际事件路径，本代理没有冒充真实复现，但这是明确存在于当前代码顺序中的回归风险。移动到click并不自动排除拖选结束click。可用既有`commentAction`：记录对应pointerdown时的动作序号，click发生时若该手势已经通过pointerup新开草稿则不关闭；或采用等价、作用域清楚的完成手势豁免。不要用无界时间窗阻止之后真正的外点。
2. **块评论按钮原先通过pointerdown stopPropagation保护。** `.review-cue`目前在自身pointerdown阻泡，onclick又打开块评论。新捕获会先关闭再打开，虽然click不应再丢失，但多做一次布局改变。建议将实际`.review-cue`显式豁免，保留旧语义；不泛化为全部按钮。
3. **文字拖选和浮动“评论所选”入口。** `watchTextSelection`在pointerdown清空pending、pointerup后requestAnimationFrame重新计算；浮动按钮通过mousedown.preventDefault保留Selection。关闭发生在click后段可能重排选区几何，但逻辑Range不应改变，需真实拖选→点击浮动入口验证准确引用，不能只用直接调用onclick测试。
4. **新增键盘click路径。** click捕获也覆盖键盘激活和程序click，原pointerdown不覆盖这些。目标onclick仍应正常工作；至少检查Enter/空格打开整体意见和已有弹窗入口，普通外点依旧收起并保留草稿。

## 最窄验收范围

S2评论已开时“添加整体意见”首次即出现编辑器；“评论整图”及块评论入口首次生效；文本拖选和区域拖选完成后编辑器保持打开且锚点准确；普通空白外点收起、重开草稿不丢；dialog内部点击、Esc/关闭返回及4类明确弹窗入口不连带改变评论状态。选择具有真实几何重排的1440或1200场景，补一窄屏检查既有行为。所有结果需新加载候选后的真实输入和前后状态；此前的零漂移循环继续有效，但覆盖的是不同动作。
