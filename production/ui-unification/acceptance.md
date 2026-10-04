# UI 统一候选验收矩阵

独立需求复审已逐项对照原始十项说明、Q1–Q7 及后续 ultra 调整。当前原 36 项中 **35 项证据充分、1 项（C.5）待最终确认与正式交付**；U.1–U.4 的执行与独立复核要求已核对。这里的通过仅表示表内样本和证据达到该检查标准，不代表用户视觉接受、作品质量接受或正式发布。

浏览器操作由主代理完成。需求审查者未操作浏览器，已实际查看关键截图、核对操作记录与当前代码，独立复算数据完整性，并维护自己的前后端回归。实施者与审查者分离；技术实体由审查者按授权创建和修订，真实采纳及页面读取仍由主代理执行。

依据：[完整任务](../../planning/system-ui-unification-task.md)。证据：[浏览器记录](evidence/browser-review.md)、[全套自动结果](evidence/automated-checks.json)、[数据回读](evidence/data-integrity.json)、[独立需求报告](evidence/requirements-review.md)、[独立兼容报告](evidence/compatibility-review.md)、[委派记录](delegation.md)、[正式应用说明](operations.md)。系统代码和测试引用以下均以系统仓库为基准。

Q1 对应 7.3；Q2 对应 6.5/10.1；Q3 对应 6.3–6.5；Q4 对应 10.4；Q5 对应 5.7；Q6 已由明确 ultra 调整替代 max，见 U.1–U.4；Q7 对应 C.5。原文“场卡包裹所有场”按有效澄清落实为当前场包裹全部镜头；选中不隐藏其他镜行。

