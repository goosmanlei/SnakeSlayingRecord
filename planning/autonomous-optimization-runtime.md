# 自主优化实验的时间控制

本工具供[自主优化任务](autonomous-optimization-task.md)的未来 mrun 执行会话使用。发布准备阶段只交付脚本、说明和验证证据，不启动计时、监督进程、Goal 或优化工作。

工具把首次任务执行时间保存为 T0，固定在六小时后允许正常结束、九小时进入收尾、十小时停止本任务。暂停、等待、断线和离线均计入这段连续墙钟时间。恢复继续使用原 T0，不能靠重启工具获得新预算。

## 启动与恢复

使用 macOS 自带或已有的 Python 3 标准库。脚本从 `~/bin/codex.project.d/scripts/task_runtime.py` 复用已安装的共享 App Server 连接；只检查现有服务，不启动另一台 App Server，不改任务账本。

在启动器给出的本任务 worktree 内，先读任务说明并执行启动器要求的 `task _bind_session`。然后由根执行代理运行：

```bash
python3 scripts/autonomous_optimization_guard.py start \
  --project '<启动器给出的主项目绝对路径>' \
  --task '<本任务 task ID>'
python3 scripts/autonomous_optimization_guard.py status
```

命令中的占位文字须替换为启动器提供的真实值。脚本所在项目目录必须与主项目账本登记的本任务 worktree 一致；不要复制脚本到另一个工作区运行。`CODEX_THREAD_ID` 必须是账本已绑定的根会话，账本必须是当前 `running` 的 `mrun`，账号目录和执行租约也须吻合。共享服务没有继承租约环境变量时，工具沿用 `codex.project` 已有的活动启动器锁核验，不要求用户手工填写租约。

首次启动从共享服务的轮次列表按时间正序读取，核对 mrun 执行标记、任务 ID 和该轮 `startedAt`，不使用草稿创建时间、任务发布时间或运行命令的当前时间。延迟初始化也会找回已经经过的时间；证据缺失、归属冲突或时间无效时拒绝初始化。后续启动不改起点。`start` 会启动带独占锁的后台监督进程；重复启动不会叠加有效监督进程。

输出中的 `times_utc` 是首次执行时间及三个节点的 UTC 时间，`elapsed_seconds` 是已过秒数。`watcher.supervision_confirmed=true` 表示本任务监督锁被持有，且最近 45 秒内有心跳；它不代表远程停止已经成功。检查 `last_error`。尚未确认监督生效时先解决初始化问题，不展开实验。

每次恢复、每批结束和每次委派前运行：

```bash
python3 scripts/autonomous_optimization_guard.py check
python3 scripts/autonomous_optimization_guard.py status
```

`status` 只读，`check` 会补执行已到期的动作。若监督进程因机器重启等原因消失，原根会话经 mrun 恢复后重新运行 `start`；也可对已初始化的状态运行 `watch --daemon` 来恢复监督。直接 `watch` 是前台运行方式。已经结束的守卫不会再次启动、提醒或唤醒会话。

## 登记子代理

所有登记由根代理执行；子代理不能以自己的 `CODEX_THREAD_ID` 替代根身份登记。每次创建子代理时，初始消息只能要求它等待登记与后续授权，不能同时给出实质优化工作。根代理取得线程 ID 后运行：

```bash
python3 scripts/autonomous_optimization_guard.py register --thread '<子代理线程 ID>'
```

成功登记且时间仍允许后，根代理才用 `followup_task` 下发实际工作。子代理需要继续委派时也采用相同顺序，由根代理登记新后代，再授权工作。登记会沿服务返回的父子关系一直核对到本任务根会话，并将途经的后代一并纳入停止范围；兄弟会话、其他任务和身份冲突均拒绝登记。不要把独立手工创建的线程当作后代；只使用真实父子关系。

工具只操作根会话与这些经核验的后代。未登记会话和任意外部进程不在自动停止范围，因此不能先让未登记的子代理开展工作再补登记。

## 收尾和结束

根代理应从第一份有效检查点开始持续维护 `planning/autonomous-optimization-run-report.md`，并在进度消息中提供固定链接；九小时收尾时再次提供。硬截止可能直接中断当前回复，不能承诺届时一定还能发送最后一条聊天消息。

