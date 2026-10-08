# 视频生成手册维护与交付

权威正文是 [视频生成手册](../seedance-video-handbook.md)。研究进度与阻断见项目 `STATE.md` 和主任务账本；没有正式验收记录时，不把任务工作区候选当作正式运行版本。

## 单一正文与阅读子页

`content/production-approach.json` 的 `video-handbook` 子页由权威 Markdown 生成。其余两页继续在原位置维护，派生脚本保留其内容与锚点。命令从故事仓库根目录执行：

```bash
python3 scripts/sync_video_handbook.py
python3 scripts/sync_video_handbook.py --check
python3 -m unittest discover -s tests -p 'test_sync_video_handbook.py' -v
```

手册使用明确的章节注释、二至四级标题、段落、单层列表、围栏代码与表格。原创示例原件唯一存放在 `content/production-approach-assets/`：正文用独立一行的 `![说明](../content/production-approach-assets/example.png)` 引用图片，用 `[说明](../content/production-approach-assets/example.mp4)` 或 `.wav`／`.mp3` 引用音视频。脚本仅把这一固定目录的明确引用转为本地媒体块，同时计算原件 SHA-256；图像和视频的实际宽高从 `production/seedance-handbook/demos/manifest.json` 读取并核对原件摘要，用于提前保留画面占位。清单只记录输入、参数及原件元数据，完整视频 Prompt 仍以手册正文为准。其他嵌入、未支持的结构、重复章节或截断代码块会失败，避免静默丢失正文。生成页保存源文件相对路径和 SHA-256；不得分别手工修改 Markdown 和子页正文。系统只读取实例 JSON 及其中明确声明的原件，不读取研究目录或调用创作脚本。

## 研究材料与审计

三份指定资料以 A、B、C 指代，准确入口仅留任务账本或任务工作区被 Git 忽略的 `.runtime/seedance-handbook/`。正文、修订、读取时点、原件摘要、逐节覆盖、对应章节、来源冲突与缺失资源均在该私有目录维护。原件下载成功、看过概览、逐帧核对与实际听辨分别记录；机器转写或未经验证的模型输出不能代替试听。

受限原件、原案例截图、链接、令牌和完整抓取响应不得进入 Git、公开附件、测试夹具、导出或发布包。正文示例只使用原创虚构内容。提交前审计两仓全部新增／修改文件及截图，核对其不含研究入口、受限地址和原件字节；真实页面检查不能请求研究资源。

## 双仓发布顺序

1. 在已纳管系统工作区完成通用格式、读取、导航与渲染校验，提交准确系统候选。
2. 将其提交写入 `config/instance.json.review_desk_commit`，检查正文派生一致性，再提交故事候选。提交引用约束和清理检查器通过主项目内部回调登记。
3. 通过 `_prepare_integration --push` 固定整组候选。检查是否吸收了新的上游改动；有变化时补验影响范围，不复用已经失效的页面证据。
4. 按 `production/generation-workspaces.md` 使用 `scripts/material_review_release.py prepare/build/preflight` 准备精确发布包。包携带系统代码、正式实例配置／方法 JSON 及正文声明的原创 Demo 原件；按准确提交和原件哈希冻结，发布后只读挂载。不得把研究目录或预览数据库装入发布包。
5. 候选研究、内容、隐私和浏览器验收全部通过后，使用 `_deliver` 受控交付，再按包内摘要 `apply --apply` 串行切换正式服务。`publish-system` 消费原生任务交付回执，不另行手工推送。
6. 核对正式 3000 服务实际系统提交、实例内容和镜像身份，真实 Chrome 重验桌面与窄屏的三页、直接链接、刷新、前进后退、目录、表格和 Prompt。业务库、评论、采用及原件保持由发布脚本逐项保全。全部完成并清理无效过程资源后才调用 `_complete`。

候选检查、实际发布、正式验收和清理回执保存在任务本机运行目录及主账本完成说明。不得为补日志改写已经交付的候选。工作区、必要研究原件与恢复资料按项目结项规则保留；其用途结束后再按准确归属清理，不使用全局缓存清空或 Docker prune。
