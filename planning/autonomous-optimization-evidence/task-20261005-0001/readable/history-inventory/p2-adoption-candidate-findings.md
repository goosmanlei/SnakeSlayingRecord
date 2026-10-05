# P2 准确采用空下拉的独立调查与有界验收方案

**先前“没有合法候选”的解释需要更正：当前数据存在准确可选原件，P2 的下拉列表漏了素材加载。** 保留 `browser/P2-adoption-no-eligible-exact-candidate.json` 原文件名和内容，将它归为界面缺陷现象。源码根因已经确认；最新真实页面已加载候选并选择阿蘅准确声音记录与原件，未提交。最新独审见 `r2-ux005-selection-independent.json/md`，成功采用/冲突仍未验。此调查只用 SQLite `mode=ro` 和既有只读记录投影，没有调用接口、写入库、操作浏览器、运行测试或创建夹具。

## 实际数据与入口

正常 P2 路线为全剧制作 → 组合与历史 → E01 / S001 → 素材缺项检查 → 阿蘅基础音色需求 → 选择素材版本。可用于准确选择核对的当前需求为 `need-form-a-heng-blue-voice`，记录修订 3 / `f389f4a222e97b6d78cb20f7050e0c48df3d01111ac799709d55cf2609ac102f`；其当前范围是 `form-a-heng-blue` / `d059be7261d09c1d14859026c60d2114478d5e2bf9ce4a06759f5292b448dc16`。

相符原件是 `asset-fg3-aheng-voice-01` / `e522f05e989232e8323608cc74addd94b5e542c15c2d69692109c5fdd3e78ecb`，组成 `original`，14.5 秒、48 kHz、双声道。其候选引用指向当前准确需求，准确完整状态覆盖也相符，文件存在。它属于素材方案版本 2；当前版本 3 没有结果。这不使旧准确结果成为无效对象，也不等于用户已采用或听审通过。

另一清楚样本是阿禾：`need-form-a-he-base-overall` / `e1d41367c078bc766ebdbc61f198fd1e0694ab921b45b5bddee24cab598fb0a7` 对应 `asset-fg3-a-he-base-image-01` / `d71d936487d92793f28f793c7d6e0eca5051138762a7ee99ebb976959f793561`，原图 1086×1448、当前准确状态和需求一致，既有要求明确允许渠道最高原生尺寸。周掌柜整体则有两个真实对象候选可用于旧新原件列表核对。逐项准确字段、历史修订与文件名见同名 JSON。

这些样本只读核对了文件存在、媒体规格及准确状态覆盖；未重新全文件哈希或声称它们已令整场就绪。若在功能克隆做技术采用验收，应明确记录为可丢弃测试，不进入正式发布包，不能写 `accepted` 或借此替用户判断作品。

## 确认的缺陷链与最小修复

- `production_breakdown.index(history)` 只返回剧本依据、集场检查、动态分镜组合和输出工程四类；准确链接最多另加一个所选对象，并没有完整素材清单。
- `loadProductionWorkspace` 把该索引赋给 `state.productionRecords`。
- 缺项检查的每行没有 `candidates` 字段。`showProductionAdoption` 因而从索引筛选 `ASSET` 和同媒体类型，常规入口必得空数组。

根已同意：仅在采用编辑器打开且调用方未提供 `row.candidates` 时，按需读取已有 `GET /api/production?kind=ASSET`。保持既有同媒体原件选择范围，不把选择收窄为当前素材版本或只有需求明确关联的候选。加载时禁用确认，校验响应记录、编辑器连接状态、当前工作区和读取代次；迟到响应不回填已经关闭或切页的编辑器。读取失败保留用户上下文并允许再次操作。采用 POST 和冲突校验不变。

现有 GET **没有分页、文本或媒体过滤**，返回所有当前 ASSET 头；契约也包括占位。此快照 417 个当前 ASSET，`placeholder=true` 为 0。不要把当前数据没有占位推成接口会排除占位。选择对象后，既有 `GET /api/production?object_id=<id>` 返回该对象全部准确历史，前端校验所有返回记录的 `object_id`，再按具体 revision 和 component 选择；历史不会因为新头加载而自动替换。直接采用允许保留待审或占位关系，readiness 另行阻止占位就绪；本修复不应顺手改变这一业务契约。

