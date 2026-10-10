#!/usr/bin/env python3
"""Index or restore the current clean production export; never replay retired plans."""
import argparse
import json
from pathlib import Path
import shutil
import sys

try:
    from .generation_workspace import generation_root, isolated_instance
except ImportError:
    from generation_workspace import generation_root, isolated_instance

ROOT = Path(__file__).resolve().parents[1]


def complete_export_index(store, production):
    """Index exact identities without expanding historical material payloads.

    Schema 6+ bundles already contain every revision. A second import replay is
    redundant and can multiply memory use by retaining all hydrated histories.
    """
    formats = tuple(production.FORMATS)
    placeholders = ','.join('?' for _ in formats)
    rows = store.db.execute(
        'SELECT id,object_id,version FROM revisions WHERE '
        "json_extract(payload,'$.format') IN (" + placeholders + ') '
        'ORDER BY object_id,version', formats)
    heads, revisions = {}, []
    for row in rows:
        heads[row['object_id']] = row['id']
        revisions.append(row['id'])
    files = {}
    for row in store.db.execute(
            "SELECT json_extract(payload,'$.components') AS components FROM revisions "
            "WHERE json_type(payload,'$.components')='array'"):
        for component in json.loads(row['components']):
            name = 'export/assets/' + component['file']
            if name in files and files[name] != component['sha256']:
                raise ValueError('conflicting original checksums: ' + name)
            files[name] = component['sha256']
    return {'format': 'production-export-index-v1', 'heads': heads,
            'revisions': sorted(revisions), 'files': files}


def verify_export_index(index, export_dir, formats):
    """Bind the small index to the exact complete bundle, including all history."""
    from review_desk.material_content_stream import members
    wanted = set(index['revisions'])
    found, heads = set(), {}
    versions = {}
    for row in members(export_dir / 'objects.json', 'revisions'):
        if json.loads(row['payload']).get('format') not in formats:
            continue
        found.add(row['id'])
        if row['version'] > versions.get(row['object_id'], 0):
            versions[row['object_id']] = row['version']
            heads[row['object_id']] = row['id']
    if found != wanted or heads != index['heads']:
        raise ValueError('complete export and production index describe different revisions')


def main():
    parser=argparse.ArgumentParser(description='Index or restore the current complete audiovisual export into an empty task instance.')
    parser.add_argument('--system',type=Path,required=True);parser.add_argument('--workspace',type=Path,default=ROOT)
    commands=parser.add_subparsers(dest='command',required=True)
    q=commands.add_parser('snapshot');q.add_argument('--instance',type=Path,required=True)
    q=commands.add_parser('recover');q.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args();root=generation_root(args.workspace);sys.path.insert(0,str(args.system.resolve()))
    from review_desk import production
    from review_desk.store import Store
    from review_desk.bundle import restore
    from publication_receipts import RECOVERY,restore_publication_receipts,sha,save
    manifest=json.loads((root/'export/manifest.json').read_text())
    if manifest.get('schema_version')!=11:raise ValueError('use the current clean unified-relationship export (schema 11)')
    index_path=root/'production/audiovisual/index.json'
    if args.command=='snapshot':
        instance=args.instance if args.instance.is_absolute() else root/args.instance
        store=Store.open_readonly(instance/'.runtime/review.sqlite3')
        try:
            data=complete_export_index(store,production);verify_export_index(data,root/'export',production.FORMATS)
            data['base_manifest_sha256']=sha(root/'export/manifest.json');save(index_path,data)
            print(json.dumps({'objects':len(data['heads']),'revisions':len(data['revisions']),'files':len(data['files'])}))
        finally:store.close()
        return
    destination=isolated_instance(root,args.destination)
    if destination.exists():raise ValueError('recovery requires a new destination; no existing database is overwritten')
    data=json.loads(index_path.read_text())
    if data['base_manifest_sha256']!=sha(root/'export/manifest.json'):raise ValueError('production index and export differ')
    verify_export_index(data,root/'export',production.FORMATS)
    destination.mkdir(parents=True)
    for folder in ('config','content','export'):shutil.copytree(root/folder,destination/folder)
    (destination/RECOVERY).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/RECOVERY,destination/RECOVERY)
    store=Store(destination/'.runtime/review.sqlite3')
    try:
        restore(store,destination/'export');restore_publication_receipts(store,destination)
        recovered=complete_export_index(store,production)
        if any(recovered[k]!=data[k] for k in ('heads','revisions','files')):raise ValueError('restored exact production index differs')
        print(json.dumps({'recovered':True,'objects':len(store.objects()),'production_objects':len(recovered['heads']),'revisions':len(store.revisions()),'comments':len(store.comments()),'files_verified':len(manifest['files']),'destination':str(destination)},ensure_ascii=False))
    finally:store.close()

if __name__=='__main__':main()
