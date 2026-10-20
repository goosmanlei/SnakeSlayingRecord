#!/usr/bin/env python3
"""Install a committed OSS runtime without restoring or replacing live databases.

prepare produces a small immutable code/configuration manifest. apply retains
one stopped predecessor for runtime rollback, reuses the same instance and
usage mounts, and holds the application's HTTP write lock during verification.
Credentials are mounted from a protected external file and never packaged.
"""
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import shlex
import subprocess
import time

TASK='task-20261019-0004'
FILES=('config/instance.json','config/resource-storage.json','config/resource-catalog.json')
HELPERS=('oss_runtime_release.py','vps_experience_remote.py')


def run(args, *, env=None):
    value=subprocess.run([str(x) for x in args],capture_output=True,text=True,env=env,timeout=180)
    if value.returncode:
        raise RuntimeError('release command failed: '+str(args[0])+' '+str(args[1])+' (exit '+str(value.returncode)+')')
    return value.stdout.strip()


def inspect(name, image=False):
    return json.loads(run(['docker',*(['image'] if image else []),'inspect',name]))[0]


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):value.update(block)
    return value.hexdigest()


def image_identity(image):
    # Docker Desktop's index ID and Linux's loaded config ID can differ. The
    # config plus ordered content-addressed filesystem layers are portable.
    value={k:image[k] for k in ('Architecture','Os','Config','RootFS')}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def safe(path):
    path=Path(path).absolute()
    if '..' in path.parts:raise ValueError('parent traversal is not a release path')
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('release paths cannot contain symlinks')
    return path.resolve()


def prepare(args):
    story,desk,out=map(safe,(args.story,args.desk,args.output))
    if out.exists():raise ValueError('release output exists; inspect its receipt before resuming')
    commits={name:run(['git','-C',root,'rev-parse','HEAD']) for name,root in (('story',story),('desk',desk))}
    from check_resource_git import check as check_resource_git
    check_resource_git(story,revision=commits['story'])
    if json.loads((story/'config/instance.json').read_text())['review_desk_commit']!=commits['desk']:
        raise ValueError('story must pin the exact system candidate')
    image=inspect(args.image,True)
    if image['Config'].get('Labels',{}).get('org.opencontainers.image.revision')!=commits['desk']:
        raise ValueError('image revision does not match the candidate')
    expected={}
    paths=run(['git','-C',desk,'ls-tree','-r','--name-only',commits['desk'],'--','review_desk']).splitlines()
    for name in paths:
        data=subprocess.check_output(['git','-C',str(desk),'show',commits['desk']+':'+name])
        expected[name]=hashlib.sha256(data).hexdigest()
    actual=json.loads(run(['docker','run','--rm','--pull','never','--network','none','--entrypoint','python',image['Id'],'-c',
        "import hashlib,json,pathlib;print(json.dumps({p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('review_desk').rglob('*') if p.is_file() and '__pycache__' not in p.parts}))"]))
    if actual!=expected:raise ValueError('image source differs from the committed system')
    out.mkdir(parents=True);hashes={}
    for name in FILES:
        data=subprocess.check_output(['git','-C',str(story),'show',commits['story']+':'+name])
        if data!=(story/name).read_bytes():raise ValueError('configuration differs from committed candidate')
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);hashes[name]=sha(target)
    if json.loads((out/'config/resource-storage.json').read_text()).get('test_namespace'):
        raise ValueError('test namespaces cannot be deployed to a formal instance')
    for name in HELPERS:
        helper=subprocess.check_output(['git','-C',str(story),'show',commits['story']+':scripts/'+name])
        if helper!=(Path(__file__).parent/name).read_bytes():raise ValueError('release helper differs from committed candidate')
        (out/name).write_bytes(helper);hashes[name]=sha(out/name)
    manifest={'format':'oss-runtime-release-v1','task':TASK,'commits':commits,'image':args.image,'image_id':image['Id'],
              'image_identity':image_identity(image),'image_architecture':image['Architecture'],'files':hashes,'source_hashes':expected}
    save(out/'manifest.json',manifest)
    print(json.dumps({'prepared':True,'manifest_sha256':sha(out/'manifest.json'),'commits':commits}))


