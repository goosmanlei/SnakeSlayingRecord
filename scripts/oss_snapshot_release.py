#!/usr/bin/env python3
"""Explicit full-state VPS publication for an already OSS-backed experience.

Code-only upgrades keep using oss_runtime_release.py. This publisher stages and
validates a separate empty instance, then retains the old directory for rollback
until the new publication can accept writes. Credentials and usage never move.
"""
import argparse
from contextlib import ExitStack
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tarfile
import time

import oss_runtime_release as code
import vps_experience_remote as vps

TASK = 'task-20261020-0004'
FORMAT = 'oss-experience-snapshot-v1'
HELPERS = ('oss_snapshot_release.py', 'oss_runtime_release.py', 'vps_experience_remote.py')


def run(args, **kwargs):
    # Never expose Docker's environment/credential-bearing arguments on failure.
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError('release command failed: '+str(args[0])+' '+str(args[1])+f' (exit {result.returncode})')
    return result.stdout.strip()


def identity(value):
    if not re.fullmatch(r'lijizhanshe-[A-Za-z0-9_-]{1,80}', value):
        raise ValueError('invalid experience publication identity')
    return value


def save(path, value):
    code.save(path, value)


def checked_bundle(root):
    root = code.safe(root)
    manifest = json.loads((root/'manifest.json').read_text())
    if manifest.get('format') != FORMAT or manifest.get('task') != TASK:
        raise ValueError('wrong snapshot release ownership')
    identity(manifest['publication_id'])
    expected = set(manifest['files']) | {'manifest.json'}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('snapshot bundle has missing or extra files')
    for name, spec in manifest['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('unsafe snapshot bundle member')
        path = code.safe(root/name)
        if not path.is_file() or path.stat().st_size != spec['bytes'] or code.sha(path) != spec['sha256']:
            raise ValueError('snapshot checksum differs: '+name)
    if json.loads((root/'source/config/instance.json').read_text())['review_desk_commit'] != manifest['commits']['desk']:
        raise ValueError('snapshot system pin differs')
    return manifest


# Run inside Docker, sharing the live application's actual mount namespace.
# Only HTTP/worker writes pause; the application stays up and serves reads.
FREEZE = r'''
import fcntl,json,sqlite3
from contextlib import ExitStack
from pathlib import Path
from review_desk.resource_bundle import copy_instance_metadata,database_identity,closure
from review_desk import resources as r
from review_desk.store import Store
root=Path('/instance');out=Path('/out/source')
out.mkdir();(out/'.runtime').mkdir()
with ExitStack() as locks:
    for name in ('publication.lock','http-write.lock'):
        stream=locks.enter_context((root/'.runtime'/name).open('a'))
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
    queue=root/'.runtime/edit-render.sqlite3'
    if queue.exists():
        db=sqlite3.connect(queue.as_uri()+'?mode=ro',uri=True)
        try:
            assert not db.execute("SELECT 1 FROM jobs WHERE status IN ('queued','running') LIMIT 1").fetchone(),'render work pending'
        finally:db.close()
    source=sqlite3.connect('file:/instance/.runtime/review.sqlite3?mode=ro',uri=True)
    target=sqlite3.connect(out/'.runtime/review.sqlite3')
    try:source.backup(target,pages=256)
    finally:source.close();target.close()
    copy_instance_metadata(root,out)
    r.freeze_catalog(root,out/'config/resource-catalog.json')
    frozen=database_identity(out/'.runtime/review.sqlite3')
    assert frozen==database_identity(root/'.runtime/review.sqlite3'),'source changed in snapshot window'
    store=Store.open_readonly(out/'.runtime/review.sqlite3')
    try:
        assert not store.db.execute("SELECT 1 FROM revisions WHERE json_extract(payload,'$.private')=1 LIMIT 1").fetchone(),'private creative records cannot be published'
        closure(store,out)
    finally:store.close()
    (out/'snapshot.json').write_text(json.dumps({'database':frozen,'catalog_sha256':r.hash_file(out/'config/resource-catalog.json')}))
print(json.dumps({'frozen':True,'tables':len(frozen),'rows':sum(t['rows'] for t in frozen.values())}))
'''


def prepare(args):
    story, desk, out = map(code.safe, (args.story, args.desk, args.output))
    identity(args.publication)
    if out.exists():
        raise ValueError('snapshot output exists; inspect the same publication before retrying')
    if run(['git', '-C', story, 'status', '--porcelain']) or run(['git', '-C', desk, 'status', '--porcelain']):
        raise ValueError('commit the candidate and keep the read-only system source clean')
    before = code.inspect(args.container)
    code.owned_runtime(before, 'local', args.formal.resolve())
    mounts = {m['Destination']:m for m in before['Mounts']}
    if mounts['/instance']['Source'] != str(args.formal.resolve()) or not before['State']['Running']:
        raise ValueError('wrong local formal source')
    code.verify_mount_sources(before)
    image = code.inspect(before['Image'], True)
    out.mkdir(parents=True, mode=0o700)
    code.prepare(argparse.Namespace(story=story, desk=desk, output=out/'code', image=image['Id']))
    for helper in HELPERS:
        data = subprocess.check_output(['git', '-C', story, 'show', 'HEAD:scripts/'+helper])
        if data != (story/'scripts'/helper).read_bytes():
            raise ValueError('snapshot helper differs from committed source')
        (out/helper).write_bytes(data)
    print(run(['docker', 'run', '--rm', '--pull', 'never', '--name', 'snapshot-freeze-'+args.publication,
        '--label', 'org.leiguoguo.task='+TASK, '--network', 'none', '--memory', '512m', '--pids-limit', '32',
        '--volumes-from', before['Id'], '--mount', 'type=bind,source='+str(out)+',target=/out',
        '--entrypoint', 'python', image['Id'], '-c', FREEZE]), flush=True)
    snapshot = json.loads((out/'source/snapshot.json').read_text())
    candidate = json.loads((out/'code/manifest.json').read_text())
    manifest = {'format':FORMAT, 'task':TASK, 'publication_id':args.publication,
        'commits':candidate['commits'], 'image_identity':candidate['image_identity'],
        'database':snapshot['database'], 'source_container':before['Id'], 'files':{}}
    for path in sorted(out.rglob('*')):
        if path.is_symlink():
            raise ValueError('snapshot bundle cannot contain symlinks')
        if path.is_file():
            manifest['files'][path.relative_to(out).as_posix()] = {'bytes':path.stat().st_size, 'sha256':code.sha(path)}
    save(out/'manifest.json', manifest)
    checked_bundle(out)
    archive = out.with_suffix('.tar.gz')
    if archive.exists():
        raise ValueError('snapshot archive already exists')
    with tarfile.open(archive, 'w:gz', compresslevel=1) as tar:
        for name in [*manifest['files'], 'manifest.json']:
            tar.add(out/name, arcname=name, recursive=False)
    result = {'prepared':True, 'publication_id':args.publication, 'archive':str(archive),
        'archive_sha256':code.sha(archive), 'bytes':archive.stat().st_size,
        'manifest_sha256':code.sha(out/'manifest.json'), 'commits':manifest['commits']}
    save(out.with_suffix('.prepare.json'), result)
    print(json.dumps(result), flush=True)


def release_path(publication):
    return code.safe(vps.CONTROL/'snapshot-releases'/identity(publication))


def receipt(release):
    value = json.loads((release/'receipt.json').read_text())
    if value['task'] != TASK or release != release_path(value['publication_id']):
        raise ValueError('wrong release receipt')
    return value


def phase(release, value, name, **fields):
    value.update(fields, phase=name)
    save(release/'receipt.json', value)


def stage(args):
    publication = identity(args.publication)
    archive = code.safe(args.archive)
    if archive != vps.CONTROL/'incoming'/publication/'bundle.tar.gz':
        raise ValueError('only this publication completed incoming archive can be staged')
    if not archive.is_file() or code.sha(archive) != args.sha256:
        raise ValueError('uploaded snapshot checksum differs; old service untouched')
    release = release_path(publication)
    if release.exists():
        raise ValueError('release exists; inspect its receipt instead of staging twice')
    vps.preflight()
    with tarfile.open(archive, 'r:gz') as tar:
        members = []
        total = 0
        for member in tar:
            if len(members) >= 100 or not member.isfile() or Path(member.name).is_absolute() or '..' in Path(member.name).parts or member.size < 0:
                raise ValueError('unsafe snapshot archive')
            if member.name in {m.name for m in members}:
                raise ValueError('duplicate snapshot archive member')
            members.append(member); total += member.size
            if total > 4*1024**3:
                raise ValueError('snapshot metadata/database exceeds 4 GiB bound')
        # New cache plus source, restored DB and retained predecessor coexist.
        if shutil.disk_usage(vps.CONTROL).free < total*3 + 16*1024**3 + 5*1024**3:
            raise ValueError('insufficient staging and recovery disk reserve')
        release.mkdir(parents=True, mode=0o700)
        target = release/'bundle'; target.mkdir()
        for member in members:
            path = target/member.name; path.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source, path.open('xb') as output:
                shutil.copyfileobj(source, output, 1024*1024)
    manifest = checked_bundle(target)
    if manifest['publication_id'] != publication:
        raise ValueError('archive publication differs')
    value = {'format':FORMAT, 'task':TASK, 'publication_id':publication, 'phase':'staged',
        'archive_sha256':args.sha256, 'manifest_sha256':code.sha(target/'manifest.json'),
        'commits':manifest['commits']}
    save(release/'receipt.json', value)
    print(json.dumps({'staged':True, 'release':str(release)}))


RESTORE = r'''
import json,sqlite3,time
from pathlib import Path
from review_desk import resources as r
from review_desk.store import Store
from review_desk.resource_bundle import closure,verify_catalog,database_identity,_install_snapshot
from review_desk.production_current_bundle import validate
from review_desk.production_media import physical_hash_scope
root=Path('/instance');snapshot=Path('/source/.runtime/review.sqlite3')
expected=json.loads(Path('/manifest.json').read_text())['database']
store=Store(root/'.runtime/review.sqlite3')
try:
    # The exact same empty-target installer/semantic validators as Schema 16.
    initial=database_identity(store.db_path)
    if initial==expected:
        assert (root/'.runtime/validated-snapshot.json').is_file(),'completed restore lacks validation receipt'
        print(json.dumps({'restored':True,'resumed':True,'tables':len(expected),'rows':sum(v['rows'] for v in expected.values())}),flush=True)
        raise SystemExit(0)
    assert not store.objects() and not store.sources() and not store.comments(),'restore requires an empty instance'
    assert not any(v['version'] for v in store.configurations().values()),'restore requires empty configurations'
    catalog=json.loads((root/'config/resource-catalog.json').read_text())
    print(json.dumps({'phase':'verifying-resources','objects':sum(1+len(x.get('variants',{})) for x in catalog['entries'].values())}),flush=True)
    verify_catalog(root,catalog)
    assert database_identity(snapshot)==expected,'snapshot business table identity differs'
    check=Store.open_readonly(snapshot);check.db_path=root/'.runtime/review.sqlite3'
    try:
        assert check.db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
        closure(check,root)
        with physical_hash_scope():validate(check)
        r.atomic_json(root/'.runtime/validated-snapshot.json',{'database':expected})
        _install_snapshot(store,snapshot,initial)
    finally:check.close()
    assert database_identity(store.db_path)==expected,'restored business state differs'
    print(json.dumps({'restored':True,'tables':len(expected),'rows':sum(v['rows'] for v in expected.values())}),flush=True)
finally:store.close()
'''


def restore(args):
    release = code.safe(args.release); value = receipt(release)
    if value['phase'] not in ('staged','restoring','restore-failed'):
        raise ValueError('restore only a staged or interrupted restoration')
    container_name='snapshot-restore-'+value['publication_id']
    if code.optional_container(container_name):
        raise ValueError('restoration container still exists; inspect its progress before retrying')
    bundle = release/'bundle'; manifest = checked_bundle(bundle)
    old = code.inspect(vps.CONTAINER); code.owned_runtime(old, 'vps', vps.TARGET)
    image = code.inspect(old['Image'], True)
    if code.image_identity(image) != manifest['image_identity']:
        raise ValueError('loaded VPS image differs from the frozen verified system image')
    credentials = next(m['Source'] for m in old['Mounts'] if m['Destination']=='/run/project-oss.json')
    if Path(credentials).stat().st_mode & 0o077:
        raise ValueError('runtime credentials must remain private')
    candidate = release/'candidate'
    if candidate.exists():
        if json.loads((candidate/'.runtime/snapshot-owner.json').read_text()) != {'task':TASK,'manifest':value['manifest_sha256']}:
            raise ValueError('restoration candidate ownership differs')
    else:
        candidate.mkdir(mode=0o700)
        for folder in ('config','content'):
            shutil.copytree(bundle/'source'/folder, candidate/folder)
        (candidate/'.runtime').mkdir()
        save(candidate/'.runtime/snapshot-owner.json',{'task':TASK,'manifest':value['manifest_sha256']})
    phase(release, value, 'restoring', image_id=old['Image'], restore_container=container_name)
    command = ['docker', 'run', '--rm', '--pull', 'never', '--name', value['restore_container'],
        '--label', 'org.leiguoguo.task='+TASK, '--network', 'bridge', '--cpus', '1', '--memory', '1g',
        '--memory-swap', '1536m', '--pids-limit', '64', '--log-opt', 'max-size=10m', '--log-opt', 'max-file=3',
        '--env', 'REVIEW_OSS_CREDENTIALS_FILE=/run/project-oss.json', '--env', 'REVIEW_RESOURCE_INSTANCE=vps',
        '--mount', 'type=bind,source='+str(credentials)+',target=/run/project-oss.json,readonly',
        '--mount', 'type=bind,source='+str(candidate)+',target=/instance',
        '--mount', 'type=bind,source='+str(bundle/'source')+',target=/source,readonly',
        '--mount', 'type=bind,source='+str(bundle/'manifest.json')+',target=/manifest.json,readonly',
        '--entrypoint', 'python', old['Image'], '-u', '-c', RESTORE]
    with (release/'restore.log').open('a') as output:
        result_code=subprocess.run(command,stdout=output,stderr=subprocess.STDOUT).returncode
    if result_code:
        phase(release,value,'restore-failed',restore_exit=result_code)
        raise RuntimeError('isolated restoration failed; inspect the protected restore.log before resuming')
    result=(release/'restore.log').read_text()
    phase(release, value, 'prepared', restore_result=json.loads(result.splitlines()[-1]))
    print(json.dumps({'prepared':True, 'release':str(release), 'result':value['restore_result']}))


def database(path):
    # Match the existing publisher's complete, disk-backed business identity.
    return vps.database(path)


def write_window(path):
    # VPS Docker shares the host Linux flock namespace. Existing root-created
    # 0644 locks are readable by the maintainer; flock does not require a
    # writable descriptor on this local filesystem. Do not chmod shared locks.
    path=code.safe(path)
    return os.fdopen(os.open(path,os.O_RDONLY|os.O_CREAT|os.O_NOFOLLOW,0o600),'rb')


def probe(publication):
    target = vps.runtime_target()
    program = "import json,urllib.request;u='http://"+target['probe_host']+":8765/lijizhanshe/api/instance';print(json.dumps(json.load(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(u,timeout=10))))"
    deadline = time.monotonic()+90
    while True:
        try:
            result = json.loads(run(['docker', 'exec', vps.CONTAINER, 'python', '-c', program]))
            if result['deployment']['publication_id'] != publication:
                raise ValueError('live publication identity differs')
            return
        except RuntimeError:
            if time.monotonic() >= deadline:raise
            time.sleep(1)


def clone_runtime(old, value):
    host = old['HostConfig']
    args = ['docker', 'create', '--pull', 'never', '--name', vps.CONTAINER,
        '--restart', host['RestartPolicy']['Name'], '--network', host['NetworkMode'],
        '--cpus', str(host['NanoCpus']/1e9), '--memory', str(host['Memory']),
        '--memory-swap', str(host['MemorySwap']), '--pids-limit', str(host['PidsLimit'])]
    for key, item in host['LogConfig']['Config'].items():args += ['--log-opt', key+'='+item]
    labels = {**old['Config']['Labels'], 'org.leiguoguo.task':TASK,
        'org.leiguoguo.snapshot-release':value['manifest_sha256'],
        'org.opencontainers.image.revision':value['commits']['desk']}
    labels.pop('org.leiguoguo.oss-release', None)
    for key, item in labels.items():args += ['--label', key+'='+item]
    environment = dict(item.split('=',1) for item in old['Config']['Env'])
    environment['REVIEW_PUBLICATION_ID'] = value['publication_id']
    for key in environment:args += ['--env', key]
    for mount in old['Mounts']:
        if mount['Destination'].startswith('/instance/'):
            continue  # The new full snapshot owns all of its application metadata.
        args += ['--mount', 'type=bind,source='+mount['Source']+',target='+mount['Destination']+(',readonly' if not mount['RW'] else '')]
    args += [value['image_id'], *old['Config']['Cmd']]
    run(args, env={**os.environ, **environment})


def rollback(release, value):
    if value['phase'] in ('opening','open','complete'):
        raise ValueError('publication may accept writes; use resume or a compatible forward release')
    old = code.inspect(value['before']['id'])
    current = code.optional_container(vps.CONTAINER)
    if current and current['Id'] != old['Id']:
        if current['Config'].get('Labels',{}).get('org.leiguoguo.snapshot-release') != value['manifest_sha256']:
            raise ValueError('another runtime owns the active name')
        run(['docker', 'stop', '--time', '30', current['Id']]); run(['docker','rm',current['Id']])
    previous = release/'previous-instance'
    if previous.exists():
        if vps.TARGET.exists():
            # Keep the failed new state for diagnosis; never merge directories.
            if (release/'failed-instance').exists():raise ValueError('failed instance already retained')
            vps.TARGET.rename(release/'failed-instance')
        previous.rename(vps.TARGET)
    if code.inspect(old['Id'])['Name'] != '/'+vps.CONTAINER:
        run(['docker', 'rename', old['Id'], vps.CONTAINER])
    if not code.inspect(old['Id'])['State']['Running']:run(['docker','start',old['Id']])
    for name in ('state.json','storage-runtime.json'):
        save(vps.CONTROL/name, json.loads((release/'before-control'/name).read_text()))
    vps.configure(False)
    phase(release, value, 'rolled-back')


def apply(args):
    if not args.replace_experience_data:
        raise ValueError('full replacement requires explicit --replace-experience-data')
    release = code.safe(args.release); value = receipt(release)
    if value['phase'] != 'prepared':raise ValueError('only a fully restored release can replace the experience')
    checked_bundle(release/'bundle'); vps.preflight(); vps.credential_check()
    old = code.inspect(vps.CONTAINER); code.owned_runtime(old,'vps',vps.TARGET)
    code.verify_mount_sources(old); vps.check_runtime_target(vps.runtime_target())
    host = old['HostConfig']; mounts = {m['Destination']:m for m in old['Mounts']}
    if (mounts['/instance']['Source'] != str(vps.TARGET) or not old['State']['Running'] or
            host['NetworkMode'] != vps.runtime_target()['network'] or host.get('Privileged') or host.get('PortBindings') or
            host.get('Devices') or host.get('CapAdd') or any(m['Type']!='bind' for m in old['Mounts'])):
        raise ValueError('live instance boundary differs')
    if (host['Memory'],host['MemorySwap'],host['NanoCpus'],host['PidsLimit']) != (1024**3,1536*1024**2,10**9,64):
        raise ValueError('live VPS runtime limits differ')
    if old['Image'] != value['image_id']:raise ValueError('live image changed since restoration')
    if vps.state().get('phase') != 'complete':raise ValueError('another publication is unfinished')
    candidate = release/'candidate'
    if not candidate.is_dir() or candidate.stat().st_dev != vps.TARGET.stat().st_dev:
        raise ValueError('candidate and target need an atomic same-filesystem switch')
    usage = vps.CONTROL/'usage/attempts.json'
    before_control = release/'before-control'
    if before_control.exists():
        if not value.get('retry_count'):raise ValueError('existing control backup requires explicit retry')
        for name in ('state.json','storage-runtime.json'):
            if json.loads((vps.CONTROL/name).read_text())!=json.loads((before_control/name).read_text()):
                raise ValueError('previous control identity changed; retain recovery state')
    else:
        before_control.mkdir()
        for name in ('state.json','storage-runtime.json'):shutil.copyfile(vps.CONTROL/name,before_control/name)
    value.update(before=code.current_identity(old), previous_name=vps.CONTAINER+'-before-'+value['publication_id'], usage_sha256=code.sha(usage))
    phase(release,value,'switching')
    try:
        with ExitStack() as locks:
            for path in (vps.TARGET/'.runtime/publication.lock',vps.TARGET/'.runtime/http-write.lock',candidate/'.runtime/http-write.lock'):
                stream=locks.enter_context(write_window(path));fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            vps.configure(True)
            run(['docker','stop','--time','30',old['Id']])
            queue=vps.TARGET/'.runtime/edit-render.sqlite3'
            if queue.exists():
                db=sqlite3.connect(queue.as_uri()+'?mode=ro',uri=True)
                try:
                    if db.execute("SELECT 1 FROM jobs WHERE status IN ('queued','running') LIMIT 1").fetchone():raise ValueError('render work is pending')
                finally:db.close()
            value['previous_database']=database(vps.TARGET/'.runtime/review.sqlite3')
            value['new_database']=database(candidate/'.runtime/review.sqlite3')
            phase(release,value,'stopped')
            run(['docker','rename',old['Id'],value['previous_name']])
            vps.TARGET.rename(release/'previous-instance')
            candidate.rename(vps.TARGET)
            phase(release,value,'swapped')
            clone_runtime(old,value); run(['docker','start',vps.CONTAINER]); probe(value['publication_id'])
            if database(vps.TARGET/'.runtime/review.sqlite3') != value['new_database']:
                raise ValueError('restored business state changed before opening')
            if code.sha(usage) != value['usage_sha256']:raise ValueError('usage changed during full replacement')
            new=code.inspect(vps.CONTAINER); value['after']=code.current_identity(new)
            phase(release,value,'verified')
            # Opening is durable BEFORE proxy reload or releasing the new write lock.
            phase(release,value,'opening')
            finalize_controls(release,value)
            vps.configure(False)
        phase(release,value,'open')
    except BaseException:
        if value['phase'] not in ('opening','open','complete'):rollback(release,value)
        raise
    print(json.dumps({'opened':True,'release':str(release),'container_id':value['after']['id'],'publication_id':value['publication_id']}))


def retry(args):
    if not args.replace_experience_data or not re.fullmatch(r'[0-9a-f]{40}',args.controller_commit):
        raise ValueError('retry needs the delivered controller commit and explicit data replacement')
    release=code.safe(args.release);value=receipt(release)
    if value['phase']!='rolled-back' or not (release/'candidate').is_dir() or (release/'previous-instance').exists() or (release/'failed-instance').exists():
        raise ValueError('retry only an unopened, restored candidate whose original instance remains active')
    current=code.inspect(vps.CONTAINER)
    if current['Id']!=value['before']['id'] or not current['State']['Running']:
        raise ValueError('the original runtime changed; inspect before recovering')
    checked_bundle(release/'bundle')
    attempt=value.get('retry_count',0)+1
    audit=release/f'attempt-{attempt}.json'
    if audit.exists():
        if json.loads(audit.read_text())!=value:raise ValueError('attempt audit differs')
    else:save(audit,value)
    controller=release/('controller-'+args.controller_commit[:12]);controller.mkdir(exist_ok=True)
    hashes={}
    for name in HELPERS:
        data=(Path(__file__).parent/name).read_bytes();target=controller/name
        if target.exists() and target.read_bytes()!=data:raise ValueError('delivered controller bytes changed')
        if not target.exists():target.write_bytes(data)
        hashes[name]=code.sha(target)
    value['controller']={'commit':args.controller_commit,'directory':str(controller),'files':hashes}
    phase(release,value,'prepared',retry_count=attempt)
    apply(args)


def finalize_controls(release, value):
    current=code.inspect(vps.CONTAINER)
    if (current['Image']!=value['image_id'] or not current['State']['Running'] or
            current['Config'].get('Labels',{}).get('org.leiguoguo.snapshot-release')!=value['manifest_sha256']):
        raise ValueError('active full publication identity differs')
    marker={'task':TASK,'release':str(release),'manifest_sha256':value['manifest_sha256']}
    if value.get('controller'):marker['controller']=value['controller']
    state={'phase':'complete','publication_id':value['publication_id'],'story_commit':value['commits']['story'],
        'desk_commit':value['commits']['desk'],'image_id':current['Image'],'container_id':current['Id'],
        'storage_upgrade':marker,'snapshot_release':marker}
    save(vps.CONTROL/'state.json',state)
    save(vps.CONTROL/'storage-runtime.json',{'release':str(release),'manifest_sha256':value['manifest_sha256'],
        'container_id':current['Id'],'image_id':current['Image'],'commits':value['commits'],'publication_id':value['publication_id']})


def resume(args):
    release=code.safe(args.release);value=receipt(release)
    if value['phase'] not in ('opening','open'):raise ValueError('resume only a possibly opened full publication')
    probe(value['publication_id']);finalize_controls(release,value);vps.configure(False)
    phase(release,value,'open')
    print(json.dumps({'opened':True,'release':str(release)}))


def finalize(args):
    release=code.safe(args.release);value=receipt(release)
    if value['phase']!='open':raise ValueError('only finalize a verified open publication')
    probe(value['publication_id']);finalize_controls(release,value)
    phase(release,value,'complete')
    print(json.dumps({'complete':True,'release':str(release),'publication_id':value['publication_id']}))


def main():
    global TASK
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', default=TASK, help='exact managed task owning this release')
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('prepare')
    for name in ('story','desk','formal','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--container',default='snakeslayingrecord-app-1');p.add_argument('--publication',required=True)
    p=commands.add_parser('stage');p.add_argument('--publication',required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--sha256',required=True)
    for name in ('restore','apply','retry','resume','finalize','rollback','status'):
        p=commands.add_parser(name);p.add_argument('--release',type=Path,required=True)
        if name in ('apply','retry'):p.add_argument('--replace-experience-data',action='store_true')
        if name=='retry':p.add_argument('--controller-commit',required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'task-[0-9]{8}-[0-9]{4}', args.task):
        parser.error('invalid managed task identity')
    TASK=args.task
    code.TASK=TASK
    if args.command=='prepare':prepare(args);return
    vps.CONTROL.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (vps.CONTROL/'publish.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.command=='rollback':rollback(code.safe(args.release),receipt(code.safe(args.release)))
        elif args.command=='status':print(json.dumps(receipt(code.safe(args.release)),ensure_ascii=False,indent=2))
        else:globals()[args.command](args)


if __name__=='__main__':main()
