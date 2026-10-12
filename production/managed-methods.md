# 受管工作方法与实际执行

“制作思路 → 基础流程”组织真实方法、准确文件阅读、版本比较和评论。后台继续保存方法整包、共用章节、环节绑定与不可改写的执行快照；故事工具取得准确快照后继续创作，通用审阅台不反向导入创作工具。

本页说明当前契约。基础启用见 [基础验收](managed-methods/VERIFICATION.md)，方法编制见 [创作制作方法](professional-methods.md)，本次导航、独立文件历史和数据模型关系图见 [SKILL 管理验收](skill-admin-data-model/VERIFICATION.md)。正式身份以配置、任务账本和发布回执为准。

## 阅读、比较和评论

左侧基础流程覆盖采编、结构、小说、剧本、视听、抽取，以及图像、声音、视频、字层四大类素材方案、生成准备、检查返修和剪辑；小说与故事剧本内分别标出“创作→独立阅读→修订→再读”；评论 AI 润色与创作协作 Review 为直接辅助节点。每个紧凑阶段框中，上方动作以短“产出”箭头连接下方纸张形数据区，主线从整个阶段底部继续。产出区标明小说稿、剧本集场、视听集场镜、实体（角色、场景、道具、歌曲 EN；承接同一镜头 ASH）、必要状态 ST、素材需求 M 及候选等，帮助对照数据模型。素材方案更新同一 M 的当前方案，生成与制作才产生提交快照、候选 MC 与原件。节点由真实工作类型绑定取得 SKILL 身份，无方法的阶段只作流程说明。普通点击读取所选 SKILL 当前文件；旧链接、共用资料引用和历史执行仍固定原准确组合。可读的最新版不会自动改变后续执行绑定。

右侧文件树包含正文、参考、模板、图示和原件。完整 Review、项目适配及系统构想沿唯一来源连续阅读；包内的 shared 路径及普通相对链接均解析到所引准确文件。视频手册、影视知识等公共部件在各 SKILL 内嵌阅读；章节评论仍属于公共部件的准确文件，点击章节不追加返回原位置引导。文件以阅读顺序编号并按正文、参考、模板、图示和媒体分组，同层项目保持对齐。页面只提供阅读、比较和评论；方法维护沿后台 CLI/API，已移除旧三个 Tab、配置编辑、正文保存／应用与下载入口。

每个文件按所属方法／资料及相对路径独立计版，仅原字节变化追加版本。只改另一文件或包元数据不会推动本文件编号；相同内容重试不追加，A→B→A 仍是三次内容变化。改名作为新文件；删除不抹掉历史。旧整包准确映射到当时的文件组合，既有评论和冻结执行身份不改写。

文件右上以普通版号直接选择版本，不另加“最新”标签；左侧“版本比较”独立打开浮窗；单版文件不可比较。每次进入默认倒数第二版与最新版，允许任选两版或选同版。文本显示真实增删行和完整上下文，图形／原件显示准确两版；缺失或摘要不符明确报错，不换当前文件补缺。关闭浮窗保持外层版本、位置和未发评论。重复段落、中文、代码、换行差异及 SVG 均纳入验证。

“查看评论”汇总当前文件各版本的未关闭意见，保留原文件、原圈选与原整包身份，并显示独立文件版号。回应关联实际回应稿；复核可分别查看原圈选、回应稿和当前稿。改名或删除不迁移旧锚点，缺原目标不静默替换。未发评论按准确对象、修订与文件隔离，切换和刷新可继续；成功提交或取消才清理相应草稿。评论关闭不表示创作获批。

“数据模型”保留原编号查询和旧 CODES URL，下方逐一对应 E、S、AE、AS、ASH、EN、ST、R、M、MC、C，以实体卡片和归属／引用连线说明数据关系。每类实体直接标明版本与评论能力：剧本集场随完整剧本版本，制作对象仅当前内容，候选保留提交事实，SKILL 文件独立计版；当前制作评论仍保存当时摘录。三个局部图之间可沿实体引用定位。唯一声明在 `content/data-model.json`；基础流程及步骤产出在 `content/skill-flow.json`。镜头属于实体，必要状态至少拥有一项真实需求；需求只归实体、状态、镜头中的一个出处。关系、拟用参考和实际提交分别表达，不混为同一事实。

