# 制作当前稿与生成候选任务输入

任务正文发布时保存为 `planning/production-current-candidates-task.md`；本目录整体保存为 `planning/production-current-candidates/`。

- `evidence.md`：已确认决定、现状与代码依据、实际验证边界。
- `dependencies.md`：直接依赖0019及共享正式发布协调。
- `sample.html`：可直接用浏览器打开的离线交互样例，虚拟文字占位，无模型调用和费用，不读写正式业务。数据存于独立localStorage；点击页面“重置本演示”可回到起点。
- `browser-observations.md`：根在Chrome实际完成的步骤与结果，包括在途修改、同参候选、失败无候选及刷新。
- `input-hashes.json`：本次发布输入字节与SHA-256，task.md映射到上一级任务正文。

样例操作：灰色方案提交→等待时改成蓝色及REF-B并保存→返回调用1，检查候选1仍灰色/REF-A→提交蓝色并返回→同参再次提交返回→切旧候选并复用到当前→再改当前→模拟无结果→刷新。所有“演示AI”按钮仅为阐明工作顺序，不承诺产品新增制作编辑器。生成API、实际模型、历史数据迁移、评论与正式发布由任务实施后验证。
