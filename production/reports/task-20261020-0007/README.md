# task-20261020-0007：M017 衔接修复与首集换版

本次修复 M016 末态与 M017 开场的人物、群众和空间跳变。M017 采用 M016 完整原片及首集实际切点前的最后一帧作为参考，从同一七人站位开始，在镜头内部推近。用户已明确接受新候选并要求继续应用到首集，准确接受记录见 [user-acceptance.json](user-acceptance.json)。

## 选材与剪辑

新 M017 为 `asset-task-20261020-0007-m017-01@466b5c2e88bcb7c2b99df06b740b4ef3cb67a7bb3eaad7e953350bf5aa4431b9`，原件 SHA256 为 `632e4bb3a02273a4fd6ef3d09661576c8781fc6b030639cbdfca5916f4f41790`。完整使用 432 帧画面与原生混合声音，内容和原速沿用户接受的候选。原生 AAC 声音为 32 kHz、17.92 秒，末尾约 80 毫秒只有画面；派生时间线补足该段时长，不循环、复制或拉伸尾音。

M016 切点保留在第 492 帧，即 20.5 秒。M017 完整延续至第 924 帧，即 38.5 秒；随后 M018 从原片第 0 帧及声音第 0 样本开始。撤去旧版尾腔反应插镜，恢复 M018 原先被该插镜使用的开头 18 帧。后续内容统一顺延 108 帧，即 4.5 秒，成片为 6946 帧、289.416667 秒。

四条 M017 字幕按新原声重新定位；59 条字幕及 7 条片头、片尾、人名条的文字全部保留。其余 21 个来源与 42 个后续声画片段的原件、入出点和处理保持，只有对应时间线位置顺延。准确决定与比对见 [episode-apply-decisions.json](episode-apply-decisions.json) 和 [unrelated-content-preservation.json](unrelated-content-preservation.json)。

## 生成与验证归属

一次小云雀 Seedance 2.5 延展调用生成完整 18 秒候选，没有再次生成。当前接口的首尾帧模式不能同时携带独立音频，因此实际采用 `extend`，尾帧以参考图提交，不声称 API 硬锁了首帧。输入始终是完整 M016、准确第 527 帧及两条完整声音原件；用户截图仅供问题定位。模型、参数、来源、提示词、真实调用与额度观察见 [generation.json](generation.json)。观察到平台积分减少 640，不等同人民币金额；货币费用保持 UNKNOWN。

用户候选接受、执行者静帧检查、实际浏览器播放、模型辅助和技术检测分别记录。两次 Seed Lite 音频定位对尾音及插话时间有分歧，只作字幕定位参考，不据此宣称同一次尾腔重叠已被直接听辨。新片保留用户接受的原生声画；执行者不冒称人耳试听或连续动态感官审片。

隔离环境已验证准确新资产缺失、云端字节哈希不符和过期工程保存均拒绝，旧工程版本保持；恢复准确原件后已成功保存并完成真实 1 秒试渲染。见 [new-asset-fault-test.json](new-asset-fault-test.json)。测试工程只在本任务故障实例中，不进入正式库。

## 已生效的成片与恢复

新成片已受管集成、推送，并通过共享写入窗口增量发布到本机正式库。页面选“生产制作 → 成片剪辑 → 第01集 → 版本 6”，总长 **4:49.417**，可切换对白与唱词字幕／无对白与唱词字幕；两版均保留片名和人名条。准确输出、工程和文件版本见 [delivery.json](delivery.json)。

