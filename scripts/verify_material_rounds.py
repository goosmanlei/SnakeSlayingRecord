#!/usr/bin/env python3
"""Verify unchanged legacy rows and exact export/recovery of an isolated migration."""
import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

LEGACY=('sources','objects','revisions','dependencies','comments','comment_events','configurations','configuration_events')

def rows(path,table):
    db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True)
    try:return sorted([list(r) for r in db.execute('SELECT * FROM '+table)],key=lambda r:json.dumps(r,ensure_ascii=False))
    finally:db.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--system',required=True,type=Path);ap.add_argument('--before',required=True,type=Path)
    ap.add_argument('--instance',required=True,type=Path);ap.add_argument('--restore-to',required=True,type=Path);ap.add_argument('--report',required=True,type=Path)
    args=ap.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk.bundle import export,restore
    from review_desk.material_versions import TABLES,dump,validate
    if args.restore_to.exists():raise ValueError('recovery destination must be new')
    after=args.instance/'.runtime/review.sqlite3';report={'format':'material-round-verification-v1','legacy_tables':{}}
    for table in LEGACY:
        before,current=rows(args.before,table),rows(after,table)
        if before!=current:raise ValueError('legacy rows changed: '+table)
        report['legacy_tables'][table]={'rows':len(current),'unchanged':True}
    store=Store(after)
    try:
        validate(store,dump(store));export(store,args.instance/'export')
        for folder in ('config','content','export'):
            if (args.instance/folder).exists():shutil.copytree(args.instance/folder,args.restore_to/folder)
        recovered=Store(args.restore_to/'.runtime/review.sqlite3')
        try:restore(recovered,args.restore_to/'export');export(recovered,args.restore_to/'export')
        finally:recovered.close()
        for table in (*LEGACY,*TABLES):
            if rows(after,table)!=rows(args.restore_to/'.runtime/review.sqlite3',table):raise ValueError('recovery differs: '+table)
        original=json.loads((args.instance/'export/manifest.json').read_text());restored=json.loads((args.restore_to/'export/manifest.json').read_text())
        if original!=restored:raise ValueError('second export differs')
        for name,sha in original['files'].items():
            for root in (args.instance,args.restore_to):
                if hashlib.sha256((root/'export'/name).read_bytes()).hexdigest()!=sha:raise ValueError('file differs: '+name)
        report.update(round_tables={name:len(values) for name,values in dump(store).items()},recovery_equal=True,manifest_files=len(original['files']),asset_files=sum(k.startswith('assets/') for k in original['files']),schema_version=original['schema_version'])
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
    finally:store.close()

if __name__=='__main__':main()
