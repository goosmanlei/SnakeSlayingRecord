# V1 验证记录

2026-09-21，本机主实例入口 `http://127.0.0.1:3000/`，Nginx 容器代理 Python 容器。系统版本固定为 `0668bdb8cc179aaf53fe20e3df894465dc30d2bc`。所有结果只表示本机与本次公开快照，不代表公网部署。

| 验收点 | 观察到的证据 |
| --- | --- |
| 整体框架 | 浏览器左栏显示当前工作、故事创作、故事设定、素材管理、全剧制作、系统管理；未实现工作区明确“待开放”。系统 `docs/architecture.md` 记录对象/修订/依赖、阶段与配置边界。 |
| 资料与图片 | 浏览器显示 3 份有实质差异的资料：通行本、四库本、白话译注；正文完整，出处、链接、采集日期和“原文/整理”类型可见；可追溯 SVG 对照图载入。 |
| 评论闭环 | 浏览器验收过圈选、保存、编辑、关闭、重开、草稿保留；当前保留 1 条验证用途评论，锚定“东越闽中，有”。原位迁移后增加对象 ID 与精确修订 ID，旧评论事件 4 条均保留，数据库 `foreign_key_check` 为零错误。通用对象评论在隔离单测中跨修订仍关联旧正文，不静默移位。 |
| 系统配置 | 浏览器“系统管理 → 系统配置”显示 SYSTEM/PROJECT/LOCAL；PROJECT 创作背景通过页面保存，版本由 1 升至 2，刷新后保留；SYSTEM 版本 1，LOCAL 仅展示 AI 密钥是否配置，不展示密钥。 |
| AI 润色上下文 | 浏览器先展示故事/创作背景、故事采编阶段、圈选及相邻段落、3 份资料全文和上下文哈希，才启用真实 AI 请求。容器通过本机 CA 只读挂载完成 TLS 校验，真实请求返回“尚未保存”建议，原评论未改；模型建议含额外想法，未替用户采用。 |
| Docker 入口 | `docker compose ps` 中 Python 服务健康、Nginx 绑定 `127.0.0.1:3000`；两服务均设 `restart: unless-stopped`。执行 `docker compose restart` 后浏览器重载仍见 3 份资料和 1 条评论，`/api/comments/context` 返回原句与资料修订哈希。容器使用故事目录绑定卷保存 SQLite；证书校验未关闭。 |
| 自动测试 | `python3 -m unittest discover -s tests -v`：4 项通过，覆盖 Unicode/跨块/并发、旧评论迁移、配置和 AI 请求内容、对象修订评论跨版本关联、完整导出恢复/复导出一致性及篡改拒绝。`node --check` 和 `git diff --check` 通过。 |
| 导出内容 | Schema 3 manifest 计数：3 资料、1 评论、4 评论事件、3 对象/修订、2 配置及事件；`materials.json`、`comments.json`、`objects.json`、`configurations.json`、SVG 均有 SHA-256。 |
| 双仓公开同步 | `gh repo view` 回读 `goosmanlei/story-review-desk`、`goosmanlei/SnakeSlayingRecord` 均为 `PUBLIC`；系统提交 `0668bdb` 已推送，故事实例正在同步对应版本锁与 Compose 配置。 |
| Schema 3 公开干净恢复 | `/tmp/snake-review-v3-Dz2FNT/` 已验证数据快照在系统 `d0bec7f` 下恢复与复导出无差异。系统随后将 Nginx 通用入口归仓升级为 `0668bdb`；需用最终版本锁再做一次公开克隆恢复。 |

验收边界：长期运行状态和浏览器效果在本机核验；公开同步验证到 GitHub 的仓库可见性与提交，未部署到公网。测试评论是验证数据，不能当作用户意见。

后续用户评论公开同步前应审阅正文；AI 建议可能偏离原意，只在用户手动采用并保存后进入业务数据。
