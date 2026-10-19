# VPS 完整体验版发布

入口为 `https://leiguoguo.me/lijizhanshe/`，远端实例为 `vps:~/www/lijizhanshe/`；发布工具、服务端凭据、阶段回执和累计 AI 调用次数统一保存在 `vps:~/lijizhanshe/`，独立于实例目录。体验库可真实写入，普通重启及代码／存储升级保留其自身数据与发布身份，不与本机互相覆盖。历史完整重置需求见 [部署任务](../planning/vps-experience-deployment-task.md)，当前存储升级边界见 [资源存储](resource-storage.md)。以下命令从当前受管故事 worktree 根目录执行。涉及系统修改时，系统代码使用同一任务纳管的 desk worktree；仅部署已正式交付版本、且任务明确系统源只读时，可通过 `--desk` 消费已核验真实路径的系统源。后者须在构建前后确认准确提交与干净状态，不 checkout、不修改共享源，也不为只读构建手造附属工作区。

## 域名 HTTPS 与证书续期

`leiguoguo.me` 的根域名 A 记录使用 Cloudflare **DNS only（灰云）**，网站流量直接访问 VPS；Cloudflare 继续提供 DNS。此设置作用于主域名的所有路径，邮箱记录独立维护。源站使用 Let’s Encrypt 根域名证书，普通浏览器可以直接验证，无需信任 Cloudflare Origin CA。

VPS 通过官方 Certbot snap 与 HTTP-01 网站验证管理证书。证书原件位于 `/etc/letsencrypt/live/leiguoguo.me/`，`snap.certbot.renew.timer` 定期检查续期。成功续期后，`/etc/letsencrypt/renewal-hooks/deploy/20-leiguoguo-nginx` 校验证书域名、有效期及公私钥匹配，持有体验版 `~/lijizhanshe/publish.lock` 发布锁，将证书链和私钥更新到 `~/my-config/nginx.me.leiguoguo/ssl/letsencrypt.crt`、`letsencrypt.key`，测试 Nginx 配置并平滑重载。容器沿用整个 `ssl` 目录的只读挂载，私钥不进入网站根目录或 Git。

共享 Nginx 的 80 与 443 端口均保留 `/.well-known/acme-challenge/` 路由，对应宿主 `~/www/.well-known/acme-challenge/`。普通 HTTP 请求继续跳转 HTTPS。发布脚本只替换体验版标记内的配置；维护时须保留标记外的验证路由和证书配置，以及脚本所需的唯一 `location / {` 接入位置。

以下命令在 VPS 上执行，分别检查定时器、演练续期与证书部署、查看当前证书：

```bash
systemctl status snap.certbot.renew.timer --no-pager
sudo /snap/bin/certbot renew --cert-name leiguoguo.me --dry-run --run-deploy-hooks --no-random-sleep-on-renew
sudo /snap/bin/certbot certificates
```

演练使用测试签发服务，部署钩子使用当前有效正式证书，不把测试证书装到线上。维护后仍需用普通域名访问确认 DNS、HTTPS 与页面正常，不能只凭配置测试通过判定生效。依据：[Certbot 续期与部署钩子说明](https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates)及 2026-10-09 服务器和 Cloudflare 配置回读。

## 发布前准备

先完成实际纳管仓库的最新主干同步与候选提交，核对系统源及 `config/instance.json.review_desk_commit` 的准确引用，通过 `codex.task _prepare_integration --push` 准备候选。只读系统源不加入可写交付组；其本地／远端主干、运行身份和构建提交仍须匹配。正式发布前由任务工具完成 `_deliver`，不要在主目录手工合并或推送。

远端复用 SSH 别名 `vps`、`nginx.me.leiguoguo` 容器与 `nginxmeleiguoguo_default` 网络。先回读架构、实际可用内存、磁盘、Xray、Nginx、已有实例、容器挂载和正在进行的发布。脚本在预检及进入维护前再次核对 x86_64、cgroup v2、至少 1.5 GiB 可用内存与 0.5 GiB 空闲 swap，以及既有 Xray、Nginx、网络和配置、网站根目录两个只读挂载的真实身份；余量不足时停止新增负载。磁盘按上传包三倍加 5 GiB 余量校验。脚本只管理本实例，拒绝符号链接、其他应用占用的容器名及未完成的另一发布；不购买资源、不增加 swap、不重启 VPS、不使用全局 prune。

