# 关系图与 Prompt 浮卡：只读调查

本记录用于定义任务，未修改产品、正式库或受管文件，未启动服务或恢复 Review。图和 Prompt 的真实操作证据由根会话提供；这里的源码函数重放不是浏览器验收。

## 当前依据与任务归属

2026-10-11 16:11 前后读取：desk 主干及故事实例引用为 `b5d2d821a869767316c32da8cbf1e93c18e6d4aa`；正式 3000 的只读索引返回 ASH001 14 节点／10 边、ASH002 11／7、ASH006 10／9。准确节点修订和边见同目录 `graph-samples.json`，避免把当前快照当作执行时固定开发基线。

账本中 0003 仍 running，0004 completed。0003 的 `planning/production-reading-followup-task.md:10` 和 `production/shot-material-navigation/VERIFICATION.md:10` 明确保留 Prompt 的关系摘要；本轮取消该摘要是新的产品决定。0004 已交付范围聚焦，原交互是单击开卡；本轮单双击分工为新要求，连线可辨认性则承接当前残留。执行时吸收最新两仓主干，正式发布共享窗口按序；无需为了这项前端调整重做旧内容迁移。

## 连线重叠的具体原因

以下路径均相对通用审阅台仓库。

- `review_desk/static/entity-relations.js:166`，`managementGraphLayout`：有方向关系已经按有向图和强连通分组计算层次；普通 related 关系按业务编号排序后 `i % 3` 分列，连接结构并未决定同组中的相对位置。三个正式样例所有边都为 related。改进无向图时应表达连通和邻接关系，不根据故事动作编造依赖箭头。
- 同文件 `:190`，`managementEdgeGeometry`：所有边独立选择节点侧边中点作为端口；相同侧的边共用端口。路由避让的是节点和摘要矩形，先画出的边不进入避让或间距计算。路径仅由 SVG M/L 组成。
- 同文件 `:210`，`managementOrthogonalRoute`：共享矩形边界可见网格，按曼哈顿最短距离路由；没有其他边的占用、独立通道或分离约束。因此同端点之外也会共享长路径。仅将拐角变圆不能消除这种共线。
- 同文件 `:225`，`renderManagementEntityGraph`：节点调用 `entitySmallCard` 后未设置图内选择事件。`management-cards.js:143` 的小卡单击直接打开准确大卡。现有图只有点击关系短摘要时，选择一条边及其两个端点；没有以节点为中心的直连高亮。
- 旧的 `renderEntityRelationGraph` 另有曲线和单击选择／双击开卡，不是本次管理图使用的函数。可以参考其交互，不应据此声称当前管理图已满足要求，也不应把旧的中心星形布局整体套入当前图。

`source-geometry-witness.json` 用当前 API 节点、边和当前源码函数重放初始 230×120 卡片几何。ASH001 的“抄写并持有”与“听曲并发现省段”路径共同经过 (155,178)→(262,178)，说明共线不只发生在不可避免的同一端点。该文件仅保留少量重叠片段；片段计数不是关系数量，真实浏览器会根据卡片实际高度重新布局，仍须看最终画面。

## 可直接验证的真实关系

- ASH001 单击 `entity-a-heng`／EN002 阿蘅：仅自身、EN112 阿蘅歌本、EN034 挑柴老汉、EN099 阿蘅米袋、EN023 米铺听客，以及连接中心的 4 条边高亮。EN050 挑柴扁担、EN103 压页河石、EN047 垫歌本竹篮是两跳，不能自动加入。
- 再单击 `entity-songbook`／EN112：自身与 EN002、EN103、EN047、对应 3 条边；不沿阿蘅继续扩展。
- `av-e01-a01-s01`／ASH001、`entity-boat-song`／EN046 三道滩是该图有效孤立节点。仅突出自身，不补造“涉及”边。
- 独立边样例：`relation-0429cc4b0086cb4478dced219bcae9fe` 阿蘅—歌本；`relation-265bf8bc23a38e19b6700e7137ccbaf9` 阿蘅—老汉；`relation-75561fcfe73b3f03b5543591329b7b3c` 河石—歌本；`relation-b379382194165dba645b7290eab0e67e` 竹篮—歌本。
- 正式样例无法覆盖真实有向、多父和环；沿已有隔离夹具验证，不在正式数据补方向。`tests/entity_graph_layout.test.cjs` 已有多父、反向、环、无向、孤立和密集关系场景；目前强制每段横平竖直，应随曲线路由修改其几何断言，并补边之间共享路径／间距验证。自动检查仍不替代视觉追线。

## Prompt 浮卡可与准确打开独立处理

`review_desk/static/production-breakdown.js:281` 的 `renderLinkedPrompt` 统一渲染 Prompt 引用。`:308` 的 `onclick` 沿准确 ref 打开 `openShotReference` 或 `openMaterialReference`；`:309` 独立调用 `bindRelationSummary`，这就是取消浮卡的准确边界。共用入口包括同文件 `:562` 的镜头方案，以及 `material-review.js:220` 的真实调用 Prompt、`:241` 的当前生成方案。

`entity-relations.js:41` 的绑定同时处理 240 ms 鼠标驻留、键盘焦点和 ArrowDown。验收须覆盖三种触发，不能只删 pointerenter。也要避免把同一摘要挪到 title 或其他提示。保留准确修订／候选／组成／范围定位、链接文字和映射、选择文本评论、返回位置及草稿。

这个绑定函数在旧图及其他关系入口仍有调用；本次应消除 Prompt 上的绑定，不应仅因同名函数存在就清空整个关系功能或关系数据。根会话已实测 ASH003 首帧 M2980 的 ArrowDown 触发浮卡，并点击准确进入 M2979，适合作为正式前后验收主例。

## 对任务正文的复核

已读根会话编写的任务正文，原文现保存为 [任务正文](../relation-interaction-task.md)。其范围、0003／0004 归属、正式验收终点、曲线分离、单击直连／双击开卡和 Prompt 精准点击保护均与当前源码、API 及根实操一致，未发现阻止发布的事实或验收缺口。保护原有图摘要点击和关系意见即可，不要求新增另一套关系编辑入口；只根据真实方向表达业务层级。
