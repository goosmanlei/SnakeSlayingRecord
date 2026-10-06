#!/usr/bin/env python3
"""Prepare and rehearse explanation-only cleanup in a task's isolated instance.

Formal application belongs to entity_material_release.py after candidate review.
The plan records hashes and facts locators, never a copy of removed prose.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generation_workspace import isolated_instance

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'production/entity-material/cleanup-plan.json'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(a):
    from review_desk.store import canonical, digest, Store
    from review_desk import relation_explanations as cleanup
    instance = isolated_instance(ROOT, a.instance)
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        approved = json.loads(a.audit.read_text())['relationship_cleanup']
        if cleanup.plan(store) != approved:
            raise ValueError('audit history changed; audit and review again')
        old_ids = {r['revision_id'] for r in approved['revisions']}
        path = ROOT / 'production/entity-relationships.json'
        before = path.read_bytes()
        archive = json.loads(before)
        removed = []
        for spec in archive['document']['records']:
            rid = digest(canonical({'object_id':spec['object_id'], 'version':spec['expected_version']+1,
                                    'payload':spec['payload']}).encode())
            if rid in old_ids:
                spec['payload'] = cleanup.cleaned(spec['payload'])
                spec['historical_revision_id'] = rid
                removed.append(rid)
        if removed:
            archive['format'] = 'entity-relationship-facts-archive-v2'
            archive['document']['format'] = 'historical-production-facts-v1'
            archive['explanation_policy'] = '旧说明已清理；原端点、来源及批次头引用保留。此归档不可重新导入为当前关系。'
            archive['removed_explanation_revisions'] = removed
            write(path, archive)
        after = path.read_bytes()
        package = {'format':'entity-material-cleanup-v1', 'task':'task-20261005-0002',
                   'relationships':approved,
                   'archives':[{'path':path.relative_to(ROOT).as_posix(), 'before_sha256':sha(before),
                                'after_sha256':sha(after), 'removed_revisions':removed}],
                   'protected':'关系事实、端点、依据、其他对象历史、评论原文、媒体原件与采用记录',
                   'recovery':'清理后以 Schema 7 导出恢复事实、评论和准确身份；不恢复已删除旧说明。既有 Git 提交不重写。'}
        write(PACKAGE, package)
        print(json.dumps({'plan':str(PACKAGE.relative_to(ROOT)), 'old_explanations':len(old_ids),
                          'archived_old_payloads':len(removed), 'formal_writes':False}))
    finally:
        store.close()


def compact(store):
    store.db.commit()
    checkpoint = store.db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
    if checkpoint and checkpoint[0]:
        raise ValueError('WAL is busy; stop the task reader before compaction')
    store.db.execute('VACUUM')
    store.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    if store.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('cleanup database integrity failure')


def isolated(a):
    from review_desk.store import Store
    from review_desk import relation_explanations as cleanup, bundle
    instance = isolated_instance(ROOT, a.instance)
    package = json.loads(PACKAGE.read_text())
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        before_comments = store.comments()
        result = cleanup.apply(store, package['relationships'])
        if store.comments() != before_comments:
            raise ValueError('comment records changed')
        compact(store)
        manifest = bundle.export(store, instance / 'export')
        result.update(schema_version=manifest['schema_version'], comments_preserved=True,
                      redacted_revisions=len(cleanup.dump(store)), formal_writes=False)
        write(a.output, result)
        print(json.dumps(result, ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare','isolated'))
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--audit', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    (prepare if args.command == 'prepare' else isolated)(args)
