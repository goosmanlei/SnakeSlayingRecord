# 本轮证据入口

任务 `task-20261005-0001`。先读[完整运行报告](../../autonomous-optimization-run-report.md)与[交付和解压校验说明](../../autonomous-optimization-delivery.md)。这里保留原始成功、失败及中断记录；早期独审结论被后续证据修正时，以完整报告的明确替代关系为准。

独审说明在 `readable/` 中提供原字节副本，便于直接阅读；其中原有 JSON、截图及相对链接须先把三个压缩包解压到同一个空目录再查看。下方逐项入口给出包内准确路径，避免依赖本机 `.runtime/`。旧窗口报告及历史提案保留原工作区／仓库链接，须按manifest来源映射或项目文档定位，解压不会自动修复这些历史路径。不按历史端口假定服务仍在线。

## 压缩包与校验

| 文件 | 条目数 | 字节 | SHA-256 |
| --- | ---: | ---: | --- |
| [browser-records.tar.gz](browser-records.tar.gz) | 1859 | 44815674 | `990e0d539426dee53e338ce08930701671996f14bb9f5eddd2e293d6fcaadf3a` |
| [backend-records.tar.gz](backend-records.tar.gz) | 774 | 4977942 | `ca465b26be942957ad157581d0d73d58164ba7e90c5fe2141a688cf2d3c59b80` |
| [supporting-records.tar.gz](supporting-records.tar.gz) | 427 | 3513004 | `1ae6699b5f5c7f91c9f8dc5ecbe5a04a99736ccfca15e25c7207fd79d5f9bc52` |

逐文件原始／交付SHA、脱敏变换及排除项见 [manifest.json](manifest.json)。该清单不是正式库恢复备份；不含SQLite、密钥、依赖目录或重复全量恢复媒体树。

## 关键页面原件

以下为压缩包中实际截图的逐字节副本；只校正展示副本的扩展名，不修改原件。截图辅助阅读，完整交互经过和断言仍在相应JSON及独审中。

- [评论避让后的准确原句](previews/L1-final-B4.jpg)；包内 `browser/supplement-reset-01/L1-final-B4.png`。
- [390像素结构原区域定位](previews/R2-UX007-S2-region-390.jpg)；包内 `browser/R2-UX007-S2-region-390.png`。
- [最新歌曲准确历史及评论](previews/blessing-v2-comments.jpg)；包内 `browser/merged-main-final/blessing-v2-comments.png`。
- [关系弹窗返回后的实体选择](previews/ux010-final.jpg)；包内 `browser/merged-main-final/ux010-final.png`。

## 报告逐项证据

<a id="e-b5f67a2f5fdb"></a>

### 旧窗口存档

来源：`completed-window-01a10a82-adf0-7103-a834-c8dec2229ea8/`。
本组 3 项；压缩包：[supporting-records.tar.gz](supporting-records.tar.gz)。按来源前缀在manifest中定位。

<a id="e-01888e2609d9"></a>

### 重置依据

来源：`reset-authorization.json`。
包内：`reset-authorization.json`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。

<a id="e-d5f808a21e99"></a>

### 守卫状态

来源：`state.json`。
包内：`clock/state.json`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/clock/state.json)；原有附件链接在解压后可用。

<a id="e-85d58259273c"></a>

### 启动诊断

来源：`startup-recovery.json`。
包内：`clock/startup-recovery.json`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/clock/startup-recovery.json)；原有附件链接在解压后可用。

<a id="e-a4749caa789e"></a>

### 真实执行历史

来源：`resume-execution-diagnostic.json`。
包内：`resume-execution-diagnostic.json`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。

<a id="e-3b7153c8bbe7"></a>

### 恢复记录

来源：`backend-investigation/supplement-final/interruption-1855.json`。
包内：`backend-investigation/supplement-final/interruption-1855.json`，位于 [backend-records.tar.gz](backend-records.tar.gz)。

<a id="e-f4271dd0c46b"></a>

### 基准记录

来源：`run-baseline.json`。
包内：`run-baseline.json`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。

<a id="e-de19b0fca919"></a>

### 启动独审

