# 素材数据验证说明

本文件区分真实故事数据的全量验证与人工夹具回归。准确候选由 `migration.json`、`final-head-evidence.json` 和 `export/material-content.json` 的哈希共同确定；所有数据库操作均在任务 `.runtime/ui-material-model/` 内，未写正式库、未修改媒体原件。

## 统计对象与物理检查

`data-evidence.json` 对照未混入页面测试评论的 `baseline/.runtime/generation-base.sqlite3`，验证 10,160 个历史修订的 JSON 原字串及修订身份、原有业务表、30 个明确共享别名和 1,855 份受管归档。归档分为 1,018 份故事 production JSON 与 837 份素材元数据；已提交 Git 历史不改写。

其 `real_media_files=418` 仅统计生产记录 `components` 中实际引用的图像、音频及视频原件。独立检查的 511 份是完整 export 中全部非 JSON 媒体，包括来源材料等；两者统计对象不同，均逐文件核对字节。另有 50 份普通 JSON 保持原样。

物理数据库启用 `secure_delete` 后执行 `wal_checkpoint(TRUNCATE)`，返回 busy=0。李寄真实调用 Prompt 对应的完整内容叶在当前 SQLite 文件和导出内容图中分别只出现一份，在 objects.json 与 1,855 个归档容器正文中均不出现。独立检查还逐一校验 78,889 个内容节点的哈希，并解压 5,092 个还原配方，确认没有在配方中另藏该 Prompt 正文。检查的是当前物理交付及数据库，不宣称清除了 Git 历史或隔离基线备份。

## D01—D05：身份、版本、候选与写入

李寄案例的 13 个状态通过旧记录中明确的 reuse 引用、相同完整要求和相同输出约定合并；title、scope、states 的差异保存在独立关联证据中。实际调用输入与原计划输入的差异、版本 1 的历史缺项均保留。版本 2 的要求来自准确旧修订，不用最新需求补写旧事实；评论通过该版本准确的原始来源授权，不把整条复用链或所有候选成员当作评论资格。

系统回归覆盖以下有区别的行为：

- `test_material_plans`：草稿修改与首次执行锁定；失败、未知调用无原件时不产生候选；同方案重复调用保留同版、多候选；仅补关联或标题不建版；评论幂等且不建版；随机策略忽略实际返回 seed，固定 seed 变化或准确输入／模型／参数变化形成新方案。
- `test_ui_material_independent`：完整要求字段变化影响定义；直接 Store 写入也执行实质变化解绑；仅有 prepared_plan 的失败／未知调用在没有 ASSET 时即锁版；不同不完整历史调用不能据共同缺项合为一版；已知同方案的 unknown 重试仍同版；后续重试不改冻结来源及旧评论资格。
- `test_production`、`test_generation`、`test_entity_review`：候选关联不等于采用，新候选不继承或替换已采用结果；并发批次冲突原子拒绝。`test_generation_publication` 验证无关修订、决定与评论历史保留，同对象竞争拒绝，重试无重复登记。
- 完整定义、别名指向和版本绑定有校验及数据库约束；独立篡改回归拒绝错绑定义、别名错误目标及缺失绑定。

`test-evidence.json` 汇集实际测试日志的数量、耗时和 SHA-256。对应完整 Python 回归在恢复锁修复后运行 216 项，24.557 秒全部通过；之后新增的独立边界测试和原 JSON 字节恢复回归分别执行，结果记录在相应证据与独立报告中，不将分批运行冒充又一次全套测试。

## D06—D08：原始字节与接口恢复

原始请求和回执的键序、空白、CRLF、Unicode 转义、数值写法、重复键以及嵌套 JSON 字符串均由词法配方恢复。`evidence/independent-full-data-check.json` 独立解码 1,855 份归档并与迁移前保存的 SHA-256 和字节数比较；`evidence/independent-final-candidate-reuse.json` 记录最终准确候选与这次实测的内容等价关系，保留各次实际执行身份。

`http-evidence.json` 使用真实李寄请求元数据，通过隔离 HTTP 服务取得完整原始 4,520 字节及 `Range: bytes=7-89`，分别得到 200／206，完整字节和局部字节均与原件一致。故事归档容器实际落盘后，CLI、生成发布、原请求读取及历史范围测试共 31 项，14.304 秒全部通过。

实际全量导出→空实例恢复已通过，耗时 397.746 秒：23 张导出契约内表逐行相等，1,855 份归档原字节相等，恢复后重新导出的 1,314 个 manifest 受管文件逐字节一致。`restore-evidence.json` 保留实际执行的 ff475e 提交／e082553 迁移身份；最终候选的定义图及数据与此相同，后续仅保留原物理／旧 JSON 字串的补丁由 18 项专门回归与 22 项独立回归验证，不能将这次全量执行身份改写成最后提交。审阅台导出契约包含修订、评论、事件、依赖、版本、候选、采用／决定记录、配置、唯一内容图和归档目录。故事发布脚本自有的 `generation_publications` 表从旧格式开始便不属于通用 bundle 导出契约；本迁移及准确逆向保留其原有 2 行，不能把通用空库恢复说成恢复任意 SQLite 私有表。

全量恢复实际暴露了归档读取的第二连接写锁问题；失败事务的 objects、revisions、comments、material_content 和 archive catalog 均回滚为 0。修复在恢复事务内复用同一数据库连接，并由强制页溢出测试和独立跨实例／嵌套／异常测试复验，见 `evidence/restore-lock-regression.json`。随后用非规范 JSON 夹具发现恢复时重新序列化会丢词法字节；现直接保存已校验的物理载荷或旧格式原字串，修订哈希、内容哈希和完整定义校验均未放宽，见 `evidence/restore-original-json-regression.json`。

## D09：事务、重试与逆向

`rollback-evidence.json` 记录真实全量准确逆向：先验证重复 apply 返回 already_applied；新增一条无关评论；validate-only 不变更；实际逆向恢复旧表和 1,855 份原始文件，保留该新增评论；再次逆向返回 already_rolled_back。`require_legacy=True` 在同一事务末检查旧运行时兼容并仅移除本功能触发器。

冲突夹具证明触碰的准确头或版本变化时整批拒绝，原表和归档均不发生部分变化。无关新编码素材写入会使旧运行时恢复检查失败并撤销整批逆向，保留已迁移数据库用于向前恢复；不会为了启动旧服务丢弃这笔新写入。另以原主干旧 Store 在三个独立数据库上实际新增修订，验证迁移后逆向、仅初始化、构造失败三条恢复路径，见 `evidence/legacy-runtime-probe.json`。

## 故事全套测试的处理

最初实际运行 255 项故事测试，结果为 252 通过、2 失败、1 跳过，耗时 866.999 秒。一个失败是旧歌曲 CLI 子进程缺少兼容模块路径，已修复并单独复验；另一个是历史生成脚本固定 267 状态／255 图像，而后续故事已增至 269／256。旧 Git 源码也重现同一范围保护错误，见 `evidence/preexisting-scope-test.json`。

经协调保留生产脚本的原范围护栏，将历史测试按 source-lock 的准确旧头构造夹具，继续核对批准后的 251 图像，同时断言当前新增状态被原护栏拒绝。该模块 5 项通过；后续包含两个修复在内的 31 项归档读写回归全部通过，没有宣称重跑全部 255 项。唯一跳过的 `test_reader_review_http.HTTPIntegrationTest.test_comments_edit_and_export_restore_on_real_http` 需要相邻审阅台夹具；本轮另有真实隔离 HTTP 检查，但不把它改记为该跳过测试已通过。
