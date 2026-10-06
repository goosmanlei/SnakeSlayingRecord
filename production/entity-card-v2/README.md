# 实体大卡第二版交付

本包供审阅候选和执行正式发布使用。完整范围来自[任务说明](../../planning/entity-card-v2-task.md)与 Notebook 对应整章，三份原图随包保留，[输入清单](input-manifest.json)记录原字节、像素与 SHA-256。现行名称为“实体大卡”，仍分左侧实体区和右侧素材区；不包含新媒体生成、小卡重设计或场镜页面重构。

## 实现与实际验证

| 要求 | 实现与实际依据 |
| --- | --- |
| 实体标题版本 | 标题行放实体版本，采纳通过间距与边线分组；基础信息不重复。状态版本留在状态内。桌面、390px窄屏及20版本夹具均可操作，准确旧版与手动选择优先。[标题](evidence/after-title.png)、[窄屏](evidence/narrow-title.png)、[页内组件](evidence/inline-title.png) |
| 基础剧情依据 | 原准确来源与框体保留，收起▼、展开▲。Chrome实际打开S001的剧本版本四来源并返回，再收起，箭头随真实状态变化。 |
| 关系图 | 正方形视窗，图内不缩放；桌面双列、窄屏单列，按完整名称、说明及依据实测高度排布。主要关系先展示，其余外侧分道。曲线、虚实线与箭头共同表达，全文和依据直接展开。阿蘅28节点、27说明的桌面636×636／窄屏328×328几何均无框体覆盖或连线穿越无关文字；拖动、方向键、关联实体、来源、评论入口和返回有效。[原拥挤图](inputs/relationship-graph-crowding.png)、[改后](evidence/after-graph.png)、[桌面几何](evidence/graph-desktop.json)、[窄屏几何](evidence/graph-narrow.json)。单关系歌曲与长名称、909字说明、12项依据另验收，[长文本](evidence/long-graph.png)。 |
| 状态双Tab | 两Tab居左，宽度按内容，默认全收起；鼠标执行“无选中→依据→镜头→收起”，键盘Enter／空格反向切换，切状态和关闭上层来源窗正常。0场／0镜目标可操作；来源为空时内容为空，镜头为空时显示未关联。方向键只移动焦点。[四步状态](evidence/tabs.json)、[截图](evidence/tabs.png) |
| 素材版本与候选 | 两行右对齐、真实序号递增，DOM与键盘一致。初始选中项可见，21版和8候选横向溢出可达。阿蘅M822、歌曲M841／M1195及未生成方案验证默认策略、准确历史、单版／多版和候选归属；最新方案无结果仍默认旧有结果版。候选行仅在有候选时显示，浏览不写采用。[版本溢出](evidence/overflow-versions.png)、[候选溢出](evidence/overflow-candidates.png) |
| 共用入口与评论 | 实体管理、素材管理、制作拆解、镜头制作与多层弹窗实测。整图评论新增、⌘+Enter提交／编辑保存、切V2后定位回V1准确候选；实体采纳／取消、原图放大、声音播放至结束、来源及关联实体返回正常。[评论](evidence/comments.png)、[拆解入口](evidence/breakdown-card.png)、[镜头入口](evidence/shot-card.png)。页内验收在一次性HTML夹具中调用同一`renderUnifiedCard`；现行管理入口沿前置任务使用弹窗，未增加产品入口。 |

实际浏览器为已连接Chrome，桌面2166×915与窄屏390×844；[浏览器记录](evidence/browser.json)区分真实对象和隔离夹具。8候选夹具只将已有准确原件绑定到测试投影，未声明它们覆盖夹具状态，未创建媒体或真实调用，不发布该副本。测试库的评论、决定和夹具与交付库分开。

系统候选与目标只维护在[双仓交付计划](system-delivery.json)，实例配置锁定同一提交。系统Python297项、JavaScript644项，故事发布守卫61项、完整状态编制6项通过；证据位于`evidence/*tests*.json`。静态检查和自动测试未代替上述浏览器操作。

## 物理清理、引用及保全

[清理计划](cleanup-plan.json)按当前133个实体头和当前完整状态范围确定90个独立历史状态，覆盖143次修订。包含86个旧局部状态和4个已撤回完整状态；打开旧实体版本不会改变范围。[逐项审计](cleanup-audit.json)列出准确身份、全部修订、所属实体、1100条历史／当前引用、素材组成和哈希、真实调用、相关评论及处置。无等价映射，不将旧引用迁移到现用状态；没有未解决的重要依赖。

清理后真实`STATE`对象从359减至269，143份状态正文已物理替换为最小删除凭据；对象种类改为`DELETED_STATE`，冗余状态出边删除。对象／修订索引只作为外键身份载体，保留准确ID、所属实体、原哈希和原因，不带原状态块、维度、剧情正文或来源列表。这些身份行不计为状态，不是另存完整状态副本。准确历史链接显示“目标已清理”，保留引用来源，[包布准确目标截图](evidence/cleaned-exact-target.png)验证没有冒用最新状态，并补验打开与刷新后均保留准确目标及原实体归属。

