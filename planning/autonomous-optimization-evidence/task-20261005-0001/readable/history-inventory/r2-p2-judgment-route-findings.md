# P2判断历史错误归属及技术成功路径独审

审查时间：2026-10-05T06:46:22.800034+00:00。守卫/心跳正常。仅只读保存的页面快照与PNG、HTTP日志、源代码和technical实例SQLite；未调用接口、运行测试/浏览器或改库。主矩阵按根要求暂不更新。

## 判断历史的真实路由问题

已确认P2级体验问题。`R2-P2-judgment-history-current-route.json`显示，组合与历史中的“查看处理历史”进入`workspace=materials.workspace`，主界面成为制作设定／素材管理，而正文仍是准确判断v2。准确数据尚在，但用户离开了正在复核的制作范围，列表也变成素材列表。

直接原因是`production.js:308`：JUDGMENT不在任何productionGroups，`navigate=true`一律回退素材工作区。相同限制还见`:311`阅读guard及`:301`刷新候选。当前没有独立的productionWorkspaceFor函数；不能仅把调用改为navigate=false，否则guard仍拒绝读取。

后端`production_breakdown.index(history):47–53`已允许明确object_id补入JUDGMENT；默认列表仍按制作记录返回，不必新增API或扩大全量索引。现有uncached judgment测试只stub openProductionRecord并检查参数，没有执行真正的路由，因此不能证明此处保持上下文。

最小修复应统一“当前production.workspace/history可以读判断”的条件，用在归属、guard及准确URL刷新；保留材料工作区已有判断入口，不把所有资产判断全局迁到全剧制作。进入处理历史时应先保源scope URL与阅读位置，再push准确判断URL；详情内部切版本沿既有准确revision机制。当前代码先replace掉原scope URL再switchWorkspace，原返回入口会丢，仅改工作区不足以解决返回。

必要真实验收：P2打开准确判断仍在组合与历史；切旧v1／当前v2及刷新保持准确内容；Back回原scope/集场、Forward回判断；材料侧原判断入口不改变。数据/评论target、实际采用、原件与历史无需修改。

静态旁证：判断的“审阅对象”是采用RELATION；未知于当前索引的记录会由productionRefLink走source-only弹窗。该路径尚未实际操作，不写成已复现问题，也不建议顺手大改全部引用；先保证原scope的返回入口。

## 技术采用、输入包与历史保存证据

独立阅读真实旧采用PNG及JSON，确认技术范围有1项必要输入、缺项0、下载按钮可用。HTTP原日志有采用201、显式换版201、过期采用409；普通判断keep201、rework201、过期判断409。失败快照分别保留旧revision2和采用理由，以及keep选择／过期判断依据，未写成失败后的当前状态。

只读技术库记录确认同一采用对象两版：v1指向voice准确修订2，保留0.1–0.9秒；v2指向准确修订3。同一普通判断两版keep→rework，target准确引用采用v2，旧新技术分集引用不变；过期正文没有新增修订。它们是可丢弃技术夹具，没有故事作品认可。

实际浏览器下载清单与CLI目录包manifest解析后完全相同；下载文件SHA256为`c4645a49d768926af3d5fe8deb66bc061559d6aee1dbafe34a6c25612b7cd030`。包内唯一96044字节WAV重新只读核对哈希与文件名一致，manifest仍指准确旧voice修订2。下载事件工具超时不等于下载失败，此处以已经落盘的实际文件为证。

完整准确修订、原HTTP行及来源指纹保存在同名JSON。来源视口按各原文件保留（2192×1359与2192×1415分开），这些n=1功能证据不作性能比较。最终覆盖矩阵等待根完成判断历史/返回证据后再更新。
