# 本轮历史来源与覆盖草案

已整理5个主页面、12个子页及61条动作。独审80份v3初始语义基线、136份基线交互和新增候选UI证据；当前矩阵为12项初始页基线、23项部分功能输出、1项带已确认缺陷（AO-UX003待实测复验）、25项NOT_RUN。AO-UX001已测桌面遮挡与位置回归通过，AO-UX002候选文字和准确旧版原件已见；输入外Esc收起仍待补验。全部动作仍按限定范围记录，未宣称整项完成。旧60份v2快照与12张截图独列，不与v3合并。

固定入口均在本目录：

- `sources-and-principles.json`：27 份来源哈希、15 条历史原则、6 项替代关系、上一轮 51 项回归索引。
- `comment-provenance.json`：73 条准确历史评论到当前 preview 的逐条对应。preview 共 271 评论，259 未关闭、12 已关闭；无作者字段。
- `coverage-draft.json`：12 子页、61 动作，各项起止点、重要状态、相关 API、适用性、已观察范围及未验原因。
- `action-baseline-audit.md/.json`：136 份真实交互文件的去重审计、每组原始计时、原断言失败和 15 个被替代的输入样本。
- `page-performance-candidate1.md/.json`：两阶段各 80 份初始页样本的中位/P95/IQR/MAD/原始数组；P1 观察到改善，C2 变慢信号与分段归因待窄复测，其余收益未证实。
- `ui-implementation-review.md`：AO-UX-001/002/003 当前候选静态审查、独立发现与返工、真实截图及几何证据、已验范围和待补项。
- `candidate-ui-evidence-audit.json`：本批UI文件哈希、7条动作范围更新和不可推断项。
- `image-dialog-panel-review.md`：AO-UX003基线归属、所有弹窗调用入口、最窄修复及剩余真实验收。
- `delivery-report-review.md`：交付串行顺序、确认后候选写入禁令、性能数字归属与待补验措辞独审。
- `outside-click-reflow-review.md`：AO-UX001新增首击丢失回归、click捕获方案与拖选后click风险，当前待修复实测。
- `ux001-review.md`：实施前的遮挡截图与几何独审、有效历史约束、桌面避让建议和验收范围；后续实施审查见 `ui-implementation-review.md`。
- `ux002-review.md`：实施前的跨版本筛选口径与显示建议；后续实施审查见 `ui-implementation-review.md`。
- `readme-correction-proposal.md`：系统 README 的已过时条目与最小替换建议，交由主协调按实际改动统一处理。

## 主协调需要吸收的结论

1. 旧“修订评论启动新轮”被 task9 固定完整方案版本替代：评论不建版；首次实际提交即锁定，失败/未知仍锁定；定义变化才建新版，同方案重试增加候选。
2. task8 的正文场镜点击选中、顶部共享素材、宽屏列表两列，已分别被 task9 替代为正文无选中、各镜明确用材、全部紧凑单列。
3. 上一轮 51 项发现全部先列回归。旧报告的通过或部分通过不迁移到本轮，不认定旧问题仍存在。
4. 73 条剧本三评论均存在于 preview。仅 C40 的记录版本由归档的 1 变为当前 3；正文、圈选、目标修订及 OPEN 状态均一致。已有历史记载误关闭后恢复，不能把版本变化认定为本轮污染。作者始终 UNKNOWN。
5. 系统 README 曾称当前导出为 Schema 5、场顶部展示共用素材，与 task9 交付和当前实现有漂移。主协调已在候选中修正文档，独立复读见 `ui-implementation-review.md`；不把文档纠偏当作本轮重做任务 9 功能。
6. preview 对象分类无 ASSEMBLY、DELIVERABLE。组合与历史入口及已有检查记录可测；真实已产出组合或成片的预览应记不适用，不能用夹具冒充成果。

## 实际代码启用子页

| 主页面 | 子页 | 路由 |
|---|---|---|
|制作思路|故事创作|`?workspace=production.approach&tab=story`|
|制作思路|生产制作|`?workspace=production.approach&tab=materials`|
|故事创作|故事采编|`?workspace=story.sources`|
|故事创作|故事结构|`?workspace=story.outline`|
|故事创作|剧本创作|`?workspace=story.script`|
|制作设定|制作拆解|`?workspace=settings.workspace&production_tab=breakdown`|
|制作设定|实体管理|`?workspace=settings.workspace&production_tab=entities`|
|制作设定|素材管理|`?workspace=materials.workspace&production_tab=materials`|
|全剧制作|镜头制作|`?workspace=production.workspace&production_tab=shots`|
|全剧制作|组合与历史|`?workspace=production.workspace&production_tab=history`|
|系统管理|故事项目|`?workspace=project.configuration&config_section=PROJECT`|
|系统管理|系统与 AI|`?workspace=project.configuration&config_section=SYSTEM`|

## 使用方法与边界

将本草案与主协调已有基线及正式服务证据合并，保持任务自己的发现 ID。快照来源及一致性由主协调基线证明；本代理仅对其 preview 以只读 SQLite 连接检查评论和对象分类。

真实浏览器从用户动作起，到准确内容可读且控件可操作为止；API 完成单独计时。固定机器、浏览器/视口、双仓版本、数据快照、样本及缓存条件；建议每条件至少五次，保留每次值、中位数和最小最大值。少量样本不能包装成可靠尾延迟；性能窗口由主协调独占。

已读现有任务正文及其保存的原话，未遍历全部历史原始会话。因此不把任务文档的转述冒充亲读原会话。作者、缺失来源、浏览器范围、性能收益需继续据本轮证据收敛。

本代理只写本目录；未改故事正文、共享代码、正式报告、正式库或运行服务，未使用浏览器、性能负载或后代委派。