- [正式成片版本 6](http://127.0.0.1:3000/?workspace=settings.workspace&production_tab=editing&edit_episode=new26-e01&edit_output=episode-film-772dde74be0ec9803315b25aa301766c0fc4e6ab0349bafca173fee9f4a021b7&production_object=episode-film-772dde74be0ec9803315b25aa301766c0fc4e6ab0349bafca173fee9f4a021b7&production_revision=940f53c6463d722f1adf548331b629bc44d9690a6613b2d880346f4f6c37eedc)
- [修复前连续片段](http://127.0.0.1:3000/api/production/files/975326c32d34428c2027b6d132d076833cc68a509a7f67ba1aa4d104044533dc.mp4)／[修复后连续片段](http://127.0.0.1:3000/api/production/files/fa8c945bd7759031fce362eb29235ba8a815a040ba1bfd2aa4a29d814ce96682.mp4)：同一 M016 尾段和 M018 起段，中间分别接完整旧／新 M017。通过正式文件入口播放，不依赖素材大卡路由。

正式发布保留 405 条评论和历史输出；C417 在真实页面仍定位旧样片版本 1 的 30.500–31.250 秒，未迁移或代为重新关闭。旧完整成片版本 5 也已实际播放。新版本 6 的准确 M017 候选 2 大卡、字幕版第一场和无字幕版播放均已核验；播放状态与感官判断分开记录。增量发布、权限与版本核对、运行容器及回退条件见 [formal-publication.json](formal-publication.json)。

发布后从最新正式完整导出取得 Schema 16 快照 `aaf89efbb412366e26e9ad29b7d86ece5143622fdb70925d12b94f2aaa7888ab`，准确私有 OSS 原件已上传并完整校验。用该快照和全部 1,707 个准确资源版本建立临时完整介质，在禁网、无凭据的新空实例实际执行标准恢复。全部业务表、制作索引、三镜、工程、新旧成片、原件绑定与旧评论一致。恢复实例的最新字幕版已从0秒正常速度、有声播放至289.416667秒结束；继续制作验证也已实际保存短段工程并成功渲染，然后恢复完整工程。这些试验未写正式库。详细证据见 [empty-restoration-verification.json](empty-restoration-verification.json)、[recovery-continued-render-verification.json](recovery-continued-render-verification.json)。

用户在看到更新后的首集后明确表示“效果不错，也发布到vps吧”，已接受本次首集版本6，并新增授权将该修订发布到既有 VPS。准确记录见 [user-final-acceptance.json](user-final-acceptance.json)。执行者未冒称自己完成人耳听感或完整运动审美判断；用户接受、模型定位和浏览器技术播放分别记录。

## VPS 后续发布

用户接受本机新版后新增授权，现已将同一个准确增量发布至[公网首集版本6](https://leiguoguo.me/lijizhanshe/?workspace=settings.workspace&production_tab=editing&edit_episode=new26-e01&edit_output=episode-film-772dde74be0ec9803315b25aa301766c0fc4e6ab0349bafca173fee9f4a021b7)。来源提交为 `612a36d49c92929489785961bcc47f5b9eb6be1b`，沿用系统 `4eb4a9ddee541aad0b64d315f023c0021613220a`、同一应用容器和镜像。先在 VPS 自身一致快照预演，再在共享发布／写入锁和维护窗口中提交，没有用本机快照覆盖体验库。

准确增量 `7ff3784ce18a0a1580891ae93a7238e2a65078c65a1a665aac7cce1b223e57ff` 已入事务日志。43张表的范围外记录逐表比较一致，405条原评论保留；新版成片、可编辑工程和114个审阅元素与本机准确对应。公网六种媒体入口的1024字节范围请求返回206并匹配准确OSS版本，工程、字幕和来源映射完整下载的SHA256一致。正式域名两版实际播放、准确M017大卡与旧评论定位沿浏览器回执分别记录。详见 [vps-publication.json](vps-publication.json)。

原完整基线仍是 task-20261020-0009，本次内容增量另记于远端 `state.json` 和 `storage-runtime.json` 的 `content_increment`，不能把旧基线提交误作当前成片版本。网站已恢复开放，凭据、既有配置、调用计数、共享Nginx标记外配置与Xray保持，没有新模型调用。两次运行器启动问题在业务写入前被拦住，修正锁文件创建和Python模块路径后沿同一原件增量完成，失败日志和实际回执保留。

未修改通用审阅系统代码，未重新设计包装或重制无关镜头。正式原件、调用事实、准确版本和必要验收证据保留；本次过程资源的实际清理和保留条件见 [cleanup.json](cleanup.json)。
