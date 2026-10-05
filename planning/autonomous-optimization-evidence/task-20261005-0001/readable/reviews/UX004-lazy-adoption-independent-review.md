# UX004 与采用素材延迟加载独立静态复核

审查者 `/root/reset_supervisor`，真实线程 `01a10a85-fd7a-7021-aa28-a867f6dea1d8`。未实施本项；按根代理授权只读产品和测试，未运行测试、浏览器或测量，未访问正式库或预览库。代码基准为通用系统隔离 worktree 中本报告末尾指纹所标识的文件。

审查前与审查末尾均核对守卫；末次 check 成功，phase=armed、last_error=null，监督锁持有、进程 20556 运行、心跳约 7.91 秒、supervision_confirmed=true。没有使用或公开 lease_digest。

## 结论

本次静态审查未发现必须修复的新增退化。可以进入根代理的真实页面验收。本结论不表示页面性能、全部 UI 或所读测试已经由审查者执行通过。

## 采用素材的完整性和生命周期

- 没有 candidates 或值为 null 时，仅在用户打开采用编辑器后请求 `/api/production?kind=ASSET`；列表等待中不能选择历史或提交。已有明确候选数组按原范围显示，空数组保持为空，不回退到全局素材。
- 服务端 snapshot 的列表分支直接返回 current_records(kind=ASSET)，后续 material_assets 信息不删减 records；current_records 没有分页或数量上限，按已验证的 production 格式输出完整当前素材头。选择仍按 media_type 筛选、object_id 去重；没有把占位素材的既有能力偷偷删去。
- 选择素材后仍通过 object_id 查询完整历史；提交依旧使用被选准确 revision、组成文件 ID、范围、裁切、原 scope/slot/usage 和 expected_version。没有改写历史，也没有把新列表写入页面导航用的 state.productionRecords。
- 根的 workspace、productionLoadEpoch、productionReadEpoch，编辑器连接状态以及取消标记共同保护迟到列表与历史响应。A→B→A 仍由 requestEpoch 判定；初始列表失败保留理由和裁切输入，清空可提交候选并显示失败状态，不使用可能失真的页面索引。
- 所读新增测试覆盖真实 readiness 入口、历史不在页面索引、明确空/单候选、初始失败/损坏响应、取消重开、工作区/读/载入代际失效，以及准确旧版本和原提交字段。原有写后不确定结果、冲突和重试契约代码未被本批改写。这里只确认测试内容具有针对性，没有执行它们。

## UX004 修正

- 上轮 P1 窄屏定位不可见已在代码上修复：仅当视口小于 1200 且评论直属统一弹窗时，先收起评论、显示原正文，再进入原准确定位流程。宽屏继续并排，不改变准确版本与锚点。
- 上轮 P2 媒体锚点选择器已改为实际 `.review-media-player`。优先当前焦点或保存的返回焦点所属播放器/文本块，再考虑已选引用和可见内容，避免把标题当作正在评论的音频阅读锚点。左右两个滚动容器分别保存；没有重建播放器、替换 src 或改变 currentTime。
- 窄屏首次打开评论把焦点置于既有收起按钮；再次打开已可见面板不抢走编辑焦点；收起后优先返回仍连接、可见且属于当前弹窗的触发元素，否则退回本弹窗关闭按钮。
- 统一弹窗 close 恢复外层 state 后使用 setPanelOpen；素材制作历史及音视频参考两个入口共用 referenceReviewSession，其 close 也使用 setPanelOpen，因此 hidden 和两个既有全局入口的 aria-expanded 同步。
- CSS 的并排与隐藏条件只匹配直接子评论面板，头部独立占据第一行。窄屏隐藏正文时保留头部；小于等于 1800 的素材标题 flex-basis=100% 与原 flex-wrap 配合，仅让既有标题独占一行，没有新增状态或入口。
- 所读测试覆盖正文与媒体节点身份、准确源和时间、草稿、窄/宽屏焦点与定位、外层 open/hidden 与嵌套 owner/aria 恢复。几何与真实浏览器行为不由这些模拟节点证明。

## 尚需真实页面覆盖的边界

这是一项验收提醒，不是已复现缺陷：嵌套关闭把共享评论面板从子弹窗搬回父弹窗会改变父正文宽度。建议在父长文已经滚动时验证，父评论原本打开和隐藏各一次；同时核对窄屏焦点落在可见父控件，以及准确历史、草稿和媒体节点保持。现有静态/模拟测试不能证明这两个滚动容器在重排后的可见阅读行完全不漂移。

根已经发送的 390、1440、2192 实际操作结果属于根的浏览器证据，独审未冒充独立重跑。相应页面是否通过以这些原始证据和根的后续边界验收为准。

## 文件指纹

记录时间：2026-10-05T14:24:58.033043+08:00

```json
{
  "review_desk/static/production.js": "10ef3df344715f74ec66f65e033356b4831a0005e1c2ae119abef597ffa9f335",
  "review_desk/static/app.js": "a8af2d373c18b10da98511224657e4c95e710a1111e8f6f714071efded5dc707",
  "review_desk/static/unified-cards.js": "d719bdb36fa5d5d9d8920181d7e1cbd4ffcd6c5bcc19171b2527835de12fb5b3",
  "review_desk/static/unified-review.css": "5e9c8e47021bb401fd449dcdad1905f68b1f8cb2c47e53fb7662f00b5ed04bb4",
  "review_desk/static/material-review.js": "80777482175abb3be0c49692e16220960dbb7a8b0b0909a286632ebfa325d209",
  "review_desk/production.py": "7278f3427931c66651e99c5f8d907277514a4a3710bd3805729ef410d7b51254",
  "tests/production_adoption.test.cjs": "d3d36cacc766fea3ed4fc1485cd3567aad431a9c904de05a2ee692197c21044f",
  "tests/comment_outside_click.test.cjs": "a212a62ce3c2f9b369c58d443bc0e1228f2ba42043084e9570dcb7e864c98531"
}
```