| 编号 | 检查及独立结论 | 状态 | 可定位证据 |
|---|---|---|---|
| 1.1 | **采编作为视觉基准**。采编截图记录左标题、多级目录、正文标题与纸色正文；结构、剧本和制作页采用相同深色标题、金色选中和浅色阅读面。 | 通过（隔离候选） | [desktop-source](evidence/screenshots/desktop-source.jpg)；[desktop-structure](evidence/screenshots/desktop-structure.jpg) |
| 1.2 | **大标题到顶后的阅读滚动**。桌面采编正文滚动664而外层0，结构外层129后正文7423→7963。窄屏修后外层555及标题top122.59保持，正文内部96→940；实际查看更新截图并核对仅max-width700的固定阅读区与内部overflow样式。 | 通过（隔离候选） | [narrow-source](evidence/screenshots/narrow-source.jpg)；[desktop-source](evidence/screenshots/desktop-source.jpg)；[滚动记录](evidence/browser-review.md) |
| 2.1 | **结构页版本与目录风格**。结构第十稿六章目录、选中章节与正文一致；第九稿区域评论后切十稿，本稿评论不串入。 | 通过（隔离候选） | [desktop-structure](evidence/screenshots/desktop-structure.jpg)；[structure-modal-draft](evidence/screenshots/structure-modal-draft.jpg) |
| 2.2 | **结构页版本常驻**。桌面版本栏保持y=70，结构草稿经弹窗关闭与切章后保留。窄屏遮挡及当前版本不可见经独立截图发现、root现场确认、导航代理补修；修后390视口版本栏top122，第十稿可见可点，更新截图已实际复核。 | 通过（隔离候选） | [desktop-structure](evidence/screenshots/desktop-structure.jpg)；[narrow-structure](evidence/screenshots/narrow-structure.jpg) |
| 3.1 | **剧本菜单保留与视觉统一**。桌面版本三→四、第2集与窄屏S04切换准确，版本→集→概览→场结构保留，正文显示02-02还回去的米；评论准确版本有自动回归。 | 通过（隔离候选） | [desktop-screenplay](evidence/screenshots/desktop-screenplay.jpg)；[narrow-screenplay](evidence/screenshots/narrow-screenplay.jpg) |
| 4.1 | **制作设定三个子页页签**。制作拆解、实体、素材三页签逐一点击及刷新，主导航保持制作设定；准确素材直接链接仍选中素材页。 | 通过（隔离候选） | [desktop-breakdown](evidence/screenshots/desktop-breakdown.jpg)；[desktop-material-filters](evidence/screenshots/desktop-material-filters.jpg) |
| 5.1 | **素材小卡**。未生成图像占位、已生成真实图片、声音和视频识别均有实页样本，状态未把技术样本或方案标为真实交付。 | 通过（隔离候选） | [desktop-breakdown](evidence/screenshots/desktop-breakdown.jpg)；[exact-historical-shot](evidence/screenshots/exact-historical-shot.jpg) |
| 5.2 | **实体小卡与素材数量**。实体小卡显示类型及图像/声音需求数；版本、候选及元数据修订不增加需求数，subject关联的无需求历史原件仍计入并可读取。 | 通过（隔离候选） | [desktop-entity-history](evidence/screenshots/desktop-entity-history.jpg)；[wide-entity-two-columns](evidence/screenshots/wide-entity-two-columns.jpg) |
| 5.3 | **大卡左侧信息与右侧切换**。阿蘅基础青衣与捞书后湿衣袖切换后状态与右侧需求同步，基础信息和关系保留；跨分组、跨实体和迟到请求有独立断言。 | 通过（隔离候选） | [desktop-entity-history](evidence/screenshots/desktop-entity-history.jpg)；[wide-entity-two-columns](evidence/screenshots/wide-entity-two-columns.jpg) |
| 5.4 | **大卡媒体、版本、候选与生成信息**。真实图片位于右侧顶部，原件→receipt→原件切换可读；技术视频两版各两候选切换时文件、实际CALL、提示词和采用范围同步。 | 通过（隔离候选） | [desktop-entity-history](evidence/screenshots/desktop-entity-history.jpg)；[exact-historical-candidate](evidence/screenshots/exact-historical-candidate.jpg) |
| 5.5 | **大卡可评论内容**。正文圈选、图像区域、音视频范围与共同评论面板可用；真实提交读回准确CALL/原件/修订，跨版评论和草稿不串入。 | 通过（隔离候选） | [prompt-text-comment](evidence/screenshots/prompt-text-comment.jpg)；[image-region-comment](evidence/screenshots/image-region-comment.jpg) |
| 5.6 | **素材 ID 与无实体归属**。素材准确旧候选保持版本1；实体原件还原实体，剧/集/场/镜挂载显示位置。历史CALL、subject-only及actual-call归属、第41项定位和筛选外目标由独立回归补齐。 | 通过（隔离候选） | [exact-historical-candidate](evidence/screenshots/exact-historical-candidate.jpg)；[modal-image-region-comment](evidence/screenshots/modal-image-region-comment.jpg) |
| 5.7 | **实体 ID 默认素材**。实体入口阿蘅默认基础青衣整体图像当前版2且显示未生成；采用优先、否则最新、没有图像再选其他媒体由共用选择器及独立断言验证，不借用旧版。 | 通过（隔离候选） | [wide-entity-two-columns](evidence/screenshots/wide-entity-two-columns.jpg)；[desktop-entity-history](evidence/screenshots/desktop-entity-history.jpg) |
| 5.8 | **大卡正文与弹窗一致**。同一挑柴老汉原件22310fec…9a86在弹窗与正文均为版本1、同文件6f9d79c6…e432及同区域评论；媒体关闭停止、共用renderer及外层草稿恢复有页面记录和独立回归。 | 通过（隔离候选） | [modal-image-region-comment](evidence/screenshots/modal-image-region-comment.jpg)；[same-exact-card-embedded](evidence/screenshots/same-exact-card-embedded.jpg) |
| 6.1 | **制作拆解顶部选集**。集导航采用同形式卡片；第2集→第1集后场列表、正文与素材回到本集。 | 通过（隔离候选） | [desktop-breakdown](evidence/screenshots/desktop-breakdown.jpg)；[desktop-screenplay](evidence/screenshots/desktop-screenplay.jpg) |
| 6.2 | **左侧选场与场信息**。场标题和场地/日夜信息在正文顶部，选场后列全部镜头；快速第2场→第1场后无前场残留。 | 通过（隔离候选） | [desktop-breakdown](evidence/screenshots/desktop-breakdown.jpg)；[exact-historical-shot](evidence/screenshots/exact-historical-shot.jpg) |
| 6.3 | **选择整场与单镜**。实际边缘点击(554,430)选整场；单镜高亮只包该镜，场内16镜保留；跨提示词链接圈选成功未误切选择。 | 通过（隔离候选） | [scene-level-selection](evidence/screenshots/scene-level-selection.jpg)；[desktop-shot-production](evidence/screenshots/desktop-shot-production.jpg) |
| 6.4 | **按镜分行、镜内左右排列**。桌面逐镜行内左正文右素材，选择场/镜不隐藏其他镜行；窄屏对应镜内上下排列且整场保留。 | 通过（隔离候选） | [desktop-shot-production](evidence/screenshots/desktop-shot-production.jpg)；[exact-historical-shot](evidence/screenshots/exact-historical-shot.jpg) |
| 6.5 | **层级筛选与共用素材**。四层级默认全选；取消镜后仅隐藏镜素材，取消场+镜后仍有16镜并只剩本集视频。共用素材按层级集中一次，明确适用不等于实际采用。 | 通过（隔离候选） | [desktop-breakdown](evidence/screenshots/desktop-breakdown.jpg)；[scene-level-selection](evidence/screenshots/scene-level-selection.jpg) |
| 6.6 | **素材小卡打开弹窗**。素材小卡在本页打开共用大卡，关闭按钮/Esc/浏览器返回均实操；外层集场镜、URL、阅读位置、焦点和提示词编辑草稿保持。 | 通过（隔离候选） | [modal-image-region-comment](evidence/screenshots/modal-image-region-comment.jpg)；[prompt-text-comment](evidence/screenshots/prompt-text-comment.jpg) |
| 6.7 | **被替代的按钮移除**。新页使用层级checkbox和归属分组；旧全剧共用、本集共用、全剧风格参考按钮不再存在，原风格和场调度需求通过小卡可读。 | 通过（隔离候选） | [desktop-breakdown](evidence/screenshots/desktop-breakdown.jpg)；[scene-level-selection](evidence/screenshots/scene-level-selection.jpg) |
| 7.1 | **实体详情嵌入大卡**。实体页右侧直接渲染共同实体/素材大卡，基础信息、状态、素材与右详情共用；与弹窗使用同一renderUnifiedCard。 | 通过（隔离候选） | [desktop-entity-history](evidence/screenshots/desktop-entity-history.jpg)；[wide-entity-two-columns](evidence/screenshots/wide-entity-two-columns.jpg) |
| 7.2 | **实体分类与列表宽度**。左侧按类型列卡；1920宽度实际两列各158像素、右正文1216像素；390下列表260高、卡364宽且无横溢。 | 通过（隔离候选） | [wide-entity-two-columns](evidence/screenshots/wide-entity-two-columns.jpg)；[narrow-entities](evidence/screenshots/narrow-entities.jpg) |
| 7.3 | **采纳状态筛选**。真实采纳→取消→清空→再次采纳链完成；技术实体UI采纳后由审查者合法修改描述为v2，旧决策保留，页面已采纳0且结果0，过滤迟到和准确撤回历史分开受保护。 | 通过（隔离候选） | [acceptance-after-content-revision](evidence/screenshots/acceptance-after-content-revision.jpg)；[narrow-entities](evidence/screenshots/narrow-entities.jpg) |
| 8.1 | **素材筛选样式与计数**。媒体/生成状态/集/场筛选平铺有计数；视频297+已生成=0，清除恢复2071；窄屏搜索仍有各类别，计数按需求并保留其他筛选。 | 通过（隔离候选） | [desktop-material-filters](evidence/screenshots/desktop-material-filters.jpg)；[narrow-material-filters](evidence/screenshots/narrow-material-filters.jpg) |
| 8.2 | **素材列表与正文大卡**。分类小卡与嵌入大卡共用交互；准确旧候选定位所属需求所在页并保留版本，普通翻页与筛选外零结果场景有前后端及HTTP独立回归。 | 通过（隔离候选） | [exact-historical-candidate](evidence/screenshots/exact-historical-candidate.jpg)；[same-exact-card-embedded](evidence/screenshots/same-exact-card-embedded.jpg) |
| 9.1 | **全剧制作子页页签**。镜头制作与组合历史页签同故事形式；主代理补验history直接URL→刷新→shots→Back history→Forward shots，三次选中态与页面一致。 | 通过（隔离候选） | [desktop-shot-production](evidence/screenshots/desktop-shot-production.jpg)；[补验操作记录](evidence/browser-review.md) |
| 10.1 | **镜头制作导航与逐镜布局**。镜头制作复用顶部集、左场、整场逐镜布局及层级过滤；快速切集场和准确旧镜还原均有页面记录。 | 通过（隔离候选） | [desktop-shot-production](evidence/screenshots/desktop-shot-production.jpg)；[exact-historical-shot](evidence/screenshots/exact-historical-shot.jpg) |
| 10.2 | **提示词与准确参考输入**。提示词上方和内联图片1打开同一准确引用；跨链接拖选提交绑定真实CALL ce1da328…a94b，字符[39,56)与原文quote相等，独立只读回算通过。 | 通过（隔离候选） | [prompt-text-comment](evidence/screenshots/prompt-text-comment.jpg) |
| 10.3 | **视频素材与挂载位置**。所有镜头制作素材小卡均为视频；技术集/场视频各显示一次、镜视频在对应镜行，可用共用版本候选切换与层级筛选。 | 通过（隔离候选） | [scene-level-selection](evidence/screenshots/scene-level-selection.jpg)；[exact-historical-candidate](evidence/screenshots/exact-historical-candidate.jpg) |
| 10.4 | **围绕视频生成的审阅**。未生成镜显示计划和真实缺项；已有候选显示真实调用、准确输入与提示词；旧版/空版不由当前方案补历史；页面无生成提交或进度操作。 | 通过（隔离候选） | [desktop-shot-production](evidence/screenshots/desktop-shot-production.jpg)；[prompt-text-comment](evidence/screenshots/prompt-text-comment.jpg) |
| C.1 | **全部评论交互回归**。新增、定位、编辑、关闭/重开、草稿、Esc/⌘Enter、文本/图像/音视频圈选均有实际操作，准确评论记录与同素材跨入口回读对应。 | 通过（隔离候选） | [prompt-text-comment](evidence/screenshots/prompt-text-comment.jpg)；[image-region-comment](evidence/screenshots/image-region-comment.jpg) |
| C.2 | **导航、返回与切换竞态**。实页快速集场、弹窗关闭与返回保持上下文；独立异步用例覆盖实体版本乱序、过滤清空、失效弹窗、文件/版本草稿及撤回实体准确历史，原断言保留。 | 通过（隔离候选） | [structure-modal-draft](evidence/screenshots/structure-modal-draft.jpg)；[exact-historical-candidate](evidence/screenshots/exact-historical-candidate.jpg) |
| C.3 | **数据与历史保护**。独立只读比较技术夹具基线与当前13历史表，原记录无缺失/改写；1247原文件SHA均一致，准确CALL/评论/采纳历史保留；本轮不改持久Schema/导出格式，既有恢复回归已执行。 | 通过（隔离候选） | [exact-historical-shot](evidence/screenshots/exact-historical-shot.jpg)；[exact-historical-candidate](evidence/screenshots/exact-historical-candidate.jpg)；[数据回读](evidence/data-integrity.json) |
| C.4 | **验证环境与证据**。审查者实际查看26张关键截图；浏览器由root独占，含1440×900、390×844、1920×1080。29项独立需求测试、全套456Node/185Python日志及49源码哈希已核对；两处窄屏补修另有真实操作和更新截图，不用自动测试代替。 | 通过（隔离候选） | [desktop-source](evidence/screenshots/desktop-source.jpg)；[narrow-source](evidence/screenshots/narrow-source.jpg)；[自动结果](evidence/automated-checks.json) |
| C.5 | **候选确认与正式交付**。系统候选已固定dab027e9725d36828d3ee77098db355eb94d5033，正式应用说明和双仓边界已审阅；故事最终提交待主代理固定，最终确认、3000应用、集成推送及正式重点回读尚未执行，不预签。 | 待最终确认／正式交付 | [应用说明](operations.md) |
| U.1 | **实际委派与边界**。实际采用root+navigation+requirements+compatibility；root负责共享状态/浏览器/正式资源，授权限定文件并在发现问题后协调修复；本审查者仅测试、报告及获批技术实体夹具写入。 | 通过（隔离候选） | [委派](delegation.md) |
| U.2 | **独立需求核对**。本矩阵逐条保留原36标准及U4要求；核对原文十项、Q1–Q7与ultra替代max，直接查看截图发现窄屏版本栏和采编内层滚动缺口，均经root实页复验与更新截图闭合；未自签生产实现。 | 通过（隔离候选） | [逐项机器记录](evidence/requirements-review.json) |
| U.3 | **独立兼容性复核**。兼容性审查者独立于root及导航实施者，保留版本/候选/评论/历史/采纳/竞态失败断言并复验；最新限定67项和32项专项、各轮hash分开记录，不把旧全套结果冒充最终。 | 通过（隔离候选） | [兼容复核](evidence/compatibility-review.md) |
| U.4 | **收益与协调成本**。委派文档与两份审查报告记录有效发现和归属、并行实施、共享接口传递、浏览器等待、夹具维护和返工；总耗时/token/费用UNKNOWN，无max对照、不报告固定改善比例。 | 通过（隔离候选） | [贡献与成本](delegation.md) |

逐项代码入口、自动测试文件和全部截图映射保存在 [机器可读复核](evidence/requirements-review.json)。自动检查不能单独证明真实布局、鼠标键盘或媒体行为；正文记录和截图共同构成当前样本的页面证据。

系统候选为 `dab027e9725d36828d3ee77098db355eb94d5033`；故事最终提交由主代理在本报告完成后固定，用户最终确认尚未取得。C.5 的批准、串行应用、双仓推送及正式重点回读必须由后续准确回执完成，本矩阵不预签。