用户已明确允许使用 VPS 现有 `OPENAI_API_KEY`，它与本机使用同一密钥。现有变量只在交互式 shell 加载；维护者在服务器内将其写入 `~/lijizhanshe/credentials.env`，目录权限 700、文件 600，不回显或经本机转存密钥。文件采用 Docker env-file 格式，设置 `OPENAI_API_KEY`、`REVIEW_POLISH_DAILY_LIMIT=100`、`REVIEW_POLISH_BUDGET_TIMEZONE=Asia/Shanghai`。不把密钥写入 Git、业务库、发布包、浏览器或命令参数。

AI 出网按用户 2026-10-09 的明确要求使用 VPS 自身 Xray 回环 HTTP inbound。当前入口为 `http-local`、`127.0.0.1:9090`，账户沿服务器现有受保护 Xray 配置取用；只在服务器内将编码后的认证代理 URL 写入同一 env-file 的 `HTTPS_PROXY`，另设 `REVIEW_USE_XRAY_LOOPBACK=1`。不回显代理认证信息。标准库的 OpenAI HTTPS 请求读取此变量，公网网站入口仍直接访问本站。每次发布前核对 Xray 监听和实际 Docker 桥接网关。

容器自身回环地址不能连接宿主回环入口，因此此模式使用宿主网络，但应用仅绑定现有 Nginx Docker 桥接网络的准确私有 IPv4 网关及 8765 端口。发布器拒绝公网地址、错误网络和其他服务占用，并核对实际启动命令与代理变量；Nginx 只在本实例前缀代理到该私有地址。Xray 现有配置、监听与服务保持原样。没有启用该模式的部署继续沿原容器网络运行。

用户授权北京时间每天最多 100 次 AI 润色请求。计数保存在同目录 `usage/attempts.json`，失败或结果未知的实际请求也计数；发版与普通重启都不清零当天次数。仅跨北京时间日期时恢复当天预算，累计总次数仍保留；达到上限时拒绝 AI 请求，其他操作和发布仍可继续。调整上限须依据新授权。未配置真实凭据时不能把 API 禁用或模拟称为完整体验版。

用户 2026-10-09 明确要求完全开放体验，`/lijizhanshe/` 不设置访客登录或 Nginx Basic 认证。页面和 API 走应用反代，普通媒体由应用核验后签发准确 OSS 地址，显式下载由应用通过准确缓存提供附件；数据库与服务端凭据不通过静态根目录暴露。每日次数限制费用，不是访客授权机制。

## 保留业务数据的代码与存储发布

已接入 OSS 的实例使用 `oss_runtime_release.py`。旧 `vps_experience.py` 全量重置入口只适用于历史未迁移实例；它不能用于更新当前体验库。原全量发布的回执仍保留原义，不作为本次存储升级步骤。

双仓受管集成前先提交候选、固定系统 pin，构建 `linux/amd64` 镜像，并在镜像标签 `org.opencontainers.image.revision` 写系统准确提交。以下变量均指本次已核验的任务路径与镜像，不包含凭据值：

```bash
python3 scripts/oss_runtime_release.py prepare \
  --story "$STORY_WORKTREE" --desk "$DESK_WORKTREE" \
  --image "$CANDIDATE_IMAGE" --output "$RELEASE_BUNDLE"
```

准备器核对提交中的配置、完整系统源码及发布脚本；包仅包含代码身份与轻量资源配置。镜像按配置及有序文件系统层摘要固定，兼容本机 Docker Desktop 的索引 ID 与 VPS 载入后的配置 ID 不同，实际运行一律使用已核验的镜像 ID。通过 SSH 的既有 `vps` 别名传输包和 `docker save` 镜像，核对传输 SHA256、加载后的身份与架构；上传超时先查已到达文件，不重复创建发布。