需求单对象 GET 的 `candidate_records` 很适合解释出处，但仅返回明确关联的候选，不能直接代替此前允许选择其他同媒体原件的入口。

## 已就绪包与历史判断的范围

当前功能克隆 **采用关系为 0**。readiness 对必需槽位要求存在采用；因此不存在可以直接成功下载的已就绪真实范围，没必要重跑所有集场来证明这一点。不得删除必需项、改状态覆盖或自动认可作品来制造就绪。

现有 194 条当前判断中，49 条是 `state_title_only / keep` 命名复核；没有普通 target 范围的变更处理记录。命名复核只允许准确的状态标题变化和 `keep`，不能拿它改成 `rework` 作为普通历史测试。其余包括既有采纳与待审结论，不能改写真实用户判断。P2 的“影响 187”只是读取，不是历史判断修订成功。

推荐把成功下载和普通变更处理放入另一个可丢弃最小实例；真实克隆只补已有数据的选择路线与界面缺陷复验。**以下是方案，尚未创建或运行。**

1. 复用 `tests/test_production.py::ProductionTest` 的现有隔离构造器，生成其技术用 1 秒 WAV、`recording` CALL、`voice` ASSET；不读取或生成故事媒体，不用密钥。新建一个测试 PREPARATION，source 指向夹具自带 episode，`checked=true, occurrences=[]`。一个必需 audio / post_audio 需求挂到这个准确 PREPARATION，entities/states 为空且 `specification={}`；只有这个槽位，不牵涉真实全剧需求。
2. 通过已有 `production.import_records` 给这个测试 ASSET 加该需求的准确 candidate reference。再创建它的第二个明确“测试元数据修订”，保留原文件和旧修订。需要不同原件时可用 `PackageReadinessTest.audio()` 的本地 PCM 技术数据，仍不得替换真实故事原件。
3. 复用 `ReviewServer`（`tests/material_ui_server.py` 的实际服务模式）开根分配的独立端口和目录。直接打开 `/?workspace=production.workspace&production_tab=history&production_object=<测试PREPARATION>`，从真实缺项按钮选择 `voice` 记录修订 1 / original，理由明确“隔离技术验收，不是作品采用”。保存后页面显示准确旧引用、ready 可下载；下载 JSON 和 `production-package` 目录包核对原件与依赖。
4. 两个编辑器读同一当前采用版本：甲改为记录修订 2 保存，乙仍持旧 expected_version 保存应冲突，保留乙输入。旧采用修订与原件保持。采用只在夹具库，不导出到正式库。
5. 包成功之后，只修改夹具 episode 的测试标题形成新修订；测试 PREPARATION 和需求仍引用旧修订，使缺项检查出现准确上游变化。记录一个普通 `target` 变更处理为 `keep`，再通过“修改变更处理”改为 `rework`；验证同 ID 的旧结论留在 history、旧编辑器冲突不覆盖。不要写真实 49 条命名复核，也不要造 `accepted`。

可执行的既有入口（命令均须在根批准并准备夹具后使用）：

```bash
PYTHONPATH=.:tests python3 tests/material_ui_server.py --port <根分配端口>
python3 -m review_desk --instance <夹具目录> production-import <测试记录包.json> --validate-only
python3 -m review_desk --instance <夹具目录> production-import <测试记录包.json>
python3 -m review_desk --instance <夹具目录> production-ready <测试PREPARATION>
python3 -m review_desk --instance <夹具目录> production-package <测试PREPARATION> --output <隔离输出目录>
```

第一个现有服务脚本可作独立素材浏览基座，本方案的 PREPARATION/槽位仍需由专用 runtime 包装器在其技术夹具上准备，不能误说已有脚本现在就包含该场景。浏览器采用用既有 `POST /api/production/adopt`；普通变更判断用 `POST /api/production/judgment`，二者都需要真实 expected_version。后台精确冲突与历史用 `tests/test_production_change_decisions.py` 现有模式补证，不以后台通过代替页面操作。

真实故事正文、当前实体/完整状态、准确旧引用、媒体文件、原任务评论、132 条当前采纳、49 条命名复核、正式库及性能冻结库均不在该夹具写入范围。保留所有前述原始证据；本调查没有落夹具。
