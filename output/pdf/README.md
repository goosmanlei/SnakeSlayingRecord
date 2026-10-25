# 《把灯带回家》完整阅读 PDF

| 作品 | 完整范围 | PDF | 核验记录 |
| --- | --- | --- | --- |
| 剧本版本七 | 17 集、42 场、1,118 个正文块，58 页 | [完整剧本](把灯带回家-完整剧本-版本七.pdf) | [剧本核验](把灯带回家-完整剧本-版本七.verification.json) |
| 小说精修九 | 10 章、622 个正文自然段，39 页 | [完整小说](把灯带回家-完整小说-精修九.pdf) | [小说核验](把灯带回家-完整小说-精修九.verification.json) |

导出日期：2026-10-25。两份均为独立的完整阅读稿，含可点击目录、章节书签和页码；保留对白、动作、演唱与结尾，不加入评论、修改理由或制作日志。

## 来源与验证

剧本使用 [版本七准确正文](../../imports/screenplay-07.json)，与[第二集反馈输入锁](../../production/episode-two-v1-source-lock.json)和任务候选库逐集、逐场、逐块一致。它承接首集修订与本次第二集三个获授权的动作／台词改动；其余正文不因导出变化。版本七是当前任务最新稿，正式库尚为版本六，导出本身不替代发布。保留源稿的分集与分场创作估时，不将估时当作成片实测。

小说使用 [精修九准确正文](../../imports/story-refinement-09.json)，整份文档与正式库最新小说相同；[完整干净稿](../../imports/story-refinement-09-clean.md)也已核对一致。剧本改编没有回写小说。

两份 PDF 均重新打开并全文提取，按空白归一后与准确来源的全部正文、标题和场次信息顺序一致。全部 97 页已渲染并检查版面，另放大检查剧本第 7、58 页及小说第 3、39 页；未发现缺字、重叠、裁切或意外空白页。中文字体已嵌入；69 个书签和54个目录点击区域的目标均已检查。分集、分章另起页，章节末页的留白保留阅读分隔。

PDF 实体在本任务工作区的 `output/pdf/` 可直接打开，原件同时按准确版本保存在项目私有 OSS；Git 保存资源目录和核验记录，不保存 PDF 二进制。恢复方式沿[资源存储](../../production/resource-storage.md)，准确身份见 [resource-catalog.json](../../config/resource-catalog.json)。本次导出未改动作品原文、制作输入锁或正式数据库。

本次页面预览、文字定位中间文件及专用依赖缓存已清理；成品、必要复核资料和任务环境保留至受管交付与工作区退役，实际范围见[清理记录](task-20261022-0001-cleanup.json)。

## 重新生成

从项目根目录运行已有导出器。依赖 `reportlab`；选择含全部原文字形的中文 TrueType 字体。本次使用 macOS 宋体简体常规字重（集合索引 6），A4 纵向、正文字号 11、行距 18；小说段首缩进两字。字体、正文或版式变化后应重新做全文与页面检查。

```bash
python3 scripts/export_screenplay_pdf.py \
  --source imports/screenplay-07.json \
  --output output/pdf/把灯带回家-完整剧本-版本七.pdf \
  --font /System/Library/Fonts/Supplemental/Songti.ttc --font-index 6 \
  --date 2026-10-25

python3 scripts/export_screenplay_pdf.py --kind novel \
  --source imports/story-refinement-09.json \
  --output output/pdf/把灯带回家-完整小说-精修九.pdf \
  --font /System/Library/Fonts/Supplemental/Songti.ttc --font-index 6 \
  --date 2026-10-25
```

导出器只读取指定来源，不自动认定正式版本。写入临时 PDF 成功后才替换目标文件；生成成功仍须完成全文和视觉检查。上述路径已经登记为不可变资源；今后重新生成不同字节时应另用新的交付路径，不能覆盖其云端身份。

历史版本四 PDF 及其[核验记录](把灯带回家-剧本版本四.verification.json)保留原准确资源身份，不作为本次最新稿。
