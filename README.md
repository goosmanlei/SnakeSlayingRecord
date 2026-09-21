# 李寄斩蛇 · 原始资料审阅实例

本仓库是公开故事实例，不包含审阅台系统代码。系统代码及后续系统迭代在 [story-review-desk](https://github.com/goosmanlei/story-review-desk)；精确版本固定于 [config/instance.json](config/instance.json) 的 `review_desk_commit`。系统从第一版就采用完整创作框架，目前只开放资料采编和“系统管理 → 系统配置”；漫剧改编留待后续任务。

## 资料与出处

实例目前有三份可独立审阅的文本，全部正文和元数据在 [export/materials.json](export/materials.json)：

1. 《搜神记》卷十九通行整理本原文：完整收录李寄一则，[维基文库来源](https://zh.wikisource.org/zh-hans/%E6%90%9C%E7%A5%9E%E8%A8%98/%E7%AC%AC19%E5%8D%B7)。
2. 《钦定四库全书》本《搜神记》卷十九：保留转录原字及异文，[维基文库来源](https://zh.wikisource.org/wiki/%E6%90%9C%E7%A5%9E%E8%A8%98_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B719)。它和通行本的“东域／东越”“斫／研”“拜其父／指其父”等差异可对照；不把繁简转换或同文转载计作另一份资料。
3. 本项目独立写作的完整白话直译与词语说明：译注是现代整理材料，不是第三个古籍底本，也不是漫剧改编。

[版本对照图](export/assets/edition-comparison.svg)由本项目据前两页原文制作并附来源，非古籍书影。图不计入三份资料。采集日期、版本类型、原文与整理说明在每份资料中明确标注。现存《搜神记》文本为后世辑本，版本字句仍可讨论。

## 从公开仓库启动

需要 Docker Compose 和 Python 3.9+（Python 只用于首次恢复与数据 CLI）。克隆两个仓库为同级目录，把审阅台切到本实例锁定提交并恢复业务数据：

```bash
git clone https://github.com/goosmanlei/story-review-desk.git
git clone https://github.com/goosmanlei/SnakeSlayingRecord.git
cd story-review-desk
git checkout af73e1909c5df225203801dbb35e6700e64c3b1d
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord restore
cd ../SnakeSlayingRecord
docker compose up -d --build
```

打开 [本机审阅台](http://127.0.0.1:3000/)：Nginx 长期运行在 Docker 容器 3000 端口并代理容器内 Python 服务；Nginx 镜像与通用代理规则由审阅台仓库维护，故事仓库只保留实例 Compose 配置。主机仅绑定 `127.0.0.1:3000`。`docker compose ps` 检查状态，`docker compose restart` 重启；`restart: unless-stopped` 保证 Docker 恢复时服务随之恢复。已有 `.runtime/review.sqlite3` 时跳过 `restore`。本机当前系统源码目录名是 `story-review-desk-python`，若在此目录运行，构建命令需加 `REVIEW_DESK_BUILD_CONTEXT=../story-review-desk-python`；公开克隆默认目录名为 `story-review-desk`，无需该变量。不要把 3000 端口转发到公网，本服务没有公网鉴权。

`OPENAI_API_KEY` 只在本机启动 Compose 的环境中提供，不提交到仓库；无密钥时其他审阅功能不受影响。若本机网络需要私有可信 CA，可建立本地、不入库的 `compose.override.yaml`，只读挂载 CA 并设置容器 `SSL_CERT_FILE`，不可关闭 TLS 校验。AI 润色先展示草稿、圈选、故事/创作背景、创作阶段、原文上下文及各版本资料，再由用户发起请求；建议必须手动采用、保存。

## Codex 读取与公开同步

本机源数据以 `.runtime/review.sqlite3` 为运行权威；公开仓库的 `export/` 是可恢复的快照。Codex 可从系统仓库运行以下命令读取评论及其原文关联：

```bash
PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord comments
```

添加资料时准备 JSON 数组并运行 `import-sources /path/to/sources.json`；字段与 API 契约见[系统说明](https://github.com/goosmanlei/story-review-desk#数据访问与公开同步)。配置可通过“系统管理 → 系统配置”修改；`config-get` 和 `objects` 命令可读版本与精确依赖。每次资料、评论、配置或未来创作稿变化后，从系统仓库执行 `PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord export`，再进入故事仓库执行：

```bash
git add config/instance.json compose.yaml export
git commit -m "Sync story review data"
git push origin main
```

公开推送前须审阅评论内容；推送意味着评论也会公开。`export/` 含资料、素材、评论及事件、对象修订/依赖、公开配置及事件，运行凭据与 SQLite 本机库不入仓。评论已锚定稳定对象与精确修订，资料评论仍可用 `source_id` 访问；后续创作稿沿同一账本和导出/校验/同步/恢复协议，不能仅留在本地运行库。

验收记录见 [VERIFICATION.md](VERIFICATION.md)。
