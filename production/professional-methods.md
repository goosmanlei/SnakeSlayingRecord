# 从工作目的选择创作制作方法

在审阅台“系统管理 → SKILL管理”沿基础流程选择实际绑定的 SKILL，阅读正文、参考、模板、准确共用章节及各文件独立历史。普通入口读当前文件，明确旧链接保持原组合；版本比较和评论沿共同阅读交互。后台显式绑定决定新执行取得哪一版，阅读最新版不自动应用；已开始的工作保持冻结旧包。操作见 [受管方法](managed-methods.md)。

执行者经下表的真实入口取得准确 `SKILL.md`、所需共用章节和工作输入。这里维护工作交接及覆盖边界，不另写方法正文。`content/managed-method-registry.json`是历史安装导出；当前版本必须回读有效实例的绑定和准确执行包。迁移只追加，不用历史定义覆盖活库或其他任务的新版本。取得方法证明交付身份，不能证明创作质量；试用证据见[方法试用](professional-methods/VERIFICATION.md)，本次目录与交接验证见[可见导航验收](working-methods-navigation/VERIFICATION.md)。

## 每一步收到什么、交出什么

| 当前工作 | 必须取得的输入 | 交给下一步的产物 | 不能替上游猜的内容 |
| --- | --- | --- | --- |
| 故事结构设计或修订 | 已选方向、用户约束、准确旧稿与相关意见 | 人物选择、关系、空间、事件因果、时间线相互一致的完整结构稿 | 没有确认的方向、其他作品设定，不能冒充当前事实 |
| 逐段逐章小说 | 一个准确结构修订、当前已采用正文和作者检查点 | 当前自然片段及同步事实；章末复读；全书完成后发布干净稿 | 后章尚未发生的事情不能填成已发生；结构冲突须联动修订 |
| 影视剧本 | 全部故事与结构、明确改编范围、已采用前场 | 逐场可见可闻的动作、对白、声源与表演；集末和全稿复核 | 不能只写“解释、道谢、读回”就算完成表演原词；候选词不等于锁词 |
| 逐集视听设计 | 准确全剧及当前集场、必要前后衔接、制作输入锁 | 具有因果和观看顺序的场、镜方案，以及未完事项的负责阶段 | 不因旧镜数或自动字段机械切镜；局部任务不能擅改上游事实 |
| 实体（普通 EN 与镜头 ASH）、必要状态 ST 与素材需求 M | 场镜用途、准确实体关系、实际图像或音频原件 | 沿同一镜头 ASH 的编排和实体身份，交复用／编辑／新制／无需独立素材判断、唯一具体分类及用途 | 动作不自动产生新实体或状态；名称、历史认可不能证明新用途适配 |
| 图像、声音、视频和字层方案 | 当前表达、准确状态、可读原件、词句状态、实际渠道 | 给制作者的路线与检查，以及单独发给模型的 Prompt、参数、参考 | 未定原词交给负责创作阶段形成候选；未选原件和未验能力保持未就绪 |
| 真实生成准备 | 当前准确方案、已选择的原件与片段、输入锁及本次调用授权 | 可追溯的准备包或可操作的缺项；实际调用另有回执 | AI自检、人的评论与调用授权分别判断；准备不授予调用许可，也不证明效果 |
| 结果检查与返修 | 实际原件、准确目标与输入、必要相邻镜 | 问题位置、原因判断、有限修订与复验范围 | 看不到／听不到就保留未验；不能用技术规格代替作品判断 |
| 独立读者、评论措辞润色 | 分别为截至当前位置的正文；或准确对象、圈选及原意见 | 有依据的读者发现；或保留原意的清楚措辞 | 读者不取后文和作者设定；润色不增加创作要求、不自动保存评论 |

本剧已确认结构与小说保持。隔离方法试用不能作为全剧重做、媒体效果或用户质量认可的证明。AI的`review`阶段保存实际回读与返修判断，继续是创作步骤；人的关闭评论只是整理讨论，不成为执行闸门。

## 共用资料按问题取用

[影视知识](filmcraft/README.md)的十二章、来源、案例与图示继续以项目文件为唯一正文；系统中的资源是准确只读投影。[视频手册](seedance-video-handbook.md)同样沿原正文维护。共用资源改版时，方法须显式引用新修订，已开始的步骤继续原快照。

先确定本次产物和问题，再选原理与制作路线。连续性用于视听设计、首帧／视频和审片；声音章节用于声源、角色和表演问题；视频手册先取方式比较，再读对应模板和案例。普通小说片段或评论措辞不加载整本视频手册。资料来源与跨集索引可供按需展开，不能当成已读原文。

具体管理、导出和恢复沿[受管方法](managed-methods.md)，隔离实例、增量发布和清理沿[生成工作区](generation-workspaces.md)。

## 实际入口与选择条件

