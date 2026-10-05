# 候选界面实现与真实证据独立审查

本代理未实施产品改动，仅静态读取系统候选、审计主协调保存的真实浏览器记录并查看本地截图，没有发起浏览器、API或测试负载。当前结论：AO-UX-001 已测桌面场景遮挡消除且最终开合位置稳定；AO-UX-002 聚合筛选文案与准确版本卡片分工正确；新发现 AO-UX-003 的最窄修复静态通过，真实复验待补。不能将这些有限场景写成全部 61 项验收通过。

## 新增阻断回归

AO-UX-001已有遮挡/开合证据成立，但S2面板打开时“添加整体意见”首击因pointerdown关闭重排而丢失，已由真实文件确认，当前不能视为该体验项完全闭环。主协调拟改click捕获；独审赞同目标已确定后关闭的方向，并指出区域拖选pointerup新开草稿后click可能再关的风险、dialog和review-cue原有豁免需保留。详见`outside-click-reflow-review.md`；尚未假称修复后验收通过。

## 已验证效果及范围

| 变化 | 独立核对的证据 | 结果与边界 |
| --- | --- | --- |
| AO-UX-001：宽桌面故事三页顶层评论避让 | `browser/AO-UX-001-after.jpg`、`after-geometry.json` | 1440×900采编精修八原引用完整换成两行，最右995.796875 < 面板左1080；reader右1063，页面scrollWidth1440。原先258.40625px被覆盖的问题在该场景消除。目录变窄、长标题换行，截图仍可读，没有缩小正文或删除评论。 |
| 1200边界 | `AO-UX-001-1200.jpg`、`1200-geometry.json` | 引用两行最右770.828125/701.59375 < 面板左840；reader右823，scrollWidth1200。截图确认整句和相邻正文可读。 |
| 采编开合位置 | `AO-UX-001-final-cycles-1440.json` | 初始和3轮开合mark top498.625、readerTop186.859375、scrollTop48756完全相等。早期`open-close-cycles`首次下移33px是已返工前记录，未删除、未充作最终零漂移样本。 |
| 结构图像位置 | `AO-UX-001-structure-image-cycle.json`、`structure-image-open.jpg` | 第8稿空间关系照片与评论并排；开合前后9张图像矩形、reader矩形与scrollTop7454一致。这只证明评论开合位置，不证明图像放大往返；后者另发现AO-UX003。 |
| 剧本评论定位 | `S3-comment-locate-settled.jpg`、`S3-comment-fixed-button-cycles.json` | 剧本三第1集S002“腰间挂着庙门钥匙”已稳定出现在可视正文并与评论同时可读；可见固定按钮3轮开合body scroll450、mark top525.671875均相等。初始`locate-1440`几何取于平滑滚动未结束；旧`cycles-settled`使用屏外header按钮被工具自动滚动，不当作产品漂移。 |
| 原窄屏范围 | `AO-UX-001-1024-closed.jpg`、`390-regression.json`、`390-open.jpg` | 1024截图显示关闭面板后旧导航/阅读布局；390截图及开/关快照显示原覆盖面板仍可开关，关闭后scrollWidth390且正文存在。不宣称1024已测打开态或窄屏已实现同时看全文与评论。 |
| 草稿往返与取消 | `AO-UX-001-draft-keys-routes.json` | Enter产生换行；收起后和S1→S2→S1返回内容完全相同；输入框内Esc后编辑器消失、面板仍打开，字段与快照一致。`hiddenAfterEsc=false`且取值时点不明，不能证明输入框外Esc收起，保留待补验。未测Command+Enter、中文组合和重复提交。 |
| AO-UX-002：历史聚合生成结果 | `AO-UX-002-history-filter.txt`、`old-version.txt`、`old-version-original.jpg` | 新筛选“生成结果（含历史版本）”中“有结果298”选中；阿禾当前素材版本2仍未生成。切到素材版本1出现单候选及1086×1448原件，放大截图中头至鞋完整。实体版本仍为2，未将实体版本与素材版本混同。无API/数据过滤变更。 |

所有新增界面证据为功能验证，没有把开合循环、截图或单次图片打开记作重复性能测量；页面性能仍以独立的`page-performance-candidate1.md/.json`为准。

## 静态契约与独立返工

