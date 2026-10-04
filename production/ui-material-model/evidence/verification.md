# 候选检查与复用范围

页面、自动检查、数据原字节与运行环境分开验收。最终系统提交由故事 `config/instance.json` 固定；双仓故事候选及正式操作结果由任务准备／完成回执记录。本文件不声称正式资源已经切换。

| 检查 | 实际结果 | 证据与复用边界 |
|---|---|---|
| 系统前端全部测试 | 521项通过，0失败，0跳过，379.580ms | `.runtime/ui-material-model/frontend-tests-final-code.log`；测试于2664a3e，后续至b874b95只改归档恢复后端及Python测试，前端未变。 |
| 恢复锁修复后的系统Python全套 | 216项通过，24.557s | `.runtime/ui-material-model/restore-fix-full-python.log`；代码已包含恢复写锁修复；后续原JSON字节保留的两行修正经18项定向复验。运行开始时尚未加入独立审查最后5项恢复边界检查。 |
| 独立Python检查 | 22项通过，0.918s | [独立报告](independent-review.md)；包含事务独占锁、不同实例隔离、异常回滚、嵌套上下文恢复。 |
| 独立前端检查 | 27项通过 | 同一独立报告；属于上面521项的一部分，不重复累计。使用真实函数及草稿键，不能代替浏览器操作。 |
| 故事读取、发布及范围护栏定向检查 | 31项通过，14.304s | `.runtime/ui-material-model/story-packaged-tests.log`；受管归档已经变为引用容器后实际执行。 |
| 单事务发布与恢复编排 | 18项通过，0.113s | `.runtime/ui-material-model/release-navigation-checkpoint-review.log`；[独立编排复核](navigation.md)。含真实WAL截断和busy拒绝，不操作正式资源。 |
| 真实Chrome | 五页、三种宽度、三层弹窗、准确版本／候选／组成、四类评论、草稿与采用 | [逐项实际操作](browser-review.md)。图片／视频采用夹具仅为本机合成测试媒体；与故事数据包隔离。 |
| 本机容器 | ff475e4系统54个源码文件与镜像逐文件一致，隔离HTTP检查通过 | [容器证据](container-check.json)。容器网络为none，独立数据库，未使用正式环境变量；后续b874b95只修bundle恢复原字节，HTTP路径未变。最终发布镜像另由不可变发布包核对全部54个源码文件。不能代替页面验收。 |

可重跑入口分别为系统仓的 `node --test tests/*.test.cjs`、`python3 -m unittest discover -s tests`，以及故事仓的 `tests/test_material_model_io.py`、`tests/test_full_generation.py`、`tests/test_song_publication.py` 和 `tests/test_ui_material_model_release.py`。故事命令按[数据契约](../data-contract.md)指定兼容系统；准确原始运行输出留在本任务 `.runtime/ui-material-model/`。

较早的故事全套执行了255项，曾有两项失败和一项跳过，不能写成当时全过。一项为旧生成范围测试把当前新增状态用于历史锁定范围，已用原source-lock的准确旧头修正夹具，并另断言当前范围漂移仍被生产护栏拒绝；[基线复现](preexisting-scope-test.json)保留原始证据。一项为旧歌曲发布子进程读取新格式的兼容入口，已修复并包含于上述31项定向复验。原有HTTP兄弟工作区夹具跳过与本轮功能无关；系统HTTP测试、真实容器请求和Chrome操作另有实际通过证据。修复后没有为收尾重复耗时较长且未受影响的全套故事检查。

全量空实例恢复曾因写入大量内容后另开归档读取连接遇到SQLite写锁而失败；失败事务回滚，未把小夹具通过当作全量成功。最终修复只在准确同实例事务范围复用连接，数据代理重跑完整恢复，独立审查另外验证错误实例不能借内容及异常后缓存不能泄漏。实际完整恢复通过，耗时397.746秒，导出契约内23表、1855归档及复导出的1314个清单文件一致；具体数据恢复、幂等、并发保留和物理扫描结果见[数据验证](../data-validation.md)；原失败日志保留在本机运行目录。

分工由主代理统一接口、共用卡片、逐镜布局、浏览器和发布顺序；导航与数据工作在约定范围并行，独立审查不代替实施者修改功能。实际增加的覆盖与返工分别见[导航贡献](navigation.md)和[独立贡献](independent-review.md)。浏览器始终由主代理独占，正式资源未在开发阶段被任何代理写入。没有观测到文件互相覆盖或Git合并冲突；共享文件窗口通过消息释放，精确等待时长、端到端耗时、Token及费用未知。没有max对照，不能据此宣称固定提速或质量提升。