小说从“故事采编”的精修组独立为“小说创作”，位于故事结构与故事剧本之间。上方切版本、左侧选章节、右侧读正文；沿原 SOURCE 与段落身份保留旧评论、回应和未发草稿。旧精修链接自动进入新页面，不改写小说正文。

制作思路的五子页、静态概览、旧入口迁移及专业资料覆盖见 [统一入口验收](approach-foundation/VERIFICATION.md)。旧 METHODS/CODES 转到基础流程／数据模型；明确的对象、整包、文件、独立版号、流程节点和节点整包一起保留，旧专业资料及无 tab 章节链按唯一源映射定位。新链接使用制作思路入口，缺准确目标明确报错。系统管理保留故事项目与系统配置。

专业源或阅读映射变更后，运行 `python3 scripts/approach_foundation.py --check`，原 `sync_video_handbook.py --check` 与 `sync_filmcraft.py --check` 继续校验源映射。执行 `approach_foundation.py --system <任务审阅台> --instance <隔离实例>` 在方法副本中准备准确投影、更新实际受影响引用与绑定，再原子导入隔离实例；导出登记包后沿受管增量发布，不能对正式库直接重跑。未变字节不追加文件版号，旧整包和冻结执行保持原文。

## 正文在哪里维护

| 内容 | 有效正文与同步方向 |
| --- | --- |
| 实例原生方法、连续性知识、环节绑定 | 启用后通过后台 `method-save` / `method-source` 与准确绑定维护。保存追加新整包及实际变化文件的版本，绑定显式选择准确版本。 |
| 创作协作 Review | 唯一方法包在 `skills/creative-system-review/`，系统构想在 `production/system-vision.md`。系统方法只保留简短引用入口，全文沿 `method-source` 追加为只读资源；操作见下节。 |
| 视频手册与影视知识 | 项目 Markdown 是唯一正文。`method-source` 把选定章节及来源摘要追加为只读资源投影；完整资料与必要图示／媒体在适用 SKILL 内嵌阅读。影视知识包含 applications 六类本剧应用及其准确输入锁。不能反向改一份正文。 |
| `content/managed-methods.json`、`managed-media-method.json` | 初始化定义，安装到空实例；不覆盖已编辑的活库。媒体初始化同时读取本项目 Markdown。 |
| `content/managed-method-registry.json` | 本次候选的准确配置历史，用于增量迁移与空实例恢复；不是启用后的编辑副本。后续导出必须来自当时有效实例。 |
| `production/method-reading-application/registry.json` | 方法阅读应用的准确配置包，追加视听条款、完整手册及明确所选绑定；既有基础历史包保留。当前选择仍以有效实例与发布回执为准。 |
| 执行包、阶段产物 | 本步骤已取得的不可改写快照；方法升级不改过去。私有写作和读者记录留本机，公开作品导出不携带这些候选。 |

主要方法覆盖结构、小说、剧本与表演原词、视听设计、素材判断、图像/音色/演唱/视频/字层、生成准备和结果返修。评论润色与独立读者保留各自边界。视频按当前问题选择案例，普通小说与评论不装入视频手册。方法试用是隔离小样，全剧重做另行开展。

影视知识投影同时保存所选正文、来源记录和原创 SVG；执行包按章节带其所需图示与来源，保持原相对路径，恢复后仍可查用。未选的延伸章节沿原阅读入口或准确资源记录按需取得，不把链接当成已读原文，也不声称附属文献全部已加载给模型。源文件改版后须显式更新方法引用，旧执行保持旧投影。

## 创作协作 Review

按 [项目 SKILL](../skills/creative-system-review/SKILL.md) 审查作品、人和 AI 的协作及系统使用。项目会话从 AGENTS 的场景入口读取；基础流程中的“创作协作 Review”通过独立 `creative-system-review` 工作类型取得同一正文，不改变评论润色、作者、读者或媒体生成的绑定。

`content/creative-system-review-method.json` 是安装定义，只含来源路径、简短入口及环节元数据。用已有 `scripts/managed_methods.py install --seed content/creative-system-review-method.json` 在任务隔离实例安装，`--system` 指向本任务审阅台工作区，`--instance` 指向隔离实例。重复安装相同正文幂等，已维护配置不同则拒绝覆盖。

