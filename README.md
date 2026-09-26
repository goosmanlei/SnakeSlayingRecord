# 李寄斩蛇 · 故事采编实例

本仓库是公开故事实例，不包含审阅台系统代码。系统代码及后续系统迭代在 [story-review-desk](https://github.com/goosmanlei/story-review-desk)；精确版本固定于 [config/instance.json](config/instance.json) 的 `review_desk_commit`。系统已开放故事采编、故事结构阅读审阅和“系统管理 → 系统配置”。本实例已选择方向三《把灯带回家》，当前双轨交付为[故事结构第一稿](http://127.0.0.1:3000/?workspace=story.outline)与[故事精修四](http://127.0.0.1:3000/?workspace=story.sources&source=refinement-04-lantern-home-v4)。两份作品均待审阅，尚未确认进入剧本创作；精修一至三及原评论均保留。

## 资料与出处

当前保留本项目写作的[白话直译与词语说明](export/materials.json)，原文出处仍链接至《搜神记》卷十九。它是现代整理材料，不是古籍底本或改编。两份文言资料、陈峰福州评话外链索引及共用异文图已按任务要求从当前实例清除；Git 历史仍可回溯。故事采编另收录 32 则通俗白话情节素材（其中缇萦为历史叙事、木兰为叙事歌谣，已明确标注）和 3 个并列的原创完整扩写方向。演绎媒体与转写子项已由用户允许取消，不计入本轮交付；用户已于 2026-09-22 确认该任务按调整后的范围完成。

三篇扩写的干净正文可单独阅读：[九女有名](imports/direction-01-clean.md)、[山心水](imports/direction-02-clean.md)、[把灯带回家](imports/direction-03-clean.md)。它们均为七场连续故事和 25 分钟制作估算，用户已于 2026-09-22 确认文字优化完成。方向一、二的评论已关闭，方向三原稿及评论保留。小说独立阅读，不把原梗概的 25 分钟估算当作小说的成片时长；历史清理与验收见 [VERIFICATION.md](VERIFICATION.md)。

[故事结构第一稿](imports/story-structure-01-clean.md)于 2026-09-26 发布，包含方向与主题、人物塑造、人物关系、空间关系、故事线、时间线六部分，以及六张可圈选评论的图示。它明确李寄与阿蘅是从小亲近、姐妹般的旧友，将人物的稳定性格、关系变化和行动动机作为精修四的共同依据。结构稿是正式阶段成果，可以先从全局审阅，再对照小说中的具体场景。

[故事精修四：《把灯带回家》第四版](imports/story-refinement-04-clean.md)依据该结构稿与精修三的 4 条评论，完成十二章、29 个片段的逐段修订。正文 33,761 字符（含标点和章内换行，不含章名）。重点补清对白归属及必要神态，贯通两位女孩从亲近、失信到互救和共同规划以后的关系，并前置李诞、孙六参与救援的交情、顾虑与责任。完整干净稿以独立条目 `refinement-04-lantern-home-v4` 发布。前三版及其分别 16 条、12 条、4 条评论原位保留，未代用户关闭评论。

本故事沿用[小说创作方案](planning/novel-creation-plan.md)与[后台执行流程](planning/incremental-writing-workflow.md)：先整理并发布可审阅的结构图文稿，再依据其具体版本逐段修小说；发现设计与正文冲突时，联动回修。创作工具 [scripts/novel_writing.py](scripts/novel_writing.py)只依赖 Python 标准库，不属于审阅台系统。未完成正文、候选、构想和检查点仅保存在本机工作库；小说只发布完本干净稿，结构稿作为独立阶段成果供审阅。

第四版本机恢复状态：在本仓库执行 `python3 scripts/novel_writing.py --run lantern-home-v4 status`。它以精修三的 29 片段建立基线，再逐段保存、独立回读和采用修订；当前为 `PUBLISHED`。前三版批次分别为 `lantern-home`、`lantern-home-v2`、`lantern-home-v3`。公开克隆可恢复全部正式作品与评论，不恢复私有创作过程。工具独立测试为 `PYTHONPATH=. python3 -m unittest discover -s tests -v`。精修四使用普通 `import-sources` 新增，未使用原地替换接口覆盖旧稿。

通用审阅台支持对 `folk-tales`、`expansion-directions`、`story-refinements` 分类的独立二级菜单；本实例的分类、正文与出处分别保存在 `export/materials.json`，采编输入见 `imports/`。三组默认收起且可独立展开。桌面页面滑至顶栏后，左侧目录与右侧正文各自滚动；切换资料不会把整页拉回顶部，窄屏目录也可内部滚动。评论浮窗可按 Esc、点击窗外或点关闭按钮收起；重新打开时未保存的编辑状态仍在。

## 从公开仓库启动

需要 Docker Compose 和 Python 3.9+（Python 只用于首次恢复与数据 CLI）。克隆两个仓库为同级目录，把审阅台切到本实例锁定提交并恢复业务数据：

```bash
git clone https://github.com/goosmanlei/story-review-desk.git
git clone https://github.com/goosmanlei/SnakeSlayingRecord.git
cd story-review-desk
git checkout 6916f697db9229fedeac3a621536bc82cdfba7eb
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord restore
cd ../SnakeSlayingRecord
docker compose up -d --build
```

打开 [本机审阅台](http://127.0.0.1:3000/)：Nginx 长期运行在 Docker 容器 3000 端口并代理容器内 Python 服务；Nginx 镜像与通用代理规则由审阅台仓库维护，故事仓库只保留实例 Compose 配置。主机仅绑定 `127.0.0.1:3000`。`docker compose ps` 检查状态，`docker compose restart` 重启；`restart: unless-stopped` 保证 Docker 恢复时服务随之恢复。已有 `.runtime/review.sqlite3` 时跳过 `restore`。本机当前系统源码目录名是 `story-review-desk-python`，若在此目录运行，构建命令需加 `REVIEW_DESK_BUILD_CONTEXT=../story-review-desk-python`；公开克隆默认目录名为 `story-review-desk`，无需该变量。不要把 3000 端口转发到公网，本服务没有公网鉴权。

`OPENAI_API_KEY` 默认只在本机启动 Compose 的环境中提供，不提交到仓库；无密钥时其他审阅功能不受影响。系统配置“系统与 AI”可选择评论润色模型、推理强度，并设置润色 API Key 的环境变量名（只保存名称，绝不保存密钥值）。若使用自定义名称，必须用本机、不入库的 `compose.override.yaml` 将同名环境变量透传给 `app` 容器；改页面配置不会自动透传宿主机变量。若本机网络需要私有可信 CA，也可在该覆盖文件中只读挂载 CA 并设置容器 `SSL_CERT_FILE`，不可关闭 TLS 校验。新建或编辑评论有文字即可点 AI 润色，系统自动生成并核验草稿、圈选、故事/创作背景、创作阶段、原文上下文及各版本资料的参考快照；也可单独点击“查看润色参考”。建议必须手动采用、保存。

## Codex 读取与公开同步

本机源数据以 `.runtime/review.sqlite3` 为运行权威；公开仓库的 `export/` 是可恢复的快照。Codex 可从系统仓库运行以下命令读取评论及其原文关联：

```bash
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord comments
```

添加资料时准备 JSON 数组并运行 `import-sources /path/to/sources.json`；字段与 API 契约见[系统说明](https://github.com/goosmanlei/story-review-desk#数据访问与公开同步)。故事结构是“故事创作”下的子页：初始页直接比较、回看和选用扩写方向；Codex 通过 `structure-get`、`structure-review` 读取方向与意见，并以 `structure-import complete.json --expected-version N` 导入完整图文稿。用户确认具体版本后，`script-input` 交接至剧本创作。完整格式、版本和图文评论约束见[故事结构接口说明](https://github.com/goosmanlei/story-review-desk/blob/main/docs/story-structure.md)。配置可通过“系统管理 → 系统配置”修改；`config-get` 和 `objects` 命令可读版本与精确依赖。每次资料、评论、配置或创作稿变化后，从系统仓库执行 `PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord export`，再进入故事仓库执行：

```bash
git add config/instance.json compose.yaml export imports
git commit -m "Sync story review data"
git push origin main
```

公开推送前须审阅评论内容；推送意味着评论也会公开。`export/` 含资料、素材、评论及事件、对象修订/依赖、公开配置及事件，运行凭据与 SQLite 本机库不入仓。评论已锚定稳定对象与精确修订，资料评论仍可用 `source_id` 访问；后续创作稿沿同一账本和导出/校验/同步/恢复协议，不能仅留在本地运行库。

验收记录见 [VERIFICATION.md](VERIFICATION.md)。
