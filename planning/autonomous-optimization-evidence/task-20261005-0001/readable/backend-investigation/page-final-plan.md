# 最终页面 A/B 交替复测准备

准备已完成，启动器仅通过 `ast.parse` 静态语法检查，尚未启动服务或执行页面采样。根代理独占浏览器与采样窗口。机器、实际 Chrome 版本、视口与页面内容须由本轮采样器再次记录；历史环境只能帮助建立一致条件。

## 冻结输入与代码

- A：`../system-baseline`，准确提交 `b874b959af9c918a482e8488dc25cb0204ab5772`。
- B：`../system-worktree`，准确提交 `3b20d609448365103ebcf381776e33869913fe8b`，包括 SOURCE 请求内复用及 UX007 评论定位改动。
- 全部阶段使用 `../preview`，端口 `62606`，实例标题 `李寄斩蛇 · 故事采编 · 任务预览`。相对路径以本文目录为基准。
- `preview/.runtime/review.sqlite3` 与 `generation-base.sqlite3` 均为 163,000,320 字节，前后 SHA-256 均为 `5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0`。两者字节、schema 及 24 表逐行规范化摘要完全相同；271 条评论、6,236 对象、10,160 修订、78,889 内容节点均相同。逐表结果在 `page-final-plan.json`。
- 统一打开 `review.sqlite3`：归档原件解析也定位这个路径，可与 Store 的请求内 reader 共享；不因使用另一个同内容文件而引入连接路径差异。
- 1,398 个实体文件的名称/大小清单一致，总计 1,215,748,516 字节；本次没有重新读取全部媒体字节。837 个 `export/assets` 归档引用容器全部存在，其 JSON 语义与数据库容器一致。另 1,018 个具名生产归档路径未在预览展开，两库保留相同配方与内容节点；这不等同于原件丢失。前序完整保全证据继续有效，本准备不宣称重新做过完整恢复。

## 启动与停止

从故事任务 worktree 执行，先确认 `62606` 无其他监听者。每阶段输出目录必须尚不存在；不要复用失败目录或覆盖旧证据。

```sh
python3 .runtime/autonomous-optimization/backend-investigation/page_readonly_probe_server.py --stage A1 --output .runtime/autonomous-optimization/backend-investigation/page-final-abab/A1 --max-seconds 1800
```

完成阶段后，以启动命令的进程会话发送 Ctrl-C，或仅向该输出 `process.json` 的 PID 发送 SIGTERM。确认 `receipt.json`、`identity-after.json` 已落盘，`identity_unchanged=true`、`error=null`、无 `final_check_error`，且端口监听已消失；再以同样命令依序替换阶段和末级输出目录为 `B1`、`A2`、`B2`。禁止广泛 `pkill`，不停止其他服务。PID 停止后应回读进程身份/端口，不能仅凭 shell 退出码认定成功。

启动器固定两端准确提交、原 probe SHA 与冻结数据库 SHA，核对产品树干净及本轮 guard 的任务、T0、监督锁和心跳确认；只保存脱敏 guard，不导出租约。上限 1,800 秒，且不得越过 T0 后 9 小时收尾边界。超时是未完整完成回执，不能作为成功采样。新 T0 为北京时间 2026-10-05 13:21:50，9 小时边界为 22:21:50。

启动器复用原 `probe_server.py` 和 SHA 为 `74a80b7f730a450f4fc00f5424120f8f60406e7fe9c4c65234e3d317958a804c` 的 `probe.js`，不改变 HTTP 计时或 DOM 采样。服务仍为单线程，保留 2 秒浏览器预连接超时。唯一适配是跳过会建表/迁移的 Store 初始化，以 SQLite `mode=ro&immutable=1`、`query_only=ON` 读取现成库，并让 POST/PATCH/PUT/DELETE 返回 405。归档内容仍使用各自代码的真实 row factory 和原件解析。启动前、退出后保存 DB/代码 SHA、实例配置 SHA、全实例非运行文件的名称/大小/mtime 清单摘要。此 metadata 检查不能证明所有原件字节从未改变。

首阶段先确认页面和只读行为真实可用；写请求拒绝检查应单独标为预检，不混入页面样本。各阶段采用相同预检步骤。若发现版本、数据、guard 或功能错误，保留首轮错误并停止，不临时换库、修 probe 或静默删除坏样本。

## 页面采样条件

使用已连接 Chrome，同一前台标签、1440×900、DPR 1、同一 origin 与浏览器配置。根代理独占，其他代理不执行测试、服务、数据库负载或浏览器操作。保留既有草稿；不以清空 localStorage 的方式制造一致条件。记录实际初始面板/选择/滚动状态，并以原 12 个固定路由逐页测量。

阶段顺序 A1 → B1 → A2 → B2。每阶段每页 1 次导航加 4 次 reload，共至少 240 个样本。12 页的准确路由、选中页签和内容区域在 `page-final-plan.json`，其中 P2 固定对象 `preparation-s001` 与修订 `dd7e073959fd188f3aecb2620fab4b967b8a4ba3f5b88fbdeaeb5c736e1b4e72`。C2 若增加重复，应在采样开始前固定所有阶段同样数量；不能看到结果后只扩某一端。

主指标 `scenario_ready_ms` 从导航起点到正确内容的语义采样结束，不包含 180ms 稳定确认等待。样本必须 `completion_reason=stable`，起止均前台可见、fetch/body 待处理数为 0、错误请求数为 0，且预期页签、非空内容区、准确 URL/修订均正确。保留完整原始值、请求与 resource timing、环境和失败原因。首次导航与 reload 分组报告，API 耗时另列；不得把后台加速直接写成页面收益。

沿原响应的 `no-store`，不清空系统文件缓存。相同前置身份扫描会读取数据库和代码、暖文件缓存，因此不声称系统冷启动或完全冷缓存。DOM 稳定只证明该采样规则下内容可用，不涵盖全部图像解码、播放就绪或滚动动画结束。

旧 `browser-baseline-v3` 开始于 UTC 00:34:13，旧 `browser-candidate-v3` 开始于 UTC 01:01:40，均记录 Python 3.9.6、macOS 26.6.2 arm64、62606 和相同 probe。旧 candidate 元数据记录 baseline HEAD 加工作区补丁，补丁 SHA 为 `98d4cd479763f379a8b06e84d3c8a0c6f5c0ac9cdcf12eb091316a889660215b`；它不是本轮 3b20d609。旧数据保留作历史证据，不与本轮干净提交的交替样本混合统计。

最终按每页每阶段列原始耗时、样本数、中位数、范围及波动，先比较 A1/B1 与 A2/B2 方向是否一致，再判断差异是否超过各阶段波动。未证实收益或明显回退分别标明；该准备本身没有新页面收益结论。