来源：`reviews/startup-supervisor.md`。
包内：`reviews/startup-supervisor.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/startup-supervisor.md)；原有附件链接在解压后可用。

<a id="e-d2a198d9a924"></a>

### 定位独审

来源：`reviews/AO-UX-007-independent.md`。
包内：`reviews/AO-UX-007-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/AO-UX-007-independent.md)；原有附件链接在解压后可用。

<a id="e-4b28992f2f6b"></a>

### 后台调查

来源：`backend-investigation/backend-findings.md`。
包内：`backend-investigation/backend-findings.md`，位于 [backend-records.tar.gz](backend-records.tar.gz)。
[直接阅读副本](readable/backend-investigation/backend-findings.md)；原有附件链接在解压后可用。

<a id="e-0d84a4c4ec0e"></a>

### 浏览器证据

来源：`browser/`。
本组 1859 项；压缩包：[browser-records.tar.gz](browser-records.tar.gz)。按来源前缀在manifest中定位。

<a id="e-66040bd1a9a9"></a>

### 页面独立对照

来源：`history-inventory/page-performance-candidate1.md`。
包内：`history-inventory/page-performance-candidate1.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/history-inventory/page-performance-candidate1.md)；原有附件链接在解压后可用。

<a id="e-c42ee483d775"></a>

### HTTP独立对照

来源：`backend-investigation/AO-PERF-001-ab-summary.md`。
包内：`backend-investigation/AO-PERF-001-ab-summary.md`，位于 [backend-records.tar.gz](backend-records.tar.gz)。
[直接阅读副本](readable/backend-investigation/AO-PERF-001-ab-summary.md)；原有附件链接在解压后可用。

<a id="e-538bf93fbaff"></a>

### 分层覆盖矩阵

来源：`history-inventory/coverage-prioritized-checkpoint.md`。
包内：`history-inventory/coverage-prioritized-checkpoint.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/history-inventory/coverage-prioritized-checkpoint.md)；原有附件链接在解压后可用。

<a id="e-bc2e31b9f40c"></a>

### 配置页面独审

来源：`history-inventory/r2-configuration-evidence-independent.md`。
包内：`history-inventory/r2-configuration-evidence-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/history-inventory/r2-configuration-evidence-independent.md)；原有附件链接在解压后可用。

<a id="e-d1397cdee228"></a>

### 实体流程独审

来源：`history-inventory/r2-d2-technical-ui-independent.md`。
包内：`history-inventory/r2-d2-technical-ui-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/history-inventory/r2-d2-technical-ui-independent.md)；原有附件链接在解压后可用。

<a id="e-69810a4ab5a2"></a>

### 适用性独审

来源：`history-inventory/r2-d3-multicandidate-applicability.md`。
包内：`history-inventory/r2-d3-multicandidate-applicability.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/history-inventory/r2-d3-multicandidate-applicability.md)；原有附件链接在解压后可用。

<a id="e-49cbd893aaf8"></a>

### 技术流程与路由独审

来源：`history-inventory/r2-p2-judgment-route-findings.md`。
包内：`history-inventory/r2-p2-judgment-route-findings.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/history-inventory/r2-p2-judgment-route-findings.md)；原有附件链接在解压后可用。

<a id="e-76774296be96"></a>

### 真实下载包校验

来源：`technical-readiness/browser-package-verification.json`。
包内：`technical-readiness/browser-package-verification.json`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。

<a id="e-55788caafd5a"></a>

### 恢复独立审查

来源：`reviews/schema6-roundtrip-independent.md`。
包内：`reviews/schema6-roundtrip-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/schema6-roundtrip-independent.md)；原有附件链接在解压后可用。

<a id="e-39b88e5c1e7c"></a>

### 原始回执

来源：`schema6-roundtrip-reset-01/receipt.json`。
包内：`schema6-roundtrip-reset-01/receipt.json`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。

<a id="e-c6e996023124"></a>

### 最新数据独审

来源：`reviews/final-coverage-review.md`。
包内：`reviews/final-coverage-review.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/final-coverage-review.md)；原有附件链接在解压后可用。

<a id="e-88540ade361c"></a>

### 写性能报告

