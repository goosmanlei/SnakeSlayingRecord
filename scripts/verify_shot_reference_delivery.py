#!/usr/bin/env python3
"""Rehearse the exact shot increment and recover its complete isolated export.

Never opens a formal database for writing. Output must be a new task runtime
directory; successful evidence can be reused only for the same package/data.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
from types import SimpleNamespace
import wave

from generation_workspace import generation_root, contained
from generation_publication import apply_plan, backup, canonical, connect, publication_id

ROOT=Path(__file__).resolve().parents[1]


def require(value, message):
    if not value:raise ValueError(message)


def copy_tree(source, target):
    if sys.platform=='darwin':subprocess.run(['cp','-cR',str(source),str(target)],check=True)
    else:shutil.copytree(source,target)


def fingerprints(path):
    # Keep one physical row in memory. SQLite spills the deterministic sort to
    # disk; do not retain two complete databases plus their serialized copies.
    result={};db=connect(path)
    try:
        db.execute('PRAGMA cache_size=-4096');db.execute('PRAGMA temp_store=FILE')
        names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='generation_publications' ORDER BY name")]
        for name in names:
            quoted='"'+name.replace('"','""')+'"'
            columns=[r[1] for r in db.execute('PRAGMA table_info('+quoted+')')]
            order=','.join('"'+c.replace('"','""')+'"' for c in columns)
            digest=hashlib.sha256();count=0
            for row in db.execute('SELECT * FROM '+quoted+' ORDER BY '+order):
                digest.update(canonical(dict(row)).encode());digest.update(b'\n');count+=1
            result[name]={'rows':count,'sha256':digest.hexdigest()}
        return result
    finally:db.close()


def compare(a,b):
    left,right=fingerprints(a),fingerprints(b)
    require(left==right,'business tables differ: '+str([k for k in left.keys()|right.keys() if left.get(k)!=right.get(k)]))
    return left


def cgroup_peak():
    path=Path('/sys/fs/cgroup/memory.peak')
    return int(path.read_text()) if path.exists() else None


def cgroup_limit_mib():
    path=Path('/sys/fs/cgroup/memory.max')
    raw=path.read_text().strip() if path.exists() else ''
    return int(raw)//(1024**2) if raw.isdigit() else None


def prepare_recovery_evidence(instance,output):
    from review_desk import material_storage
    from review_desk.production_media import physical_file_hash,probe
    db=connect(instance/'.runtime/review.sqlite3')
    try:
        names=set()
        for row in db.execute("SELECT json_extract(payload,'$.components') FROM revisions WHERE json_extract(payload,'$.components') IS NOT NULL"):
            names.update(c['file'] for c in json.loads(row[0]) if c.get('duration_seconds') is not None)
        rows=[]
        for name in sorted(names):
            path=instance/'export/assets'/name;sha=physical_file_hash(path)
            require(sha==path.stem,'native probe original changed')
            rows.append({'file':name,'sha256':sha,'bytes':path.stat().st_size,'probe':probe(path)})
        version=subprocess.check_output(['ffprobe','-version'],text=True,timeout=10).splitlines()[0]
        (output/'native-media-probes.json').write_text(json.dumps({'format':'exact-native-probes-v1','ffprobe':version,'rows':rows},indent=2)+'\n')
        checks=json.loads((ROOT/'production/publications/songs-current-model-v2.json').read_text())['origin']['historical_pcm_precision_checks']
        originals={}
        for check in checks:
            path=instance/'export/assets'/check['file']
            require(physical_file_hash(path)==path.stem,'historical WAV original changed')
            with wave.open(str(path)) as stream:duration=stream.getnframes()/stream.getframerate()
            require(duration==check['pcm_duration']==check['range_end'] and 0<duration-check['recorded_duration']<.0000005,'PCM evidence differs')
            row=dict(db.execute('SELECT * FROM revisions WHERE id=?',(check['revision_id'],)).fetchone())
            row['payload']=material_storage.hydrate(SimpleNamespace(db=db),row['payload'])
            require(hashlib.sha256(canonical({'object_id':row['object_id'],'version':row['version'],'payload':json.loads(row['payload'])}).encode()).hexdigest()==row['id'],'historical CALL differs')
            originals[row['id']]=row
        (output/'historical-precision.json').write_text(json.dumps({'checks':checks,'originals':originals},ensure_ascii=False,indent=2)+'\n')
    finally:db.close()


def export_worker(instance, output):
    from review_desk.store import Store
    from review_desk.bundle import export
    store=Store(Path(instance)/'.runtime/review.sqlite3')
    try:manifest=export(store,Path(instance)/'export')
    finally:store.close()
    Path(output,'export-worker.json').write_text(json.dumps({'manifest':manifest,'peak_cgroup_bytes':cgroup_peak()},ensure_ascii=False,indent=2)+'\n')


def restore_worker(original, restored, output):
    from review_desk.store import Store
    from review_desk.bundle import restore
    from review_desk import production_media as media
    from recover_song_publication import precision_validation
    restored=Path(restored);store=Store(restored/'.runtime/review.sqlite3')
    evidence=json.loads(Path(output,'native-media-probes.json').read_text())
    probes={row['file']:row for row in evidence['rows']};probe=media.probe;used=set()
    def native_probe(path):
        item=probes.get(path.name)
        if item is None:return probe(path)
        require(media.physical_file_hash(path)==item['sha256']==path.stem and path.stat().st_size==item['bytes'],'native probe original differs')
        used.add(path.name)
        return item['probe']
    historical=json.loads(Path(output,'historical-precision.json').read_text())
    media.probe=native_probe
    try:
        with precision_validation(historical['checks'],historical['originals']) as validated:
            restore(store,restored/'export')
        require(validated=={c['revision_id'] for c in historical['checks']},'historical PCM compatibility scope incomplete')
        require(store.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','restored database integrity failed')
        require(not store.db.execute('PRAGMA foreign_key_check').fetchall(),'restored references failed')
    finally:media.probe=probe;store.close()
    recovery=compare(Path(original)/'.runtime/review.sqlite3',restored/'.runtime/review.sqlite3')
    Path(output,'recovery-worker.json').write_text(json.dumps({'tables':recovery,'peak_cgroup_bytes':cgroup_peak(),
        'resource_limit_mib':cgroup_limit_mib(),
        'native_probes_used':len(used),'native_ffprobe':evidence['ffprobe'],'historical_precision_revisions':sorted(validated),
        'historical_payloads_changed':False},ensure_ascii=False,indent=2)+'\n')


def isolated_recovery(instance,output,system,image,memory_mib):
    prepare_recovery_evidence(instance,output)
    temporary=output/'container-tmp';temporary.mkdir()
    worker_input=output/'worker-input';worker_input.mkdir()
    for directory in ('config','content','export'):
        if (instance/directory).exists():copy_tree(instance/directory,worker_input/directory)
    (worker_input/'.runtime').mkdir()
    backup(instance/'.runtime/review.sqlite3',worker_input/'.runtime/review.sqlite3')
    def run(stage,code):
        name='task-20261006-0003-'+output.name+'-'+stage
        command=['docker','run','--name',name,'--label','codex.task=task-20261006-0003',
            '--network','none','--memory',str(memory_mib)+'m','--memory-swap',str(memory_mib)+'m','--cpus','1','--pids-limit','32',
            '--read-only','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/app:/scripts',
            '--mount',f'type=bind,src={system.resolve()},dst=/app,readonly',
            '--mount',f'type=bind,src={ROOT / "scripts"},dst=/scripts,readonly',
            '--mount',f'type=bind,src={instance},dst=/original,readonly',
            '--mount',f'type=bind,src={worker_input},dst=/input',
            '--mount',f'type=bind,src={output},dst=/output',
            '--mount',f'type=bind,src={temporary},dst=/tmp',
            '--entrypoint','python',image,'-c',code]
        try:subprocess.run(command,check=True,timeout=1800)
        finally:
            subprocess.run(['docker','stop','--time','1',name],capture_output=True,timeout=5)
            state=subprocess.run(['docker','inspect','--format','{{json .State}}',name],capture_output=True,text=True,timeout=3)
            (output/(stage+'-container-state.json')).write_text(state.stdout or state.stderr)
    run('export','from verify_shot_reference_delivery import export_worker; export_worker("/input","/output")')
    exported=json.loads((output/'export-worker.json').read_text())
    # Native APFS clones avoid reading/writing all media again inside the VM.
    restored=output/'restored';restored.mkdir()
    for directory in ('config','content','export'):
        if (worker_input/directory).exists():copy_tree(worker_input/directory,restored/directory)
    print('Stage: independent restore preflight and transaction',flush=True)
    run('restore','from verify_shot_reference_delivery import restore_worker; restore_worker("/original","/output/restored","/output")')
    result=json.loads((output/'recovery-worker.json').read_text())
    result['manifest']=exported['manifest'];result['export_peak_cgroup_bytes']=exported['peak_cgroup_bytes']
    return result


def increment_worker(args):
    root=generation_root(ROOT);instance=contained(root,args.instance);output=contained(root,args.output)
    require(instance.is_relative_to(root/'.runtime') and output.is_relative_to(root/'.runtime'),'task runtime paths required')
    package=contained(root,args.package);plan=json.loads(package.read_text())
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p
    candidate=instance/'.runtime/review.sqlite3';baseline=instance/'.runtime/generation-base.sqlite3'
    rehearsal=output/'delta.sqlite3';backup(baseline,rehearsal)
    print('Stage: isolated increment and idempotency',flush=True)
    db=connect(rehearsal,readonly=False)
    try:first=apply_plan(db,plan)
    finally:db.close()
    delta=compare(candidate,rehearsal)
    db=connect(rehearsal,readonly=False)
    try:second=apply_plan(db,plan)
    finally:db.close()
    require(second['already_published'],'repeat did not reuse transaction receipt')
    compare(candidate,rehearsal)
    conflicts=[]
    print('Stage: head and number conflict rollback',flush=True)
    for case in ('changed_head','number_collision'):
        path=output/(case+'.sqlite3');backup(baseline,path)
        if case=='changed_head':
            store=Store(path)
            try:
                row=p.record(store,'shot-e01-007');payload={**row['payload'],'title':row['payload']['title']+' · 隔离并发夹具'}
                p.import_records(store,{'format':'production-import-v1','records':[{'object_id':row['object_id'],
                    'kind':row['kind'],'expected_version':row['version'],'payload':payload}]})
            finally:store.close()
        else:
            code=next(v['after'] for v in plan['changes']['business_codes'] if v['after']['prefix']=='SH')
            db=connect(path,readonly=False)
            try:
                db.execute('INSERT INTO business_codes VALUES (?,?,?)',('verification-number-reservation',code['prefix'],code['number']));db.commit()
            finally:db.close()
        before=fingerprints(path);db=connect(path,readonly=False)
        try:
            try:apply_plan(db,plan)
            except (ValueError,sqlite3.IntegrityError) as exc:conflicts.append({'case':case,'error':str(exc)})
            else:raise ValueError('conflicting increment was accepted: '+case)
        finally:db.close()
        require(before==fingerprints(path),'failed increment left partial writes: '+case)
    (output/'increment-worker.json').write_text(json.dumps({'publication_id':publication_id(plan),'delta_application':first,'delta_tables':delta,'repeat_application':second,'conflicts':conflicts},ensure_ascii=False,indent=2)+'\n')


def verify(args):
    root=generation_root(ROOT);instance=contained(root,args.instance);output=contained(root,args.output)
    require(instance.is_relative_to(root/'.runtime') and output.is_relative_to(root/'.runtime'),'task runtime paths required')
    require(not output.exists(),'new verification output required; preserve previous receipts')
    require(256<=args.restore_memory_mib<=1024,'restore limit must be between 256 and 1024 MiB')
    output.mkdir(parents=True);package=contained(root,args.package);candidate=instance/'.runtime/review.sqlite3'
    # Increment planning materializes the reviewed delta. End that process before
    # export/restore so its Python allocator and payload caches cannot overlap.
    command=[sys.executable,str(Path(__file__).resolve()),'--increment-worker',
        '--system',str(args.system.resolve()),'--instance',str(instance),
        '--package',str(package),'--output',str(output),'--restore-image',args.restore_image]
    subprocess.run(command,check=True,timeout=600)
    checked_increment=json.loads((output/'increment-worker.json').read_text())
    sys.path.insert(0,str(args.system.resolve()))
    print('Stage: export and independent restore',flush=True)
    recovery_origin=output
    if args.recovery_evidence:
        recovery_origin=contained(root,args.recovery_evidence)
        require(recovery_origin.is_relative_to(root/'.runtime'),'isolated recovery evidence required')
        worker=json.loads((recovery_origin/'recovery-worker.json').read_text())
        checked=compare(candidate,recovery_origin/'restored/.runtime/review.sqlite3')
        require(checked==worker['tables'],'recovery changed after successful verification')
        from review_desk.production_media import physical_file_hash
        manifest=json.loads((recovery_origin/'restored/export/manifest.json').read_text())
        for name,expected in manifest['files'].items():
            path=contained(root,recovery_origin/'restored/export'/name)
            require(physical_file_hash(path)==expected,'recovery original changed: '+name)
        worker['manifest']=manifest
    else:worker=isolated_recovery(instance,output,args.system,args.restore_image,args.restore_memory_mib)
    manifest,recovery=worker['manifest'],worker['tables'];restored=recovery_origin/'restored'
    result={'format':'shot-reference-delivery-verification-v1','recorded_at':datetime.now(timezone.utc).isoformat(),
        'package':str(package.relative_to(root)),'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
        'publication_id':checked_increment['publication_id'],'formal_writes':False,'media_generated':0,
        **{key:checked_increment[key] for key in ('delta_application','delta_tables','repeat_application','conflicts')},
        'conflict_rollback':'exact business rows unchanged','recovery_tables':recovery,
        'export_schema':manifest['schema_version'],'originals_verified':sum(k.startswith('assets/') for k in manifest['files']),
        'restore_resource_limit_mib':worker.get('resource_limit_mib'),'restore_peak_cgroup_bytes':worker.get('peak_cgroup_bytes'),
        'recovery':str(restored.relative_to(root)),'browser_acceptance':'not performed by this tool'}
    (output/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return {'tables':len(recovery),'originals':result['originals_verified'],'delta_and_restore':'passed',
        'conflicts_rejected':len(checked_increment['conflicts']),'repeat_application':'no duplicate writes','evidence':str((output/'verification.json').relative_to(root))}


def main():
    def terminate(_number,_frame):raise SystemExit(143)
    signal.signal(signal.SIGTERM,terminate)
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('system','instance','package','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--restore-image',required=True,help='local compatible Python image; restore runs with a hard cgroup limit')
    parser.add_argument('--recovery-evidence',type=Path,help='reuse a successful exact isolated recovery after complete table/file revalidation')
    parser.add_argument('--restore-memory-mib',type=int,default=768)
    parser.add_argument('--increment-worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.increment_worker:increment_worker(args)
    else:print(json.dumps(verify(args),ensure_ascii=False))


if __name__=='__main__':main()
