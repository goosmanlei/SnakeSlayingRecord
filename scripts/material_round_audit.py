#!/usr/bin/env python3
"""Build an evidence map; applying it uses the shared guarded migration command.

This audit is specific to the verified first production batch in this story.
It refuses later production feedback so new history must be reviewed separately.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p, material_versions as mv
    store = Store(args.instance.resolve() / '.runtime/review.sqlite3')
    try:
        records = [p.record(store, revision_id=r['id']) for r in store.revisions() if json.loads(r['payload']).get('format') in p.FORMATS]
        relevant = {r['object_id'] for r in records if r['kind'] in ('REQUIREMENT', 'CALL', 'ASSET')}
        if any(c['target_object_id'] in relevant for c in store.comments()):
            raise ValueError('new production feedback exists; review it before creating a migration map')
        requirements = [r for r in records if r['kind'] == 'REQUIREMENT']
        assets = [r for r in records if r['kind'] == 'ASSET']
        calls = [r for r in records if r['kind'] == 'CALL']
        if len({r['object_id'] for r in assets}) != 6 or len({r['object_id'] for r in calls}) != 7:
            raise ValueError('production batch changed; this evidence decision no longer applies')
        members = {}
        def add(mid, row, evidence):
            members[(mid, row['id'])] = {'material_id': mid, 'number': 1, 'revision_id': row['id'], 'evidence': evidence}
        for row in requirements:
            add(row['object_id'], row, '首次需求、方案准备或全局声音流程调整；无修订评论。原始方案修订完整保留。')
        for oid in sorted({r['object_id'] for r in assets}):
            history = sorted((r for r in assets if r['object_id'] == oid), key=lambda r:r['version'])
            ids = sorted({ref['object_id'] for r in history for ref in r['payload'].get('candidate_requirements', [])}) or [oid]
            for mid in ids:
                for row in history:
                    add(mid, row, '首轮真实候选及后续状态／需求关联补全；同一素材身份归组不补写原始调用或采用。')
                    if row['payload'].get('production'):
                        call_id = row['payload']['production']['object_id']
                        for call in calls:
                            if call['object_id'] == call_id:
                                add(mid, call, '真实提交与完成状态属于同一调用；不把调用状态修订视为新素材轮次。')
        result = {'format':'material-round-migration-v1','expected_fingerprint':mv.fingerprint(store),
                  'members': sorted(members.values(), key=lambda v:(v['material_id'],v['revision_id'])),
                  'gaps':[{'material_id':'need-form-li-ji-paste-overall',
                           'detail':'两次实际图像调用均为第一轮基准尝试，第二次核对原生 4K；库内没有区分独立修订轮次的评论或触发记录。按已证实首轮归组并保留两个候选，不推定两个用户修订轮次。'}]}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({'members':len(members),'materials':len({v[0] for v in members}),'assets':len(assets),'calls':len(calls),'gaps':len(result['gaps'])}))
    finally:
        store.close()


if __name__ == '__main__':
    main()
