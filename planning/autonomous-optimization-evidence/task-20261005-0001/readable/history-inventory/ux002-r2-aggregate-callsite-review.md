# AO-UX-002-R2：逐镜小卡的历史生成结果范围

D1 已确认存在与素材管理相同的表达缺口：小卡的“已生成”表示这项持续需求任一版本曾有真实原件，点开默认当前素材版本仍可能未生成。此处没有证据表明系统错误采用了旧结果；问题是生成状态的展示范围没有说明。P1 复用同一小卡和聚合字段，静态存在同类路径，但当前无实际生成视频，不能写成P1已真实复现。

这是基线 `b874b959af9c918a482e8488dc25cb0204ab5772` 已有的行为，AO-UX002 只修改D3列表，修复范围不完整。`git show`独立确认基线已有相同material_entries聚合、scene继承generated、逐镜materialSmallCard调用和无归属需求candidate_records计数。不要把本发现记为本轮引入的数据或采用回退。

本次只读代码和根保存的两份真实页面证据，不操作浏览器、发API请求、运行测试或修改产品。

## 直接页面证据

- `../browser/R2-D1-history-audio-current-empty.json`：D1/S001多个明确关联镜的小卡显示“阿蘅·日常洗旧青衣 · 阿蘅 · 基础音色 声音 · 已生成”；打开后URL含 `material_id=need-form-a-heng-blue-voice&material_version=3`，准确需求修订为 `f389f4a222e97b6d78cb20f7050e0c48df3d01111ac799709d55cf2609ac102f`；右侧“版本3 · 当前”选中、“声音 · 未生成”。
- `../browser/R2-audio-play-pause-keyboard-seek.json`：切至版本2，准确资产修订 `e522f05e989232e8323608cc74addd94b5e542c15c2d69692109c5fdd3e78ecb`，单候选阿蘅基础音色出现播放器，保存快照显示9.51/14.50秒。外围逐镜列表仍显示原聚合文字；实体大卡内部的状态素材小卡则随版本变为“已生成”，这两类小卡的计算范围不同。

## 数据链与采用的区别

`ui_projection.material_entries`在9—14行收集所有material_plan_members结果及旧candidate_requirements，不按素材版号限制。32—37行只要任一非placeholder候选含original组成就令generated=true；这是跨版本真实结果口径，不是调用次数、失败回执、内容采纳或镜头采用。

`scene`在148行一次取得all_entries。enrich按镜头直接需求、计划输入、真实输入和采用建立关联；186—194行继承聚合item，再替换所关联行的id/title/record，**没有**按该准确行、所选轮次或adoption重算generated。`association`和`usage_evidence`说明为什么关联，不能作为generated仅代表采用版的证据。

前端`showBreakdownScene/renderMaterials`在110—111行按规范素材身份去重，然后直接将上述item交给materialSmallCard。P1的`breakdownVideoSelections`只影响点击后打开的素材版本/候选参数；它不改变item.generated。故即使P1左侧已选准确视频版本，右侧小卡仍可能是需求全历史状态。不能把该boolean改解释成当前视频已经产出。

边界：当 `all_entries.get(mid)` 不存在时，scene有精确行fallback。该分支按ASSET且非placeholder判断，未扫描全历史。它可能服务旧/退出当前列表的引用；不要为了统一一个词而推定其完成了全历史核验。若增加生成范围字段，应由实际聚合/精确分支赋值，而不是按association或kind猜测。

## 全部 materialSmallCard 调用及处理边界

| 调用点（系统仓库） | 当前计算范围 | 应如何表达／保留 |
| --- | --- | --- |
| `production-breakdown.js:149` D3普通列表 | material_list→material_entries，需求全历史；无需求独立原件为自身 | 已传includesHistory=true，“有生成结果/无生成结果”；筛选组“含历史版本”解释范围，保留。 |
| `production-breakdown.js:150` D3筛选外准确项 | 同一material_entries聚合；打开时另保留准确URL | 同上，已修；不能因打开历史准确URL就把聚合boolean当该版状态。 |
| `production-breakdown.js:111` D1本镜素材 | scene.enrich主要继承全历史generated，准确关联行另附 | 聚合分支需要使用含历史范围的表达；保留id/record/点击参数及准确引用，不改默认打开版本。真实阿蘅样本已证明必要性。 |
| 同一行 P1本镜视频 | 同一全历史generated；过滤media_type=video | 同类改法，不能借左侧版本控件将旧聚合字段冒作所选版状态。该实例没有真实视频，不要求生成媒体；可用隔离夹具核对范围并保留N/A说明。 |
| `unified-cards.js:47` 实体/状态大卡内素材小卡 | modelSmallItem只扫描当前model.candidates，排除placeholder并要求original | **不能改为全历史标签。** 它应随准确素材版本切换；阿蘅v3未生成、v2已生成即正确行为。 |
| `unified-cards.js:80` 无实体归属大卡左侧需求小卡 | REQUIREMENT分支使用candidate_records.length；production.snapshot:693—695按object_id收集全历史候选 | 另一个遗漏的聚合入口。若保留持续需求导航含义，应明确含历史，并按真实原件口径计算，而非任意候选记录存在。当前仅静态发现，需合法无归属样本/小夹具验证。 |
| 同一行无归属ASSET小卡 | 当前直接以row.kind===ASSET为true | 是准确资产入口，不宜无条件改成历史聚合。还应区分placeholder和实际original；此为静态风险，不冒称已在故事数据复现。 |

全目录检索只有上述5个调用位置（其中111与80各含两个语义分支）。`materialSmallCard`本体默认不能全局改为历史口径。Prompt中准确参考、准确候选的大卡/播放器、实际采用信息与真实调用展示不属于这次聚合文案修复，继续按准确版本表达。

## 建议的最小方向与验证

1. 保留现有API与采用行为。对明确继承material_entries的逐镜小卡给出范围正确的生成结果表达；若沿用“有生成结果/无生成结果”，页面需要能清楚知晓它包括历史版本，不能再让“本镜视频”标题暗示该所选视频已经生成。无需增加第二个筛选器、改变当前版默认或借用旧原件。
2. 有界处理无归属需求卡：从已取得的material_versions结果和兼容候选中取非placeholder且含original的真实结果，明确其持续需求/全历史范围；准确ASSET和实体modelSmallItem保持精确语义。选哪种实现由主协调决定，本审查不将建议当已修。
3. 同一阿蘅样本回归D1外层标签、当前v3空态、v2原件和返回；保留准确id、原件、版本、评论与采用。D3既有298项筛选与当前/历史对照可复用未变数据证据；新增测试针对调用范围和placeholder/original边界，不重复全套。
4. P1和无归属卡按真实数据适用性登记；没有真实视频时不制造生成。若scene fallback实际存在，不把它的false泛化为“该需求全部历史无成果”，必要时单独保留精确结果表达或补足明确聚合信息。

这项发现影响用户判断生成进度，优先级P1（表达范围），不构成故事、历史或采用数据损坏的证明。原始证据、源码哈希及静态/实际边界见同名JSON。
