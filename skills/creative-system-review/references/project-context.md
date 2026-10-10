# 本项目适配

本文件中的路径相对故事项目根目录。本适配说明当前项目的入口；通用方法不固定故事人物、集数、镜数、生成供应商或任务调度工具。迁移时先核对目标项目，再替换这里的入口。

- 愿景与人的工作定位：`production/system-vision.md`；它也是“制作思路 → 愿景”的唯一正文，阅读页由此派生。
- 产品设计依据：[产品演化原则](https://bytedance.larkoffice.com/wiki/wikcnDKbbkpMqO8zeTdBmwToQIe)。本项目结合创作主场景理解必要性、持有成本、稳定体验、价值先于入口、关键路径与先预测再验证，不机械套用消费产品的流量指标。需要核对这些原则时查原文；内部原文不复制到交付包，其他使用者没有该文档权限也能独立使用本 SKILL。
- 有效规则、作品输入与当前状态：依次读 `AGENTS.md`、`KNOWLEDGE.md`、`STATE.md`，按其中入口查当前已确认故事和作品；不根据本适配猜当前版本。
- 影视专业知识：`production/filmcraft/README.md`、`production/filmcraft/quick-reference.md`；具体制作问题只读相关章节。
- 视频生成方法与 Prompt 模板：`production/seedance-video-handbook.md`，在制作方案或 Prompt 工作前读取适用部分。
- 方法正文、共用资源与准确执行：`production/managed-methods.md`。本 SKILL 文件包是本方法唯一维护正文；系统配置中的入口引用其准确只读投影，导出和快照不成为第二份可编辑正文。修改后沿既有同步和发布流程更新，不能静默改写过去的执行。
- 任务定义与发布：`skills/task-definition-publish/SKILL.md`。形成任务时按需从本次明确的故事项目根读取，继续为目标、范围、关键取舍与验收调查研究；它是项目材料，不包含在当前 Review 三文件导出包中。缺少项目材料时补取对应方法，不把包内不存在的文件当作已读。
- 任务、隔离工作区与发布：`production/generation-workspaces.md`，任务现状以主项目 `.codex-task/tasks.json` 与实际回执为准。通用审阅台承担展示、审阅、评论与数据管理；本剧特有创作工具留在故事仓。

本项目持续 Review 的运行约定、暂停状态与历史证据在本机 `.runtime/system-review/`；这些是会话运行资料，不是可移植方法，也不因加载此 SKILL 自动恢复。用户本次已授权的任务范围优先，不能沿旧计时或旧计划继续执行。
