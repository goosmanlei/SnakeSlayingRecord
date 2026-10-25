# Docker 残留清理：2026-10-25

本机 `desktop-linux` 中已核实的残留已清理。当前保留审阅台、Nginx、RiskEval 三个正式容器及其镜像，以及审阅台上一版回退／构建基底镜像；没有停止容器、无标签镜像、构建缓存或数据卷残留。

## 实际删除

| 类别 | 本次删除 | 删除后 |
| --- | ---: | --- |
| 停止的旧审阅台容器 | 2 个 | 仅保留 3 个运行中的正式容器 |
| 无有效引用的旧镜像 | 6 个 | 保留 4 个镜像 ID，共 5 个标签 |
| 未被构建占用的缓存 | 439 条 | Docker 统计从 23.36 GB 降至 0 |
| 数据卷、网络 | 0 个 | 无数据卷；保留 3 个 Docker 默认网络和 2 个正式服务网络 |

六个镜像为五个被后续正式版本替代的审阅台旧镜像，以及无容器引用的 `nginx:1.27-alpine` 上游镜像。删除按准确 ID 执行，容器未使用强制删除，镜像使用 `--no-prune`，缓存使用冻结的 439 个 ID 过滤；未运行全局清理命令。准确名单见[清理回执](cleanup.json)。缓存过滤语义依据 [Docker 官方说明](https://docs.docker.com/reference/cli/docker/buildx/prune/#provide-filter-values---filter)。

核对期间，`ma-research-worker:20261021`、`cloudflare/cloudflared:latest` 和 `python:3.12-slim` 已被本次执行之外的操作删除；Docker 事件与准确 ID 回读均确认不存在。这三个镜像不计入本次删除数量。

Docker 的镜像占用统计从删除前的 2.36 GB 降至 1.45 GB。这里 GB 为十进制单位，缓存与镜像可能共享底层内容，不能将两项差额相加作为宿主机实际释放空间；本次没有测量 Docker 虚拟磁盘文件的物理缩减。

## 正式服务与恢复保护

| 保留资源 | 用途 |
| --- | --- |
| `snakeslayingrecord-app-1`、`story-review-desk:current` | 当前正式审阅台 |
| `snakeslayingrecord-nginx-1`、`snakeslayingrecord-nginx:latest` | 正式入口代理 |
| `riskeval-prompt-risk-eval-1`、`riskeval-prompt-risk-eval:latest` | RiskEval 正式服务 |
| `story-review-desk:previous`、`story-review-desk:base` | 上一版准确回退与构建基底；两个标签指向同一个镜像 |

在既有集成、发布和镜像标签锁内完成删除与最终验证。三个正式容器的 ID、镜像、启动时间、挂载、端口和网络保持一致，没有重启；审阅台和 RiskEval 保持 healthy，Nginx 未配置 Docker 健康检查。审阅台首页、实例 API 与 RiskEval 健康 API 均返回 HTTP 200。四个保留镜像的标签与文件层未变。

正式数据库、运行身份、导出清单及当前／上一版存储发布配置，共 13 份保护文件的完整 SHA256 未变。未操作媒体原件、恢复介质、Git LFS、任务归档或远端服务。此次验证覆盖清理后的服务与数据保全，不包含新增页面交互或作品感官验收。

初次清理后校验曾因容器对象比较不一致退出，未重复执行任何删除。紧接着逐字段回读未发现差异，最终按挂载目标排序后完成容器身份、启动时间、健康、文件哈希及准确删除结果的独立复核；未将该校验异常推定为服务故障。

## 追溯记录

本机最小记录位于项目内 `.runtime/task-receipts/docker-cleanup-20261025/`，包含冻结删除清单、逐项操作、缓存删除输出、前后清单与最终验证；不包含被删除内容的备份。维护者在不再需要解释本次删除或保留边界时，可按项目清理规则移除这组审计记录。此次使用的项目内 Buildx 配置和空临时目录已清理。
