#!/usr/bin/env python3
"""Review and apply state title changes without replacing historical inputs.

The authored inventory supplies names. All other live payload fields must still
match that inventory. Default is a dry run; --apply commits names and explicit
title-only review decisions together through the shared business operation.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def without_revision(value):
    if isinstance(value, dict):
        return {k: without_revision(v) for k, v in value.items() if k != 'revision_id'}
    if isinstance(value, list):
        return [without_revision(v) for v in value]
    return value


def content(payload):
    return without_revision({k: v for k, v in payload.items() if k != 'title'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    instance = args.instance.resolve()
    if ROOT not in instance.parents or '.runtime' not in instance.relative_to(ROOT).parts:
        parser.error('use an existing isolated instance inside this task worktree .runtime')
    if not (instance / '.runtime/review.sqlite3').is_file():
        parser.error('instance database must already exist')
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk import production
    from review_desk.store import Store

    store = Store(instance / '.runtime/review.sqlite3')
    clone = Store(':memory:')
    try:
        store.db.backup(clone.db)
        clone.db_path = store.db_path
        heads = {r['object_id']: r for r in production.current_records(store)}
        inventory = json.loads((ROOT / 'production/inventory.json').read_text())
        changes, renames = [], []
        for authored in inventory['records']:
            if authored['kind'] != 'STATE':
                continue
            current = heads[authored['object_id']]
            if content(current['payload']) != content(authored['payload']):
                raise ValueError('state content differs from the naming input: ' + current['object_id'])
            title = authored['payload']['title']
            parent = heads[current['payload']['entity']['object_id']]
            if not title.startswith(parent['payload']['title'] + '·'):
                raise ValueError('state name does not match its entity: ' + current['object_id'])
            if title == current['payload']['title']:
                continue
            payload = copy.deepcopy(current['payload'])
            payload['title'] = title
            changes.append({'object_id': current['object_id'], 'kind': 'STATE',
                            'expected_version': current['version'], 'payload': payload})
            # Enumerate impact before deciding this rename requires no rework.
            affected = production.impact(store, current['id'])['affected']
            renames.append({'object_id': current['object_id'], 'old_revision': current['id'],
                            'old_title': current['payload']['title'], 'new_title': title,
                            'affected_objects': sorted({r['object_id'] for r in affected})})
        if not changes:
            print(json.dumps({'applied': False, 'renamed': 0, 'message': 'names already match'}))
            return
        imported = production.import_records(clone, {'format': 'production-import-v1', 'records': changes})
        new_refs = {change['object_id']: result['revision']
                    for change, result in zip(changes, imported['records'])}
        decisions = []
        reason = '已逐项核对命名及依赖影响；仅实体状态标题优化，所属实体、正文、状态维度和全部精确引用不变，现有输入继续使用原修订，无需内容返工；不代表创作审阅通过。'
        for rename in renames:
            oid = rename['object_id']
            new = {'object_id': oid, 'revision_id': new_refs[oid]}
            old = {'object_id': oid, 'revision_id': rename['old_revision']}
            suffix = hashlib.sha256((old['revision_id'] + new['revision_id']).encode()).hexdigest()[:24]
            decision_id = 'review-state-title-' + suffix
            decisions.append({'object_id': decision_id, 'kind': 'JUDGMENT', 'expected_version': 0,
                              'payload': {'format': 'production-judgment-v1',
                                          'title': rename['new_title'] + ' · 命名复核',
                                          'blocks': [{'id': 'reason', 'text': reason}],
                                          'target': new, 'verdict': 'impact_resolved',
                                          'actor': 'Codex 技术命名复核', 'reason': reason,
                                          'change': {'old': old, 'new': new, 'action': 'keep',
                                                     'scope': 'state_title_only'}}})
            rename.update(new_revision=new_refs[oid], review_object=decision_id)
        production.import_records(clone, {'format': 'production-import-v1', 'records': decisions})
        batch = {'format': 'production-import-v1', 'records': changes + decisions}
        # Validation rolls back the complete batch; application is atomic and
        # rechecks all expected versions to reject concurrent edits.
        production.import_records(store, batch, validate_only=not args.apply)
        report = {'applied': args.apply, 'renamed': len(renames), 'reviews': len(decisions),
                  'changed_payload_fields': ['title'], 'renames': renames}
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        clone.close()
        store.close()


if __name__ == '__main__':
    main()