def verify_bundle(bundle):
    manifest=json.loads((bundle/'manifest.json').read_text())
    if manifest['format']!='oss-runtime-release-v1' or manifest['task']!=TASK:raise ValueError('wrong release ownership')
    if set(manifest['files'])!=set(FILES)|set(HELPERS):raise ValueError('release file manifest is incomplete')
    for name,digest in manifest['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha(safe(bundle/name))!=digest:
            raise ValueError('release bundle changed')
    return manifest


def database(image, instance):
    return json.loads(run(['docker','run','--rm','--pull','never','--network','none','--memory','256m',
        '--mount','type=bind,source='+str(instance)+',target=/instance,readonly','--entrypoint','python',image,'-c',
        "import json;from review_desk.resource_bundle import database_identity;print(json.dumps(database_identity('/instance/.runtime/review.sqlite3')))"]))


def current_identity(container):
    # Deliberately omit environment values and credentials from every receipt.
    return {'id':container['Id'],'image':container['Image'],'name':container['Name'],
            'mounts':container['Mounts'],'command':container['Config']['Cmd'],
            'environment_names':sorted(item.split('=',1)[0] for item in container['Config']['Env']),
            'network':container['HostConfig']['NetworkMode']}


def optional_container(name):
    result=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=30)
    if result.returncode:
        error=result.stderr.lower()
        if 'no such object' in error or 'no such container' in error:return None
        raise RuntimeError('cannot determine container state; retain recovery window')
    return json.loads(result.stdout)[0]


def owned_runtime(container,kind,instance):
    labels=container['Config'].get('Labels') or {}
    if kind=='local':
        expected={'com.docker.compose.project':'snakeslayingrecord','com.docker.compose.service':'app',
                  'com.docker.compose.project.working_dir':str(instance)}
    else:expected={'org.leiguoguo.instance':'lijizhanshe'}
    if any(labels.get(k)!=v for k,v in expected.items()):raise ValueError('runtime ownership differs')


def verify_mount_sources(container):
    """Reject vanished/replaced host binds while the old runtime is still live."""
    mounts=container['Mounts']
    destinations=[mount['Destination'] for mount in mounts]
    actual=json.loads(run(['docker','exec',container['Id'],'python','-c',
        "import json,os,stat,sys;print(json.dumps({p:stat.S_IFMT(os.stat(p).st_mode) for p in sys.argv[1:]}))",
        *destinations]))
    for mount in mounts:
        source=Path(mount['Source'])
        try:kind=stat.S_IFMT(source.stat().st_mode)
        except FileNotFoundError:kind=None
        if kind not in (stat.S_IFREG,stat.S_IFDIR) or kind!=actual.get(mount['Destination']):
            raise ValueError('live bind source is missing or changed type: '+mount['Destination'])


def rollback_runtime(release,receipt):
    """Reconcile Docker reality, including stop/create that succeeded but timed out."""
    name=receipt['before']['name'].lstrip('/');old_id=receipt['before']['id']
    old=inspect(old_id);owned_runtime(old,receipt['environment'],Path(receipt['instance']))
    active=optional_container(name)
    if active and active['Id']!=old_id:
        labels=active['Config'].get('Labels') or {}
        if (labels.get('org.leiguoguo.task')!=TASK or active['Image']!=receipt['image_id'] or
                labels.get('org.opencontainers.image.revision')!=receipt['commits']['desk'] or
                labels.get('org.leiguoguo.oss-release')!=receipt['manifest_sha256'] or
                not any(m['Destination']=='/instance' and m['Source']==receipt['instance'] for m in active['Mounts'])):
            raise ValueError('another runtime owns the target name; retained recovery window')
        run(['docker','stop','--time','30',active['Id']]);run(['docker','rm',active['Id']])
    if inspect(old_id)['Name']!='/'+name:run(['docker','rename',old_id,name])
    if not inspect(old_id)['State']['Running']:run(['docker','start',old_id])
    if not inspect(old_id)['State']['Running']:raise ValueError('previous runtime did not recover')
    if receipt['environment']=='local':run(['docker','exec','snakeslayingrecord-nginx-1','nginx','-s','reload'])
    keeper=optional_container(receipt['write_window'])
    if keeper:
        if (keeper['Config'].get('Labels') or {}).get('org.leiguoguo.task')!=TASK:raise ValueError('write window owner differs')
        run(['docker','stop','--time','5',keeper['Id']]);run(['docker','rm',keeper['Id']])
    receipt['phase']='runtime-rolled-back';save(release/'receipt.json',receipt)