九小时后，监督进程仅对根会话当前活动回合发送一次收尾提示。没有活动回合时保留待提醒状态，等待下一次活动检查；不会创建或唤醒会话。执行代理据此停止新大项，完成报告、验证、独立审查和候选。

达到任务收敛标准且已满六小时、尚未满十小时时，先完成报告和候选，再由执行代理将已经实现的本任务 Goal 标为 `complete`，随后运行：

```bash
python3 scripts/autonomous_optimization_guard.py finish --reason converged
```

该命令要求报告已保存、根 Goal 已完成；六小时之前及十小时整点以后均拒绝使用此原因。正常结束会暂停已登记后代仍未完成的 Goal、中断其活动回合，保留根回合完成交付回复。脚本本身从不把 Goal 标为完成。

仅在用户明确要求提前结束时运行：

```bash
python3 scripts/autonomous_optimization_guard.py finish --reason user_stop
```

用户结束优先于六小时下限。普通暂停、等待、断线不是 `user_stop`。十小时到期会自动触发截止，也可以在原会话已恢复且时间到期后显式补执行：

```bash
python3 scripts/autonomous_optimization_guard.py finish --reason deadline
```

`user_stop` 和 `deadline` 先把原因、原时间节点及当前报告的路径和校验值写入停止回执，再由独立监督进程暂停根 Goal 并立即中断根活动回合，随后停止已登记后代的 Goal 和活动回合。报告不存在时如实登记缺失，停止动作不会为等报告而延期。已经到十小时的结束请求统一按截止处理，不能包装成正常收敛。

远程中断请求被接收不等于停止已确认；工具会重新读取活动状态。出现错误时保持 `phase=stopping` 和 `stop.complete=false`，保存具体错误并继续重试本任务范围，不再发九小时提醒，也不新建会话或把 Goal 恢复为 active。只有本轮所有必需停止动作得到核验后才保存 `phase=finished` 和 `stop.complete=true` 并退出监督。正常结束发生子代理停止错误时，也保持待重试；如期间到达十小时，按截止处理根会话。

## 回执与限制

所有运行文件都位于本任务 worktree 的 `.runtime/autonomous-optimization/`：

| 文件 | 用途 |
| --- | --- |
| `state.json` | 原 T0、固定节点、身份、已登记后代、提醒和停止状态；原子写入并有文件锁 |
| `stop-receipt.json` | 结束原因、报告校验值、各会话停止结果、错误与重试次数 |
| `watcher.json` | 本任务监督进程及最近心跳；结合监督锁判断是否有效 |
| `watch.log` | 监督进程异常输出 |

停止回执是运行证据，独立于面向读者的 Markdown 报告。重试成功后仍保留首次失败和最近一百次失败记录。报告只覆盖其最后一次实际更新的检查点；回执时间更晚时须说明二者差别。不要删除状态文件重新计时，也不要把运行文件提交或复制到主项目作为另一份活跃状态。

监督最多每十五秒检查一次，并在下个九／十小时节点前缩短等待；每次服务请求有八秒总超时。机器休眠、服务故障或网络不可达时无法保证恰在十小时完成远程停止，回执必须保留实际重试和确认时间。后台进程不安装系统启动项；机器重启后由原 mrun 会话先恢复检查，预算不延长。回合中断也不等于撤销已提交的外部操作或终止所有 shell 子进程，执行中仍须避免跨截止点的无界操作。

## 已验证范围

发布准备阶段检查了当前安装版本生成的协议 Schema，并通过现有 mrun 根会话的真实只读查询验证：分页轮次及首条输入可以恢复准确首次执行时间，最新轮次可定位当前活动回合，`thread/read` 和 `thread/goal/get` 可通过现有共享连接访问。没有执行真实 Goal 修改、中断或十小时实验。

隔离测试使用临时目录、假服务和注入时钟，不会启动真实守卫或修改任务账本。运行方式：

```bash
python3 -m unittest discover -s tests -p test_autonomous_optimization_guard.py -v
```

覆盖时间边界、延迟与分页恢复、租约与身份、兄弟会话拒绝、后代 Goal 清理、停止回执先落盘、断线及部分失败重试、无唤醒重启、监督去重与启动失败、请求总超时。实际运行开始后仍须核对真实监督心跳和本任务状态，不能把这些隔离测试写成真实停止动作已经验收。