准备请求沿 `POST /api/methods/prepare` 或 `method-prepare`，提供 `work_type: creative-system-review`、独立 `run_id/step_id/target`，以及 `inputs` 中的 `goal`（当前目标）、`scope`（准确对象、版本及范围）、`authorization`（本次委托边界）、`evidence`（实际材料和实践证据）。返回包以完整 SKILL 为一个准确章节，随章附带项目适配和系统构想，保留源目录关系；专业制作所需章节及作品输入由本步按需补齐，这三个文本不能代替真实看、听、操作或其他专业材料。`review` 产物登记实际判断，不以取得方法代表完成审阅。

作者 `creative_method.py begin` 与标准 `method-export` 都从包根 `SKILL.md` 进入 `shared/0/skills/creative-system-review/SKILL.md`，正文的相对链接直接通向同目录的 `references/project-context.md`；系统构想为 `shared/0/production/system-vision.md`，由包根入口链接。正文原字节保持，使用者无需改名。三份文本均保留来源路径和摘要；标准导出另含 `registry.json`、`execution.json` 与准确输入，恢复到新空实例后仍可重取同一执行。作者交付以 `delivery.json` 固定请求及执行，`RESOURCES.md` 只索引本次实际资料。

包内链接以当前文件为基准；适配列出的 `AGENTS.md`、`KNOWLEDGE.md`、`STATE.md`、作品和专业资料路径以**本次输入明确给出的故事项目根**为基准。begin 的 `inputs` 应包含该根及准确作品/页面范围、授权、已有证据；没有提供的项目材料须沿本项目或本次输入补齐。加载方法不授予正式写入、持续运行或生成许可，方法可读也不等于创作完成。

仅恢复定义可用 `content/creative-system-review-registry.json`：只含本方法资源、引用入口与专用绑定的连续历史，不携带其他方法或私有试用。恢复完整作品后可显式追加，目标前进时拒绝旧包覆盖。旧第1版定义、执行和已经交付的历史包仍是原文与原目录：当前作者交付器对旧平面资源与标准导出统一使用 `shared/0.md` 等，解决重取时的顶层命名差异；**旧完整方法中的内部适配链接仍不可用**，从旧入口的第二份资源 `shared/1.md` 读取适配、第三份 `shared/2.md` 读愿景。原作者历史包的带章节名路径由其 `RESOURCES.md` 索引。不得向旧执行补入新附件或改写旧正文；要完整内链须显式采用保留目录的第2版或后续绑定、另建步骤。导出和恢复只包含显式选中的私有执行，不会为其他历史身份补造记录。

后续修改先改唯一包或系统构想，用 `method-source` 同步对应来源定义并提供资源当前 `expected_version`，再以 `method-save` 追加引用新资源准确修订的方法版本，最后显式更新本工作类型的绑定。旧执行继续旧资源及绑定。将相应准确历史从有效实例导出到登记包，再沿 [工作区发布](generation-workspaces.md) 增量发布；不能手改导出正文或用旧任务整库覆盖正式库。

当前首子页名称为“系统构想”，只保留两层协作图：审阅台的数据模型与基础流程共同支撑人与 AI 完成影视创作，以共同约束提升协作效率与质量。页面突出基础层，复用系统浅色纸面与柔和绿色。唯一源稿、阅读页与 Review 第6版准确投影一致；第1至5版和旧执行保持原文。当前候选、恢复与正式回执入口见 [协作图示验收](vision-collaboration/VERIFICATION.md)，旧布局沿准确 Git 历史和原回执追溯。

系统构想阅读页由 `python3 scripts/sync_system_vision.py` 确定性派生；`--check` 检查全文和首项位置。系统构想是方向说明，不代表全部能力已经实现。初次交付的正文与试用边界见 [交付验收](creative-system-review/VERIFICATION.md)。

## 外部小说作者

沿 [逐步创作流程](../planning/incremental-writing-workflow.md) 使用 `scripts/novel_writing.py`。新建步骤须指定本任务隔离审阅实例的 `--method-url`：

```bash
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT begin step.json
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT save-candidate step-id candidate.json
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT read-candidate step-id
python3 scripts/novel_writing.py --run my-run --method-url http://127.0.0.1:PORT accept step-id acceptance.json
```

`begin` 返回 `method_execution`：完整方法、适用共用章节、种子材料、当前检查点和本步范围。作者实际读取后工作；保存候选、回读候选和采用分别登记真实阶段产物，再形成原有检查点。方法接收的种子不包含用于发布保全的整库 `formal_baseline`。工具不会调用作者模型，也不会把候选当正式小说发布。

