# V1 验证记录

2026-09-21，本机主实例入口 `http://127.0.0.1:3000/`，Docker Nginx 代理 Python 服务。故事实例锁定审阅台系统 `bc87ed407140ca68b8044213caf1fc326a9acb7a`。以下区分本机浏览器验证、公开仓库同步与干净恢复；不是公网部署证明。

| 验收点 | 本轮证据 |
| --- | --- |
| 1. 双公开仓库 | `goosmanlei/story-review-desk` 的系统提交 `bc87ed4` 已推送；故事仓库本轮同步与最终远端回读待完成。 |
| 2. 项目归属与版本 | Python/Nginx 及 UI 系统代码只在审阅台仓库；故事仓库 `config/instance.json` 锁定上述提交，`export/` 保存实例业务快照。 |
| 3. 资料差异与出处 | 3 份文本为《搜神记》卷十九通行本、四库本异文和本项目白话直译/词语说明。另有一份福州评话《李寄斩蛇》陈峰演绎线索：在浏览器核验[哔哩哔哩上传页](https://www.bilibili.com/video/BV1fs41137q5/)的标题、表演者标注、2018-08-04 上传时间和优酷来源线索；[福建师范大学实践报道](https://www.dxsyb.com/paper/2025/0203/677157.html)另证传统曲目与艺人。演出来源、录制日期、授权和具体词句未知；该对象不是演出逐字稿或第四种古籍底本。各资料的版本类型、采集日及链接见 `export/materials.json`。 |
| 4. 本机审阅 | Chrome 访问 3000，左侧切换四项资料，右侧正文与元数据、SVG 异文图均可见；演出页含视频平台外链及旁证，不再分发视频文件。页面 `document.scrollHeight=2065` 大于视口 `1891`，原文阅读区 `overflow=visible`、阅读卡高 `1547`，不再受 820px 固定上限。左上角点击后 URL 为无参数的 `http://127.0.0.1:3000/`，显示“当前工作”；“来源资料”入口已显示为“故事采编”。 |
| 5. 评论与 AI | 1 条评论仍锚定“东越闽中，有”及精确资料修订。旧版交互核对见系统仓库 `docs/comment-checklist.md`；浏览器已验收圈选、保存、编辑、关闭、重开、草稿保留。编辑现有评论时，已有文字便可直接点“AI 润色修改意见”，真实请求返回“尚未保存”的建议，并展示故事/创作背景、阶段、上下文、4 项资料和哈希；未采用建议，原评论未变。配置页平铺显示模型及联动强度：切至 `gpt-4.1-mini` 仅有“不适用”，切回 `gpt-5.6-sol` 可见 `none/low/medium/high/xhigh/max`，保存后 Schema 2、版本 3、强度 `medium`。 |
| 6. Codex 读取 | 系统仓库命令 `PYTHONPATH=. python3 -m review_desk --instance ../SnakeSlayingRecord comments` 返回评论 ID、`source_id`、对象 ID、精确修订 ID、原文圈选、所在正文及来源 URL；HTTP `/api/comments/context` 同用途。 |
| 7. 导出与公开同步 | 本机 `export` 生成 Schema 3 manifest：4 资料对象、1 评论、5 评论事件、4 对象/修订、2 配置及事件。`materials.json`、`comments.json`、`objects.json`、`configurations.json` 和 SVG 均列 SHA-256；运行库、密钥、私有 CA 不纳入同步。故事仓库本轮推送待完成。 |
| 8. 干净恢复 | 当前版本的“公开同步 → 从双公开仓库干净恢复 → 复导出比较”待完成。上一版曾以系统 `8e95a3a`、故事 `bc60d6a` 在隔离克隆完成 3 资料/1 评论的恢复与浏览器回读；该历史结果不冒充本轮验证。 |

自动测试：`python3 -m unittest discover -s tests -v` 通过 5 项，覆盖评论锚点/生命周期、迁移、配置 Schema 2 与模型强度校验、外部媒体 URL 校验、AI 请求体和导出恢复完整性；`node --check`、`git diff --check` 通过。浏览器演出资料不声称已逐句听辨，后续改编须回原视频核对。