来源：`backend-investigation/write-performance-results.md`。
包内：`backend-investigation/write-performance-results.md`，位于 [backend-records.tar.gz](backend-records.tar.gz)。
[直接阅读副本](readable/backend-investigation/write-performance-results.md)；原有附件链接在解压后可用。

<a id="e-e2ce799f3c11"></a>

### 独立复算

来源：`reviews/write-performance-independent.md`。
包内：`reviews/write-performance-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/write-performance-independent.md)；原有附件链接在解压后可用。

<a id="e-ec304d9ff1e8"></a>

### 页面写入独审

来源：`reviews/ui-write-independent.md`。
包内：`reviews/ui-write-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/ui-write-independent.md)；原有附件链接在解压后可用。

<a id="e-9e3dd883ba7d"></a>

### 补测独审

来源：`reviews/supplement-independent.md`。
包内：`reviews/supplement-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/supplement-independent.md)；原有附件链接在解压后可用。

<a id="e-71613b06bee1"></a>

### 浏览器记录

来源：`browser/supplement-reset-01/`。
本组 352 项；压缩包：[browser-records.tar.gz](browser-records.tar.gz)。按来源前缀在manifest中定位。

<a id="e-3712468e34d7"></a>

### 服务回执

来源：`backend-investigation/supplement-final/`。
本组 82 项；压缩包：[backend-records.tar.gz](backend-records.tar.gz)。按来源前缀在manifest中定位。

<a id="e-c7c6ee8a282a"></a>

### 最终页面样本

来源：`browser/final-page-abab-reset-01/`。
本组 282 项；压缩包：[browser-records.tar.gz](browser-records.tar.gz)。按来源前缀在manifest中定位。

<a id="e-d4f41c6f2f01"></a>

### 阶段回执

来源：`backend-investigation/page-final-abab/`。
本组 36 项；压缩包：[backend-records.tar.gz](backend-records.tar.gz)。按来源前缀在manifest中定位。

<a id="e-5ef8feae2df0"></a>

### 页面独审

来源：`reviews/final-page-independent.md`。
包内：`reviews/final-page-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/final-page-independent.md)；原有附件链接在解压后可用。

<a id="e-4f5adf0926fe"></a>

### 后台与页面对应分析

来源：`backend-investigation/page-final-backend-analysis.md`。
包内：`backend-investigation/page-final-backend-analysis.md`，位于 [backend-records.tar.gz](backend-records.tar.gz)。
[直接阅读副本](readable/backend-investigation/page-final-backend-analysis.md)；原有附件链接在解压后可用。

<a id="e-4d1cc6800b76"></a>

### 独立交互报告

来源：`reviews/final-action-independent.md`。
包内：`reviews/final-action-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/final-action-independent.md)；原有附件链接在解压后可用。

<a id="e-1cb451236b7c"></a>

### UX010独审

来源：`reviews/ux010-independent.md`。
包内：`reviews/ux010-independent.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/ux010-independent.md)；原有附件链接在解压后可用。

<a id="e-cda24db2178f"></a>

### 成包检查点

来源：`reviews/delivery-final-package-checkpoint-audit.md`。
包内：`reviews/delivery-final-package-checkpoint-audit.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/delivery-final-package-checkpoint-audit.md)；原有附件链接在解压后可用。

<a id="e-12cc856af518"></a>

### A阶段计划

来源：`reviews/delivery-final-cleanup-plan.md`。
包内：`reviews/delivery-final-cleanup-plan.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/delivery-final-cleanup-plan.md)；原有附件链接在解压后可用。

<a id="e-22b33e219e9d"></a>

### B阶段计划

来源：`reviews/cleanup-after-publication-plan.md`。
包内：`reviews/cleanup-after-publication-plan.md`，位于 [supporting-records.tar.gz](supporting-records.tar.gz)。
[直接阅读副本](readable/reviews/cleanup-after-publication-plan.md)；原有附件链接在解压后可用。

## 冻结归档后的收尾回执

[收尾说明](closing-receipts/README.md)记录真实结束时间、Goal和后代状态，并链接最终归档与实际清理独审。这些记录晚于三包冻结，通过独立 [manifest](closing-receipts/manifest.json)映射原始与交付SHA，不重写上述3060项。本轮优化收尾不等于用户确认、_complete、推送或正式发布。
