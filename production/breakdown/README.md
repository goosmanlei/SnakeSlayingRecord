# 全剧制作拆解与逐镜首稿

本次交付版本四的 **17 集、42 场、297 镜**，含逐镜设计、素材需求、参数、提示词及参考输入方案。预计剪辑时长合计 3026 秒（50 分 26 秒），只是按对白、演唱和动作安排的估时，尚无成片或镜头媒体。第 1 集保留 33 镜及 227 秒的原排练尺度，复核了机位、单镜连续动作、墨耳与对白承接；其余各集按表达需要拆镜。

先阅读 [全剧逐镜首稿](shots.md)，再对照 [连续性自审](continuity.md)及 [逐场逐镜覆盖清单](coverage.json)。每镜正文给出剧情原句及准确块号，构图、调度、节奏与声音处理另标为制作选择。版本四整版修订为 `7287b25a34d4b0db242ec5688f33349fa6d449874a3c6acb30033e2260cd2686`；输入文件及 1114 个正文块见 [来源锁定](../source-lock.json)。本轮没有改写已确认剧本，也没有把歌曲阶段档案的扩词代入版本四。

## 在页面中审阅

隔离实例使用 39117；正式 3000 只有完成最终确认和发布后才应用本候选。

| 入口 | 阅读与操作 |
| --- | --- |
| 制作设定 → 制作拆解 | 左侧选集，中间按场读镜头，点场名或“查看实体与素材”联动右栏。剧情正文默认收起，从准确来源弹窗查看。 |
| 制作设定 → 实体管理 | 阅读实体身份、完整状态、关系与共用素材卡；版本与候选分开选择。 |
| 制作设定 → 素材管理 | 集、场、媒体、生成状态与搜索可组合筛选，每页 40 项；原独立素材入口兼容保留。 |
| 全剧制作 → 镜头制作 | 选集场镜，右侧优先显示本镜视频需求、输入、参数、提示词与候选；显式采用准确候选和文件。 |
| 全剧制作 → 组合与历史 | 保留旧集场、组合及准确修订入口；新的场／集／剧组合编辑另行安排。 |

全剧共用、本集共用只列该范围直接归属的需求。出现、提及、适用、真实调用输入和最终采用分别保存；共用素材不会被推定为每一镜都出现或已经使用。评论和预览沿用同一素材卡，返回保留阅读对象、位置与未提交草稿。后台维护继续使用 HTTP／CLI，页面不增加生成和数据维护表单。

## 方案与原件的边界

每镜都有关键画面、声音参考及视频需求；每场另有调度图，全剧有风格参考。视频默认 `seedance2.0_fast_vision`、720p，超过 15 秒的单次方案采用 `Seedance_2.5`、720p；超过 30 秒的设计列出多次生成段落。图像沿用 `gpt-image-2-5-sunburst`；4K 是请求档位，实际原件仍须检查像素。声音参考的制作渠道、声线／旋律听选及精确时间段尚待确定。

所有新方案都明确列出阻断项。现有图像和声音在 [准确候选目录](reference-candidates.json) 中以不可变候选修订、候选编号、原件与哈希列出；没有替用户默认选最新候选。先选定并采用准确原件，按需固定裁切或时间范围，再形成执行包。本稿完整可审阅，但新镜头方案均未被标为可直接执行。本任务新增调用、媒体候选与用户认可均为零。

本轮将仓院量米木斗独立于米铺木斗维护：原文没有确认两者为同件，不虚构跨场搬运；另将李寄念写歌词与阿蘅低唱分成完整状态。原 132 实体、263 个完整状态范围增加 1 实体和 2 状态，当前有效范围为 133 实体、265 完整状态；旧部分状态与历史不删除。依据见 [新增记录](additional-records.json)与[出现标注修正](occurrence-review.json)。

## 交付文件与恢复

| 文件 | 用途 |
| --- | --- |
| `design.tsv`、`additional-records.json`、`occurrence-review.json` | 人工编写的第 2—17 集镜头、补充身份／状态与旧标注修正；第一集仍以原 33 镜为基础，在编制器中保留明确复核项。 |
| `drafts.json`、`changes.json` | 完整编制输入及相对隔离基线的准确变更；不是模型调用回执。 |
| `shots.md`、`coverage.json`、`reference-candidates.json` | 完整阅读稿、逐场逐镜原文覆盖与现有原件候选目录。 |
| `migration.json`、[迁移说明](migration.md) | 旧轮次逐项映射、评论锚点及证据边界。 |
| `publication.json` | 从本任务冻结基线得到的准确增量；不等同于可覆盖活库的快照。 |
| `../../export/` | Schema 5 完整导出，含历史记录、评论、准确引用与原件清单；用于空实例恢复。 |
| [验证证据](verification.md)、[发布与恢复步骤](operations.md) | 自动检查、真实页面、性能样本及最终确认后的串行操作。 |

命令从故事任务 worktree 根目录执行；系统工作区为 `.runtime/breakdown/system`，隔离候选为 `.runtime/breakdown/review`。重新编制前核对输入与基线，不能盲跑旧任务编制器覆盖当前已审内容：

```bash
python3 scripts/production_breakdown.py --system .runtime/breakdown/system --instance .runtime/breakdown/review
python3 scripts/production_breakdown.py --system .runtime/breakdown/system --instance .runtime/breakdown/review --apply
python3 scripts/generation_review.py --system .runtime/breakdown/system --instance .runtime/breakdown/review export
python3 scripts/verify_production_breakdown.py --system .runtime/breakdown/system --instance .runtime/breakdown/review --run .runtime/breakdown/new-verification
```

第一条只验证数据库写入并输出本机编制文件；第二条只写所选隔离实例。验证目录必须全新。正式业务写入另走准确增量发布。系统 HTTP／CLI、种子规则及 Schema 5 契约见系统仓库 `docs/production-breakdown.md`、`docs/material-versions.md`；具体系统提交由故事 `config/instance.json` 固定。