| 工作类型 `work_type` | 实际入口（相对项目根） | 选择的方法稳定标识与按需资料 |
| --- | --- | --- |
| `story-structure` | [scripts/creative_method.py](../scripts/creative_method.py) `begin` | `story-structure`；叙事与连续性 |
| `novel-writing` | [scripts/novel_writing.py](../scripts/novel_writing.py) `begin` | `novel-writing`；连续性；候选须保存、实际read后再accept |
| `screenplay-writing` | [scripts/screenplay_writing.py](../scripts/screenplay_writing.py) `context --full`→`begin` | `screenplay-scene`；叙事、表演、声音；表演原词与剧本同属可表演产物 |
| `audiovisual-design` | `scripts/creative_method.py begin` | `audiovisual-scene`；五个实际阶段；按`need_narrative`、`need_coverage`、`need_staging`、`need_performance`、`need_sound`、`need_editing`等当前问题取章 |
| `material-assessment` | `scripts/creative_method.py begin` | `material-assessment`；调度、美术，涉及声音加`need_sound`。实质抽取与命名升级由本轮抽取任务负责，本页沿稳定身份读取其实际新版本 |
| `media-plan`：四类图像 | [scripts/media_method.py](../scripts/media_method.py) `begin`；需求保存唯一 `material_category` | `image-plan` 共同正文与自动选中的角色、场景、道具或镜头画面专项；`applicable_files` 明确本步必读文件 |
| `media-plan`：人物音色 | 同一媒体入口，分类 `voice` | `voice-plan`；准确单人声音身份与选段；不另传声音类型 |
| `media-plan`：场景音 | 同一媒体入口，分类 `scene-sound` | `scene-sound-plan`；独立声源、空间、同步与对白/音乐关系；没有独立交付目标不造需求 |
| `media-plan`：演唱 | 同一媒体入口，分类 `song` | `song-plan`；完整歌曲与省段清唱各守职责，复用保持准确范围 |
| `media-plan`：视频 | 同一媒体入口，分类 `video` | `video-plan`；`case` 选择 action/dialogue/extension/style/song，按问题取准确手册章节；保留正确当前方案 |
| `media-plan`：字层 | 同一媒体入口，分类 `text-layer` | `text-layer`；准确 blocks、specification、UTF-8/SVG 与逐镜交接，无生成时不填虚构模型 |
| `text-layer` | `scripts/creative_method.py begin` | 同一字层方法的通用作者入口；制作需求的保存仍通过媒体作者入口取得准确基线与导入包 |
| `generation-preflight` | `scripts/creative_method.py begin` + [单项媒体准备](managed-methods.md#单项媒体方案)的既有入口 | `generation-preflight`；当前方案、准确原件和调用授权核查；没有逐项审批或自动付费调用 |
| `result-review` | `scripts/creative_method.py begin` | `result-review`；实际看、听、连看后检查与返修；调度、动画、连续性及按需声音、剪辑 |
| `reader-review` | [scripts/reader_review.py](../scripts/reader_review.py) | `reader-review`；full/summary-reader/summary/recall-reader/grounding按阅读进度取资料，不泄露后文 |
| `comment-polish` | 评论输入中的“AI润色修改意见” | 当前`comment-polish-clear`；准确原文帮助消歧，不增加要求；建议明确使用后另行保存 |
| `creative-system-review` | `scripts/creative_method.py begin`；项目会话沿[Review入口](../skills/creative-system-review/SKILL.md) | `creative-system-review`；唯一正文、项目适配与系统构想的准确只读投影；加载不启动持续运行 |

制作分类来自准确需求，不能在条件里改类或以通用分支兜底。合法改类后开始新步骤，重新取得方法和输入，旧冻结执行仍取原组合。条件可先通过 `MethodClient.resolve(work_type, conditions)` 查看入口、资源与阶段，再 begin 冻结。只增加当前有用的章节；发现需要未加载章节时以新步骤取得准确包并复核受影响工作。完整命令与恢复方式见[受管方法](managed-methods.md)。

旧`comment-polish`方法现在没有工作环节绑定，仍在“全部方法”及原准确链接可读，保留原评论与执行。它与当前`comment-polish`工作类型使用的`comment-polish-clear`不是同一选择。陌生新增工作类型在页面“其他”目录可见，不因未列入上表消失。

影视知识、视频手册、连续性、独立读者契约及Review适配是共用资料，按需供上述环节使用，不各自冒充创作步骤。项目的[任务定义与发布](../skills/task-definition-publish/SKILL.md)服务任务交接，继续从AGENTS进入，没有注册成作品创作执行类型。

初期采编与方向比较、尚无实际作品镜头视频的剪辑成片流程不在本表的已验证执行覆盖内。本轮没有查明需要新造方法的具体缺陷，不用空方法或目录项承诺能力。后续实际目标与输入明确后再判断独立方法的必要性。

执行者必须实际读包和原件。程序能证明交付身份、输入及阶段先后，不能证明方法被正确理解。真实试用中的问题、修订、正确反例与未验边界见[本轮验证](professional-methods/VERIFICATION.md)。
