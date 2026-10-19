"""Read legacy bytes from managed material archives without changing ordinary files.

Core codecs live in the review system. Commands with --system load that checkout;
standalone authoring tools can set PYTHONPATH or REVIEW_DESK_SYSTEM explicitly.
"""
import importlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace


def backend(name):
    try:return importlib.import_module('review_desk.'+name)
    except ModuleNotFoundError as exc:
        system=os.environ.get('REVIEW_DESK_SYSTEM')
        if system:
            sys.path.insert(0,str(Path(system).resolve()))
            return importlib.import_module('review_desk.'+name)
        raise RuntimeError('读取引用化素材需指定兼容系统：使用 --system，或设置 REVIEW_DESK_SYSTEM / PYTHONPATH。') from exc


def resource_path(path):
    path=Path(path).absolute()
    for root in path.parents:
        if (root/'config/instance.json').is_file():
            if not (root/'config/resource-storage.json').is_file():
                break
            resources=backend('resources')
            relative=path.relative_to(root).as_posix()
            try:
                resources.descriptor(root,relative)
            except FileNotFoundError:
                break
            return resources.materialize(root,relative)
    return path


def read_bytes(path):
    is_json=Path(path).suffix.lower()=='.json'
    path=resource_path(path)
    raw=path.read_bytes()
    if is_json and b'material-archive-reference-v1' in raw[:160]:
        return backend('material_archives').read_bytes(path)
    return raw


def read_json(path):
    return json.loads(read_bytes(path))


def sqlite_compatibility(db,hydrate=False):
    """Install codecs on an existing connection; no schema or data writes."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='material_content'").fetchone():return db
    import hashlib
    store=SimpleNamespace(db=db)
    def revision_hash(oid,version,payload):
        if '"_material_fields"' in payload:payload=backend('material_storage').hydrate(store,payload)
        value={'object_id':oid,'version':version,'payload':json.loads(payload)}
        return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    db.create_function('material_model_migrating',0,lambda:0)
    db.create_function('material_sha256',1,lambda text:hashlib.sha256(text.encode()).hexdigest(),deterministic=True)
    db.create_function('material_revision_sha256',3,revision_hash)
    def valid(oid,version,payload,rid):
        return int(backend('version_consolidation').valid_identity(store,oid,version,
                   json.loads(backend('material_storage').hydrate(store,payload)),rid))
    db.create_function('material_revision_valid',4,valid)
    if hydrate:db.row_factory=backend('material_storage').row_factory(store)
    return db


def open_bytes(path):
    import io
    path=resource_path(path)
    if path.suffix.lower()=='.json':
        with path.open('rb') as stream:head=stream.read(160)
        if b'material-archive-reference-v1' in head:return io.BytesIO(read_bytes(path))
    return path.open('rb')


def logical_file_hash(path):
    import hashlib
    value=hashlib.sha256()
    with open_bytes(path) as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def logical_size(path):
    path=resource_path(path)
    if path.suffix.lower()=='.json':
        with path.open('rb') as source:head=source.read(160)
        if b'material-archive-reference-v1' in head:return len(read_bytes(path))
    return path.stat().st_size


def read_framework(path, *, current_only=False, revision_ids=None, kinds=None):
    """Read logical revisions from either legacy JSON or a Schema 6 export.

    current_only / revision_ids project just objects and selected revisions;
    other export tables are omitted and unselected revision bodies are not hydrated.
    """
    path=Path(path)
    manifest=path.parent/'manifest.json'
    if path.name=='objects.json' and manifest.is_file() and json.loads(manifest.read_text()).get('schema_version')==16:
        import sqlite3
        root=path.parent.parent;document=json.loads(manifest.read_text())
        resources=backend('resources')
        snapshot=resources.materialize(root,'database.sqlite3',spec=document['snapshot'])
        db=sqlite3.connect(snapshot.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        try:
            objects=[dict(row) for row in db.execute('SELECT * FROM objects ORDER BY id') if kinds is None or row['kind'] in kinds]
            wanted=set(revision_ids or ())
            if current_only:wanted.update(row['current_revision'] for row in objects)
            if current_only or revision_ids is not None:
                revisions=[dict(row) for rid in sorted(wanted) for row in db.execute('SELECT * FROM revisions WHERE id=?',(rid,))]
                return {'objects':objects,'revisions':revisions}
            excluded={'sources','comments','comment_events','configurations','configuration_events','read_generations','material_content'}
            result={table:[dict(row) for row in db.execute('SELECT * FROM "'+table+'" ORDER BY 1')]
                    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall() if table not in excluded}
            result['objects']=objects
            return result
        finally:db.close()
    path=resource_path(path)
    if current_only or revision_ids is not None:
        members=backend('material_content_stream').members
        objects=[o for o in members(path,'objects') if kinds is None or o['kind'] in kinds]
        wanted=set(revision_ids or ())
        if current_only:wanted.update(o['current_revision'] for o in objects)
        value={'objects':objects,'revisions':[row for row in members(path,'revisions') if row['id'] in wanted]}
    else:
        value=read_json(path)
        if kinds is not None:value['objects']=[o for o in value['objects'] if o['kind'] in kinds]
    if not any('"_material_fields"' in row.get('payload','') for row in value.get('revisions',[])):return value
    storage=backend('material_storage');resolve=backend('material_archives').resolver(path)
    try:
        for row in value['revisions']:
            row['payload']=storage.hydrate(None,row['payload'],resolve)
            resolve.clear()
        return value
    finally:resolve.close()


def framework_members(path, table):
    """Stream one table from the disk snapshot or a legacy JSON bundle."""
    path=Path(path);manifest=path.parent/'manifest.json'
    value=json.loads(manifest.read_text()) if manifest.is_file() else {}
    if value.get('schema_version')!=16:
        yield from backend('material_content_stream').members(resource_path(path),table)
        return
    import sqlite3
    snapshot=backend('resources').materialize(path.parent.parent,'database.sqlite3',spec=value['snapshot'])
    db=sqlite3.connect(snapshot.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():
            return
        for row in db.execute('SELECT * FROM "'+table.replace('"','""')+'" ORDER BY 1'):
            yield dict(row)
    finally:db.close()
