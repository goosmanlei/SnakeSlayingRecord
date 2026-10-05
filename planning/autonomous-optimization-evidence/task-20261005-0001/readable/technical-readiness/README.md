# 技术采用、下载与变更判断夹具

这份实例用于浏览器验收准确采用、旧版本保留、冲突、输入包下载，以及普通目标的变更判断。所有内容都是可丢弃技术数据；音频是本地合成的一秒静音。`instance/` 的生成基准为零采用、零判断；它随后已交根协调者用于实际浏览器验收，不能把生成基准当作当前库状态。不把本夹具导出到故事正式库。

本目录由 task-20261005-0001 的已登记 worker 创建。脚本依赖相邻 `../system-worktree` 的实际产品和测试构造器；命令以下均从故事任务 worktree 根目录执行。当前 Guard T0 为 2026-10-05 13:21:50 +0800，创建前核对过 armed、有效监督锁和心跳。worker 的准备与配置修复不使用浏览器、不启动服务、不写共享产品或测试；服务与浏览器操作由根协调者持有。

## 启动与入口

```bash
python3 .runtime/autonomous-optimization/technical-readiness/probe_server.py --instance .runtime/autonomous-optimization/technical-readiness/instance --port 62609
```

服务只绑定 `127.0.0.1:62609`；启动器核对实例标记、直接子目录和非符号链接数据库。停止服务保留实例和全部证据，不触发清理。

浏览器打开 <http://127.0.0.1:62609/?workspace=production.workspace&production_tab=history&production_object=technical-scene>。这是组合与历史入口，选择“技术分集一”，保留技术音频场的准确引用，打开素材缺项检查。只有一个必需音频槽位，没有实体或完整状态前置；生成时的缺项原因仅为尚未采用。根协调者随后已报告实际采用 voice 修订 2、0.1–0.9 秒且缺项为 0；当前准确状态以根的浏览器回执与实例检查为准。

准确输入在 `instance/technical-fixture.json` 和 `instance/baseline.json`，主要值如下：

| 对象 | ID / 准确修订 |
| --- | --- |
| 场次 | `technical-scene` / `41c661d1a0f2df294eb1dc95a41b09eaa31dd40627680e87c8030011d5681597` |
| 需求 | `technical-audio-need` / `55e0c53a5cf3f4c75ef3fa1b1417a50d28d0698ab4825075291115b6d5f85e96` |
| 初始分集 | `technical-script-e1` / `810f3e5affbe36cf0820d862b91a360f986f29a49f621b97fcfbe7327e4b5b43` |
| 旧可用音频 | `voice` 记录修订 **2** / `f41380e5d5015f6c2daa0e71b5ce0430c5e1af3697db6eae4dabe7484f9b61bd` |
| 当前音频 | `voice` 记录修订 **3** / `4ef11a2585bb8919555684af2edb86a96371b35b6acfa36973da4a13c8e387a7` |
| 文件组成 | `original`，1 秒、48000 Hz、单声道、16 位 PCM；96044 字节 |
| 原件及 SHA-256 | `0a8f76d89c709043814cb74f331a4578d17ff61256303bd0019a263d053f86e8.wav`；同名去后缀即哈希 |

记录修订 1 是构造器最初登记的静音；修订 2 增加准确需求引用，修订 3 只改变技术标题。三者使用相同原件。这里的记录修订数字不是素材方案版本，页面准确选择应使用“候选记录修订”。

## 浏览器验收顺序

1. 打开需求的“选择素材版本”，确认历史索引不含 ASSET 时仍能按需加载 `voice`。选择记录修订 2、`original`、入点 `0.1` / 出点 `0.9`。理由填“隔离技术验收，不是作品采用”。页面采用操作没有操作者字段；不要把操作代理推断成作品评论作者。
2. 确认采用后检查仍引用旧准确修订。后台预演已证明此时必需项为 1、缺项为 0，输入就绪且可以导出；浏览器仍须真实验收保存、写后可见性和下载。下载 JSON，再使用相同实例的 `production-package` 导出目录包，检查准确依赖和原件哈希。
3. 两个编辑器读取同一已采用版本。甲选择记录修订 3 保存；乙使用原 expected_version 再保存应冲突，保留乙输入且不覆盖甲。后台历史应包含两次采用；旧准确原件保持。
4. 完成包验证后，再由根串行执行下方 `advance-upstream`。它只把本技术分集标题修订为第二版，保留场次、需求和采用的旧依赖，不写真实故事。它要求该技术范围已就绪、分集仍为修订 1；重复执行拒绝覆盖。
5. 刷新缺项检查，会出现同一分集变化对**两个目标**的影响：采用关系与需求。选择其中一个普通目标，操作者填 `Codex technical fixture; not user acceptance`，理由写明技术验收，先记 `keep`，再从“修改变更处理”改为 `rework`。应使用同一判断 ID，历史保留先前 keep；旧编辑器再次修改应冲突。只复核一个目标时另一个仍待复核，整场不会自动就绪。不要使用 `state_title_only`，不要写 `accepted`。

