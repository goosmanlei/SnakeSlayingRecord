"""Append independently mapped closing receipts without rebuilding frozen archives."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timedelta, timezone

workspace = Path(__file__).resolve().parents[3]
runtime = workspace / '.runtime/autonomous-optimization'
out = workspace / 'planning/autonomous-optimization-evidence/task-20261005-0001'
spec = importlib.util.spec_from_file_location('evidence_builder', runtime / 'delivery/build_evidence.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
sources = [
    'stop-receipt.json', 'state.json', 'watcher.json',
    'reviews/delivery-final-archive-audit.json',
    'reviews/delivery-final-archive-audit.md',
    'reviews/delivery-final-cleanup-execution-receipt.json',
    'reviews/delivery-final-cleanup-result-audit.json',
    'reviews/delivery-final-cleanup-result-audit.md',
    'delivery/release-checkpoint-prepare.json',
    'delivery/release-checkpoint-build.json',
    'delivery/release-checkpoint-preflight.json',
    'delivery/goal-complete.json',
    'delivery/close_evidence.py',
]
stop = json.loads((runtime / 'stop-receipt.json').read_text())
state = json.loads((runtime / 'state.json').read_text())
watcher = json.loads((runtime / 'watcher.json').read_text())
assert watcher['running'] is False and watcher['last_error'] is None
goal = json.loads((runtime / 'delivery/goal-complete.json').read_text())['goal']
assert goal['status'] == 'complete'
assert state['phase'] == 'finished' and state['stop']['complete'] is True
assert stop['complete'] is True and stop['reason'] == 'converged'
assert stop['errors'] == []
report = workspace / 'planning/autonomous-optimization-run-report.md'
assert stop['report']['sha256'] == builder.file_digest(report)
manifest_sha = builder.file_digest(out / 'manifest.json')
assert manifest_sha == 'd1cea8ad4c549a4290d35fd22fb36688f91e0f32aef718942c1a7d56cc5b21d4'
rows = []
with tempfile.TemporaryDirectory(prefix='.closing-', dir=out.parent) as directory:
    stage = Path(directory) / 'closing-receipts'
    stage.mkdir()
    for name in sources:
        source = runtime / name
        assert builder.allowed(source), name
        raw = source.read_bytes()
        final = builder.sanitize(raw, name)
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(final)
        rows.append({'path': 'closing-receipts/' + name, 'source': name,
                     'bytes': len(final), 'sha256': hashlib.sha256(final).hexdigest(),
                     'source_sha256': hashlib.sha256(raw).hexdigest(),
                     'transformation': 'credential-key redaction' if final != raw else 'byte exact'})
    tz = timezone(timedelta(hours=8))
    fmt = lambda value: datetime.fromtimestamp(value, tz).isoformat(timespec='milliseconds')
    elapsed = stop['finished_at'] - state['t0']
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    root = state['root_thread_id']
    assert stop['threads'][root]['goal'] == 'complete'
    assert stop['threads'][root]['turn'] == 'finish_allowed'
    assert all(stop['threads'][child]['turn'] == 'inactive' for child in state['children'])
    body = f'''# 本轮优化收尾回执

本轮以正常质量收敛结束优化，未执行任务完成、集成、推送或正式服务切换；仍等待用户对最终双仓候选和发布包的明确确认。[运行报告](../../../autonomous-optimization-run-report.md)中的实际变更、验证与剩余限制继续适用。

| 时间与状态 | 真实回执 |
| --- | --- |
| 用户重置后的 T0 | {fmt(state['t0'])} |
| 请求正常收敛 | {fmt(stop['requested_at'])} |
| 守卫确认停止完成 | {fmt(stop['finished_at'])} |
| 连续墙钟 | {int(hours)}小时{int(minutes)}分{seconds:.3f}秒，含等待和离线，不等同有效工作工时 |
| 停止原因／尝试次数 | converged／{stop['attempts']} |
| 根 Goal | complete，无 token 预算；根回合仅允许收尾，不代表 task _complete |
| 已登记后代 | {len(state['children'])}个，全部回合inactive；各 Goal 状态见原始回执 |
| 停止错误 | 0；后续监督提醒已撤销 |

这是用户明确重置后的窗口。原02:25:41窗口的截止、52次重试及未达质量标准仍保留在冻结归档，不与本次正常收敛混为一轮。

[Goal工具回执](delivery/goal-complete.json)的累计字段为tokensUsed={goal['tokensUsed']}、timeUsedSeconds={goal['timeUsedSeconds']}（约{goal['timeUsedSeconds']/3600:.2f}小时），没有token预算。它们是整个既有Goal的工具口径，不等同本次重置后的墙钟、有效工时、逐代理用量或计费额；Goal中旧T0文本没有覆盖用户后来明确重置的授权。[watcher退出回执](watcher.json)确认running=false，未仅凭停止请求推断守卫已退出。

实际[停止回执](stop-receipt.json)及[状态快照](state.json)保留来源与脱敏映射。停止时主报告 SHA-256 为 `{stop['report']['sha256']}`，与交付正文一致。三包 manifest SHA-256 为 `{manifest_sha}`；本目录另用[manifest](manifest.json)逐项核验，不重建三包。

[最终归档独审](reviews/delivery-final-archive-audit.md)确认3060项来源完整；[实际清理独审](reviews/delivery-final-cleanup-result-audit.md)核回18目标6504文件、5,990,693,557字节已删。新增歌曲恢复树2430文件、1,523,541,473字节因共享VM占用保留。B阶段预览／技术夹具清理仅准备，须在真实用户确认、正式发布及正式页面验收之后、_complete之前执行。

报告与归档检查点故事提交3e6a6392cd71050d2470f39121851d1870e28e7f也已完成准确发布包[准备](delivery/release-checkpoint-prepare.json)、[构建](delivery/release-checkpoint-build.json)和[preflight](delivery/release-checkpoint-preflight.json)。追加本目录产生的最终故事提交仍须按自身完整SHA重新准备；产品源码继续固定24e926d446a9424a8cbc3c8b9910aaa322ff9632，不重复未变范围的性能或浏览器验收。

本说明由本目录中的停止／状态／独审回执派生，归档内较早的active和待清理记录是历史检查点。最终确认候选及不可变包身份由随确认请求展示的准备和preflight回执给出；发布或推送结果只能以之后真实执行的任务账本和回执为准。
'''
    readme = stage / 'README.md'
    readme.write_text(body, encoding='utf-8')
    rows.append({'path': 'closing-receipts/README.md', 'source': None,
                 'bytes': readme.stat().st_size, 'sha256': builder.file_digest(readme),
                 'transformation': 'derived summary of mapped stop, state and independent audit receipts'})
    mapping = {'task_id': 'task-20261005-0001', 'format': 'autonomous-review-closing-v1',
               'archive_manifest_sha256': manifest_sha, 'source_base': '.runtime/autonomous-optimization',
               'note': 'Generated after the frozen archives; archives and their 3060 source entries are not rewritten. This is optimization closeout, not task completion, user approval, integration or push.',
               'files': rows}
    (stage / 'manifest.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
    for row in rows:
        path = stage / row['path'].removeprefix('closing-receipts/')
        assert path.stat().st_size == row['bytes'] and builder.file_digest(path) == row['sha256']
    assert builder.file_digest(out / 'manifest.json') == manifest_sha
    builder.publish_bundle(stage, out / 'closing-receipts')
print(json.dumps({'files': len(rows), 'archive_manifest_sha256': manifest_sha,
                  'closing_manifest_sha256': builder.file_digest(out / 'closing-receipts/manifest.json')}))