同一运行和步骤恢复时校验原输入及方法，当前绑定改变不影响旧步骤；新步骤取得新绑定。没有方法的历史检查点可只读，不能伪装为采用了新方法。新写作须用新步骤。

## 剧本作者与其他创作工作

`screenplay_writing.py` 的新场次先 `context --full`，再 `begin`；JSON 从标准输入传入。begin 需要 `step_id`、`scene_id`、当前 `base_revision` 和包含准确材料及范围的 `context`，可附资源选择 `conditions`。返回完整方法执行包。之后 `save` 保存一场，`read` 实际回读，`accept` 传入 `assessment` 与 `continuity`，形成检查点；有问题用 `reject` 后开始新步骤。保存/采用均须连接原 `--method-url`；旧候选可读，不能无方法继续采用。工具只保存作者工作，不调用模型或改正式剧本。原词候选是否锁定沿作品审阅决定，本地 accept 不授予生成许可。

结构、视听、素材判断、字层、生成准备与结果审阅使用同一服务的通用外部作者入口：

```bash
python3 scripts/creative_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-step begin --request request.json
python3 scripts/creative_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-step record --stage draft --file draft.md
python3 scripts/creative_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-step read --stage draft
```

请求包含 `work_type`、独立 `run_id`、`step_id`、`target`、`conditions`、`inputs.context`（准确正文及项目材料）。默认 private，执行只留本机。视听按包内五个阶段工作，其余通常为 draft/review/result；以实际包为准。每步产物保存并重读后才进入依赖步骤。`RESOURCES.md` 指向本次实际交付的准确章节与图示；缺文件、中断或恢复用同一请求继续，文件有异则拒绝覆盖。换输入、范围或条件须开新步骤。

制作摘要化的六类工作（视听设计、素材评估、字层、生成准备、结果审阅、媒体方案）共用本机原值交付：提交前先将原字符串或 JSON 对象及执行、目标、阶段身份安全落盘，服务确认后关联准确回执。`read` 核对原方法、前置产物、原值摘要与服务压缩外层摘要，返回原始值；字符串保留 Unicode、LF/CRLF，JSON 保留值和类型。服务继续只保存约定摘要，已有完整旧产物仍可准确读回；本机过程全文不进入公开作品导出，不建立永久草稿库。

服务已接受但响应或本机回执丢失时，先 `read --stage 原阶段` 重取已有确认。服务尚未确认时，`read` 明确报未确认；沿原目录执行 `recover --stage 原阶段` 才幂等继续本机保存的原值。原值写入尚未完成、或旧摘要步骤只有准确原文件时，使用 `recover --stage 原阶段 --file 原文件`；工具先核验原执行及摘要再接入，不从当前方案或相似文本补造。已确认阶段不能换正文，不同阶段可以按实际修订交接。换目标、输入、条件或支持材料须新步骤；恢复不导入作品，也不修改当前稿。

目录里的 `stage-阶段-value.json` 是带归属和摘要的原值，`stage-阶段.json` 是确认回执；回执单独存在不意味着拥有全文。文件均以完整临时文件原子交付，拒绝不同内容和符号链接；中断遗留的 `.method-write-*` 不是确认产物。全文缺失、内容或归属冲突时保留现场并按错误回查，不能删除回执后假装新提交。操作与两条真实 CLI 恢复链见 [阶段回读验收](method-stage-recovery/VERIFICATION.md)。

## 评论润色与独立读者

评论润色请求实际装入当前绑定的方法全文、适用资料和准确原文上下文，共用既有字符预算。方法过长或条件不匹配会给出修正原因，不回退到硬编码自由 Prompt。建议仍由人手动采用；方法保存不改评论或作品。

`reader_review.py` 新运行在初始化时固定普通逐段、摘要后阅读、摘要整理、有限回看和意见核对五种方法选择。每个实际请求再登记自己的阅读位置和准确输入，结果与该请求关联。它不通过润色接口读整稿，也不把方法管理当成向读者泄露后文的通道。

历史读者运行继续已冻结的 instructions、源、摘要与回看策略，方法历史未知。恢复不会用当前常量重写历史请求。操作和费用授权沿 [读者流程](../planning/reader-review-workflow.md)；本任务只构建新请求并核验已保存旧运行，没有发起新的付费读者调用。

## 单项媒体方案

