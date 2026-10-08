#!/usr/bin/env python3
"""Prepare and apply this story's exact new-production package; never generate media."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','apply'])
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--db',type=Path,required=True)
    parser.add_argument('--design',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--receipt',type=Path)
    parser.add_argument('--fault',choices=['after_delete','after_import','before_commit','after_commit'])
    args=parser.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p,production_cutover as cut
    design=json.loads(args.design.read_text());records=design['records']
    store=Store.open_readonly(args.db) if args.command=='plan' else Store(args.db)
    try:
        if args.command=='plan':
            keep={r['object_id'] for r in design['preserve_exact_requirements']}
            delete=[r['id'] for r in store.db.execute("SELECT id,kind FROM objects WHERE kind IN ('PREPARATION','SHOT_DESIGN','REQUIREMENT')") if r['id'] not in keep]
            used={r['object_id'] for row in records for r in row['payload'].get('entities', [])}
            retention=[]
            for row in p.current_records(store,{'ASSET'}):
                subjects=[r['object_id'] for r in row['payload']['subjects'] if r['object_id'] in used]
                reason='用于当前实体身份、完整状态或声音的准确候选比较；不代表已选用'
                if not subjects:
                    if row['object_id']!='asset-fg3-bandage-base-image-02':
                        raise ValueError('existing candidate requires an explicit useful purpose: '+row['object_id'])
                    reason='李寄额角、手掌布条的材质和包扎结构局部对照；不能代替带伤人物整体参考'
                retention.append({'object_id':row['object_id'],'revision_id':row['id'],'subjects':subjects,'purpose':reason})
            result=cut.plan(store,delete,records,retention)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            args.plan.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({'id':result['id'],'deletions':dict(Counter(r['kind'] for r in result['delete_revisions'])),
                              'deleted_objects':len(result['delete_objects']),'deleted_comments':len(result['delete_comments']),
                              'retained_assets':len(retention),'retained_files':len(result['files']),
                              'new_records':dict(Counter(r['kind'] for r in records))},ensure_ascii=False))
        else:
            result=cut.apply(store,json.loads(args.plan.read_text()),records,fault=args.fault)
            if args.receipt:
                args.receipt.parent.mkdir(parents=True,exist_ok=True)
                args.receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({k:v for k,v in result.items() if k!='created_heads'},ensure_ascii=False))
    finally:store.close()

if __name__=='__main__':main()
