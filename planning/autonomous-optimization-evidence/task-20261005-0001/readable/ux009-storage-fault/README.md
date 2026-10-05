# UX009 浏览器存储故障夹具

本目录只提供功能测试注入，尚未启动或在 Chrome 中验证。`serve.py` 在 `127.0.0.1:62611` 只读使用原 frozen preview（271 条既有评论）；数据库以 `mode=ro&immutable=1`、`query_only=ON` 打开，跳过 Store 初始化，沿用真实 row factory、GET handler 与原件读取。POST/PATCH/PUT/DELETE 均返回 405。`ui-write-performance`、62609、正式数据库和原件均不改动。

根审阅后，从故事任务 worktree 启动：

```sh
python3 .runtime/autonomous-optimization/ux009-storage-fault/serve.py --output .runtime/autonomous-optimization/ux009-storage-fault/run-01 --max-seconds 1800
```

先确认 62611 无其他进程；只接受精确 Host `127.0.0.1:62611`。新输出目录必须不存在。URL 为 `http://127.0.0.1:62611/`，可继续带原 SOURCE/structure/script 路由。未注入性能 probe，没有页面性能结论。服务仍为单线程并保留 2 秒预连接超时；守卫核对本轮 T0、armed、监督锁和心跳，最多 1,800 秒且不能越过 22:21:50 收尾边界。

允许 `system-worktree` 存在根协调者未提交的 UX009 修复；每次启动记录准确 HEAD、dirty 状态、整个产品树摘要、相关 JS/Python SHA 和 `product-at-start.patch`，保留真实注入源码副本及 SHA。不要在正在验收时继续改相关源码；退出 identity 若不一致，须明确期间输入变化，不能把该轮当作单一版本通过。初始 frozen DB SHA 固定为 `5c6d00ee6efa7506201bbef46ffd69bde49f7300c4697fe66036e87ace7ed4f0`，首尾回读。原件只沿用既有保全证据及文件 metadata 不变检查，不重复全量 hash。

页面 `<head>` 在 app.js 之前加载 `/__fault__/storage-fault.js`。页面左下角显示**草稿存储故障**下拉框和“恢复正常”按钮，带明显“客户端测试注入；非浏览器真实安全策略”说明。初始为正常，每次刷新仍默认正常，控制状态只存在内存，绝不通过被测 localStorage 保存。

| 模式 | 准确故障范围 |
| --- | --- |
| 正常 | 原生 localStorage，未安装代理。 |
| 仅草稿正文 set 抛 QuotaExceededError | `setItem` 的键以 `review-draft:` 开头，且不以 `:submission` 或 `:discussion` 结尾时抛出。提交回执和意见选择字段仍走原方法。 |
| 仅故事/剧本 meta set 抛 QuotaExceededError | 只对 `review-story-editor:`、`review-script-editor:` 前缀的 `setItem` 抛出；正文写入不受此模式影响。 |
| getItem 抛 SecurityError | 该文档所有 `localStorage.getItem` 调用抛出，set/remove 等仍走原方法；这是方法故障，不是 window 属性访问或真实浏览器策略故障。 |

为了避免 Storage 对象的特殊命名属性把 `setItem` 赋值当成存储内容，本注入仅在该文档的 `window.localStorage` 入口返回一个对象代理，包装 getItem/setItem。其他方法绑定真实 Storage 对象；不改 `Storage.prototype`、sessionStorage、其他 origin、浏览器权限或真实安全设置。“恢复正常”恢复原 window.localStorage 属性描述符，解除代理；它不会清空、伪造或重写已有草稿。源码链接可直接打开阅读全文。若原 localStorage 不可访问、代理无法安装，控件显示“注入失败”，`data-ready=failed`，不得继续当作故障已生效。

功能验收由根用真实控件执行：先正常创建明确的未保存测试输入，记下正文/准确目标/编辑状态；选择某一故障模式，继续输入以触发对应失败，再点击既有评论定位、切换与返回，核对 UX009 所承诺的正文/锚点/编辑上下文保留。三条路径分别验证 SOURCE、故事结构与剧本。不要点保存去写既有评论；即使误点，服务也只会 405。故障控制是测试面板，不计入产品布局或性能验收。

取证读取 DOM 中 `#storage-fault-test-evidence` 的 JSON；它记录模式、是否安装代理、注入失败次数、触发操作/键/异常名和控制切换，不记录草稿正文值。`#storage-fault-test-controls` 还带 `data-mode`、`data-ready`、`data-injected-failures`。仅选中选项不证明路径已受测，必须有相应 get/set 的实际抛错记录以及真实页面前后正文证据。恢复后应再次实际输入并验证正常保存草稿；只点击按钮不等于恢复行为已经验收。

完成后只停止本次 `process.json` 的准确 PID（Ctrl-C 或 SIGTERM），等待 `receipt.json` 与首尾身份文件。核对 error/final_check_error、database_unchanged、inputs_metadata_unchanged、identity_unchanged，确认端口释放。相关源码若在运行中改变，数据库不变也不能替代代码一致性检查。源码与文档在本 runtime 目录，未写入产品代码。
