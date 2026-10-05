# 写性能工具静态审查

本文记录首次执行前的静态判断。后续实际窗口及对 Python 3.9.6 commit 嵌套行为的纠正见 [写性能结果](write-performance-results.md)；下文的“尚未执行”均指静态审查时点，不覆盖之后的真实回执。

本次可以安排一次不超过 180 秒的独占验证窗口。当前还没有运行测量，语法检查和下列源码审查不代表数据库写入或性能已通过。产品 Python 仍为 `e91c57a4a1136e55946d4a2a6377949a932a76fa`，本次只修改调查目录的两份探针及方案。

审查者是新登记的 `/root/write_performance`，线程 `01a10a86-2f7f-7c90-aeae-e4f64657125b`；旧工具由前一写性能调查者准备。本次初次审查独立于旧实现；修复后的工具仍须由主协调或监督者核对，不能把本人修复写成本人独立验收。

## 查到的问题及范围内修复

1. 原工具对普通 EPISODE 使用整体评论锚点，违反 `Store.validate_target` 的明确校验。现在指向合成 ENTITY 的准确修订，启动就绪前调用原验证方法确认整体锚点有效，POST 白名单同时限定实体、修订与锚点。该问题属于测试夹具，未改产品契约。
2. 原窗口起点在源码和数据哈希之后，收尾取消闹钟后无兜底。现在从 main 起点计时，保留 20 秒，170 秒普通超时，180 秒独立 watchdog 只停止自身服务并落独立超时回执；git、guard、子进程回收设 timeout。超时结果不会标为完整审计。
3. 原 DB 最终文件检查不能排除上层 write-ab 符号链接。runner 与服务均核对规范路径，数据库必须为普通文件，初始 SHA 与独立 inode 均核对；拒绝已有输出目录。
4. 原方案承诺评论和配置竞争，但脚本只执行配置。现补同一准确评论版本两条竞争请求，检查一成功一 409、只新增一个事件及 HTTP/独立只读连接可见结果。仍是原单线程 HTTPServer 的版本门禁验证，不是多写者 SQLite 压测。
5. 原 context-exit 命名未区分无事务退出。现分开记录 active commit、rollback、no-transaction，明确 execute 不包含之后的 cursor 取行，分项不代表完整数据库时间。计时包装只在 ACTIVE 请求期间生效，准备数据不混入请求样本；没有使用 trace callback 伪装语句完成。
6. 原跨端检查仅比较 fixture 和请求载荷。现增加固定顺序样本后完整业务状态对比，仅剔除方案逐项列明的记录元数据时间戳；不删除 payload 字段。竞争赢家不确定，因此另外验证，不混入确定性比较。
7. 守卫校验现要求本任务 ID、新 T0 `2026-10-05 13:21:50 +0800`、armed、无停止记录以及有效监督锁/心跳。旧一致快照和旧基线继续沿用原时间，不冒作新采集。

## 已核对的安全与测量边界

- 数据只从固定不可变快照复制到新的 write-ab 子目录；clone 文件初始 SHA 必须相同，服务只监听 loopback 62607。没有挂载媒体目录、读取密钥、外部请求或正式服务操作。
- 成功写通过原 HTTP handler、Store 及 production API 执行，测试实体无媒体需要，actor/reason 明确技术测试；没有自动认可真实作品。
- comments、configuration、decision 成功后分别 HTTP 回读及新只读连接检查版本、事件和准确目标。连续重放旧版本必须 409 且数据库状态不变。采纳撤销后还读第一条准确历史 JUDGMENT。
- 结束后与不可变原快照逐表双向 EXCEPT，排除范围只限三个 fixture 对象、其决定对象、测试评论、PROJECT 预期更新和新配置事件；PROJECT 其余字段与旧事件仍比较，另做外键核验。
- `ACTIVE` 全局计时容器与原单线程服务匹配；每个真实写请求都有唯一 request_id，runner 核对与服务日志状态一致。
- `Store` 所走写路径使用 Connection.execute/executemany 和 context-exit 或显式 commit；启动 executescript 不计为写样本。响应 JSON 格式化包含在 handler/HTTP，日志格式化和文件写入位于 handler 计时之后。
- 两端按固定顺序基线后候选，OS 缓存未清，每项 1 次预热、5 个正式样本；只作为小样本写路径检查。合成对象的性能不外推为大型素材的真实采纳耗时，也不代替浏览器保存体验。

## 执行命令与未验证项

从故事任务 worktree 根执行，输出名必须全新。执行前需主协调明确授予独占窗口，所有其他代理暂停测试、页面测量和重 CPU 工作：

```sh
python3 .runtime/autonomous-optimization/backend-investigation/run_write_ab.py \
  --output-name reset-window-01 --max-seconds 180 \
  --candidate-commit e91c57a4a1136e55946d4a2a6377949a932a76fa \
  > .runtime/autonomous-optimization/backend-investigation/write-reset-window-01.log 2>&1
```

仍未验证：实际 fixture 导入和 HTTP 结果、180 秒内是否完成两端、各计时分项真实出现次数、写后可见性和旧数据全量保留、端口停止回执。任何失败保留原输出，不覆盖日志，不以纸面方案判为通过。两脚本当前均通过 AST 语法解析，尚未执行数据库代码、创建克隆或启动服务。
