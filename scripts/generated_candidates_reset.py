#!/usr/bin/env python3
"""Exact local reset: inspect/prepare, transaction, resumable byte deletion."""
import argparse
import fcntl
import json
from pathlib import Path
import sys

from generation_workspace import generation_root, primary_root, verify_integrated
from publish_generation import formal_application_stopped


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--source-commit')
    parser.add_argument('action',choices=('prepare','apply','clean','check'))
    args=parser.parse_args()
    workspace=generation_root(Path(__file__).resolve().parents[1])
    target=args.instance.resolve(strict=True); plan_path=args.plan.resolve()
    formal=target==primary_root(workspace)
    sys.path.insert(0,str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk import production_reset as reset
    from review_desk import candidate_reset
    from review_desk.production_current_bundle import validate,required_assets
    if args.action=='prepare':
        if plan_path.exists():
            raise ValueError('plan exists; resume the exact manifest')
        store=Store.open_readonly(target/'.runtime/review.sqlite3')
        try:plan=reset.prepare(store)
        finally:store.close()
        plan_path.parent.mkdir(parents=True,exist_ok=True)
        plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'id':plan['id'],'assets':len(plan['assets']),'files':len(plan['erased_files'])}));return
    plan=json.loads(plan_path.read_text())
    from contextlib import ExitStack
    with ExitStack() as stack:
        if formal and args.action in ('apply','clean'):
            if not args.source_commit:
                raise ValueError('formal reset requires the exact integrated source commit')
            verify_integrated(workspace,target,args.source_commit,plan_path,[])
            for name in ('http-write.lock','publication.lock'):
                lock=stack.enter_context((target/'.runtime'/name).open('a'))
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            stopped=formal_application_stopped(target)
        store=(Store.open_readonly if args.action=='check' else Store.open_existing)(target/'.runtime/review.sqlite3')
        try:
            if args.action=='apply':result=reset.apply(store,plan)
            elif args.action=='clean':result=candidate_reset.cleanup(store,plan)
            else:
                validate(store)
                counts={table:store.db.execute('SELECT count(*) FROM '+table).fetchone()[0]
                        for table in ('production_candidates','production_candidate_targets','production_submissions','comments')}
                present=[name for name in plan['erased_files'] if (target/'export/assets'/name).exists()]
                if counts['production_candidates'] or counts['production_candidate_targets'] or present:
                    raise ValueError('zero-candidate baseline incomplete')
                for kind in reset.KINDS:
                    if store.db.execute('SELECT 1 FROM objects WHERE kind=?',(kind,)).fetchone():
                        raise ValueError('production layer is not empty: '+kind)
                result={'zero_candidates':True,'counts':counts,'erased_media_still_present':present,
                        'required_nonmedia_files':len(required_assets(store))}
            print(json.dumps(result,ensure_ascii=False))
        finally:store.close()


if __name__=='__main__':main()
