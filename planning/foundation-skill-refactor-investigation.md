# 基础流程与 SKILL 重构的调查依据

本记录服务于本次任务定义，不是新方法或执行验收。调查日期：2026-10-13。业务数据只读；本轮未调用付费生成、未改写作品、未部署。页面结论来自真实 Chrome 操作，方法与执行结论来自当前正式服务只读读取、源码及定向历史核对。

## 真实页面

入口：本机正式 `http://127.0.0.1:3000/?workspace=production.approach&tab=foundation`。

- 左侧流程向下滚动至素材方案／生成准备，整页已吸顶；点击“生成准备”后，右侧正确打开该方法，但整页标题重新出现、左图返回“采编与方向”顶部。重新向下滚动后点击文件列表的“准确依据与连续性”，再次发生同样的位置丢失。
- 故事结构的文件树列出影视知识全部专业章节、图示、Seedance 视频手册和视频案例，超过该方法声明的叙事章节。
- “独立读者”的边框／点击表达与主方法不一致；图像、声音有明显分组，视频、字层未保持相同边界表达。

实现定位：系统 `review_desk/static/methods.js` 的 `rememberMethodPosition` 保存 window.scrollY；`methodOpen`／`methodSelectNode` 进入 `drawMethods`，其重建 root 并按新文件位置或默认 0 滚整页；左侧自身滚动未保留。同文件的引用按资源修订去重，再读取并绘制整个资源目录，没有按声明的 section／when 缩小文件树。

## 实际方法与引用

正式只读接口 `/api/methods`、`/api/methods/record?object_id=...`、`/api/methods/resolve` 用于核对当前方法、引用与适用组合。当前 whole-package 版本不等于页面逐文件版本；以下身份用于追溯调查，执行从最新主干与正式绑定开始。

| 对象 | 调查时包版本／准确修订 | 已核对事实 |
| --- | --- | --- |
| method.skill.story-structure | 4 / 9c150127a86a8541d4fe66dfa36bd0a0ea3bcb52f31f7e0261f6084a66c151ff | 实际引用 narrative 与 continuity；含一次性“本轮方法试用”边界，正文写“读 narrative 选择观众获知方式” |
| method.skill.novel-writing | 4 / 3e5e0d9b0a4043c95395495caa656f9342751fd37470dc00422148c3edab082b | 已有逐步写作、回读和连续性；文学表达取舍不足，重复混入素材候选／正式发布通用段落 |
| method.skill.screenplay-scene | 4 / 7dc14c8593000db8a03353f2f51eb7172a5565fad98492ff6170377c0012c911 | 实际引用 narrative、performance、sound 与 continuity，没有 Seedance |
| method.skill.material-assessment | 12 / 89bacd8a926fe4970c6e9bd85cb65ca0aaa8e735f64ed01e72bce41aed111a6e | 默认 staging／design，need_sound=true 加 sound；与抽取的通用职责相比引用范围偏宽 |
| method.skill.generation-preflight | 8 / fe25ae57340198eacb2f65382ec9acc968d9d21dba7823248632e6f3ba8db597 | 仍写“本轮方法库试用只做准备，不发起生成”；准备能力与真实生成节点分离 |
| method.resource.continuity | 2 / b2886e752736f9b20312300c4c4dbffbf15b6feb08728fed96a82f508aa6848f | 准确原文、读者范围、评论不扩要求混合为统一公共规则 |

正式方法解析四个对照包——故事结构、剧本、默认抽取、need_sound=true 抽取——均未加载 Seedance。因此不能将页面的宽目录误报为真实执行已经加载视频手册。系统 `review_desk/methods.py` 的解析按章节和条件选择；页面展示范围与真实依赖不一致是独立问题。

当前连续性资源由 task-20261009-0020 引入，最初服务评论与小说，随后一次评论润色扩大需求的试用导致第二版补充；依据 `production/managed-methods/VERIFICATION.md`。后续专业方法扩展引用。该规则没有独立创作产物，“不用后文、作者设定”未区分作者与首次独立读者的工作目的。本次未声称已证实它导致具体作品错误。

`production/filmcraft/01-narrative.md` 的题目是“导演与视觉叙事”，有共通因果／信息安排知识，也大量围绕可见行为、镜头、视线、声音和剪辑。用户讨论后确认小说结构不再依赖它，另以适合小说的专业创作方法补强 SKILL。选择并非只改资料标题。

## 生成与素材分类

`content/skill-flow.json` 当前将“生成准备”绑定独立方法并产出准备包，真正的“生成与制作”却没有 SKILL。系统 `review_desk/generation.py`、`review_desk/production_operations.py` 的真实提交会重新校验准备包，不以先完成独立 generation-preflight 方法为前提。合并后的执行应保留原件／参数／准确方案检查、调用身份、快照及回收能力，而不是新增一套准备审批。

现行图像共用 image-plan 及四专项，声音有三个独立方法，视频、字层各自单项；图形分组标题仅在多项时显示，造成视觉不一致。字层的真实职责包含准确文字和可编辑工程，系统 `review_desk/method_media.py` 与故事 `scripts/register_text_handoffs.py` 均有对应路径。用户已同意字层保持独立分类，不归入图像；本次不存在再次全剧分类迁移目标。

## 任务归属

首次查重时账本 129 项均 completed，无保留澄清草稿。0010 的旧方法目录已由后续替代；0013 提供逐文件历史／比较／评论；0016 提供九类素材与专项选择；0017 提供制作思路入口和流程图；20261013-0001／0002 处理素材筛选，不覆盖此次职责和 SKILL 重构。本次为已交付能力的确证残留与用户新确认的完整改进，不重开旧任务，也不继承全剧重做授权。

发布期间再次回查，另一会话已发布 task-20261013-0003（大卡加载）、0004（参考小卡候选选择）、0005（全站素材参考合理性核查与既有候选复用表达）。它们不承担本次基础流程阅读和完整方法重构；0005 的真实素材引用核查与本任务方法／执行规则可能有可合并交点，按正文明确归属、吸收最新成果及组合复验，仍无必要硬依赖。

任务验收中的试写效果、交互后例、新方法解析与正式交付，均是执行者需完成的目标，未被本调查预先宣称通过。
