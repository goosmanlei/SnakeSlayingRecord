# 非歌曲素材交付与恢复操作

本任务已产出并登记 369 张新图和 42 份新录音。图像中有至少一张自检合格原件覆盖每个已锁定的 251 个完整状态；探索、返工和已撤回包布目标的原件保留，不能重复计作状态完成。全部原件、真实请求、回执、准确方案与参考、用户认可及评论均在本任务工作区。最终候选尚待用户确认后受控集成；完成和推送结果只以任务账本与运行回执为准。

声音为 40 个基础身份和 2 个声音变化，76 条状态关联中 34 条复用。42 份均为新的可播放 48 kHz 双声道 PCM16 WAV，总长 411.68 秒。四份已有用户听审认可，其余 38 份按用户“全部正式提交，我在系统中做审阅即可”交付，仍待实际听审；Codex 未独立听辨。图像自检、母版认可、用户接受与镜头采用分别保留。

## 审阅与权威位置

路径均相对本任务 worktree。通用系统主仓库由故事主项目定位同级 `../story-review-desk-python`，不能从嵌套 worktree 直接套用这个相对路径。

| 内容 | 位置 |
| --- | --- |
| 用户日常审阅 | [独立素材入口](http://127.0.0.1:64401/?workspace=materials.workspace) |
| 固定母版、末批七项与声音链接 | [生成交接](README.md) |
| 活跃业务库 | `.runtime/full-generation/all-pending/review/.runtime/review.sqlite3` |
| 逐项方案与准确实际调用关联 | [recipes.json](recipes.json) |
| 原件与完整导出 | `export/`，清单 `export/manifest.json` |
| 准确制作修订回放 | `production/replay.json` |
| 本轮逐原件目视／声音核对记录 | [representative-review.json](representative-review.json) |
| 唯一任务状态 | 主项目 `.codex-project`，仅用 `codex.project` 内部命令维护 |

固定链接指定准确原件、素材轮次和需求。页面默认只显示该原件；同轮探索图通过“本轮候选”切换，真实调用、参考和评论同步切换。没有替用户点击采纳，也没有自动采用最新候选。

## 已完成验证

- [完整交付核验](../evidence/full-generation-delivery-verification.json)：411 个成功调用／原件、另外 4 个无原件的输入拒绝调用、251 项覆盖、332 个内置调用的准确计划及认可谱系、42 份音频规格全部通过；最深图生图谱系为两代。
- [空恢复导出](../evidence/full-generation-checkpoint-411-export.json)：1,312 个清单文件、1,255 个制作文件校验；完整业务表恢复一致，原 264 条评论保留，当前 271 条评论、300 条事件。
- [实际浏览器验收](../evidence/full-generation-checkpoint-411-browser.json)：Chrome 在 64405 空恢复实例打开准确八人第四候选和后院第三候选并放大，核对实际参考；点击播放李寄 WAV 至 8.50 秒结束。播放可用性不等于听辨合格。
- 准确候选前端 21 项、参考登记保护 12 项及此前未变范围的检查沿用已有证据；系统交付保护新增 3 项，验证只读预检、准确快进、重复回执、并发目标变化和脏文件拒绝。未在用户库写测试评论。

原生尺寸按真实文件记录。OpenArt 37 次调用使用现有 credits，余额从 9,979 到 77；之后内置渠道只记录工具暴露的 GPT Image 名称和实际输出像素，底层型号、服务端 ID 与用量未知。四次输入超限拒绝没有原件，不计完成。无充值、放大冒充 4K 或新增计费渠道。声音额度与记录见生成交接。

## 重启独立审阅入口

确认 64401 上没有本任务现有服务后，在 worktree 执行；不要终止其他任务的服务：

```bash
PYTHONPATH=.runtime/review-desk-worktree python3 -m review_desk \
  --instance .runtime/full-generation/all-pending/review serve --port 64401
```

使用本机已有 Python 和 FFmpeg；不复制密钥、虚拟环境或依赖目录。当前系统 worktree 分支为 `codex/task-20261002-0003-material-context`，候选为 `5b7de33e77b08c3b9e738d2a140118a333b131c2`。若该检出遗失，从通用系统仓库保留的这个提交重新建立只供恢复的隔离检出；不要恢复覆盖主业务库。

## 从交付包恢复空实例

已有 411 原件核验实例为 `.runtime/full-generation/checkpoint-411-restored`，验收端口 64405。另行恢复时必须使用一个不存在的新目录：

```bash
python3 scripts/production_review.py --system .runtime/review-desk-worktree \
  recover --destination .runtime/full-generation/recovered-delivery-copy
PYTHONPATH=.runtime/review-desk-worktree python3 -m review_desk \
  --instance .runtime/full-generation/recovered-delivery-copy serve --port 64406
```

恢复入口会检查完整清单、制作原件 SHA 和准确对象修订；已有目标会被拒绝。重新核对本机保留的验收快照可执行：

```bash
python3 scripts/verify_full_generation_delivery.py \
  --snapshot .runtime/full-generation/checkpoint-411-export/.runtime/review.sqlite3 \
  --restored .runtime/full-generation/checkpoint-411-restored \
  --baseline .runtime/full-generation/publication/before.sqlite3 \
  --report .runtime/full-generation/recovery-check.json
```

恢复后新增的用户评论继续保存在相应实例，不用旧导出覆盖它们。历史调用已有完成回执，不重新提交给生成渠道。

## 最终本地集成顺序

此顺序只有在展示最终故事候选、以下系统候选、验证和文件范围，并获得用户明确完成与集成确认后执行。用户要求保持独立审阅：本次不向主项目数据库导入任务数据，不重建或切换 3000 服务。**故事 Git 集成会把已跟踪的素材原件和完整归档包写入主分支工作目录**；这项文件影响须与最终候选一起明确确认。工作区审阅入口和活库继续保留。

1. 系统主分支以 `15822ae77d9b6c3851852555a677d11d7adc7c10` 为预期目标，只快进到 `5b7de33e77b08c3b9e738d2a140118a333b131c2`。准确范围见 [system-delivery.json](system-delivery.json)。预检入口 `python3 scripts/integrate_generation_review_system.py` 已通过；目标、候选或受管文件发生变化会拒绝写入。未跟踪的其他工作区不暂存或清理。
2. 用户确认后执行：
   ```bash
   python3 scripts/integrate_generation_review_system.py --apply
   codex.project task _complete -g creative -p SnakeSlayingRecord \
     --task task-20261002-0003 \
     --note '251图像状态均有本轮合格原件；42份新音色已交付，38份按用户要求待系统听审；411原件及完整空恢复、原评论保留、Chrome图片放大和音频实播通过；保留独立入口，仅本地集成。'
   ```
3. 系统回执写在 `.runtime/full-generation/system-integration/receipt.json`。如果系统已快进而故事集成暂未完成，保护脚本按相同候选可恢复，不重写旧回执。故事 `_complete` 自行复查候选与目标；变化影响确认时重新准备、补验和确认，不自行覆盖。
4. 本次未申请推送，两个仓库均不推送。不执行旧的主库增量发布脚本，不重复导入本轮登记，不撤掉工作区素材挂载。没有服务切换，已通过且输入未变的页面验证复用；仅发生实际发布变化才做对应一次验收。

确认前的过程提交保留。完成成功后只回读与报告，不补写文档、提交或推送；后续修改重新准备交付。正常退出会话后释放任务运行锁，工作区和分支保留。

