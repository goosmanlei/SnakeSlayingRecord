# 导航、共用卡片与素材模型验收

本表对应[完整任务说明](../../planning/ui-material-model-task.md)的33项。“隔离通过”表示候选实现及隔离输入已验证；正式发布与验收单列为F02，待用户确认后执行。真实页面由主代理独占Chrome，隔离数据不作为作品接受或正式运行证据。

| 编号 | 核对内容 | 当前结果 | 证据 |
|---|---|---|---|
| N01 | 五页全部子页进入同一固定顶栏，无旧位置重复入口，样式／选中态／键盘／窄屏一致 | 隔离通过 | [五页、三种宽度及固定顶栏](evidence/browser-review.md)；[页签和键盘回归](evidence/navigation.md) |
| N02 | 链接、刷新、前进后退和切页保持准确子页、位置、既有草稿与未提交配置 | 隔离通过 | [真实后退／前进、刷新、原文与配置草稿](evidence/browser-review.md)；真实路由、迟到保存及状态保持自动检查 |
| N03 | 筛选、标题、来源及系统描述统一 E／S／SH，编号和链接不变，原文不被批量替换 | 隔离通过 | [准确显示范围](evidence/navigation.md)；[历史列表及逐镜截图](evidence/browser-review.md)；原payload逐字节核对见D07 |
| N04 | 五页及弹窗控件对照完成，剧情依据、关系版本及素材选择风格统一 | 隔离通过 | [实体／关系版本实切、五页与弹窗](evidence/browser-review.md)；同一版本控件及剧情依据组件 |
| P01 | 每镜独立行、左右明显区隔且归属对齐，窄屏仍按每镜阅读 | 隔离通过 | [1440桌面](evidence/breakdown-desktop.jpg)、[1920宽屏](evidence/shot-production-wide.jpg)、[390窄屏](evidence/shot-production-narrow.jpg) |
| P02 | 场标题、说明、依据与筛选滚动常驻且无遮挡，按钮多选默认全选，无 checkbox 外观 | 隔离通过 | [真实滚动与几何测量](evidence/browser-review.md)；[滚动场头](evidence/shot-production-scrolled.jpg) |
| P03 | 顶部无剧／集／场素材列表及预留空白，上级归属不自动扩散到各镜 | 隔离通过 | [14镜实页与零场顶列表](evidence/browser-review.md)；ui_projection仅接收明确需求／原件 |
| P04 | 镜头明确需求、计划参考、实际输入／采用准确显示，镜内去重、归属多选及空选正确 | 隔离通过 | [全选、排除状态、全部取消](evidence/browser-review.md)；准确输入投影、镜内去重及归属自动检查 |
| P05 | 镜头制作右侧仅视频，左侧其他参考仍可准确打开，制作拆解支持相关其他媒体 | 隔离通过 | [镜头制作14行右侧仅视频、左侧准确图音输入](evidence/browser-review.md) |
| P06 | 正文场镜无点击或键盘选中态，场导航、旧链接定位及评论继续有效 | 隔离通过 | [正文无选中属性、场导航](evidence/browser-review.md)；[旧镜链接切场与声音原文锚点](evidence/navigation.md) |
| C01 | 大卡页内／弹窗等宽，窄屏顺序合理；实体四区与状态素材区清楚分隔 | 隔离通过 | [等宽大卡及四区](evidence/entity-relations-desktop.jpg)、[三层弹窗](evidence/entity-three-layer-migrated.jpg)、[窄屏弹窗](evidence/entity-dialog-narrow.jpg) |
| C02 | 关系图节点、连线、文字及底部完整，切版本和变尺寸后仍可读 | 隔离通过 | [关系历史版本实切](evidence/browser-review.md)；[窄屏最后节点完整](evidence/entity-relations-narrow-bottom.jpg) |
| C03 | 至少三层实体大卡打开并逐层关闭，各层上下文和草稿不串用，焦点恢复、关闭媒体停止 | 隔离通过 | [李寄→阿蘅→孙六→李诞、逐层关闭与草稿／焦点／暂停](evidence/browser-review.md)；父层迟到版本独立检查 |
| C04 | 状态列表明显紧凑，同容器可呈现更多条目，完整信息在选定状态区可读 | 隔离通过 | [13状态实际逐个切换](evidence/browser-review.md)；[选定状态详细信息](evidence/entity-relations-desktop.jpg) |
| C05 | 全部列表采用共用单列紧凑卡，缩略图真实、缺图图标清楚、长名称可访问 | 隔离通过 | [60px小卡、真实缩略图与类型图标](evidence/browser-review.md)；[历史列表](evidence/history-small-cards.jpg)；视频预览独立回归 |
| C06 | 独立需求计数不重复累计版本、候选、文件与多状态关联，合并后的数量有对应证据 | 隔离通过 | [李寄图像15／声音1与13状态共用](evidence/browser-review.md)；[独立身份与计数核对](evidence/independent-review.md) |
| C07 | 未生成、单／多版本、单／多候选、多个媒体组成及快速切换／刷新／旧链接均正确 | 隔离通过 | [未生成v3不借v2结果、准确刷新、候选和组成切换](evidence/browser-review.md)；非故事视频夹具覆盖双候选 |
| C08 | 无 original · original 等内部名称，无已生成素材“查看原方案”及无效说明，必要定义只准确显示一次 | 隔离通过 | [版本2一次要求／实际内容、原件／预览名称](evidence/browser-review.md)；[旧跨段评论兼容](evidence/independent-review.md) |
| C09 | 文字、图像、音视频评论的新增／定位／编辑／关闭重开／草稿／快捷键回归；采纳取消重采纳与准确采用保留 | 隔离通过 | [文字、图像、音视频完整操作与采纳取消重采纳、准确采用](evidence/browser-review.md)；真实草稿键及评论成员资格独立回归 |
| D01 | 实体→状态→素材→版本→候选成立，多状态显式共享，实质不同要求不误合并 | 隔离通过 | [数据契约](data-contract.md)；[不同实质要求解除共享、跨实体保持独立](evidence/independent-review.md) |
| D02 | 唯一定义覆盖要求、输出、Prompt、参考、模型和参数，数据库约束与全部写入口防止多份定义漂移 | 隔离通过 | [唯一定义、数据库约束及物理引用](data-contract.md)；[定义改绑／缺失独立篡改拒绝](evidence/independent-review.md) |
| D03 | 首次提交、失败及未知均锁定；修改要求或制作字段建新版，同方案多次生成同版多候选，评论不建版 | 隔离通过 | [失败／未知 prepared_plan 锁定及同方案重试](evidence/independent-review.md)；完整要求、输出、制作字段签名回归 |
| D04 | 幂等回执、关联补全、并发冲突、随机／固定种子正确，无原件无候选，新增候选不改变采用 | 隔离通过 | [模型、随机策略、幂等、并发、候选与采用检查](data-validation.md)；[准确采用实页](evidence/browser-review.md) |
| D05 | 李寄基础音色版本 2 和 13 状态关系复验，状态指向正确共享素材，卡片不堆叠 13 份要求，旧链接准确 | 隔离通过 | [13状态实页](evidence/li-ji-state-browser-proof.json)、[版本2截图](evidence/li-ji-voice-v2-before-comment.jpg)；[独立历史缺口](evidence/independent-review.md) |
| D06 | 存储检查证明数据库、导出、受管归档重复方案已物理去重，不能仅隐藏或新增引用 | 隔离通过 | [SQLite物理扫描和集中定义计数](data-evidence.json)；[独立78889节点／1855归档检查](evidence/independent-full-data-check.json) |
| D07 | 旧记录、请求及回执无损还原，旧修订身份、原始字节哈希、媒体哈希、评论及采用准确 | 隔离通过 | [独立10160修订、1855归档、511媒体逐项字节核对](evidence/independent-full-data-check.json)；[归档范围盘点](evidence/independent-archive-coverage.json) |
| D08 | HTTP／CLI、生成登记使用同一事实来源，旧格式读取及全量导出→空实例恢复通过 | 隔离通过 | [统一读写与Schema1—5兼容](data-validation.md)；[真实全量空实例恢复](restore-evidence.json)；[读取方式](data-contract.md) |
| D09 | 映射和合并依据可审阅，重复执行无新增、冲突整体回滚、并发修改保留，恢复步骤隔离验证 | 隔离通过 | [准确映射及逆迁移](migration.json)、[真实幂等与逆向恢复](rollback-evidence.json)；[冲突／并发边界](data-validation.md)；[发布编排与真实SQL事务独立检查](evidence/navigation.md) |
| U01 | 主代理、导航、数据和独立审查实际分工明确，共享接口有负责人，浏览器及正式资源互斥 | 通过 | [原始分工边界](../../planning/ui-material-model-task.md)；[导航实际窗口](evidence/navigation.md)、[独立审查分工](evidence/independent-review.md)；浏览器仅root |
| U02 | 独立对照原要求和数据历史，记录有效发现、修复复验，关键改动不只有实施者自审 | 通过 | [13项独立发现、共同发现及修复复验](evidence/independent-review.md)；[草稿、声音评论和发布编排复核](evidence/navigation.md) |
| U03 | 记录预期收益和实际贡献、并行区间、等待与返工；未知指标如实标明，无对照不宣称固定提升 | 通过 | [实际贡献、观测时间、协调和返工](evidence/navigation.md)；[独立贡献与未知项](evidence/independent-review.md)；无max对照，不宣称固定提升 |
| F01 | 完整双仓候选、迁移／恢复方案、必要数据包、使用说明和逐项页面证据可审阅 | 候选备齐 | [完整交付与串行操作](README.md)；最终双仓提交和不可变发布包哈希见任务准备回执及最终确认展示 |
| F02 | 最终候选确认后按当前头与依赖串行集成、增量应用正式库和服务、推送回读，不以副本覆盖活库 | 待最终候选确认 | 确认前不执行；[已准备的发布与恢复顺序](README.md)。正式结果进入唯一任务账本／运行回执，不补写候选文档 |
