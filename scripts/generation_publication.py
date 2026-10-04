"""Exact production increments and transaction-bound publication receipts.

Snapshots are inputs for computing a delta, never replacements for a live DB.
The journal is operational metadata; ordinary review exports remain unchanged.
"""
import hashlib
import json
from pathlib import Path
import sqlite3

KEYS = {
    'objects': ('id',), 'revisions': ('id',),
    'dependencies': ('from_revision', 'to_revision', 'role'),
    'comments': ('id',), 'material_rounds': ('material_id', 'number'),
    'material_members': ('material_id', 'number', 'revision_id'),
    'material_feedback': ('comment_id',),
    'material_comment_scopes': ('comment_id', 'material_id'),
    'material_plan_versions': ('material_id','number'),
    'material_plan_members': ('material_id','revision_id'),
    'material_candidate_members': ('candidate_id','revision_id'),
    'material_plan_comments': ('comment_id','material_id'),
}
PLAN_TABLES={'material_plan_versions','material_plan_members','material_candidate_members','material_plan_comments'}
MUTABLE = {'objects', 'comments', 'material_rounds','material_plan_versions'}
PRODUCTION_KINDS = {'ENTITY', 'STATE', 'REPRESENTATION', 'REQUIREMENT', 'CALL',
                    'ASSET', 'JUDGMENT', 'RELATION', 'PREPARATION',
                    'ASSEMBLY', 'DELIVERABLE', 'SHOT_DESIGN', 'INPUT_LOCK'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def publication_id(plan):
    return hashlib.sha256(canonical(plan).encode()).hexdigest()


def connect(path, *, readonly=True):
    db = sqlite3.connect(Path(path).resolve().as_uri() + ('?mode=ro' if readonly else '?mode=rw'), uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


def backup(source, destination):
    destination = Path(destination)
    with destination.open('xb'):
        pass
    src, dst = connect(source), sqlite3.connect(destination)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()


def tables(path):
    db = connect(path)
    try:
        db.execute('BEGIN')
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {name: [dict(r) for r in db.execute('SELECT * FROM "' + name.replace('"', '""') + '"')]
                for name in names if name != 'generation_publications'}
    finally:
        db.close()


def key(table, row):
    return tuple(row[k] for k in KEYS[table])


def revision_media(changes):
    media = {}
    for change in changes:
        for component in json.loads(change['after']['payload']).get('components', []):
            name = component['file']
            entry = {k: component[k] for k in ('file', 'sha256', 'bytes')}
            if name in media and media[name] != entry:
                raise ValueError('conflicting media components')
            media[name] = entry
    return [media[name] for name in sorted(media)]


def build_plan(before_path, after_path):
    before, after = tables(before_path), tables(after_path)
    for table in PLAN_TABLES:
        before.setdefault(table,[]);after.setdefault(table,[])
    if set(before) != set(after):
        raise ValueError('review schema changed; migrate and validate before preparing publication')
    changes = {table: [] for table in KEYS}
    for table in before:
        if table == 'comment_events':
            continue
        if table not in KEYS:
            if sorted(map(canonical, before[table])) != sorted(map(canonical, after[table])):
                raise ValueError('generation cannot publish changes to ' + table)
            continue
        old = {key(table, r): r for r in before[table]}
        new = {key(table, r): r for r in after[table]}
        if old.keys() - new.keys():
            raise ValueError('generation publication cannot delete history: ' + table)
        for pk, row in new.items():
            previous = old.get(pk)
            if row == previous:
                continue
            if previous is not None and table not in MUTABLE:
                raise ValueError('immutable history changed: ' + table)
            changes[table].append({'before': previous, 'after': row})
    old_events = {r['id']: r for r in before['comment_events']}
    new_events = {r['id']: r for r in after['comment_events']}
    if any(new_events.get(i) != r for i, r in old_events.items()):
        raise ValueError('existing comment events changed')
    events = [r for i, r in sorted(new_events.items()) if i not in old_events]
    objects = {r['id']: r for r in after['objects']}
    old_objects = {r['id']: r for r in before['objects']}
    scope = {c['after']['id'] for c in changes['objects']}
    scope.update(c['after']['target_object_id'] for c in changes['comments'])
    scope.update(c['after']['material_id'] for t in KEYS if t.startswith('material_') for c in changes[t] if 'material_id' in c['after'])
    if any(objects[oid]['kind'] not in PRODUCTION_KINDS for oid in scope):
        raise ValueError('generation publication cannot change story or system objects')
    new_revisions = {c['after']['id'] for c in changes['revisions']}
    refs = {c['after']['to_revision'] for c in changes['dependencies']}
    refs.update(c['after']['target_revision_id'] for c in changes['comments'])
    before_revisions = {r['id']: r for r in before['revisions']}
    expected_references = {rid: before_revisions[rid] for rid in refs - new_revisions}
    return {'format': 'generation-publication-v1', 'scope': sorted(scope),
            'expected_heads': {oid: old_objects.get(oid) for oid in sorted(scope)},
            'expected_references': expected_references,
            'guard_heads': {r['object_id']: r['id'] for r in expected_references.values()
                            if old_objects[r['object_id']]['current_revision'] == r['id']},
            'changes': changes,
            'comment_events': events, 'media': revision_media(changes['revisions'])}


def receipt(db, pid):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='generation_publications'").fetchone():
        return None
    row = db.execute('SELECT receipt FROM generation_publications WHERE id=?', (pid,)).fetchone()
    return json.loads(row[0]) if row else None


def journal(db, pid, callback):
    """The callback must not begin or commit a transaction of its own."""
    if db.in_transaction:
        raise ValueError('publication requires ownership of the database transaction')
    db.execute('BEGIN IMMEDIATE')
    try:
        previous = receipt(db, pid)
        if previous is not None:
            db.rollback()
            return {**previous, 'already_published': True}
        result = callback()
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('publication would leave broken references')
        result.update(publication_id=pid, already_published=False)
        db.execute('CREATE TABLE IF NOT EXISTS generation_publications (id TEXT PRIMARY KEY, receipt TEXT NOT NULL)')
        db.execute('INSERT INTO generation_publications VALUES (?,?)', (pid, canonical(result)))
        db.commit()
        return result
    except BaseException:
        db.rollback()
        raise


def apply_plan(db, plan, *, identity=None):
    active_keys={k:v for k,v in KEYS.items() if k in plan.get('changes',{})}
    if plan.get('format') != 'generation-publication-v1' or set(plan.get('changes',{})) != set(active_keys) or set(active_keys) not in (set(KEYS),set(KEYS)-PLAN_TABLES):
        raise ValueError('invalid generation publication package')
    if sorted(plan['media'], key=lambda row: row['file']) != revision_media(plan['changes']['revisions']):
        raise ValueError('media manifest differs from published revisions')
    scope = set(plan['scope'])
    if scope != set(plan['expected_heads']):
        raise ValueError('publication scope differs from expected heads')

    def current(table, row):
        result = db.execute('SELECT * FROM ' + table + ' WHERE ' + ' AND '.join(k + '=?' for k in KEYS[table]), key(table, row)).fetchone()
        return dict(result) if result else None

    def mutate():
        if PLAN_TABLES <= set(active_keys):
            from review_desk.material_plans import SCHEMA
            # Additive schema and data belong to the same transaction. executescript
            # would commit the caller's transaction before running its statements.
            for statement in SCHEMA.split(';'):
                if statement.strip():
                    db.execute(statement)
        columns = {t: {r[1] for r in db.execute('PRAGMA table_info(' + t + ')')} for t in active_keys}
        for oid, expected in plan['expected_heads'].items():
            if current('objects', {'id': oid}) != expected:
                raise ValueError('formal object changed: ' + oid)
        for oid, rid in plan.get('guard_heads', {}).items():
            row = current('objects', {'id': oid})
            if not row or row['current_revision'] != rid:
                raise ValueError('formal input changed: ' + oid)
        for rid, expected in plan['expected_references'].items():
            if current('revisions', {'id': rid}) != expected:
                raise ValueError('exact dependency changed or missing: ' + rid)
        changed_revisions = {c['after']['id'] for c in plan['changes']['revisions']}
        changed_comments = {c['after']['id'] for c in plan['changes']['comments']}
        for table in active_keys:
            changes = plan['changes'][table]
            seen = set()
            for change in changes:
                old, new = change['before'], change['after']
                if set(new) != columns[table] or old is not None and set(old) != columns[table]:
                    raise ValueError('publication columns differ from database schema')
                pk = key(table, new)
                if pk in seen or old is not None and key(table, old) != pk:
                    raise ValueError('duplicate or changed row identity')
                seen.add(pk)
                owner = (new['id'] if table == 'objects' else new.get('object_id') or
                         new.get('target_object_id') or new.get('material_id'))
                if owner and owner not in scope:
                    raise ValueError('row outside publication scope')
                if table == 'objects' and new['kind'] not in PRODUCTION_KINDS:
                    raise ValueError('non-production object')
                if table == 'dependencies' and new['from_revision'] not in changed_revisions:
                    raise ValueError('dependency outside new history')
                if old is not None and table not in MUTABLE:
                    raise ValueError('immutable history cannot be updated')
                protected = {'objects': ('id', 'kind', 'created_at'),
                             'comments': ('id', 'source_id', 'target_object_id', 'target_revision_id', 'anchor', 'created_at'),
                             'material_rounds': ('material_id', 'number', 'created_at')}
                if old and any(old[k] != new[k] for k in protected.get(table, ())):
                    raise ValueError('immutable identity or comment anchor changed')
                if current(table, new) != old:
                    raise ValueError('formal row changed: ' + table)
        for table in active_keys:
            changes = plan['changes'][table]
            for change in changes:
                row = change['after']
                if change['before'] is None:
                    names = list(row)
                    db.execute('INSERT INTO ' + table + ' (' + ','.join(names) + ') VALUES (' + ','.join('?' for _ in names) + ')', tuple(row.values()))
                else:
                    names = [k for k in row if k not in KEYS[table]]
                    db.execute('UPDATE ' + table + ' SET ' + ','.join(k + '=?' for k in names) +
                               ' WHERE ' + ' AND '.join(k + '=?' for k in KEYS[table]),
                               tuple(row[k] for k in names) + key(table, row))
        for oid in scope:
            obj = current('objects', {'id': oid})
            head = current('revisions', {'id': obj['current_revision']}) if obj else None
            if not head or head['object_id'] != oid or head['version'] != obj['version']:
                raise ValueError('invalid current revision after publication: ' + oid)
        events = []
        for row in plan['comment_events']:
            if set(row) != {'id', 'comment_id', 'action', 'body', 'at'} or row['comment_id'] not in changed_comments:
                raise ValueError('comment event outside changed comments')
            result = db.execute('INSERT INTO comment_events(comment_id,action,body,at) VALUES (?,?,?,?)',
                                tuple(row[k] for k in ('comment_id', 'action', 'body', 'at')))
            events.append({'source_id': row['id'], 'published_id': result.lastrowid, 'comment_id': row['comment_id']})
        if PLAN_TABLES <= set(active_keys):
            from review_desk.material_plans import validate
            from types import SimpleNamespace
            validate(SimpleNamespace(db=db,comment=lambda cid:dict(db.execute('SELECT * FROM comments WHERE id=?',(cid,)).fetchone())))
        return {'changed_rows': {t: len(c) for t, c in plan['changes'].items()}, 'comment_events': events}

    return journal(db, identity or publication_id(plan), mutate)
