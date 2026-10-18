# 本轮制作编号迁移

本任务只重编本轮六类可读编号，不重做制作。准确范围、旧分配和新分配在 [plan.json](plan.json)：AE001—017、AS001—042、ASH001—416、EN001—122、ST001—021、M001—650。AS跨集连续，ASH跨场跨集连续；EN／ST／M保持原有效分配顺序。五项撤回需求与旧删除对象的编号仅保留为历史事实，不占新当前号。

当前搜索、编号目录及派生关系码使用新映射；准确旧链接仍凭对象／修订身份定位，旧评论及真实调用快照不改写。此后新建沿本轮最大已分配号继续，普通删除不回收，日常调序与刷新不重编。完整规则见系统 `docs/business-codes.md`。

## 操作与恢复

以下命令从任务故事工作区运行，`DESK` 指本任务纳管的系统工作区，`INSTANCE` 指已核验的目标实例。明确授权由任务入口取得，不从清单文件本身推断：

```bash
python3 scripts/restart_production_numbering.py --system "$DESK" --instance "$INSTANCE" \
  --plan production/numbering-restart/plan.json --authorization task-20261016-0001 prepare
python3 scripts/restart_production_numbering.py --system "$DESK" --instance "$INSTANCE" \
  --plan production/numbering-restart/plan.json apply
python3 scripts/restart_production_numbering.py --system "$DESK" --instance "$INSTANCE" \
  --plan production/numbering-restart/plan.json check
```

已存在清单直接读取，不再次prepare。正式apply须先完成双仓受管集成、核对最新正式数据和在途任务，持共享写锁停止准确应用；另传 `--source-commit` 指向已合入主干、含此清单的准确提交。流程沿 [生成工作区](../generation-workspaces.md)。过期基线拒绝后从最新正式数据重新准备清单和候选，不修改清单中的哈希来绕过检查。事务中断全部回滚，提交后回执丢失沿同一清单重试；不回灌旧库。

迁移事实随Schema 14完整导出和 [恢复索引](../audiovisual/index.json) 保存。新空实例恢复后保留当前映射、旧码事实和未来分配依据。0005等在途任务应先同步最新主干，再以最新正式数据为基线，按稳定对象身份重新准备范围内增量；旧包即使只改方案也不能直接重放，不改其他任务依赖或状态。

执行自验、正式发布、最终恢复与过程资源收尾见 [验收记录](VERIFICATION.md)及主项目任务账本。本任务没有付费生成、VPS发布、作品实质修订或用户接受。
