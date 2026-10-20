# Group 2 独立复核记录

本组初查发现 1 个 P1 引入缺陷：跨请求缓存会掩盖原件删除后的不可用状态。实现方已修复，我用同一真实私有夹具复验通过。最终开放缺陷为 0，`group_2.jsonl` 为空；原缺陷、修复与复验结论保留在 `group_2-resolved.json`。

本组独立于实现，只读取候选代码并运行私有夹具，不修改实现、正式数据库、正式服务或资源配置。复核基线为 desk `254d509cbe644f75e90344bc1ae40b7279aa418f`；复核的候选文件摘要见 `group_2-source-hashes.json`，后续这些文件变化需按影响复核。

## 范围与方法

核心文件为 `audiovisual.py`、`editing.py`、`editing_api.py`、`editing_review.py`、`entity_contract.py`、`production_breakdown.py`、`production_current.py`、`production_scope.py`、`reference_candidates.py`、`ui_projection.py`。共享边界为 `read_cache.py` 与 `server.py` 的返回与失效处理。

按 bits-code-guard 通用工作流 Step 3.1–3.4 完成：先读新旧 diff、变更函数完整上下文与一层直接调用方，再检查逻辑、业务语义、安全、并发、健壮性和性能；仅报告新引入且有明确触发路径的问题。全部为 Python，没有适用的 Go 或 TypeScript 语言专项。风格问题未报告。

进一步沿直接调用读取了 material_plans、material_review、list_reading、production、shot_references、production_media、editing_worker、business_codes 与相关前端摘要读取使用点。重点确认当前/准确历史引用、缓存依赖、评论目标附加、字层每个 entry 绑定、候选摘要与实际选择的验证边界。

## 行为证据

`group_2-probes.json` 记录这些私有验证：

- 首次读取已选需求后删除真实原件。修复后跨请求 entity_workspace 与直接重建都报告缺失；再执行真实候选选择被拒，需求正文未改变。
- 云候选摘要使用 2 个真实候选的元数据夹具，`materialize` 和 `asset_path` 调用均为 0；可用性均为 `unknown`，没有把目录登记说成实际可读。
- 3 个真实 owner 的批量准确 scope 查询与 HEAD 旧 direct_materials 完整返回值相等。
- 成片摘要目录的准确 output 顺序和所选 get 返回值与旧接口一致；不指定 summary 的旧接口仍有 episodes、projects、outputs、jobs；只读事务与请求缓存退出时释放。
- 合成的真实 JSON 字层包含 2 个 entry，同一只读范围内只做 1 次原件校验。缓存命中后仍拒绝不存在的 entry、已变化的实时归属与随后被篡改的原件。

上述验证已整理为可重放的 `group_2_probe.py`，在最终跨组复核时独立运行 **5/5 通过，1.156 秒**；日志为 `group_2-replay-tests.txt`。从 desk 工作区执行 `PYTHONPATH=.:tests python3 "$STORY_WT/.runtime/performance/independent-review/group/group_2_probe.py" -v`，其中 `$STORY_WT` 是主任务工作区。脚本沿用临时私有夹具，批量 scope 对比读取上述准确 Git 基线；不读写正式实例或云原件。

运行 5 个现有测试类，共 32 个用例：MaterialSourceWorkspaceTest、ProductionScopeTest、AvReaderTest、ReferenceCandidatesTest、TimelineReviewTest。候选与独立导出的 HEAD 基线均为 24 个通过、8 个错误；8 个错误的测试身份及异常原因一致。3 个来自旧 ProductionScopeTest 历史/归属夹具，5 个来自 AvReaderTest 的素材标题/生成输出名称契约夹具。它们不是本次新增缺陷，也未算作通过。完整日志为 `group_2-candidate-tests.txt` 与 `group_2-HEAD-tests.txt`。

## 证据边界

当前结论是本组代码与私有行为复核，不替代全量测试、正式部署、真实浏览器、VPS、性能指标或完整恢复验收。评论新鲜度通过缓存依赖和每次附加目标的调用链审阅；本组没有向正式实例写测试评论。测试所需原件仅为临时合成媒体和 JSON，临时实例由夹具正常退出清理；无外部生成调用。
