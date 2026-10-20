# 发布恢复补丁独立复核

**结论：通过，未发现本次两个补丁引入的 P0／P1／P2 缺陷。** 复核覆盖 `optional_container` 的大小写兼容、`verify_mount_sources` 的失败分支及 apply 中的保护顺序；未修改生产源码，未执行正式发布或回退。

复核基线为 primary `4f9823f4768d4555c196299f0719a80dbdfbad55`。准确输入摘要：

| 输入 | SHA256 |
| --- | --- |
| `scripts/oss_runtime_release.py` 完整源码 | `12cc870d9e797ea1341928419b76ba0d1fcbeb4896860385068e0dc33fa18ada` |
| 该脚本相对 HEAD 的 diff | `52de1c33b251f791a14f963d88f50c7ed20d1bd86277d81ae189b3a46739d399` |
| `tests/test_oss_runtime_release.py` | `70df5eddc9a422b1f71c000eea64a99e4d5ceb571e9090d586a063a14815ec60` |

## 检查结论

`optional_container` 第 128–134 行只在非零退出时，将 stderr 转为小写后识别 Docker 的 `no such object`／`no such container`。大小写差异均表示对象不存在；其他错误仍抛出异常，超时同样向外传播，不被当作容器不存在。因此回退不会因本次大小写修复而把未知 Docker 状态直接判为空。

`verify_mount_sources` 第 146–158 行先读取仍在运行的准确旧容器内每个目标的文件类型，再逐项检查对应宿主 Source。宿主缺失、普通文件与目录类型不符、FIFO／socket、容器目标缺失或结果缺键均拒绝。宿主权限错误、容器内 stat 失败、docker exec 失败、非 JSON 输出也直接终止检查，没有采用“无法检查即安全”的回退。

apply 在第 308 行调用新检查，此时已经通过原容器归属、实例根挂载、Running 状态和全部 bind 类型检查，并持发布锁；尚未创建 release 目录（第 316 行）、保存 cutover receipt、启动 HTTP 写入锁容器或停止旧服务（第 350 行）。检查抛错直接退出该阶段并释放发布锁，不进入停服／切换及其回退分支。该顺序能够在旧服务仍可运行时拦住已知的宿主 bind 源缺失和类型不符。

## 有限验证

- 独立重跑 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_oss_runtime_release.py -v`：**4 项通过，0.004 秒**。
- 额外使用内存 mock 验证普通文件／目录匹配、FIFO／socket 拒绝、目标报告缺键、宿主权限拒绝、目标报告损坏、Docker inspect 超时，以及权限／连接／内部错误三种未知 stderr 均保留失败状态。没有调用真实发布处理函数。
- 通过 AST 复核新 guard 的调用行 308 位于首个 `docker stop` 的行 350 之前，并人工检查中间与异常控制流。
- 对当前恢复后的正式旧容器执行了一次只读挂载类型核查：容器 `3d83d96072c484fb37cde5c22d37376a1bdc365ed250ea66d7fae8d19bf97c82` 为 Running，**9 个 bind 均通过新 guard**。镜像仍为 `sha256:94152aa4fddab208cfdbb59f9803aaf001898da8888d483cb8e580b9c757303a`，desk 标签仍为 `254d509cbe644f75e90344bc1ae40b7279aa418f`。检查只读取文件类型，没有读取凭据正文或改动业务库。

## 恢复事实与证据边界

主目录 `.runtime/task-evidence/task-20261020-0003/recovery/receipt.json` 记录：恢复使用原旧镜像，只替换 `/run/local-ca/cacert.pem` 的宿主 bind 源，业务表指纹前后一致，HTTP 写入锁已释放。此处已读取该回执，但没有重新扫描正式数据库，不能把回执中的完整数据校验写成本复核另做了一次。

首次 `docker create` 的 stderr 被原发布器隐藏，准确失败原因无法追溯。可以确认的是：**创建失败后的核查发现 CA 宿主路径变为目录，阻止原容器恢复**；不能把该发现直接写成首次 create 根因已经证实。

新 guard 证明的是检查当时宿主路径存在且类型与活容器一致；它不证明同类型文件的内容／inode 相同，也不锁住外部清理者。继续发布仍须保留现行发布协调和实际配置／镜像回读。上述范围是补丁的适用边界，未发现本次新增的可复现功能缺陷。本复核不代表新候选已经正式生效。