当前传入引用包括旧判断、状态前身追溯、已撤回需求和真实素材／调用。它们保留原准确目标及删除提示；没有当前采用关系指向目标。现有素材、真实调用、评论引文和其他对象修订不重写。新写入不能重建目标或增加对它的引用；需要继续修改含旧引用的历史对象时，须明确处置该引用，不能自动换成当前状态。

[归档计划](archive-plan.json)同步清理当前重放包、编制库存和包布登记源，将不对应已审计修订的旧来源占位改为来源删除凭据，不冒充准确修订。清理可在同一事务核对全部状态、内容节点与归档输入；330个不再被引用的旧节点删除，151个净化节点加入。相关Git旧提交保留，不重写历史。

[数据保全](evidence/conservation.json)核对未批准改动的全部业务表和其他修订相同、外键无悬空；1396份受管原件文件摘要不变，285评论与314事件不丢失，素材版本、候选、真实调用及判断／采用均保留。SQLite启用安全删除，并在停读后checkpoint、VACUUM、完整性核查，避免空闲页／WAL残留正文。重复执行零额外删除，冲突整批回滚已有自动检查和完整副本预演。

[恢复实测](evidence/recovery.json)将当前Schema 7导出恢复为空库，31张业务表逐行一致，四份核心数据文件再次导出逐字节一致，未复活目标。历史PCM的两个精度例外沿原准确范围验证，不改真实调用。实例配置中的删除身份策略使旧导出即使恢复到空库也被拒绝；清理后的导出允许恢复。删除凭据及已有不可变引用按登记哈希校验，新普通写入不能绕过该策略。

## 受控正式发布与向前恢复

`--auto`授权本任务自行验收和依次交付，不表示用户接受任何作品或媒体。正式库是主项目`.runtime/review.sqlite3`，服务为3000；不得用隔离快照覆盖活库。候选、来源或数据发生变化时重新冻结并补验。

1. 在各自任务工作区提交系统和故事候选，故事执行`codex.project task _prepare_integration -g creative -p SnakeSlayingRecord --task task-20261006-0001 --push`。核对目标main、upstream与准确候选。
2. `python3 scripts/entity_card_v2_release.py prepare --system-worktree .runtime/entity-card-v2/system --bundle .runtime/entity-card-v2/release-final --push-system --story-candidate <SHA> --story-target <SHA> --system-candidate <SHA> --system-target <SHA>`冻结代码、配置、清理文件、全库前后指纹和唯一系统upstream。正式库必须准确等于清理前或清理后指纹；已清理库只核验既有删除凭据，重复发布不再删除。通过同包`material_review_release.py build`及`entity_card_v2_release.py preflight`，只在临时影子库预演。
3. 候选验收后通过任务`_deliver`完成故事受控集成／普通推送，再执行`entity_card_v2_release.py apply`，带`--apply`及service manifest、image receipt、cleanup manifest三个准确摘要。共享锁内复核完整数据指纹、系统受控fast-forward、停止旧服务；在同一事务应用批准差异，核对指纹与存储，建立净化恢复包，再切换正式镜像与配置。恢复包首次导出直接在同一净化事务中读取归档内容，避免要求尚未写出的内容图。漂移整批停止，绝不恢复旧正文或强推。
4. Chrome在正式3000验证实体标题、双Tab、关系、准确删除目标和共用入口；核对真实镜像、配置pin与源码。再使用同包`material_review_release.py publish-system`带两个准确摘要和`--apply`普通推送，回读远端。
5. 首次正式清理回执保留在`.runtime/entity-card-v2/release/run/`；支持直接初始化恢复包的最终冻结包为`release-final/`，首次初始化与零删除重入均需实际通过。实际发布与验收回执留在本任务`.runtime/entity-card-v2/release-final/run/`和主任务账本，不在已交付候选中补日志。全部完成标准满足并清理过程资源后才调用`_complete`；之后结束文件写入并保持TUI。

失败只能从同一冻结包继续`apply`，或使用净化后的`run/sanitized-recovery`及支持删除凭据的候选重新建立实例。服务目录在主项目`.runtime/service-releases/entity-card-v2-20261006-0001-<故事短SHA>-<系统短SHA>/`，保留准确配置／镜像挂载；数据库不回滚到旧备份。此前恢复包由本包替代，旧代码或旧Git提交不是现行数据恢复入口。

预览、浏览器夹具、重复恢复实例、试验脚本、失效日志及缓存在正式验收后按PID／路径核对清除。冻结包、净化恢复资料、必要回执与双仓分支保留用于恢复和追溯；原图任务输入保留用于账本来源核验。实际删除数量、回读和仍保留用途读取`release-final/run/cleanup-final.json`，未执行时不宣称清理完成。worktree待TUI退出释放锁后另由受管清理命令退役，不递归删除嵌套Git工作区。