AO-UX-001 CSS仅在>=1200、故事采编/结构/剧本及body直接子评论面板时预留360px；导航200px、目录180px并减少留白。面板搬入素材dialog后不满足条件，未增加另一个要同步的状态class。API、准确锚点、正文和草稿存储未改变。

初审发现 R-UX001-01：恢复绝对字符top时，窄栏导致标题换行增高，可将原字符放到新可读边界之上。主协调接受并改为相对可读区top，恢复时重新读取reader边界和结构sticky标题下沿；无可见段落时保留图像纵向比例点。首轮真实测试再出现33px漂移后，主协调优先锚定可见已选原文，普通阅读选择完全可见非空白字符。临时Range不改变Selection或评论偏移。最终上述开合证据覆盖同一采编引用、结构图像和一个剧本评论；其他Unicode、跨段拖选及页首尾钳制不能因此补为通过。

AO-UX-002 `includesHistory`仅传给素材管理聚合列表及筛选外准确链接列表；准确版本小卡继续显示所选版已生成/未生成。`generated`字段含义、URL值和默认当前版选择未改变。历史规则明确“任一版本有原件”与“当前版有结果”分开，原问题是展示歧义，并非筛选逻辑或历史数据错误。

AO-UX-003在4类实际弹窗入口创建时标记`data-review-dialog-trigger`，独审确认没有改全局小卡、空白处关闭器、Esc或退出时无条件打开评论。S2照片路径已真实复现，其他3类初始为静态同根因，真实复验仍待主协调记录。详见`image-dialog-panel-review.md`。

## 文档与旧成果归属

README、production-breakdown及素材规则中的旧三栏、场顶部共用素材和旧生成状态用语已按当前代码修正；条件Schema6/旧实例Schema5及兼容1—5规则保留。comment-checklist限定桌面故事三页和顶层评论，没有宣称全站均避让。task9已完成的导航、完整素材方案版本和逐镜布局仍为本轮基线，不计作本轮新实现。文档纠偏登记DOC-001。

## 当前未验或待补

1. AO-UX003四类入口真实开关、鼠标与键盘、普通外点仍收起、圈选不误放大、嵌套面板与准确上下文恢复。
2. 输入框外Esc的独立前后焦点、面板状态及草稿快照；不能凭字段名倒推原始false含义。
3. 真实Unicode跨段拖选、提交/编辑/关闭重开、采纳/采用、导出恢复、配置保存与音视频操作按矩阵保持原状态，未在本轮截图中发生的动作不填通过。
4. 宽度与场景结论只覆盖实际样本；没有以API/静态验证替代页面操作。

证据文件身份及本次覆盖更新见`candidate-ui-evidence-audit.json`，初始基线和失败记录分别保留于基线审计。以下源码哈希说明本次复读的候选字节，不代表根代理已冻结最终候选。

| 文件 | SHA-256 |
| --- | --- |
| `review_desk/static/app.js` | `9a3e2394f62b605cae200560944ad2f4036c7e74490464177b99fb68c3811967` |
| `review_desk/static/navigation.css` | `f62a96150aa21748b7b83137f1cb329b142e3f1925db725ad22c8f19ff4b5b7b` |
| `review_desk/static/structure.js` | `477c1620990e0fbd163e9b8c873a5017e31cc981dbac14b0bf34e442d4238dc5` |
| `review_desk/static/production-breakdown.js` | `4b7f06ca0588fe323003c9fed737f32384e17f830669dcb74c69670cd97d3d6d` |
| `review_desk/static/entity-relations.js` | `7bc2477821dd603715dccd33ed3f05684be4fd9189b99fce8eed0d13d1fe7c3b` |
| `review_desk/static/unified-cards.js` | `b57ca50498379d0907e427f62dee97d93eee0b7f46eb106ba9ca06e4dac16c03` |
| `docs/comment-checklist.md` | `c42423a4ba8d47c1f07de57bafec6423b39bc40f4d2ad73119c0689cc3962c87` |
| `docs/materials-and-relationships.md` | `923f07db04c047aba5e268f0c845cdce80acc2177ca0496791aa6eb5aed09c08` |
| `README.md` | `808af2a2c442d618159c4c992b95da7dabc6c5fcd078eb8a972a71c71f2743be` |
