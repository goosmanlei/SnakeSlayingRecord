#!/usr/bin/env python3
"""Prepare/check/apply one explicitly authorized, exact numbering migration."""
import argparse
from contextlib import ExitStack
import fcntl
import json
from pathlib import Path
import sys

from generation_workspace import generation_root, primary_root, verify_integrated
from publish_generation import formal_application_stopped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--authorization')
    parser.add_argument('--source-commit')
    parser.add_argument('action', choices=('prepare', 'apply', 'check'))
    args = parser.parse_args()
    workspace = generation_root(Path(__file__).resolve().parents[1])
    target = args.instance.resolve(strict=True)
    plan_path = args.plan.resolve()
    if not plan_path.is_relative_to(workspace) or any(p.is_symlink() for p in [plan_path, *plan_path.parents] if p != workspace.parent):
        raise ValueError('migration plan must be inside this task workspace without symlinks')
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk import numbering_restart as numbering
    from review_desk.candidate_reset import fingerprint
    from review_desk.production_current_bundle import validate
    if args.action == 'prepare':
        store = Store.open_readonly(target/'.runtime/review.sqlite3')
        try:
            plan = numbering.prepare(store, args.authorization)
        finally:
            store.close()
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        with plan_path.open('x') as stream:
            stream.write(json.dumps(plan, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({'id': plan['id'], 'counts': plan['counts'], 'historical_allocations': len(plan['history']), 'excluded_ids': len(plan['excluded_ids'])}))
        return
    plan = json.loads(plan_path.read_text())
    formal = target == primary_root(workspace)
    with ExitStack() as stack:
        if formal and args.action == 'apply':
            if not args.source_commit:
                raise ValueError('formal migration requires the exact integrated source commit')
            verify_integrated(workspace, target, args.source_commit, plan_path, [])
            for name in ('http-write.lock', 'publication.lock'):
                lock = stack.enter_context((target/'.runtime'/name).open('a'))
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            formal_application_stopped(target)
        store = (Store.open_existing if args.action == 'apply' else Store.open_readonly)(target/'.runtime/review.sqlite3')
        try:
            if args.action == 'apply':
                result = numbering.apply(store, plan)
            else:
                validate(store)
                if plan not in numbering.facts(store):
                    raise ValueError('exact migration receipt is missing')
                actual = fingerprint(store)
                protected = {k: v for k, v in plan['baseline'].items() if k not in ('business_codes', 'production_current_operations')}
                if any(actual.get(k) != v for k, v in protected.items()):
                    raise ValueError('protected data changed since migration baseline')
                result = {'id': plan['id'], 'counts': plan['counts'], 'protected_tables': len(protected), 'protected_rows_unchanged': True}
            print(json.dumps(result, ensure_ascii=False))
        finally:
            store.close()


if __name__ == '__main__':
    main()