每项素材按独立交付职责保存唯一 `material_category`（具体素材分类）。系统从此字段自动取得大类、方法及专项文件；物理 `media_type` 校验文件类型，原出处保持不变。分类不由名称、scope 或 Prompt 关键词推断，人不必另选声音类型或 SKILL。

| 素材分类 | 取得的方法与专项 |
| --- | --- |
| 角色图像、场景图像、道具图像、镜头画面 | `image-plan` 共同正文，加 `references/character-image.md`、`scene-image.md`、`prop-image.md`、`shot-image.md` 中对应的一项 |
| 人物音色、场景音、演唱 | 分别取得 `voice-plan`、`scene-sound-plan`、`song-plan`；沿声音专业知识审阅 |
| 视频 | `video-plan`，沿准确视频手册和相邻镜头 |
| 字层 | `text-layer`，交准确文字与可编辑工程，不虚构模型调用 |

类别键依次为 `character-image`、`scene-image`、`prop-image`、`shot-image`、`voice`、`scene-sound`、`song`、`video`、`text-layer`。例如 M2798 是镜头所属的独立角色参考，仍归角色图像；M2977 是首帧，归镜头画面。M2725 虽属角色状态，独立交付清唱片段，仍归演唱。没有独立场景音目标时不新造正式需求。

合法改类后重新开始方法步骤，重取方法、专项和准确输入；旧准备不能混用。条件中的同值旧 `audio_type` 只在输入边界转换，异值明确拒绝，不再保存第二套分类。缺分类、方法、专项文件或不兼容物理类型时拒绝当前执行；旧候选和冻结执行沿原准确组合读取。完整导出、恢复和正式发布还核查全量有效需求，不能把部分迁移当作完成。

先在隔离实例取得准确 REQUIREMENT（素材需求）记录；`record.json` 保留 `object_id`、`kind`、当前 `expected_version` 和完整 `payload`。以下命令均只准备或登记，不生成媒体：

```bash
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step begin --record record.json --run-id my-run --step-id shot-01
# 实际读取目录中的 SKILL.md、references/、shared/、request.json 和 record.json 后创作
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step draft --record draft-record.json
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step read --stage draft
# 保存后实际重读，再写发现、依据和修订判断
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step review --assessment review.md
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step read --stage review
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step finish --record final-record.json --output .runtime/my-media-step/registered.json
python3 scripts/media_method.py --method-url http://127.0.0.1:PORT --directory .runtime/my-media-step read --stage result
```

需要输入锁正文、相邻镜或真实原件记录时，begin 加 `--supporting references.json`，传准确引用数组；包中同时提供可读文档，避免只给修订号。每条外层引用仍受可用性检查；文档内引用历史退役候选仅作为原文保存，不重新激活为本步骤的生产依赖。`--conditions conditions.json` 选择具体章节，如视频的 `{"case":"dialogue","need_sound":true,"need_staging":true}`；不能借条件改变素材分类或物理媒体类型。已冻结请求恢复时，补充材料和选择条件也须保持原样。

媒体 `read --stage draft` 返回完整 requirement/generation 和准确原记录；字层同时返回 `text_layer.blocks/specification` 并核验其摘要；`read --stage review` 返回原 assessment；`read --stage result` 返回定稿原值、带准确 method_basis 的记录及 `import_package`。原提交值与加入 method_basis 后的待导入包分别核验，不能混用摘要。finish 包写入中断后，`recover --stage result --output 原步骤目录/registered.json` 从同一确认结果重建同一包；正常 finish 重试也幂等。输出须在原步骤目录内，已有不同内容或损坏的目标不会被覆盖。旧 draft/result 若缺全文但尚有准确原记录，recover 加 `--record`；旧 review 加 `--assessment`。不存在准确证据时诚实报缺。

`finish` 生成待 `production-import` 的准确包，只有当前内容并发标记、现有制作规则和方法产物摘要同时通过才更新受管方案。目标前进时不要手改 `expected_version` 继续提交；回读新目标并开始新步骤。方法步骤的执行事实不能覆盖，进一步改稿显式新建步骤；制作正文仍写回同一对象，不追加完整稿件。新制作步骤在数据库只保存输入及结果摘要，完整输入和草稿留在任务工作区，完成恢复用途后清理。见 [当前制作与候选](current-candidates/README.md)。

复用与本地编辑沿真实原件、区间和交接保存；没有模型调用就不填 model、tool、Prompt 或随机生成字段。字层可无 generation，但准确文字、SVG 版面及镜头交接不能省略。