运行凭据是项目级 RAM 文件，位于远端实例目录和发布包之外，目录 700、文件 600。它只向本项目应用只读挂载为 `/run/project-oss.json`，不会更改既有 AI 凭据、Xray 或每日次数预算。主干受管 `_deliver` 完成后，在远端执行：

```bash
python3 "$RELEASE_BUNDLE/oss_runtime_release.py" apply \
  --bundle "$RELEASE_BUNDLE" --instance "$HOME/www/lijizhanshe" \
  --credentials "$OSS_CREDENTIAL_FILE" --environment vps
python3 "$RELEASE_BUNDLE/oss_runtime_release.py" finalize --release "$EXACT_RELEASE"
```

`EXACT_RELEASE` 取 apply 的真实回执。apply 持 `~/lijizhanshe/publish.lock`、实例发布锁和容器内 HTTP 写入锁，核验本实例标签、真实挂载、网络与限制，正常停止应用，并拒绝存在排队／运行中渲染的切换。它保存该 VPS 自己的一致性数据库备份，核对全部业务表、资源闭包、独立发布身份及 `usage/attempts.json`，随后替换镜像和资源配置。它不安装本机数据库、不清空实例、不重启共享 Nginx／Xray／VPS，也不修改 TLS 和其他站点。

正常运行沿用 1 CPU、1 GiB 内存、1.5 GiB 内存与 swap 总限额、64 进程及三份 10 MiB 日志限制。原渲染 worker 与代理环境继续启用。媒体原件转到 OSS，数据库和正常有界缓存保留在 VPS；资源的 8 GiB 上传、范围读取及缓存规则见 [资源存储](resource-storage.md)。

## 中断、恢复与长期入口

所有超时先查准确回执、容器实际 ID／状态和锁持有者。未开放的切换可执行：

```bash
python3 "$EXACT_RELEASE/oss_runtime_release.py" rollback --release "$EXACT_RELEASE"
```

恢复只切回准确旧容器与配置，不回灌旧数据库。发布器在释放 HTTP 写入锁前，持久化 `opening` 阶段并安装旧全量部署入口的保护；从这一阶段起，新服务可能已接受修改，不再自动回旧代码。若回执停在 `opening`，执行同脚本的 `resume --release "$EXACT_RELEASE"` 核对新服务并收尾释锁，再执行 finalize。已经开放的服务通过兼容的向前发布修复。

永久入口为 `~/lijizhanshe/storage-runtime.json` 和 `storage-releases/<准确提交>/`。finalize 回读固定容器名、准确 ID、镜像与发布标记，更新 `state.json` 的当前代码／镜像字段，保留原 `publication_id`、累计调用计数及体验数据。`vps_experience.py status` 仍可查询；旧全量写入命令看到 `storage_upgrade` 会拒绝执行。临时进程日志不承担运行身份权威。

## 验收与收尾

存储升级分别验证本机和 VPS 的准确业务表、最新修改、发布身份、累计调用次数与共享服务前后状态。两端实际 Chrome 从空媒体缓存打开图文、素材、历史候选、成片、评论定位及下载；请求须证明使用准确 OSS 版本。正式读路径不写测试评论。签名失效、上传中断、缓存损坏及恢复后编辑／渲染在私有实例验证。

在线新 clone 空库恢复与 Git 外完整介质禁用 OSS 网络恢复各自验收，不用一次成功代替另一种。介质和必要回退的真实位置、摘要、用途与解除条件记入本次回执。业务审阅、生成效果与用户接受不能由工程检查代签。

成功后清理本任务准确归属的测试对象、临时容器、镜像和重复媒体；保留正常缓存、正式原件、准确历史、独立恢复介质及仍有有效回退用途的上一容器。别的任务仍在使用的文件不删除，未清项记明归属与条件，不运行全局 prune。退出会话并释放挂载后，通过 `codex.project task cleanup` 退役受管工作区。
