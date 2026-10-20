# 成片范围评论字层预读独立复核

归因成立，且已在准确 HEAD `254d509cbe644f75e90344bc1ae40b7279aa418f` 独立复现：离线原件包和模拟云冷缓存均在事务内首次读取选中字层时得到 `resource was not preflighted before the database transaction`，没有保存评论。它是 HEAD 已有缺陷，不是本次性能改动引入。

当前最小修复的六项独立探针全部通过；最终运行 **6/6，1.049 秒**。没有仍开放的 P0–P2 新缺陷，`comment-preflight-followup.jsonl` 为空。该结论覆盖真实 Store 评论创建及原件读取链，不替代主任务的真实 UI 重新提交验收。

## 原因与修复顺序

按 bits-code-guard Step 3.1–3.4 读取新旧函数及直接调用方。`Store._create_comment` 原先在事务前调用 `validate_target`；后者的 `validate_anchor` 会核对选段、轨道、元素和准确绑定。无追加关联时，选中 clip 通过 `verify_binding` 验证，而 text 的 `material_ref` 仅被附到预期元素后参与一致性比较。由此不会在事务前读取字层 JSON。带追加关联的选段也不会由这一层预读所有绑定原件。

原实现直到 `BEGIN IMMEDIATE` 和 `frozen_physical_hashes` 内才调用 `validate_new_anchor`，该函数再验证最新关联及选中 binding 的实时归属。选中字层因而首次进入 `text_layer_document` → `asset_path` → `resources.materialize`；资源冻结作用域发现原件没有在本次操作租约中预读，即拒绝新的读取。HEAD 具有同样调用顺序和冻结检查。

修复在事务前增加 `validate_new_anchor`，将字层原件的下载、全字节校验和租约获取移到写锁之前；事务内原调用保留，继续拒绝预检后变化的关联、归属或原件。

复核中另指出，事务前新调用应在已有同 id 评论的 `existing/matches` 幂等返回之后。若直接紧跟 `validate_target`，后来追加的关联可能让已经保存的旧评论重放先失败。实现方已按此顺序调整；当前探针实际确认已有评论在关联升级后仍原样返回，评论和事件均不重复。此项是补丁位置的静态反馈及修复后验证，没有伪称运行过错误位置的失败版本。

## 可迁入的独立测试

`comment-preflight-followup.py` 使用已有隔离成片夹具、真实 JSON 字层原件和 SQLite。默认运行六项 unittest，可迁入 tests；没有修改正式测试或实现。

1. **冷离线字层范围。** 实际 `Store.create_comment` 保存准确文本轨道选段；`validate_new_anchor` 的观察顺序为事务外、事务内，评论 anchor 与原请求相同。
2. **冷模拟云字层范围。** 保留真实 `materialize`、`_remote_hash`、SHA256、资源租约与物理身份校验，仅替换 SDK 请求对象和客户端传输。每次请求断言 bucket/key/version 精确匹配且数据库不在事务中；字层下载 1 次，响应 body 全部关闭，最终评论保存成功。
3. **离线缺字层原件。** 删除夹具的准确原件包后，创建在第一次 `BEGIN` 之前失败，没有评论写入；没有遗留 `.part` 或 `.reserve`。
4. **预检后原件变化。** 在事务外校验完成后改动已租约字层文件的真实字节，事务内因租约物理身份变化拒绝，评论回滚，事务及作用域释放。
5. **预检后关联升级。** 在事务外校验之后，通过另一 SQLite 连接正常追加第二版关联；原请求在事务内校验最新关联时被拒。第二版关联确实提交，但没有插入评论。
6. **已保存评论幂等重放。** 保存第一版关联下的评论，再正常追加第二版关联；同 id、同正文及 anchor 重放直接返回原评论，只有 1 条评论事件，未再调用新评论校验。

结构化结果为 `comment-preflight-followup.json`，最终日志为 `comment-preflight-followup-tests.txt`。脚本首次行为执行也是 6/6 通过；随后将 patch 清理收敛为逐个释放本脚本所建 patch，并复跑得到上述最终结果。

从 desk 工作区运行，`$STORY_WT` 是主任务工作区：

```sh
PYTHONPATH=.:tests python3 "$STORY_WT/.runtime/performance/independent-review/group/comment-preflight-followup.py" -v
```

## HEAD 对照与边界

从准确 HEAD 只读导出 `review_desk` 和 `tests` 到自动清理的临时目录，在该目录运行相同脚本并显式设置 `COMMENT_PREFLIGHT_EXPECT_FAILURE=1`。两条冷读取用例都断言并观察到上述精确异常，`validate_new_anchor` 仅在事务内执行，字层还未下载，评论数为 0。结果见 `comment-preflight-followup-HEAD.json`、`comment-preflight-followup-HEAD-tests.txt`。日志中的 2 个 ok 是“旧缺陷复现符合预期”，不是旧功能通过；另外 4 项修复后安全测试在 HEAD 对照中明确跳过。临时 HEAD 导出已清理。

源码与夹具身份见 `comment-preflight-followup-source-hashes.json`。没有访问真实 OSS、凭据、正式业务库、正式服务或浏览器；模拟云测试不能代替云账号权限和网络验收。字层逐 entry、实时归属和物理身份的其他校验沿用此前 group 2 的独立证据，本次不扩展为完整音视频质量或发布验收。
