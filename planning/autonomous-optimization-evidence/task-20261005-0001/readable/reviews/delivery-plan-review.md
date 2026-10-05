# 本轮双仓与正式服务交付路径审计

任务 `task-20261005-0001`。本记录来自只读规则、脚本与现有基准审计；没有执行 prepare、build、apply、recover、Git 集成／推送、正式数据库写入或容器切换。后续仅在主协调授权范围内，为代码发布脚本增加本任务身份及测试；该部分由本记录作者实施，必须由主协调独立审阅。

## 可复用入口与本轮边界

本轮应复用 **`scripts/material_review_release.py` 的代码发布流程**，而非执行前置任务的迁移发布器。该脚本明确不导入业务数据、不生成或采纳作品、不推送、不调用任务完成；apply 内串行完成受控系统 fast-forward、服务切换、只读备份及历史保留检查。

下列入口不能直接重放：

- `scripts/autonomous_optimization_release.py` 顶层 prepare/apply/recover 包含上一轮 PROJECT 三字段及版本 14 的准确更新，`TASK` 也是 `task-20261004-0002`。本轮只复用其镜像、容器身份、快照及 Compose 辅助函数，不能沿用旧业务更新或一次性 ultra 发布例外。
- `scripts/ui_material_model_release.py` 是前置 `task-20261004-0009` 的素材物理迁移与逆迁移流程。本轮没有 schema、素材数据或公开导出增量，不能调用它的 apply/recover、WAL 清理、prepare_legacy_runtime 或重放旧迁移。
- `scripts/integrate_generation_review_system.py` 只负责确认后的系统仓准确 fast-forward；不部署、不推送、不写库、不完成故事任务。代码发布 apply 已调用它，不需再手工重复合并。

已只读核对通用系统 AGENTS/README、故事任务规则、工作区流程、前置交付文档、三个发布脚本及集成器。基准记录说明正式容器的 54 个系统源文件曾与本轮基准逐文件一致；本审计未再次运行 Docker，实际服务身份最终仍由 prepare/preflight 和执行时检查决定。

## 确认前可完成的准备

1. 完成系统代码、说明及独立验证，提交系统任务分支；在该 worktree 获取并合并最新 `origin/main`，核对系统目标仍为预期本地 main 与已记录远端。任何新增合并按实际影响补验，不在系统主目录开发。
2. 故事候选更新 `config/instance.json.review_desk_commit` 为系统完整候选 SHA，准备报告、STATE/KNOWLEDGE、操作顺序与证据。提交全部应交付文件，再调用本任务 `_prepare_integration` 合并故事最新 upstream；冲突仍在任务 worktree 解决、提交和重试。系统候选、故事候选及两个原目标均取实际回执，不填写猜测值。
3. 使用本任务已扩展的代码发布身份生成新的不可变 bundle，保存在本任务 `.runtime/autonomous-optimization/`，不可复用旧任务 bundle。脚本自身及被复制 helpers 必须来自已提交故事候选，保证用户审阅的代码与执行代码一致。
4. 本地构建候选镜像、核对镜像内完整源码哈希，并进行只读 preflight。完成必要隔离镜像验证后展示两个候选、两个 `main / origin / refs/heads/main` 目标、manifest 与 image receipt 哈希、预览与验证结果、正式操作及恢复顺序。准备和构建不等于用户确认。

由主协调根据实际完整 SHA 填入以下变量后执行；此处只是建议命令，尚未运行：

```bash
python3 scripts/material_review_release.py prepare \
  --task task-20261005-0001 \
  --system-worktree .runtime/autonomous-optimization/system-worktree \
  --bundle "$RELEASE_BUNDLE" \
  --story-candidate "$STORY_CANDIDATE" --story-target "$STORY_TARGET" \
  --system-candidate "$SYSTEM_CANDIDATE" --system-target "$SYSTEM_TARGET"
python3 scripts/material_review_release.py build --bundle "$RELEASE_BUNDLE"
python3 scripts/material_review_release.py preflight --bundle "$RELEASE_BUNDLE"
```

`RELEASE_BUNDLE` 必须是不存在的新任务运行目录；四个提交必须是完整 SHA。最终 prepare 之后若代码、数据输入、目标或 helper 变化，需要重新准备并补验相应范围，不能继续用旧哈希请求确认。

### 镜像与静态文件可以在确认前固定

现有 prepare 从**已提交系统候选**逐文件 `git show` 复制 `review_desk/`，其中包括 Python 与 `review_desk/static/` 的 CSS、JS、HTML。发布 Dockerfile 以当前准确旧镜像 ID 对应的固定本地标签为基础，只移除 `/app/review_desk` 并 COPY 新目录；build 使用 `--pull=false --network=none`，不执行系统仓普通 Dockerfile 中的 apt-get，不需要拉取基础镜像或接触业务库。构建仅产生本地候选镜像和任务 bundle 回执。

Nginx 当前通用配置的 `/` 全量代理到 app:8765；静态文件由 Python 从包内 static 路径提供。因此本轮无需新 static 绑定卷、复制到主目录、重建 Nginx 镜像或使用临时源代码挂载。source_check 会比较完整文件集合及 SHA，能发现遗漏旧文件或 COPY 内容不匹配。

