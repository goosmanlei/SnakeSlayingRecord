# 便携证据选择与脱敏：独立审查

**已修正当前实证的6份守卫回执漏脱敏；本次不等于最终包验收。** 脚本尚未执行真实打包，未输出或发布包含守卫摘要的交付包。独立审查者只读取源码、枚举选入文件、做内存变换与元数据核对，全部审查输出留在 `reviews/`；未读取数据库、调用服务或修改产品/打包脚本。

初版脚本 SHA 为 `bf76519a6411294eaae6c7bac6e0712e1f8bd2e8e5155ed67d473e23ba71a008`；本报告复验版本为 `bf82f85a1b8583f579d0c59c2ef88fb0d601d4b0bf739e7d74a5c3e10a1645bb`。后续源码或最终日志变化需按差异增量核验，不能沿用本次有限扫描声称未来所有文件安全。

## 已查明并复验的实际缺口

初版仅对固定 clock 名单脱敏，后台目录整体原字节入包。当前选择中6份 JSON 含非空真实 `lease_digest`：

- `backend-investigation/ao-perf-001-ab-guard-before.json`、`ao-perf-001-ab-guard-after.json`。
- `backend-investigation/ao-perf-002-guard-before.json`、`ao-perf-002-guard-after.json`。
- `backend-investigation/write-ab/reset-window-01/guard-before.json`、`guard-after.json`。

独审仅输出路径、字段名、类型及长度64，没有输出摘要值。使用当前/原窗口 state 中的摘要在选入字节中精确核对，命中同6份；不存在“只因字段名出现便推断真实泄露”的混淆。根在打包前改为对所有选入 JSON/JSONL 递归脱敏、对文本中的带引号凭据键/值脱敏，并记录发生字节变化的来源/产物双SHA。

修正版对上述6份真实文件的内存复验确认：lease_digest 变为 `[REDACTED]`，真实值不再存在，其他数据完全等于递归脱敏的预期结构；再次 sanitize 字节不变。9份实际 clock 输入经过既有首轮映射与全量二次 sanitize 后均未再变化。加上无敏感键 JSON 字节保留、JSONL按行变换与空行保留、Python repr 文本、SQLite魔数拒绝，共31项检查通过。原文件未改写，未压缩任何实际包。

独审当前原始选择快照为2373份文件、353,170,927字节；其中没有SQLite文件头、选入symlink或常见数据库/密钥容器后缀。此为扫描时快照，不是最终产物数量。随后专项检查325份 `.log/.txt/.md/.jsonl` 及明确文本补充文件，共11,274,033字节、64,541行，含旧窗口报告、恢复文本和Schema6的CLI日志：没有当前或原窗口守卫摘要，没有带值凭据字段命中，JSONL均可解析。文本规则不等于通用秘密识别器，未来新增日志仍须重新扫描。

## 源码审查结论

当前方向正确：按明确证据目录选择，保留失败与异常原件；不递归带走Schema6源/恢复库和媒体树；gzip/tar固定时间且排序，未改变的输入字节保持不动；每份条目及各压缩包都记录SHA。新增数据库后缀、环境文件、依赖目录排除，并在写包之前拒绝SQLite魔数。未知JSON解析失败也会在压缩前终止，避免静默遗漏。

以下几点应在最终交付前收口：

| 项目 | 当前事实与影响 | 最小建议 |
| --- | --- | --- |
| clock的双重变换归属 | 现有9份二次不变，因此当前真实manifest链不矛盾。但合成“clock字符串内有凭据文本”会触发二次变换：首条artifact SHA指向中间字节，第二条source写成clock路径，该路径不是原始runtime来源 | 每个最终artifact只保存原source→最终artifact的一条变换；或显式标注中间链，保证最终hash可直接对到tar条目 |
| 无变化也标redaction | 实际 `startup-recovery.json` 和旧 `stop-receipt.json` 首轮字节没有变化，仍登记“redaction; not raw copy” | 区分路径重映射与实际字节脱敏；只对真实变换写脱敏说明，保留准确来源映射 |
| 显式补充文件的排除规则 | 通用目录走allowed，固定supplement和旧报告只判断is_file；当前扫描没有这类symlink | 所有来源统一走allowed，避免脚本声称的“不带symlink”仅覆盖部分分支 |
| 重跑后的陈旧readable | 脚本不清理readable，之前存在而本次不再选入的文档会留下；manifest只列archive内容，不列这些遗留副本 | 每次从全新交付暂存目录构建，避免残留已撤回/过期解释；完成后核对可读副本与最终条目 |
| 失败时保留最近完整包 | 三个archive逐个replace，readable在压缩过程中写，manifest最后写；后半失败会留下新旧混合输出 | 新同级暂存目录全部成功并验证后再发布；失败只保留未发布暂存和最近完整交付，不覆盖已验收包 |
| 便携阅读入口 | 当前readable只直接复制MD及clock，MD链接的JSON/图片须解压才能找到；主planning报告仍有runtime链接 | 根已提出把三个archive解压至readable以还原相对结构，并把主报告改为固定便携路径。最终须提供解压/校验说明并实际验证入口和链接 |

其中前两项由合成内存输入和现有9份clock原件共同界定，不把潜在二次变换说成当前已经出现的错误hash。排除规则和重跑问题属打包脚本边界，当前没有发现已有包混合或外发。建议按当前已授权的交付工作收口，不引入新的发布权限流程。

## 读者入口与证据核对的最小验收

最终正式报告正文应能独立解释已改、未改、收益和限制，路径指向受管便携入口。读者不应必须拥有这个工作区的 `.runtime/` 或本机绝对路径才能理解结论。原始证据可以保持绝对路径作为当时环境事实，但可点击的本地链接应指向包内准确条目；改写副本或脱敏产物须标注变换，不能冒称原字节。

根提出的“先阅读MD，再将三个archive解压至readable以打开原始JSON/PNG”方案可行，条件是：入口说明所需命令与相对基准目录；三个archive条目路径无冲突且与manifest逐项一致；解压后JSON、截图和来源文档相对链接确实可打开；clock重映射的state/回执链接指向实际 `clock/...` 文件；旧报告中的历史本机路径如保留，应明确它是原始快照，当前读者使用旁边的来源映射。

最终成包后建议一次性只读验证：压缩包SHA、条目数量和逐条大小/内容SHA都与manifest一致；脱敏条目最终SHA能对应原source与转换说明；SQLite魔数/排除路径及实际守卫摘要在产物中无残留；三个包解压至空目录后检查可读文档的相对链接。该验收不需要重跑浏览器、性能或Schema6恢复。本代理本轮没有执行它，亦未做全量打包。

## 审查产物

- [delivery-selection-audit.json](delivery-selection-audit.json)：初版实际原始选择、已确认6份漏脱敏；只含字段位置及长度。
- [delivery-text-credential-audit.json](delivery-text-credential-audit.json)：325份文本/日志/JSONL专项扫描，逐份SHA、无值结果及限制。
- [delivery-sanitize-review.json](delivery-sanitize-review.json)：修正版31项内存验证、六份双SHA、九份clock映射、潜在两次变换的合成复现。
- 相应 `.py` 和 `.log` 同目录，均未调用builder的main。脚本导入会生成本地Python字节码，该目录被打包规则排除；没有写入受管产品。

当前可以继续准备便携入口和打包收尾，但“最终包可读、无凭据且manifest完整”必须以最后冻结输入下的实际包检查为准。本审查不授权集成、推送或正式服务切换。
