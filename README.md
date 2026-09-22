# 李寄斩蛇 · 故事采编实例

本仓库是公开故事实例，不包含审阅台系统代码。系统代码及后续系统迭代在 [story-review-desk](https://github.com/goosmanlei/story-review-desk)；精确版本固定于 [config/instance.json](config/instance.json) 的 `review_desk_commit`。系统已开放故事采编、故事结构阅读审阅和“系统管理 → 系统配置”。三个漫剧扩写候选留在故事采编并列审阅；**本实例尚未选定真实改编方向，也没有真实结构稿或创作确认**。

## 资料与出处

当前保留本项目写作的[白话直译与词语说明](export/materials.json)，原文出处仍链接至《搜神记》卷十九。它是现代整理材料，不是古籍底本或改编。两份文言资料、陈峰福州评话外链索引及共用异文图已按任务要求从当前实例清除；Git 历史仍可回溯。故事采编另收录 32 则通俗白话情节素材（其中缇萦为历史叙事、木兰为叙事歌谣，已明确标注）和 3 个并列的原创完整扩写方向。演绎媒体与转写子项已由用户允许取消，不计入本轮交付；用户已于 2026-09-22 确认该任务按调整后的范围完成。

三篇扩写的当前干净正文可单独阅读：[九女有名](imports/direction-01-clean.md)、[山心水](imports/direction-02-clean.md)、[把灯带回家](imports/direction-03-clean.md)。它们已导入正式审阅台，均为七场连续故事和 25 分钟制作估算；用户已于 2026-09-22 确认本轮文字优化完成，但尚未选定最终方向。方向一、二的评论已于 2026-09-23 全部关闭；方向三原稿及其评论保持不变。基于方向三十条当前评论重构的独立干净稿见[故事精修一：《把灯带回家》第一版](imports/story-refinement-01-clean.md)，它位于审阅台“故事精修”二级菜单，供下一轮审阅。用户允许通过删除旧资料替换，因此旧《山心水》的一条评论及旧修订不再在当前实例中；历史内容仍可从 Git 记录追溯。

通用审阅台支持对 `folk-tales`、`expansion-directions`、`story-refinements` 分类的独立二级菜单；本实例的分类、正文与出处分别保存在 `export/materials.json`，采编输入见 `imports/`。三组默认收起且可独立展开。桌面页面滑至顶栏后，左侧目录与右侧正文各自滚动；切换资料不会把整页拉回顶部，窄屏目录也可内部滚动。评论浮窗可按 Esc、点击窗外或点关闭按钮收起；重新打开时未保存的编辑状态仍在。

## 从公开仓库启动

需要 Docker Compose 和 Python 3.9+（Python 只用于首次恢复与数据 CLI）。克隆两个仓库为同级目录，把审阅台切到本实例锁定提交并恢复业务数据：

```bash
git clone https://github.com/goosmanlei/story-review-desk.git
git clone https://github.com/goosmanlei/SnakeSlayingRecord.git
cd story-review-desk
git checkout 779f3323137ff82d5b29bb29f3de8b508dab9c44
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
