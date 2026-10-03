#!/usr/bin/env python3
"""Publish an already validated generation increment under the shared writer lock.

Never imports an inventory snapshot, resets a database, deploys code, or calls a
provider. A partial publication requires inspecting receipts before recovery.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]


def backup(source,target):
    a=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(target)
    try:a.backup(b)
    finally:b.close();a.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--registration',type=Path,default=ROOT/'production/full-generation/registration.json')
    parser.add_argument('--run-name',default='publication')
    args=parser.parse_args();target=args.instance.resolve()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',args.run_name):
        parser.error('run-name must be a safe, unique runtime directory name')
    if target==ROOT or target==Path('/') or not (target/'.runtime/review.sqlite3').is_file():
        parser.error('explicit existing formal instance required; no task checkout or empty instance')
    source=args.registration.resolve()
    if ROOT/'production/full-generation' not in source.parents:
        parser.error('registration must be a reviewed package within production/full-generation')
    document=json.loads(source.read_text());batches=document['batches']
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk import production as p
    from review_desk.production_media import ingest,validate_component
    from review_desk.store import Store
    from verify_full_generation import verify
    runtime=ROOT/'.runtime/full-generation'/args.run_name;runtime.mkdir(parents=True,exist_ok=True)
    receipt=runtime/'applied.json'
    if receipt.exists():parser.error('publication already has a receipt; inspect and do not blindly replay')
    with (target/'.runtime/publication.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=runtime/('before.sqlite3' if args.apply else 'preflight.sqlite3')
        if before.exists():parser.error('previous publication attempt exists; inspect before recovery')
        backup(target/'.runtime/review.sqlite3',before)
        # Guard all exact heads before copying media or opening a writable store.
        db=sqlite3.connect(before);heads=dict(db.execute('select id,current_revision from objects'));db.close()
        changed={oid:{'expected':rid,'actual':heads.get(oid)} for oid,rid in batches[0]['expected_heads'].items() if heads.get(oid)!=rid}
        if changed:
            (runtime/'input-delta.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n')
            raise ValueError('formal inputs changed; inspect input-delta.json before rebuilding')
        if not args.apply:
            print(json.dumps({'validated_heads':len(heads),'pending_apply':True}));return
        components={c['file']:c for batch in batches for r in batch['records'] for c in r['payload'].get('components',[])}
        for name,c in components.items():
            path=validate_component(ROOT,c)
            with path.open('rb') as f:
                actual=ingest(target,f,path.name)
            if actual['sha256']!=c['sha256']:raise ValueError('published original differs')
        s=Store(target/'.runtime/review.sqlite3');result=[]
        try:
            for i,batch in enumerate(batches):
                result.append(p.import_records(s,batch))
                (runtime/('batch-'+str(i+1)+'.json')).write_text(json.dumps(result[-1],ensure_ascii=False,indent=2)+'\n')
        finally:s.close()
        after=runtime/'after.sqlite3';backup(target/'.runtime/review.sqlite3',after)
        evidence=verify(before,after,document)
        evidence.update(registration_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),new_files={k:v['sha256'] for k,v in components.items()},
                        publication_lock='main .runtime/publication.lock',provider_calls_during_publication=0)
        receipt.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
        evidence_name='full-generation-formal-publication.json' if args.run_name=='publication' else 'full-generation-'+args.run_name+'.json'
        (ROOT/'production/evidence'/evidence_name).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in evidence.items() if k not in ('changed_objects','new_files')},ensure_ascii=False))


if __name__=='__main__':main()