```bash
python3 .runtime/autonomous-optimization/technical-readiness/check_fixture.py --instance .runtime/autonomous-optimization/technical-readiness/instance --action advance-upstream --output browser-upstream-change.json
python3 .runtime/autonomous-optimization/technical-readiness/check_fixture.py --instance .runtime/autonomous-optimization/technical-readiness/instance --action inspect --output browser-final-inspection.json
```

输出文件必须是本目录内新的文件；不覆盖既有回执。两条命令留给根在上述实际阶段执行，本次准备未执行。

目录包命令从系统 worktree 运行，输出须用尚不存在的新目录：

```bash
cd .runtime/autonomous-optimization/system-worktree
python3 -m review_desk --instance ../technical-readiness/instance production-package technical-scene --output ../technical-readiness/browser-package
```

CLI 会先读取 `instance/config/instance.json`，最小配置包含本夹具的 `id` 和 `title`，无凭证。`build_fixture.py` 现在随生成一并写入它。首次交付遗漏了此文件，导致根按上述命令执行时在 `review_desk/__main__.py:95` 报 `FileNotFoundError`。函数级预演只调用 `write_package`，没有覆盖 CLI 启动过程，因此其成功不能替代 CLI 验收。这是夹具交付缺口，非产品采用或原件问题。

此次失败原始输出在根会话工具 chunk `e3171b`；本目录 `cli-first-failure-summary.json` 只保存根转交的摘要，明确不是原始 traceback。最小配置已补齐，数据库和原件由根持有且未因本次修复写入；CLI 的一次重试由根执行，配置补齐本身不等于重试成功。浏览器下载工具曾超时重置，根另报告真实下载文件及 package 200；其内容核对由根继续，不以本说明宣称下载验收完成。

## 已有验证与重建

`build-first.log`、`instance-build-receipt.json`、`instance/build-inputs.json` 保存第一次构建的输入及结果。生产记录先 `validate_only=True`，再经现有 `production.import_records` 实际导入；SOURCE、结构和分集通过原有合法入口准备。没有结构确认、采纳或作品接受。构造器自带一个未使用的 `episode` 技术测试对象及其测试文本，保留在库中；它不在技术剧本版本与场次引用链中。

构造器原本清理自己的 TemporaryDirectory；此脚本把它限定到本目录 `.build-*`，复制到全新实例后只清理该临时目录。目标实例存在则拒绝运行，不删除、不覆盖。需要重建时使用新名字，例如：

```bash
python3 .runtime/autonomous-optimization/technical-readiness/build_fixture.py --name instance-rebuild-01
```

逻辑与原件可复现；创建时间进入部分源版本，重建时准确版本可能变化，应读取新实例标记，不能照抄上表旧哈希。

`preflight-first.json` 是对 `preflight-instance/` 独立副本的后台预演：旧音频采用可就绪、目录包产生原件与 manifest、旧 expected_version 采用冲突、keep→rework 使用同判断 ID 且保留历史、旧判断版本冲突。预演前后浏览器实例数据库 SHA-256 一致。第一次预演成功，没有失败需要掩盖；该结果不代表页面验收。后续在检查脚本中增加了两项对已留证值的断言（keep 减少一个待复核目标、rework 恢复该目标），未重复创建预演。

预演脚本必须在源实例服务停止、没有写入时运行；它复制到新的 `preflight-instance/`，该目录存在时拒绝重跑。这是小型后台功能检查，不是性能测量。检查/服务脚本均只接受本目录内带标记的实例。
