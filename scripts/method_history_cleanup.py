"""Task 0010's explicitly reviewed method history consolidation.

The publisher owns the stopped formal write window and recovery snapshot.
Nothing runs on import. Plans are exact, rechecked inside one transaction, and
never attribute old creative results to a new method. Future history is enabled.
"""
import argparse
import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

try:
    from . import method_migration
except ImportError:
    import method_migration

TASK = 'task-20261013-0010'
FORMAT = 'method-history-cleanup-v1'
SKILLS = frozenset('method.skill.' + name for name in (
    'comment-polish-clear', 'story-structure', 'novel-writing', 'screenplay-scene',
    'audiovisual-scene', 'material-assessment', 'image-plan', 'voice-plan',
    'scene-sound-plan', 'song-plan', 'video-plan', 'text-layer',
    'generation-preflight', 'result-review', 'creative-system-review'))
USAGE = re.compile(r'method\.(?:execution|artifact)\.[0-9a-f]{64}')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def usage_refs(value):
    return set(USAGE.findall(json.dumps(value, ensure_ascii=False)))


def clean_receipt(value, removed):
    """Scrub only method provenance fields, preserving operation facts."""
    if isinstance(value, list):
        return [clean_receipt(item, removed) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        # A semantic-migration basis can contain a method basis alongside its
        # own operation identity and assessment evidence. Only the complete,
        # known method-reference record belongs to this cleanup. Unknown
        # shapes retain their data and build_plan refuses any remaining refs.
        method_record = isinstance(item, dict) and set(item) == {
            'execution', 'artifact', 'run_id', 'step_id'}
        if (key in ('method_basis', 'basis', 'original_media_plan_basis')
                and method_record and usage_refs(item) & removed):
            if key != 'method_basis':
                result[key] = {'history': 'cleared-by-user', 'cleanup_task': TASK}
        else:
            result[key] = clean_receipt(item, removed)
    return result


def plan_operation_id(plan):
    """Keep legacy receipts readable; give each new exact plan its own receipt."""
    from review_desk import methods
    require(plan.get('format') == FORMAT and plan.get('task') == TASK, '不是本任务的准确清理方案')
    require(methods.checksum({key: value for key, value in plan.items() if key != 'sha256'}) == plan.get('sha256'),
            '清理方案摘要不匹配')
    prefix = TASK + '-method-history-cleanup'
    if 'operation_id' not in plan:
        return prefix
    expected = prefix + '-' + methods.checksum({key: value for key, value in plan.items()
                                               if key not in ('sha256', 'operation_id')})
    require(plan['operation_id'] == expected, '清理操作身份与准确方案不匹配')
    return expected


def build_plan(store, *, legacy=False):
    from review_desk import methods
    catalog = methods.catalog(store)
    skills = {row['object_id']: row for row in catalog['skill'] if row['object_id'] in SKILLS}
    require(set(skills) == SKILLS, '本次十五项方法不完整，不能推断清理范围')
    bindings = {row['object_id']: row for row in catalog['binding']
                if any(ref['object_id'] in SKILLS for ref in row['payload']['rules'])}
    require(bindings, '未找到本范围有效绑定')
    configs = {**skills, **bindings}
    execution_rows = []
    for row in store.db.execute("SELECT * FROM revisions WHERE json_extract(payload,'$.format')='managed-method-execution-v1'"):
        payload = json.loads(row['payload'])
        package = payload['package']
        if package['method']['object_id'] in SKILLS or package['binding']['object_id'] in bindings:
            execution_rows.append((dict(row), payload))
    executions = {row['object_id'] for row, _ in execution_rows}
    artifacts = set()
    for row in store.db.execute("SELECT object_id,payload FROM revisions WHERE json_extract(payload,'$.format')='managed-method-artifact-v1'"):
        if json.loads(row['payload'])['execution']['object_id'] in executions:
            artifacts.add(row['object_id'])
    removed_objects = executions | artifacts
    # Retired predecessors of the SAME work type can still freeze old branches
    # of its binding. Their usage belongs to this cleanup; their definitions do
    # not. In particular, the old combined voice/song execution is included.
    predecessor_usage = [{'object_id': row['object_id'], 'method': payload['package']['method'],
                          'binding': payload['package']['binding']}
                         for row, payload in execution_rows if payload['package']['method']['object_id'] not in SKILLS]
    resource_ids = {ref['object_id'] for row in skills.values() for ref in row['payload'].get('resources', [])}
    resource_history_kept = []
    for oid in sorted(resource_ids):
        if oid in ('method.resource.reader-contract', 'method.resource.continuity'):
            continue
        resource = methods.read(store, oid)
        outside = store.db.execute('''SELECT DISTINCT r.object_id FROM dependencies d
            JOIN revisions target ON target.id=d.to_revision JOIN revisions r ON r.id=d.from_revision
            WHERE target.object_id=?''', (oid,)).fetchall()
        outside = sorted({row[0] for row in outside} - set(configs) - removed_objects)
        # A comment on the retained head does not need an older package. Only
        # an exact historical vision anchor prevents removing that history.
        protected_comments = [row['id'] for row in store.db.execute(
            'SELECT id,anchor,target_revision_id FROM comments WHERE target_object_id=?', (oid,))
            if json.loads(row['anchor']).get('file') == 'production/system-vision.md'
            and row['target_revision_id'] != resource['revision_id']]
        if outside or protected_comments:
            resource_history_kept.append({'object_id': oid, 'required_by_outside_definitions': outside,
                                          'protected_system_vision_comments': protected_comments})
        else:
            configs[oid] = resource
    removed_revisions = []
    for row in store.db.execute('SELECT id,object_id FROM revisions'):
        if row['object_id'] in removed_objects or (row['object_id'] in configs
                and row['id'] != configs[row['object_id']]['revision_id']):
            removed_revisions.append(row['id'])
    removed_revisions = set(removed_revisions)
    changes = []
    allowed_incoming = set()
    for row in store.db.execute("SELECT o.kind,r.* FROM revisions r JOIN objects o ON o.id=r.object_id WHERE r.payload LIKE '%method.execution.%' OR r.payload LIKE '%method.artifact.%'"):
        if row['id'] in removed_revisions:
            continue
        payload = json.loads(row['payload'])
        if not usage_refs(payload) & removed_objects:
            continue
        require(row['kind'] == 'REQUIREMENT' and usage_refs(payload.get('method_basis')) & removed_objects,
                '范围外正文仍引用待清理使用记录：' + row['object_id'])
        current = store.db.execute('SELECT * FROM production_current_records WHERE object_id=?', (row['object_id'],)).fetchone()
        require(current and current['revision_id'] == row['id'], '不能改写历史制作快照的方法依据')
        after = copy.deepcopy(payload)
        del after['method_basis']
        require(not usage_refs(after) & removed_objects, '制作正文还有未识别的方法使用引用')
        changes.append({'object_id': row['object_id'], 'revision_id': row['id'],
                        'before_sha256': methods.checksum(payload), 'after': after,
                        'expected_marker': {'edit_token': current['edit_token'], 'content_sha256': current['payload_sha256']}})
        allowed_incoming.add(row['id'])
    for row in store.db.execute('SELECT * FROM dependencies'):
        if row['to_revision'] in removed_revisions:
            require(row['from_revision'] in removed_revisions | allowed_incoming,
                    '范围外准确依赖仍需要待清理版本：' + row['from_revision'])
    operations = []
    for row in store.db.execute('SELECT * FROM production_current_operations ORDER BY id'):
        value = json.loads(row['result'])
        if not usage_refs(value) & removed_objects:
            continue
        after = clean_receipt(value, removed_objects)
        require(not usage_refs(after) & removed_objects, '操作回执还有未识别的使用引用：' + row['id'])
        operations.append({'id': row['id'], 'before_sha256': methods.checksum(dict(row)), 'after': after})
    for row in store.db.execute('SELECT operation_id,snapshot FROM production_submissions'):
        require(not usage_refs(json.loads(row['snapshot'])) & removed_objects,
                '真实提交仍引用待清理记录，须单独核对：' + row['operation_id'])
    comments = []
    for row in store.db.execute('SELECT * FROM comments ORDER BY id'):
        if row['target_revision_id'] in removed_revisions:
            comments.append({'id': row['id'], 'before_sha256': methods.checksum(dict(row))})
        elif row['target_object_id'] in configs:
            from review_desk.method_document import validate_file_anchor
            validate_file_anchor(configs[row['target_object_id']]['payload'], json.loads(row['anchor']))
    result = {'format': FORMAT, 'task': TASK,
              'heads': {oid: methods.reference(row) for oid, row in sorted(configs.items())},
              'remove_objects': sorted(removed_objects), 'remove_revisions': sorted(removed_revisions),
              'remove_comments': comments, 'current_changes': sorted(changes, key=lambda item: item['object_id']),
              'operation_changes': operations, 'predecessor_usage': sorted(predecessor_usage, key=lambda item: item['object_id']),
              'preserved_resource_history': resource_history_kept,
              'counts': {'skill_latest': len(skills), 'execution': len(executions), 'artifact': len(artifacts),
                         'removed_versions': len(removed_revisions), 'comments': len(comments),
                         'current_method_links': len(changes), 'operation_receipts': len(operations)}}
    if not legacy:
        result['operation_id'] = TASK + '-method-history-cleanup-' + methods.checksum(result)
    result['sha256'] = methods.checksum(result)
    return result


def apply_plan(store, plan):
    """Only call inside the publisher-owned stopped write/recovery window."""
    from review_desk import methods, method_files, material_archives, production_current as current
    from review_desk.store import canonical
    from review_desk.production_current_methods import verify
    operation_id = plan_operation_id(plan)
    require(not store.db.in_transaction, '清理入口必须拥有独立完整事务')
    # Original metadata may be a lossless archive reference. Its validation
    # must use this transaction, not open a second reader while deletion holds
    # an exclusive SQLite lock. The existing scope clears each file's cache.
    with store.db, material_archives.read_scope(store):
        store.db.execute('BEGIN IMMEDIATE')
        saved = store.db.execute('SELECT * FROM production_current_operations WHERE id=?', (operation_id,)).fetchone()
        if saved:
            require(saved['request_sha256'] == plan['sha256'], '该清理操作已执行另一份方案，不能重复删除')
            return json.loads(saved['result'])
        require(build_plan(store, legacy='operation_id' not in plan) == plan,
                '清理对象或引用已变化，保留现场并重核方案')
        removed = set(plan['remove_revisions'])
        for item in plan['current_changes']:
            oid = item['object_id']
            current.guard(store, oid, item['expected_marker'])
            old = store.db.execute('SELECT * FROM objects WHERE id=?', (oid,)).fetchone()
            deps = [{'revision_id': row['to_revision'], 'role': row['role']} for row in store.db.execute(
                'SELECT * FROM dependencies WHERE from_revision=?', (item['revision_id'],)) if row['to_revision'] not in removed]
            current.write_record(store, oid, old['kind'], item['after'], old, deps)
            # Only this exact, already-existing body is grandfathered after its
            # provenance was deliberately cleared. New content still requires
            # a real new method execution; activation is never disabled.
            store.db.execute('''INSERT INTO production_current_baselines VALUES (?,?,?)
                ON CONFLICT(object_id) DO UPDATE SET payload_sha256=excluded.payload_sha256''',
                (oid, current.checksum(item['after']), item['before_sha256']))
        for item in plan['operation_changes']:
            store.db.execute('UPDATE production_current_operations SET result=? WHERE id=?',
                             (canonical(item['after']), item['id']))
        for item in plan['remove_comments']:
            store.db.execute('DELETE FROM comment_events WHERE comment_id=?', (item['id'],))
            store.db.execute('DELETE FROM business_comments WHERE comment_id=?', (item['id'],))
            store.db.execute('DELETE FROM comments WHERE id=?', (item['id'],))
        # Replaying each retained owner rebuilds its one actual file version;
        # the method revision identity and content are preserved.
        for oid in plan['heads']:
            store.db.execute('DELETE FROM method_file_members WHERE package_revision IN (SELECT revision_id FROM method_file_packages WHERE object_id=?)', (oid,))
            store.db.execute('DELETE FROM method_file_packages WHERE object_id=?', (oid,))
            store.db.execute('DELETE FROM method_file_versions WHERE object_id=?', (oid,))
        store.db.execute('CREATE TEMP TABLE cleanup_revisions(id TEXT PRIMARY KEY)')
        store.db.executemany('INSERT INTO cleanup_revisions VALUES (?)', [(rid,) for rid in plan['remove_revisions']])
        store.db.execute('DELETE FROM dependencies WHERE from_revision IN (SELECT id FROM cleanup_revisions)')
        store.db.execute('DELETE FROM revisions WHERE id IN (SELECT id FROM cleanup_revisions)')
        for oid in plan['remove_objects']:
            store.db.execute('DELETE FROM business_codes WHERE object_id=?', (oid,))
            store.db.execute('DELETE FROM objects WHERE id=?', (oid,))
        store.db.execute('DROP TABLE cleanup_revisions')
        method_files.sync(store)
        method_files.validate(store)
        for oid, expected in plan['heads'].items():
            require(methods.reference(methods.read(store, oid)) == expected, '最新版身份被改变')
            require(store.db.execute('SELECT count(*) FROM revisions WHERE object_id=?', (oid,)).fetchone()[0] == 1,
                    '方法仍存在旧版本：' + oid)
        for item in plan['current_changes']:
            require(verify(store, item['object_id'], item['after']) == {'history': 'unknown', 'migration_verified': True},
                    '已清理历史被错误归因于新方法')
        require(not store.db.execute('PRAGMA foreign_key_check').fetchone(), '清理留下外键缺口')
        from review_desk.production_current_bundle import validate
        validate(store)
        receipt = {'format': FORMAT, 'task': TASK, 'operation_id': operation_id,
                   'plan_sha256': plan['sha256'], 'counts': plan['counts'],
                   'heads': plan['heads'], 'business_content_changed': False,
                   'method_provenance_cleared': True, 'future_history_enabled': True}
        store.db.execute('INSERT INTO production_current_operations VALUES (?,?,?)',
                         (operation_id, plan['sha256'], canonical(receipt)))
    return receipt


def compare(before, after, plan):
    """Compare every table, exempting only the plan's exact row identities.

    Changed production rows are then compared against their full expected
    content; exemptions never mean that arbitrary changes are acceptable.
    """
    from review_desk import methods
    from review_desk.store import Store
    operation_id = plan_operation_id(plan)
    with sqlite3.connect(Path(before).resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.execute('PRAGMA cache_size=-4096')
        db.execute('PRAGMA temp_store=FILE')
        db.execute('ATTACH DATABASE ? AS after', (Path(after).resolve().as_uri() + '?mode=ro',))
        schema = "SELECT type,name,tbl_name,sql FROM %s.sqlite_master WHERE name NOT LIKE 'sqlite_%%' ORDER BY type,name"
        require(db.execute(schema % 'main').fetchall() == db.execute(schema % 'after').fetchall(), '清理改变了数据库结构')
        groups = {
            'removed_objects': plan['remove_objects'], 'removed_revisions': plan['remove_revisions'],
            'changed_objects': [row['object_id'] for row in plan['current_changes']],
            'changed_revisions': [row['revision_id'] for row in plan['current_changes']],
            'changed_comments': [row['id'] for row in plan['remove_comments']],
            'changed_operations': [row['id'] for row in plan['operation_changes']] + [operation_id],
            'configured_objects': list(plan['heads']),
        }
        for name, ids in groups.items():
            db.execute('CREATE TEMP TABLE ' + name + '(id TEXT PRIMARY KEY)')
            db.executemany('INSERT INTO ' + name + ' VALUES (?)', [(oid,) for oid in ids])
        filters = {
            'objects': 'id NOT IN (SELECT id FROM removed_objects UNION SELECT id FROM changed_objects)',
            'revisions': 'id NOT IN (SELECT id FROM removed_revisions UNION SELECT id FROM changed_revisions)',
            'dependencies': 'from_revision NOT IN (SELECT id FROM removed_revisions UNION SELECT id FROM changed_revisions)',
            'comments': 'id NOT IN (SELECT id FROM changed_comments)',
            'comment_events': 'comment_id NOT IN (SELECT id FROM changed_comments)',
            'business_comments': 'comment_id NOT IN (SELECT id FROM changed_comments)',
            'business_codes': 'object_id NOT IN (SELECT id FROM removed_objects)',
            'production_current_records': 'object_id NOT IN (SELECT id FROM changed_objects)',
            'production_current_baselines': 'object_id NOT IN (SELECT id FROM changed_objects)',
            'production_current_operations': 'id NOT IN (SELECT id FROM changed_operations)',
            'method_file_versions': 'object_id NOT IN (SELECT id FROM configured_objects)',
            'method_file_packages': 'object_id NOT IN (SELECT id FROM configured_objects)',
        }
        evidence = {}
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for table in tables:
            if table == 'read_generations':
                evidence[table] = {'purpose': 'disposable cache invalidation tokens'}
                continue
            queries = []
            for prefix in ('main', 'after'):
                condition = filters.get(table)
                if table == 'method_file_members':
                    condition = 'package_revision NOT IN (SELECT revision_id FROM ' + prefix + '.method_file_packages WHERE object_id IN (SELECT id FROM configured_objects))'
                queries.append('SELECT * FROM ' + prefix + '."' + table.replace('"', '""') + '"' + (' WHERE ' + condition if condition else ''))
            for left, right in (queries, queries[::-1]):
                require(not db.execute('SELECT 1 FROM (' + left + ' EXCEPT ' + right + ') LIMIT 1').fetchone(), '清理改变了范围外数据：' + table)
            evidence[table] = {'unchanged_rows': db.execute('SELECT count(*) FROM (' + queries[0] + ')').fetchone()[0]}
    old, new = Store.open_readonly(Path(before)), Store.open_readonly(Path(after))
    try:
        require(build_plan(old, legacy='operation_id' not in plan) == plan, '比较基线不是清理时的准确内容')
        removed = set(plan['remove_revisions'])
        for item in plan['current_changes']:
            oid, rid = item['object_id'], item['revision_id']
            previous = old.db.execute('SELECT * FROM objects WHERE id=?', (oid,)).fetchone()
            actual = new.db.execute('SELECT * FROM objects WHERE id=?', (oid,)).fetchone()
            expected = {**dict(previous), 'version': previous['version'] + 1, 'updated_at': actual['updated_at']}
            require(dict(actual) == expected, '当前制作身份变化不符合清理方案：' + oid)
            row = new.db.execute('SELECT * FROM revisions WHERE id=?', (rid,)).fetchone()
            require(json.loads(row['payload']) == item['after'] and row['version'] == actual['version'], '当前制作正文变化不符合清理方案：' + oid)
            prior_deps = {tuple(row) for row in old.db.execute('SELECT * FROM dependencies WHERE from_revision=?', (rid,)) if row['to_revision'] not in removed}
            require({tuple(row) for row in new.db.execute('SELECT * FROM dependencies WHERE from_revision=?', (rid,))} == prior_deps, '范围外制作依赖被改变：' + oid)
        for item in plan['operation_changes']:
            previous = dict(old.db.execute('SELECT * FROM production_current_operations WHERE id=?', (item['id'],)).fetchone())
            actual = dict(new.db.execute('SELECT * FROM production_current_operations WHERE id=?', (item['id'],)).fetchone())
            require(actual['request_sha256'] == previous['request_sha256'] and json.loads(actual['result']) == item['after'], '操作事实变化不符合清理方案')
        for oid, ref in plan['heads'].items():
            require(methods.reference(methods.read(new, oid)) == ref, '保留的准确最新版不同')
        require(not new.db.execute('PRAGMA foreign_key_check').fetchone(), '清理留下外键缺口')
    finally:
        old.close()
        new.close()
    return {'schema_unchanged': True, 'unaffected': evidence,
            'production_payloads_except_method_basis_unchanged': len(plan['current_changes']),
            'operation_provenance_only': len(plan['operation_changes'])}


def retained_registry(registry, plan):
    """Derive the committed latest configuration, without storing another copy."""
    from review_desk import methods
    BASELINES = method_migration.BASELINES
    result = copy.deepcopy(registry)
    result.pop('sha256', None)
    result.pop(BASELINES, None)
    removed = set(plan['remove_revisions'])
    result['records'] = [row for row in result['records'] if row['revision_id'] not in removed]
    first = {}
    for row in sorted(result['records'], key=lambda row: (row['object_id'], row['version'])):
        first.setdefault(row['object_id'], row)
    starts = {oid: {'version': row['version'], 'revision_id': row['revision_id']}
              for oid, row in first.items() if row['version'] > 1}
    if starts:
        result[BASELINES] = starts
    result['sha256'] = methods.checksum(result)
    method_migration.check_registry(result)
    return result


def verify_release_package(package, latest):
    from review_desk import methods
    require(package.get('format') == 'method-history-release-v1' and package.get('task') == TASK,
            '不是本任务的历史清理发布包')
    require(methods.checksum({k: v for k, v in package.items() if k != 'sha256'}) == package.get('sha256'),
            '清理发布包摘要不匹配')
    plan = package['plan']
    require(plan.get('format') == FORMAT and plan.get('task') == TASK
            and methods.checksum({k: v for k, v in plan.items() if k != 'sha256'}) == plan.get('sha256'),
            '发布包的准确清理方案不匹配')
    plan_operation_id(plan)
    method_migration.check_registry(package['install_registry'])
    require(methods.checksum({k: v for k, v in package['install_registry'].items() if k != 'sha256'})
            == package['install_registry'].get('sha256'), '安装配置摘要不匹配')
    require(retained_registry(package['install_registry'], plan) == latest,
            '清理结果不是候选提交中的准确最新版配置')
    require(package.get('latest_registry_sha256') == latest['sha256'], '最新配置摘要不同')
    return {'task': TASK, 'sha256': package['sha256'], 'plan_sha256': plan['sha256'],
            'latest_registry_sha256': latest['sha256'], 'counts': plan['counts']}


def snapshot(database, destination):
    require(not destination.exists(), '不能覆盖已有清理核对快照')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as source:
        with closing(sqlite3.connect(destination)) as target:
            source.backup(target)


def prepare_release(database, install_registry, latest):
    """Read the live cutoff into a disposable copy; never write the live DB."""
    from review_desk import methods
    from review_desk.store import Store
    with tempfile.TemporaryDirectory(prefix='method-cleanup-plan-') as temp:
        copy_path = Path(temp) / '.runtime/review.sqlite3'
        snapshot(database, copy_path)
        method_migration.apply(copy_path, install_registry)
        store = Store.open_readonly(copy_path)
        try:
            plan = build_plan(store)
            actual_registry = method_migration.configuration_registry(store)
        finally:
            store.close()
        # The installation package must include any current outside definitions
        # unchanged; a stale task copy cannot silently drop a concurrent method.
        require(actual_registry == install_registry, '正式配置与安装包不同，先吸收准确当前配置')
    package = {'format': 'method-history-release-v1', 'task': TASK,
               'install_registry': install_registry, 'plan': plan,
               'latest_registry_sha256': latest['sha256']}
    package['sha256'] = methods.checksum(package)
    verify_release_package(package, latest)
    return package


def apply_release(database, package, latest, receipt_directory):
    """Called only by the publisher after stopping its exact application.

    A committed cleanup receipt prevents a retry from reinstalling removed
    versions. Each pre-service preservation boundary has an exact local copy;
    the publisher subsequently compares the cleaned copy with the live result.
    These copies are temporary verification resources, never recovery inputs.
    """
    from review_desk import methods
    from review_desk.store import Store
    verify_release_package(package, latest)
    directory = Path(receipt_directory)
    directory.mkdir(parents=True, exist_ok=True)
    plan = package['plan']

    def file_hash(path):
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest()

    def saved_snapshot(name):
        path = directory / (name + '.sqlite3')
        note = directory / (name + '.json')
        if not path.exists():
            snapshot(database, path)
            digest = file_hash(path)
            note.write_text(json.dumps({'sha256': digest}) + '\n')
        else:
            require(note.is_file(), '快照保存中断，需核对已有文件后恢复：' + str(path))
            digest = file_hash(path)
            require(json.loads(note.read_text()) == {'sha256': digest}, '清理核对快照被改变')
        return path

    store = Store.open_readonly(Path(database))
    try:
        old = store.db.execute('SELECT * FROM production_current_operations WHERE id=?',
                               (plan_operation_id(plan),)).fetchone()
        if old:
            require(old['request_sha256'] == plan['sha256'], '已执行的清理方案不同')
            require(all(methods.reference(methods.read(store, oid)) == ref
                        for oid, ref in plan['heads'].items()),
                    '该清理发布后方法版本已前进，旧包不能作为当前发布重放')
            cleanup_receipt = json.loads(old['result'])
    finally:
        store.close()
    if not old:
        before = saved_snapshot('configuration-before')
        migration = method_migration.apply(database, package['install_registry'])
        migrated = saved_snapshot('configuration-after')
        config_evidence = method_migration.compare(before, migrated, package['install_registry'])
        (directory / 'configuration-migration.json').write_text(json.dumps(
            {'migration': migration, 'preservation': config_evidence}, ensure_ascii=False, indent=2) + '\n')
        store = Store.open_existing(Path(database))
        try:
            cleanup_receipt = apply_plan(store, plan)
        finally:
            store.close()
    else:
        require(all((directory / (name + '.sqlite3')).is_file()
                    for name in ('configuration-before', 'configuration-after')),
                '已清理但缺少原始核对快照，不能重新安装历史')
        migrated = saved_snapshot('configuration-after')
    cleaned_path = directory / 'cleaned.sqlite3'
    if not cleaned_path.exists():
        # Remove freed pages only after the exact transaction has committed.
        # A failed compaction can be resumed without repeating the deletion.
        with closing(sqlite3.connect(database)) as db:
            db.execute('VACUUM')
            require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', '压实后数据库损坏')
    cleaned = saved_snapshot('cleaned')
    preservation = compare(migrated, cleaned, plan)
    actual = method_migration.export_configuration(cleaned)
    require(actual == latest, '清理后的配置与候选最新版不同')
    result = {'cleanup': cleanup_receipt, 'preservation': preservation,
              'cleaned_database': str(cleaned), 'latest_registry_sha256': latest['sha256'],
              'temporary_snapshots': 3, 'recovery': 'forward-only; never restore old snapshots'}
    (directory / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    prepare = sub.add_parser('plan')
    prepare.add_argument('--database', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    change = sub.add_parser('apply')
    change.add_argument('--database', type=Path, required=True)
    change.add_argument('--plan', type=Path, required=True)
    check = sub.add_parser('compare')
    check.add_argument('--before', type=Path, required=True)
    check.add_argument('--after', type=Path, required=True)
    check.add_argument('--plan', type=Path, required=True)
    release = sub.add_parser('prepare-release')
    release.add_argument('--database', type=Path, required=True)
    release.add_argument('--install-registry', type=Path, required=True)
    release.add_argument('--latest-registry', type=Path, required=True)
    release.add_argument('--output', type=Path, required=True)
    for name in ('verify-release', 'apply-release'):
        release = sub.add_parser(name)
        release.add_argument('--package', type=Path, required=True)
        release.add_argument('--latest-registry', type=Path, required=True)
        if name == 'apply-release':
            release.add_argument('--database', type=Path, required=True)
            release.add_argument('--receipts', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    if args.action == 'prepare-release':
        package = prepare_release(args.database, json.loads(args.install_registry.read_text()),
                                  json.loads(args.latest_registry.read_text()))
        with args.output.open('x') as stream:
            stream.write(json.dumps(package, ensure_ascii=False, indent=2) + '\n')
        result = {'sha256': package['sha256'], 'counts': package['plan']['counts'], 'output': str(args.output)}
    elif args.action in ('verify-release', 'apply-release'):
        package, latest = json.loads(args.package.read_text()), json.loads(args.latest_registry.read_text())
        result = (verify_release_package(package, latest) if args.action == 'verify-release'
                  else apply_release(args.database, package, latest, args.receipts))
    elif args.action == 'compare':
        result = compare(args.before, args.after, json.loads(args.plan.read_text()))
    else:
        store = (Store.open_readonly if args.action == 'plan' else Store.open_existing)(args.database)
        try:
            if args.action == 'plan':
                plan = build_plan(store)
                with args.output.open('x') as stream:
                    stream.write(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
                result = {'sha256': plan['sha256'], 'counts': plan['counts'], 'output': str(args.output)}
            else:
                result = apply_plan(store, json.loads(args.plan.read_text()))
        finally:
            store.close()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