生成准备包把方法快照与模型 Prompt 分开。模型只得到方案 Prompt、准确媒体和实际参数；手册不会被拼成最终视频 Prompt。新调用登记必须来自同一准备包，仍检查准确输入、原词、输入锁、渠道、原件与局部范围。已有候选／片段／路线选择记录准确父方案与确定性操作；不补造作者方法历史，也不能夹带 Prompt 修订。

本任务未向 OpenArt、Seedance、Seed Audio 或 Lyria 发起生成。`seed_audio.py`、`lyria_music.py` 的独立实验入口仍保留原账号、费用和恢复边界；它们不自动变成合格生产方案。进入受管制作必须通过准备和 CALL 登记校验。图像／视频 CLI 是外部执行通道，不存在自动生成全剧的服务。

## 正式切换与恢复

沿 [生成工作区流程](generation-workspaces.md) 准备准确双仓候选。在途盘点须覆盖具体工作类型、运行／步骤、冻结输入、待交付内容及后续新步骤，不能按任务创建时间或任务编号永久豁免。

基础任务首次启用采用先完成相关旧交付、再启用媒体约束的切点。后续方法改版只追加定义及绑定，不扩张既有旧方案冻结范围。`scripts/material_review_release.py prepare` 可接受项目内的 `--method-registry` 和 `--method-audit`。审计的 `wait_for_delivery` 逐项检查任务真实完成；正式 apply 同时持有既有发布锁，停止核验过身份的准确 app 容器，检查 3000 与 64401 的评论、准确选择、配置和内容写入口停止后才取得切点快照。停机前已接受的新写入包含在快照中，不用旧任务库覆盖活库。新服务同时提供 API 写入锁，单独持有发布锁仍不足以排除页面写入。

`method_migration.py` 只追加配置历史，并记录启用时库中已有方案的准确修订及摘要。它不新增表、索引或触发器；已启用文件历史时同步相应准确映射。迁移前后逐表比较所有无关数据，只有所选方法记录、其文件历史及可重建读取代号可以变化。作品、评论、准确选择、原件索引和准确历史不能减少或改写。媒体新步骤启用后必须采用相应方法；未知旧历史仍保持未知。

恢复分三件事：

正式迁移先从隔离实例导出配置专用包；它仅含方法、资源和绑定，完整运行包中的启用记录及私有产物不能混入。准备发布包时先检查此边界，避免停写后才拒绝：

```bash
python3 scripts/method_migration.py --system PATH_TO_DESK export \
  --database .runtime/generation/review/.runtime/review.sqlite3 \
  --output content/managed-method-registry.json
```

1. 方法定义包可在空实例恢复同样的正文、版本和引用；目标已经更新时不能覆盖。
2. 完整 Schema 14 导出恢复当前制作、提交快照、故事版本、评论、准确选择、原件索引和公开方法／制作关联；实际原件按哈希保全。私有执行另按原运行范围显式导出，公开作品包不恢复本机阶段全文。
3. 方法约束启用后，本次发布的 `recover` 会拒绝切回启用前镜像：旧代码不能执行新方法约束。运行故障先用本次发布的 `restart` 重启已验证的兼容版本，代码故障则准备兼容修复版本；修复期间需要停写就保持维护窗口。不能改用旧发布包绕过此边界。这些运行操作**不恢复数据库**；如需要数据修正，应在保全新写入的前提下作新的准确变更，不能回灌旧快照。

执行记录证明读取入口交付了具体内容与阶段结果，不能证明模型内部理解。受控请求、独立会话实践、真实页面与付费外部调用分别验收，不互相代替。

当前方法按评论理解、实际修订及准确回查推进，不要求逐对象审批。`scripts/comment_review_methods.py` 追加资源、方法和工作类型绑定；历史方法、冻结执行和真实 CALL 保留原文。本次准确迁移及恢复契约见 [评论流程](comment-review/README.md)。

文件历史首次启用使用 `material_review_release.py prepare --method-file-history`，在既有停写窗口内运行冻结的 `method_file_history.py`。它从所有旧准确整包派生三张文件历史表，逐行保全原业务数据，并校验映射和读取缓存。失败不回灌旧库；启用后只运行支持该历史的代码。完整公开导出携带文件历史，旧公开包在恢复时派生同样映射。私有执行仅显式导出恢复；新执行另带 `file_manifest` 与标准导出的 `file-manifest.json`，旧执行不补写新字段。