正式配置仍使用不可变 release 目录中的 `config/instance.json` 与 `content/production-approach.json` 只读挂载，主故事目录 `/instance` 保留数据库与素材。代码发布器目前要求 production-approach 与正式覆盖文件相同；若本轮将来要修改该文件，必须另行审阅实际差异与发布规则，不能为了通过而删掉检查。当前 root 的 UI 文案修改位于系统前端，不自动意味着该故事文件也改动。

## 确认后的唯一串行顺序

1. 用户明确确认当前完整候选及双仓 `main / origin / refs/heads/main` 目标后，调用 `material_review_release.py apply --bundle ... --apply --manifest-sha256 ... --image-receipt-sha256 ...`。内部重新校验身份、候选、旧目标、helper、镜像、旧 Compose/挂载及 CA，持有共享发布／系统集成锁，受控 fast-forward 系统 main；复制必要不可变发布文件到正式 `.runtime/service-releases/`，以固定 Compose 切换 app 和 Nginx。原件和活库继续使用原路径，业务增量为 0。
2. 复用 verify_service 的容器镜像、源码哈希、准确挂载、实例文件及 3000/64401 接口回读；对正式页面只做一次受影响必要验收：素材页/关键卡片读取、桌面评论避让与窄屏行为、准确版本／草稿/锚点保留。测试评论或采纳不得写正式实例；用已有内容做只读验收。运行回执留 task bundle/run，不改已确认候选。
3. 系统仓按已确认目标执行普通 push 到 `origin refs/heads/main` 并回读完整 SHA。必须仍是已确认候选，无 force 或绕过远端分叉；系统变更若需合并新远端，在任务 worktree 处理、补验并重新确认。发布器本身不 push，不把 apply 成功当作已推送。
4. 执行故事任务 `codex.project task _complete -g creative -p SnakeSlayingRecord --task task-20261005-0001 --note '准确验证与发布回执'`。它是最后的受控故事集成、自动推送与回读入口，不提前执行，也不手工合并故事主目录。复用完成回执，不再重复全套 Git/测试查询。
5. `_complete` 成功后结束本任务文件写入和正式操作，只读报告；保留 worktree、分支及不可变服务 release。正式挂载是既有永久部署约定，不是需在完成后撤除的临时预览挂载。正常退出会话才释放运行锁。

以上沿用现有代码发布顺序，使正式必要验收在任务完成前结束。确认等待不延长优化预算；必须提前完成可执行流程，不在确认后临时研究或修改发布器。

## 恢复必须保存什么

确认前的 manifest／bundle 至少保存并校验：旧 app/代理准确镜像 ID、本轮候选镜像 ID及源码哈希；旧容器过程配置、重启策略、环回端口及 mounts；旧 Compose 文件路径与哈希；旧 config/approach 挂载源文件与哈希；CA 位置及哈希；环境变量名称；两仓候选与原目标；执行 helper 哈希。旧镜像及旧不可变挂载目录必须仍可用，不能清理。

环境秘密不写入报告、日志或 bundle。既有 compose_up 从当前容器内存读取环境并仅通过子进程环境透传；若容器已被移除，当前恢复入口不能凭 bundle 重建秘密，应保留现场并走既有操作者凭据恢复渠道。不要为了自动恢复复制 `.env` 或回显 docker inspect 的完整 Env。

apply 的 before.sqlite3 是**只读一致备份与审计基准**，不是恢复时覆盖活库的来源。本轮无 schema 或业务变更，运行失败恢复只切回准确旧镜像和旧挂载，不恢复数据库、不 reset Git、不重放旧素材逆迁移；新产生的真实评论与历史保留。

代码发布器的 apply 当前没有承诺任意失败自动回滚，失败时应停在明确阶段并回读实际容器身份；准备好同 bundle、同两个确认哈希的 `recover` 命令。调用前额外确认旧镜像与旧覆盖文件字节仍与 manifest 一致，当前运行仅是本候选或原版本；未知第三方容器／挂载不得覆盖。recover 仅解决运行态，系统 main 或已推送提交不会倒退。

恢复窗口限定在故事 `_complete` 成功前。若故事已集成但推送未完成，优先按回执安全重试 `_complete`；若必须改变候选或部署方案，另行准备、补验及确认，不能沿用本次完成授权继续写文件。完成后若需回退，作为新的受控工作办理。

## 本轮已实施的有界入口扩展与待验证

主协调授权仅修改 `scripts/material_review_release.py` 和 `tests/test_material_review_release.py`：已新增 `task-20261005-0001 → autonomous-20261005-0001`，默认旧 task 不变；现有命名、bundle prepare/load、错配任务拒绝、故事已集成拒绝用例加入本任务。没有改变 apply、恢复、数据保留、锁或推送流程。

主协调已独立审阅一行身份映射及四类测试扩展，回报未见身份、默认或停止校验削弱。随后在主协调授予的 ≤30 秒独占窗口运行 `python3 -m unittest discover -s tests -p 'test_material_review_release.py' -v`：**9 项通过，0.343 秒，退出码 0**，原始日志见[身份映射聚焦测试](delivery-prefix-tests.log)。本任务不继承前置 task-0007 的“故事先集成”特例；错配任务名在任何 Docker 操作前拒绝，旧默认继续兼容。测试窗口已明确释放。

本项未执行真实 prepare/build/preflight/apply；这些由主协调在完整候选冻结后办理，模拟测试和本审计不替代实际镜像、服务与交付结果。
