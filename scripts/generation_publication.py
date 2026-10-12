"""Exact production increments and transaction-bound publication receipts.

Snapshots are inputs for computing a delta, never replacements for a live DB.
The journal is operational metadata; ordinary review exports remain unchanged.
"""
import hashlib
import json
from pathlib import Path
import sqlite3

try:
    from .material_model_io import sqlite_compatibility
except ImportError:
    from material_model_io import sqlite_compatibility

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def publication_id(plan):
    return hashlib.sha256(canonical(plan).encode()).hexdigest()


def connect(path, *, readonly=True):
    db = sqlite3.connect(Path(path).resolve().as_uri() + ('?mode=ro' if readonly else '?mode=rw'), uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    sqlite_compatibility(db)
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
                for name in names if name not in ('generation_publications','read_generations')}
    finally:
        db.close()


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
    if not before.get('production_current_policy') or not after.get('production_current_policy'):
        raise ValueError('只支持当前制作模型，请从最新正式基线重新准备')
    try:from .production_current_publication import build
    except ImportError:from production_current_publication import build
    return build(before, after)


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


def apply_plan(db, plan, *, identity=None, media_root=None):
    if plan.get('format') != 'production-current-publication-v1':
        raise ValueError('旧制作增量不能写入当前模型，请从最新正式基线重新准备')
    try:from .production_current_publication import apply
    except ImportError:from production_current_publication import apply
    return apply(db, plan, identity=identity, media_root=media_root)


def validate_numbered_row(db, table, row, scope, guarded):
    """Allocate display identities without renumbering or changing story content."""
    if type(row['number']) is not int or row['number'] < 1:
        raise ValueError('invalid business number')
    if table == 'business_codes':
        from review_desk.business_codes import PREFIXES
        oid = row['object_id'];scene = None
        if oid.startswith('scene:'):
            _, oid, scene = oid.split(':',2)
        if oid not in scope and oid not in guarded:
            raise ValueError('numbered identity outside guarded objects')
        obj = db.execute('SELECT kind,current_revision FROM objects WHERE id=?',(oid,)).fetchone()
        if not obj:raise ValueError('numbered object is missing')
        payload=json.loads(db.execute('SELECT payload FROM revisions WHERE id=?',(obj['current_revision'],)).fetchone()[0])
        prefix='RL' if obj['kind']=='RELATION' and payload.get('relation_type')=='entity' else PREFIXES.get(obj['kind'])
        if scene is not None:
            exists=obj['kind']=='EPISODE' and any(scene==v.get('id') for r in db.execute('SELECT payload FROM revisions WHERE object_id=?',(oid,)) for v in json.loads(r[0]).get('scenes',[]))
            if not exists:raise ValueError('numbered scene is missing')
            prefix='S'
        if row['prefix']!=prefix:raise ValueError('business prefix differs from exact object kind')
    elif not db.execute('SELECT 1 FROM comments WHERE id=?',(row['comment_id'],)).fetchone():
        raise ValueError('numbered comment is missing')