def rollback(args):
    release=safe(args.release);receipt=json.loads((release/'receipt.json').read_text())
    if receipt['task']!=TASK or receipt['phase'] in ('opening','open','runtime-rolled-back'):
        raise ValueError('rollback is only for an interrupted cutover; open services require a compatible forward release')
    instance=safe(receipt['instance']);control=instance/'.runtime' if receipt['environment']=='local' else safe(Path.home()/'lijizhanshe')
    with ExitStack() as locks:
        for path in set((control/('publication.lock' if receipt['environment']=='local' else 'publish.lock'),instance/'.runtime/publication.lock')):
            lock=locks.enter_context(path.open('a'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        rollback_runtime(release,receipt)
    print(json.dumps({'recovered':True,'receipt':str(release/'receipt.json')}))


def active_runtime(receipt):
    current=inspect(receipt['before']['name'].lstrip('/'))
    owned_runtime(current,receipt['environment'],Path(receipt['instance']))
    if (current['Id']!=receipt['after']['id'] or current['Image']!=receipt['image_id'] or not current['State']['Running'] or
            (current['Config'].get('Labels') or {}).get('org.leiguoguo.oss-release')!=receipt['manifest_sha256']):
        raise ValueError('active runtime name or exact release identity changed')
    return current


def open_runtime(release,receipt):
    active_runtime(receipt)
    keeper=optional_container(receipt['write_window'])
    if keeper:
        if (keeper['Config'].get('Labels') or {}).get('org.leiguoguo.task')!=TASK:raise ValueError('write window owner differs')
        try:run(['docker','stop','--time','5',keeper['Id']])
        except Exception:
            actual=optional_container(keeper['Id'])
            if actual and actual['State']['Running']:raise
        try:run(['docker','rm',keeper['Id']])
        except Exception:
            if optional_container(keeper['Id']):raise
    receipt['phase']='open';save(release/'receipt.json',receipt)


def protect_vps(control,release,receipt):
    # Install the guarded legacy entry before publishing its marker. This runs
    # under publish.lock and before the new writer is allowed to accept work.
    temporary=control/'deploy.py.oss-new'
    with temporary.open('wb') as stream:
        stream.write((release/'vps_experience_remote.py').read_bytes());stream.flush();os.fsync(stream.fileno())
    temporary.chmod(0o700);temporary.replace(control/'deploy.py')
    state_path=control/'state.json';state=json.loads(state_path.read_text())
    if state['publication_id']!=receipt['publication_id']:raise ValueError('VPS publication changed')
    state['storage_upgrade']={'task':TASK,'release':str(release),'manifest_sha256':receipt['manifest_sha256']}
    save(state_path,state)


def resume(args):
    release=safe(args.release);receipt=json.loads((release/'receipt.json').read_text())
    if receipt['task']!=TASK or receipt['phase']!='opening':raise ValueError('resume only releases a verified opening write window')
    instance=safe(receipt['instance']);control=instance/'.runtime' if receipt['environment']=='local' else safe(Path.home()/'lijizhanshe')
    with ExitStack() as locks:
        for path in set((control/('publication.lock' if receipt['environment']=='local' else 'publish.lock'),instance/'.runtime/publication.lock')):
            lock=locks.enter_context(path.open('a'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        open_runtime(release,receipt)
    print(json.dumps({'opened':True,'release':str(release)}))


def finalize(args):
    release=safe(args.release);receipt=json.loads((release/'receipt.json').read_text())
    if receipt['task']!=TASK or receipt['phase']!='open':raise ValueError('only a verified open cutover can be finalized')
    instance=safe(receipt['instance']);kind=receipt['environment']
    control=instance/'.runtime' if kind=='local' else safe(Path.home()/'lijizhanshe')
    with ExitStack() as locks:
        for path in set((control/('publication.lock' if kind=='local' else 'publish.lock'),instance/'.runtime/publication.lock')):
            lock=locks.enter_context(path.open('a'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        current=active_runtime(receipt)
        if kind=='local':
            lock=locks.enter_context((control/'docker-image-tags.lock').open('a'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            desired={'story-review-desk:base':current['Image'],'story-review-desk:current':current['Image'],
                     'story-review-desk:previous':receipt['before']['image']}
            for tag,target in desired.items():
                before=subprocess.run(['docker','image','inspect',tag],capture_output=True,text=True,timeout=30)
                actual=json.loads(before.stdout)[0]['Id'] if before.returncode==0 else None
                if actual not in (None,target,receipt['before']['image'],receipt.get('previous_aliases',{}).get(tag)):
                    raise ValueError('another release changed a fixed image alias')
                try:run(['docker','tag',target,tag])
                except Exception:
                    if inspect(tag,True)['Id']!=target:raise
            receipt['fixed_image_aliases']=desired
        else:
            state_path=control/'state.json';state=json.loads(state_path.read_text())
            if state['publication_id']!=receipt['publication_id']:raise ValueError('VPS publication changed')
            state.update(story_commit=receipt['commits']['story'],desk_commit=receipt['commits']['desk'],
                         image_id=current['Image'],container_id=current['Id'],
                         storage_upgrade={'task':TASK,'release':str(release),'manifest_sha256':receipt['manifest_sha256']})
            save(state_path,state)
        save(control/'storage-runtime.json',{'release':str(release),'manifest_sha256':receipt['manifest_sha256'],
              'container_id':current['Id'],'image_id':current['Image'],'commits':receipt['commits']})
        receipt['runtime_entry_updated']=True;save(release/'receipt.json',receipt)
    print(json.dumps({'finalized':True,'release':str(release)}))


def apply(args):
    bundle,instance,credentials=map(safe,(args.bundle,args.instance,args.credentials))
    manifest=verify_bundle(bundle);kind=args.environment
    image=inspect(manifest['image'],True)
    if image_identity(image)!=manifest['image_identity'] or image['Architecture']!=manifest['image_architecture'] or image['Config'].get('Labels',{}).get('org.opencontainers.image.revision')!=manifest['commits']['desk']:
        raise ValueError('loaded runtime identity differs')
    if not credentials.is_file() or credentials.stat().st_mode&0o077:raise ValueError('runtime credentials must be a private external file')
    if credentials.is_relative_to(instance) or credentials.is_relative_to(bundle):raise ValueError('credentials must stay outside instance and release')
    resource=json.loads((bundle/'config/resource-storage.json').read_text())
    private=json.loads(credentials.read_text())
    if private.get('project')!=resource['project'] or private.get('instance')!=kind:raise ValueError('wrong scoped runtime credentials')
    name='snakeslayingrecord-app-1' if kind=='local' else 'lijizhanshe-app'
    control=instance/'.runtime' if kind=='local' else safe(Path.home()/'lijizhanshe')
    if kind=='vps' and instance!=Path.home()/'www/lijizhanshe':raise ValueError('wrong VPS instance')
    release=control/'storage-releases'/('oss-'+manifest['commits']['story'][:12]+'-'+manifest['commits']['desk'][:12])
    with ExitStack() as locks:
        for path in (control/('publication.lock' if kind=='local' else 'publish.lock'),instance/'.runtime/publication.lock'):
            path.parent.mkdir(parents=True,exist_ok=True)
            if str(path) in getattr(args,'locked_paths',set()):continue
            lock=locks.enter_context(path.open('a'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            args.locked_paths=getattr(args,'locked_paths',set())|{str(path)}
        if (release/'receipt.json').exists():raise ValueError('release has a receipt; inspect or use explicit rollback, do not repeat apply')
        before=inspect(name);host=before['HostConfig'];owned_runtime(before,kind,instance)
        mounts={m['Destination']:m for m in before['Mounts']}
        if Path(mounts.get('/instance',{}).get('Source','/')).resolve()!=instance.resolve():raise ValueError('live instance mount differs')
        if not before['State']['Running'] or host.get('Privileged') or host.get('PortBindings') or host.get('Devices') or host.get('CapAdd'):
            raise ValueError('unexpected live runtime boundary')
        if any(m['Type']!='bind' for m in before['Mounts']):raise ValueError('unreviewed non-bind mount')
        verify_mount_sources(before)
        if kind=='local':
            if run(['git','-C',instance,'rev-parse','HEAD'])!=manifest['commits']['story']:raise ValueError('managed story delivery is not integrated')
        else:
            import sys
            sys.path.insert(0,str(bundle))
            import vps_experience_remote as previous
            previous.preflight()
        release.mkdir(parents=True)
        # Keep the VPS's own business configuration and only advance the code pin.
        old_config=Path(mounts.get('/instance/config/instance.json',{}).get('Source',str(instance/'config/instance.json')))
        actual=json.loads(old_config.read_text());actual['review_desk_commit']=manifest['commits']['desk']
        if actual['id']!=resource['instance_id']:raise ValueError('live business instance identity differs')
        for logical in FILES:
            target=release/logical;target.parent.mkdir(parents=True,exist_ok=True)
            if logical=='config/instance.json':save(target,actual)
            else:shutil.copyfile(bundle/logical,target)
        shutil.copyfile(bundle/'manifest.json',release/'manifest.json')
        for helper in HELPERS:shutil.copyfile(bundle/helper,release/helper)
        release_suffix=manifest['commits']['story'][:10]+'-'+manifest['commits']['desk'][:10]
        previous_name=name+'-before-oss-'+release_suffix
        keeper='oss-write-window-'+kind+'-'+release_suffix
        receipt={'format':'oss-runtime-cutover-v1','task':TASK,'environment':kind,'phase':'prepared',
                 'before':current_identity(before),'previous_name':previous_name,'write_window':keeper,
                 'instance':str(instance),'manifest_sha256':sha(bundle/'manifest.json'),'commits':manifest['commits'],
                 'image_id':image['Id']}
        if kind=='local':
            receipt['previous_aliases']={}
            for tag in ('story-review-desk:base','story-review-desk:current','story-review-desk:previous'):
                found=subprocess.run(['docker','image','inspect',tag],capture_output=True,text=True,timeout=30)
                receipt['previous_aliases'][tag]=json.loads(found.stdout)[0]['Id'] if found.returncode==0 else None
        save(release/'receipt.json',receipt)
        try:
            # Acquire the lock in the same Docker filesystem environment as HTTP.
            run(['docker','run','-d','--pull','never','--name',keeper,'--label','org.leiguoguo.task='+TASK,
                 '--network','none','--memory','64m','--pids-limit','16','--mount','type=bind,source='+str(instance)+',target=/instance',
                 '--entrypoint','python',image['Id'],'-u','-c',
                 "import fcntl,time;f=open('/instance/.runtime/http-write.lock','a');fcntl.flock(f,fcntl.LOCK_EX);print('locked',flush=True);time.sleep(86400)"])
            deadline=time.monotonic()+60
            while run(['docker','logs',keeper])!='locked':
                if time.monotonic()>deadline:raise ValueError('write window is busy')
                time.sleep(.2)
            run(['docker','stop','--time','30',before['Id']])
            run(['docker','run','--rm','--pull','never','--network','none','--memory','64m',
                 '--mount','type=bind,source='+str(instance)+',target=/instance,readonly',
                 '--entrypoint','python',image['Id'],'-c',
                 "import pathlib,sqlite3;p=pathlib.Path('/instance/.runtime/edit-render.sqlite3');d=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) if p.exists() else None;assert d is None or not d.execute(\"SELECT 1 FROM jobs WHERE status IN ('queued','running') LIMIT 1\").fetchone(),'render work is pending; finish it before cutover'"])
            receipt['database_before']=database(image['Id'],instance)
            run(['docker','run','--rm','--pull','never','--network','none','--memory','256m',
                 '--mount','type=bind,source='+str(instance)+',target=/instance,readonly',
                 '--mount','type=bind,source='+str(release)+',target=/backup',
                 '--entrypoint','python',image['Id'],'-c',
                 "import sqlite3;from pathlib import Path;p=Path('/backup/before.sqlite3');assert not p.exists();s=sqlite3.connect('file:/instance/.runtime/review.sqlite3?mode=ro',uri=True);d=sqlite3.connect(p);s.backup(d,pages=256);d.close();s.close()"])
            receipt['database_backup_sha256']=sha(release/'before.sqlite3')
            usage=control/'usage/attempts.json'
            receipt['usage_before']=sha(usage) if usage.is_file() else None
            # Freeze locally registered resources while all instance writers are
            # stopped, preserving their exact descriptors for closure checks.
            overlay=safe(instance/'.runtime/resources/catalog.json')
            receipt['resource_overlay_sha256']=None
            if overlay.exists():
                if not overlay.is_file():raise ValueError('runtime resource catalog is not a file')
                target=release/'.runtime/resources/catalog.json'
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(overlay,target)
                receipt['resource_overlay_sha256']=sha(target)
                if sha(overlay)!=receipt['resource_overlay_sha256']:raise ValueError('runtime resource catalog changed during cutover')
            # Keep the candidate separate: old instances need not have the new
            # files, and Docker cannot create mountpoints inside a read-only bind.
            run(['docker','run','--rm','--pull','never','--network','none','--memory','256m',
                 '--mount','type=bind,source='+str(instance)+',target=/instance,readonly',
                 '--mount','type=bind,source='+str(release)+',target=/candidate,readonly',
                 '--entrypoint','python',image['Id'],'-c',
                 "from review_desk.store import Store;from review_desk.resource_bundle import closure;s=Store.open_readonly('/instance/.runtime/review.sqlite3');closure(s,'/candidate');s.close()"])
            receipt['phase']='stopped';save(release/'receipt.json',receipt)
            run(['docker','rename',before['Id'],previous_name])
            command=['docker','create','--pull','never','--name',name,'--restart',host['RestartPolicy']['Name'],'--network',host['NetworkMode']]
            if host['NetworkMode']!='host':command+=['--network-alias','app']
            for option,key in (('--memory','Memory'),('--memory-swap','MemorySwap'),('--pids-limit','PidsLimit')):
                if host.get(key):command += [option,str(host[key])]
            if host.get('NanoCpus'):command+=['--cpus',str(host['NanoCpus']/1e9)]
            health=before['Config'].get('Healthcheck')
            if health and health['Test'][0]!='NONE':
                command+=['--health-cmd',shlex.join(health['Test'][1:]) if health['Test'][0]=='CMD' else health['Test'][1]]
                for option,key in (('--health-interval','Interval'),('--health-timeout','Timeout'),('--health-start-period','StartPeriod')):
                    if health.get(key):command += [option,str(health[key])+'ns']
                if health.get('Retries'):command+=['--health-retries',str(health['Retries'])]
            for key,value in (host.get('LogConfig',{}).get('Config') or {}).items():command+=['--log-opt',key+'='+value]
            labels=before['Config'].get('Labels') or {}
            labels={**labels,'org.leiguoguo.task':TASK,'org.opencontainers.image.revision':manifest['commits']['desk'],
                    'org.leiguoguo.oss-release':receipt['manifest_sha256']}
            if kind=='local':
                labels.update({'com.docker.compose.project.config_files':str(release/'compose.release.json'),
                               'com.docker.compose.image':image['Id']})
                labels.pop('com.docker.compose.config-hash',None)
            for key,value in labels.items():command+=['--label',key+'='+value]
            environment=dict(item.split('=',1) for item in before['Config']['Env'])
            environment.update(REVIEW_OSS_CREDENTIALS_FILE='/run/project-oss.json',REVIEW_RESOURCE_INSTANCE=kind)
            for key in environment:command+=['--env',key]
            for destination,mount in mounts.items():
                if destination in ('/run/project-oss.json',*('/instance/'+x for x in FILES)):continue
                command+=['--mount','type=bind,source='+mount['Source']+',target='+destination+(',readonly' if not mount['RW'] else '')]
            for logical in FILES:command+=['--mount','type=bind,source='+str(release/logical)+',target=/instance/'+logical+',readonly']
            command+=['--mount','type=bind,source='+str(credentials)+',target=/run/project-oss.json,readonly',image['Id'],*before['Config']['Cmd']]
            # Permanent compose stores variable names only, preserving future release discovery.
            if kind=='local':
                source_mounts=[m for m in before['Mounts'] if m['Destination'] not in ('/run/project-oss.json',*('/instance/'+x for x in FILES))]
                source_mounts += [{'Source':str(release/x),'Destination':'/instance/'+x,'RW':False} for x in FILES]
                source_mounts += [{'Source':str(credentials),'Destination':'/run/project-oss.json','RW':False}]
                service={'image':image['Id'],'restart':host['RestartPolicy']['Name'],
                         'environment':{k:'${OSS_RELEASE_ENV_'+str(i)+'?required}' for i,k in enumerate(sorted(environment))},
                         'volumes':[{'type':'bind','source':m['Source'],'target':m['Destination'],'read_only':not m['RW']} for m in source_mounts],
                         'expose':['8765']}
                proxy=inspect('snakeslayingrecord-nginx-1')
                save(release/'compose.release.json',{'services':{'app':service,'nginx':{'image':proxy['Image'],'restart':'unless-stopped','ports':['127.0.0.1:3000:3000','127.0.0.1:64401:3000']}}})
            run(command,env={**os.environ,**environment})
            run(['docker','start',name])
            if kind=='local':run(['docker','exec','snakeslayingrecord-nginx-1','nginx','-s','reload'])
            command_line=before['Config']['Cmd']
            health_host=command_line[command_line.index('--host')+1] if '--host' in command_line else '127.0.0.1'
            if health_host=='0.0.0.0':health_host='127.0.0.1'
            deadline=time.monotonic()+120
            while True:
                try:
                    run(['docker','exec',name,'python','-c',
                        "import sys,urllib.request;from review_desk.deployment import settings;d=settings();u='http://'+sys.argv[1]+':8765'+d['base_path']+'/api/instance';print(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(u,timeout=5).status)",health_host])
                    break
                except RuntimeError:
                    if time.monotonic()>deadline:raise
                    time.sleep(1)
            receipt['database_after']=database(image['Id'],instance)
            if receipt['database_after']!=receipt['database_before']:raise ValueError('business database changed during code-only cutover')
            if receipt['usage_before']!=(sha(usage) if usage.is_file() else None):raise ValueError('usage counter changed during cutover')
            after=inspect(name);actual_env=dict(item.split('=',1) for item in after['Config']['Env'])
            if any(actual_env.get(k)!=v for k,v in environment.items()):raise ValueError('runtime environment changed unexpectedly')
            receipt.update(phase='verified',after=current_identity(after),publication_id=environment.get('REVIEW_PUBLICATION_ID'),credentials_mounted=True)
            save(release/'receipt.json',receipt)
            if kind=='vps':protect_vps(control,release,receipt)
            # Persist the no-rollback boundary before the lock can be released.
            # Any later uncertainty must keep this compatible writer alive.
            receipt['phase']='opening';save(release/'receipt.json',receipt)
            open_runtime(release,receipt)
            print(json.dumps({'switched':True,'release':str(release),'receipt':str(release/'receipt.json'),'previous_container':before['Id'],'new_container':after['Id'],'publication_id':receipt['publication_id']}))
        except BaseException:
            if receipt['phase'] in ('opening','open'):raise
            receipt['phase']='recovery-required';save(release/'receipt.json',receipt)
            rollback_runtime(release,receipt)
            raise


def main():
    global TASK
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', default=TASK, help='exact managed task owning this release')
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('prepare')
    for name in ('story','desk','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--image',required=True)
    p=commands.add_parser('apply')
    for name in ('bundle','instance','credentials'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--environment',choices=('local','vps'),required=True)
    p=commands.add_parser('rollback');p.add_argument('--release',type=Path,required=True)
    p=commands.add_parser('finalize');p.add_argument('--release',type=Path,required=True)
    p=commands.add_parser('resume');p.add_argument('--release',type=Path,required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'task-[0-9]{8}-[0-9]{4}', args.task):
        parser.error('invalid managed task identity')
    TASK=args.task
    globals()[args.command](args)


if __name__=='__main__':main()
