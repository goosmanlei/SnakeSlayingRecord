# 评论创建与内容缓存失效补充复核

未发现新增排除 `business_comments`、`production_comment_quotes` 后产生的开放 P0–P2 缺陷。独立真实制作评论探针首次运行 **2/2 通过，0.949 秒**，覆盖实际 SQLite 写入和本机回环 HTTP 返回。`content-domain-followup.jsonl` 为空。本结论补充此前跨组报告，仅更新评论表排除及新鲜度部分；正式 UI、部署和性能验收仍不在本复核范围。

## 依赖核对

`read_cache.token(domain='content')` 现排除四张表：`comments`、`comment_events`、`business_comments`、`production_comment_quotes`，其他表仍影响内容缓存代际。按照 bits-code-guard Step 3.1–3.4，检查新旧变更、完整相关函数、直接调用方与逻辑/业务/并发/健壮性/性能维度；仅判断新增缺陷，不修改实现。

- HTTP 内容域仅用于 `/api/production/index`、`/api/production/materials`、`/api/business-codes`。索引和素材列表投影不返回评论正文、状态或评论计数；其中 `candidate_count` 来自 `production_candidate_targets`，素材分组数量来自素材和使用关系。`business_codes.display_dump` 返回业务对象编号，不返回评论编号。
- 投影层的 `material_entries`、`_material_av_catalog` 依赖素材、准确 scope、别名、候选和业务对象编号，未沿调用链读取新增排除的评论表。未展开镜头工作区只缓存原有允许的纯结构；`_comment_targets` 在缓存命中后仍读取评论目标及相关关系，历史/关系评论目标不会被纯结构缓存吞掉。
- `business_comments` 只用于评论编号分配、恢复及响应装饰；`annotate` 将编号加在具有评论 id、anchor 和 body 的评论上。包含评论的响应不使用内容域缓存；评论 API 本身绕过 HTTP 响应缓存。
- `production_comment_quotes` 由真实制作评论创建写入，`Store._comment` 经 `production_current.comment_context` 读取，返回原内容哈希、准确修订、摘录及是否仍匹配当前内容。其余引用是导出/恢复或重置、合并时保留评论的写入路径，不是上述纯内容投影。评论创建、正文事件及制作内容变化仍会使完整域失效。
- breakdown 返回当前 `comment_index` 与准确 episode/material 目标，使用完整域。`_comment_targets` 只补目标；评论状态、正文、编号和摘录由独立评论读取返回。

## 私有行为证据

使用已有合成夹具建立当前制作模型、真实 AV 集/场/镜、镜头声音需求和业务关系；通过正常 `Store.create_comment` 创建需求 Prompt 文本评论与镜头业务关系整体评论，没有直接伪造评论表。

1. 创建前后的表代际比较确认，变化恰为上述四张评论表；内容域 token 相同，完整域 token 改变，两张新增排除表各新增 2 行。
2. 预热后读取实体索引、普通素材列表、准确视听集紧凑素材列表、业务编号这 4 个 HTTP 查询。创建评论后全部仍为 `X-Review-Cache: hit`，解码后的完整 JSON 与创建前逐值相等。
3. breakdown 在创建评论与关闭评论后均重新构建，索引立即包含新评论及 CLOSED 状态，集的评论目标包含需求的准确 object/revision。
4. 未展开 shot 工作区的结构构建函数只执行 1 次，评论目标补齐函数执行 2 次。缓存命中后的目标新增刚被评论的业务关系准确身份；预热时该目标不存在于工作区评论列表。
5. 评论 API 立即返回新评论 `C001`、原准确修订、原文本 anchor 和原内容 SHA256，`matches_current=true`。
6. 正常导入后续制作内容后，内容域 token 改变，原评论摘录与哈希保留，`matches_current=false`。错误 object/revision 组合和旧 `expected_edit_token` 分别被拒绝，未插入额外评论。

可重放脚本为 `content-domain-followup.py`，结构化结果为 `content-domain-followup.json`，运行日志为 `content-domain-followup-tests.txt`。从 desk 工作区执行，`$STORY_WT` 是主任务工作区：

```sh
PYTHONPATH=.:tests python3 "$STORY_WT/.runtime/performance/independent-review/group/content-domain-followup.py" -v
```

另已读取实现方新增的 `tests/test_read_cancellation_contract.py` 普通 EPISODE 评论用例，未把它算为本次独立运行结果。本次实际探针覆盖会写 `production_comment_quotes` 的制作评论，而不仅是普通 EPISODE 评论。

## 身份与边界

源码基线与复核文件摘要见 `content-domain-followup-source-hashes.json`。本报告说明的是该候选的依赖和功能正确性，没有量化生产性能收益。未修改生产实现、正式测试、正式数据库或服务；没有访问 OSS、凭据、浏览器、VPS 或外部生成服务。临时 SQLite、文件和 HTTP 服务由夹具正常清理。
