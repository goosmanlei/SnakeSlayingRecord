#!/usr/bin/env python3
"""Prepare and verify this story's complete material storage migration in isolation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def inventory(workspace):
    from review_desk.material_archives import read_json
    names=subprocess.check_output(['git','-C',str(workspace),'ls-files','production'],text=True).splitlines()
    result=[]
    def definition(value):
        if isinstance(value,dict):
            if any(k in value for k in ('generation','prompt','text_prompt')):return True
            return any(definition(v) for v in value.values())
        if isinstance(value,list):return any(definition(v) for v in value)
        if isinstance(value,str) and value.lstrip().startswith(('{','[')):
            try:return definition(json.loads(value))
            except ValueError:return False
        return False
    for name in names:
        if not name.endswith('.json') or name.startswith(('production/ui-material-model/','production/ui-unification/','production/evidence/','production/autonomous-optimization-release/')):continue
        path=workspace/name
        if path.is_symlink():raise ValueError('managed archive is a symlink: '+name)
        value=read_json(path)
        if name.startswith(('production/requests/','production/receipts/')) or definition(value):result.append(name)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',required=True,type=Path)
    parser.add_argument('--workspace',default=ROOT,type=Path)
    parser.add_argument('--instance',required=True,type=Path)
    parser.add_argument('--package',default=Path('production/ui-material-model/migration.json'),type=Path)
    parser.add_argument('action',choices=('plan','apply','verify','rollback','package'))
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args();workspace=args.workspace.resolve();instance=args.instance.resolve()
    if workspace/'.runtime' not in instance.parents:raise ValueError('story migration helper only operates on this worktree isolated instances')
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import material_model as model,material_storage as storage,material_archives as archives
    from review_desk.bundle import export
    package=args.package if args.package.is_absolute() else workspace/args.package
    store=Store(instance/'.runtime/review.sqlite3')
    try:
        if args.action=='plan':
            paths=inventory(workspace)
            for name in paths:
                source=workspace/name;destination=instance/name;destination.parent.mkdir(parents=True,exist_ok=True)
                original=archives.read_bytes(source)
                if destination.exists() and archives.read_bytes(destination)!=original:raise ValueError('isolated archive differs: '+name)
                if not destination.exists():destination.write_bytes(original)
            head=subprocess.check_output(['git','-C',str(args.system),'rev-parse','HEAD'],text=True).strip()
            document=model.migration_plan(store,system_head=head,archive_paths=paths)
            # Preparation artifacts stay private until the package action.
            target=instance/'migration.json';target.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
            result={'migration':str(target),**document['counts'],'id':document['id']}
        elif args.action=='apply':
            document=model.load_migration(instance/'migration.json')
            result=model.migrate(store,document,args.validate_only)
            if not args.validate_only:result['export']=export(store,instance/'export')['schema_version']
        elif args.action=='rollback':
            result=model.rollback(store,model.load_migration(instance/'migration.json'),args.validate_only)
        elif args.action=='package':
            document=model.load_migration(instance/'migration.json')
            if not store.db.execute('SELECT 1 FROM material_model_migrations WHERE id=?',(document['id'],)).fetchone():raise ValueError('package requires an applied, verified isolated migration')
            result=model.verify(store)
            export(store,instance/'export')
            # Exactly the isolated, verified export and archive containers are
            # candidates for Git review. No live database or media byte changes.
            for row in document['archives']:
                relative=row.get('path','export/assets/'+row['file']);source=instance/relative;target=workspace/relative
                if archives.read_bytes(source)!=archives.decode(row['container'],lambda key:storage.expand(store,key)):raise ValueError('archive readback differs')
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            manifest=json.loads((instance/'export/manifest.json').read_text())
            for name in [*manifest['files'],'manifest.json']:
                source=instance/'export'/name;target=workspace/'export'/name
                if name.startswith('assets/') and source.suffix!='.json':
                    if hashlib.sha256(source.read_bytes()).hexdigest()!=hashlib.sha256(target.read_bytes()).hexdigest():raise ValueError('real media differs: '+name)
                    continue
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            result.update(model.write_migration_package(store,document,package,workspace/'export/material-content.json'))
        else:
            result=model.verify(store)
            document=model.load_migration(instance/'migration.json')
            result['archives']=len(document['archives'])
            for row in document['archives']:
                path=instance/row.get('path','export/assets/'+row['file'])
                if hashlib.sha256(archives.read_bytes(path)).hexdigest()!=row['before_sha256']:raise ValueError('archive original SHA differs')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:store.close()


if __name__=='__main__':main()
