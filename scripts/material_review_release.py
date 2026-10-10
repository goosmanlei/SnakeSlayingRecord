#!/usr/bin/env python3
"""Prepare an immutable runtime release; apply only the authorized bundle.

Optional exact method or explicitly packaged data migration is applied during
a stopped-app window. No generation, acceptance or task completion. The system
fast-forward, live preservation checks, service switch and prepared ordinary
system push run serially; story Git delivery stays with the task launcher.
"""
import argparse
from contextlib import ExitStack, closing
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import sqlite3
import tempfile
import time
import autonomous_optimization_release as base

TASK='task-20261004-0004'
RELEASE_PREFIXES={TASK:'materials-20261004-0004', 'task-20261004-0005':'asset-cleanup-20261004-0005',
                  'task-20261004-0007':'breakdown-20261004-0007',
                  'task-20261004-0008':'ui-unification-20261004-0008',
                  'task-20261004-0009':'ui-material-model-20261004-0009',
                  'task-20261005-0001':'autonomous-20261005-0001',
                  'task-20261005-0002':'entity-material-20261005-0002',
                  'task-20261005-0003':'small-cards-20261005-0003',
                  'task-20261005-0004':'breakdown-page-20261005-0004',
                  'task-20261005-0005':'shot-production-20261005-0005',
                  'task-20261005-0006':'system-page-style-20261005-0006',
                  'task-20261005-0007':'approach-20261005-0007',
                  'task-20261006-0001':'entity-card-v2-20261006-0001',
                  'task-20261006-0002':'entity-cards-20261006-0002',
                  'task-20261006-0003':'breakdown-shot-v2-20261006-0003',
                  'task-20261006-0006':'approach-20261006-0006',
                  'task-20261008-0002':'seedance-handbook-20261008-0002',
                  'task-20261008-0006':'filmcraft-20261008-0006',
                  'entity-acceptance-20261004':'entity-acceptance-20261004'}
require,sha,read,save,run,git,inspect=base.require,base.sha,base.read,base.save,base.run,base.git,base.inspect
METHOD_MEDIA_DIRECTORY='content/production-approach-assets'


def check_vision_change(previous, candidate, raw):
    """Only this source-derived first tab may differ in the Review delivery."""
    from sync_system_vision import update
    require(candidate == update(previous, raw),
            'Review delivery may only prepend/update the exact vision tab; old approach content must remain')


def method_media_files(document):
    files={}
    for tab in document.get('tabs',[]):
        for section in tab.get('sections',[]):
            for block in section.get('blocks',[]):
                if block.get('type')!='media':continue
                filename,digest=block.get('file'),block.get('sha256')
                require(isinstance(filename,str) and re.fullmatch(r'[a-z0-9][a-z0-9._-]*\.(png|jpg|jpeg|webp|svg|mp4|webm|mp3|wav)',filename),'unsafe method media filename')
                require(isinstance(digest,str) and re.fullmatch(r'[a-f0-9]{64}',digest),'method media hash missing')
                relative=METHOD_MEDIA_DIRECTORY+'/'+filename
                require(relative not in files or files[relative]==digest,'conflicting method media versions')
                files[relative]=digest
    return files


def method_directory_hashes(folder):
    folder=Path(folder)
    require(folder.is_dir() and not folder.is_symlink(),'method media mount must be a directory')
    files={}
    for path in folder.iterdir():
        require(path.is_file() and not path.is_symlink(),'unexpected method media mount entry')
        files[path.name]=file_sha256(path)
    return files


def release_name(task, story_candidate, system_candidate):
    require(task in RELEASE_PREFIXES or re.fullmatch(r'task-[0-9]{8}-[0-9]{4}', task), 'unsupported release task')
    return RELEASE_PREFIXES.get(task, task)+'-'+story_candidate[:12]+'-'+system_candidate[:12]


def prepare(a):
    task=getattr(a,'task',TASK)
    release_id=release_name(task,a.story_candidate,a.system_candidate)
    story,system=a.story_worktree.resolve(),a.system_worktree.resolve()
    sm,gm=base.primary(story),base.primary(system)
    native=None
    if re.fullmatch(r'task-[0-9]{8}-[0-9]{4}', task):
        import task_repository_delivery
        if task_repository_delivery.uses_native_backend(sm,task):
            native=task_repository_delivery.freeze(sm,task,story,system,a.story_candidate,a.system_candidate)
    base.repo_check(story,sm,a.story_candidate,a.story_target)
    base.repo_check(system,gm,a.system_candidate,a.system_target,system=True)
    upstream=system_upstream(system,a.system_target,a.system_candidate) if getattr(a,'push_system',False) and not native else None
    root=a.bundle.resolve();require((story/'.runtime').resolve() in root.parents and not root.exists(),'new task runtime bundle required')
    app,nginx=inspect(base.APP),inspect(base.NGINX)
    old,proxy=base.safe_container(app),base.safe_container(nginx)
    require(old['working_dir']==str(sm) and proxy['working_dir']==str(sm),'another formal instance')
    require(proxy['ports']==base.PORTS and not nginx['Mounts'],'formal proxy layout changed')
    require(app['State']['Running'] and app['State'].get('Health',{}).get('Status')=='healthy','formal app unhealthy')
    mounts={m['Destination']:m for m in old['mounts']}
    expected_mounts={'/instance','/instance/config/instance.json','/instance/content/production-approach.json','/run/local-ca/cacert.pem'}
    media_mount=mounts.get('/instance/'+METHOD_MEDIA_DIRECTORY)
    if media_mount:expected_mounts.add('/instance/'+METHOD_MEDIA_DIRECTORY)
    require(set(mounts)==expected_mounts,'review unknown formal mounts')
    require(mounts['/instance']['Source']==str(sm) and mounts['/instance']['RW'],'normal live instance mount differs')
    require(all(not mounts[n]['RW'] for n in mounts if n!='/instance'),'overlay and CA must be read-only')
    # Preserve exact service process/environment semantics of the verified images.
    for current in (app,nginx):
        image=inspect(current['Image'],image=True)
        for key in ('Cmd','Entrypoint','WorkingDir','User'):
            require((current['Config'].get(key) or '')==(image['Config'].get(key) or ''),'nondefault process configuration')
        require(current['HostConfig']['RestartPolicy']=={'Name':'unless-stopped','MaximumRetryCount':0},'restart policy changed')
    require(base.env_values(nginx)==base.env_values(inspect(nginx['Image'],image=True)),'custom proxy environment')
    hashes={}
    def put(rel,raw):base.write_once(root/rel,raw);hashes[rel]=sha(raw)
    for name in base.INSTANCE_FILES:put('instance/'+name,base.git_file(story,a.story_candidate,name))
    managed_methods = None
    if getattr(a, 'method_registry', None):
        require(getattr(a, 'method_audit', None), 'method cutover requires an in-flight delivery audit')
        paths = {}
        for key, path in (('registry', a.method_registry), ('audit', a.method_audit)):
            relative = Path(path).as_posix()
            require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'method cutover paths must be project-relative')
            raw = base.git_file(story, a.story_candidate, relative)
            require(raw == (story / relative).read_bytes(), 'method cutover input differs from candidate')
            if key == 'registry':
                import method_migration
                method_migration.check_registry(json.loads(raw))
            paths[key] = 'methods/' + key + '.json'; put(paths[key], raw)
        managed_methods = paths
    latest = None
    if getattr(a, 'audiovisual_package', None):
        require(a.latest_registry, 'latest migration requires exact registry')
        latest = {}
        for key, path in (('package', a.audiovisual_package), ('registry', a.latest_registry)):
            relative = Path(path).as_posix()
            require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'migration must be project relative')
            raw = base.git_file(story, a.story_candidate, relative)
            require(raw == (story / relative).read_bytes(), 'migration input differs from candidate')
            if key == 'package':
                for filename, digest in json.loads(raw)['authored_sha256'].items():
                    require(not Path(filename).is_absolute() and '..' not in Path(filename).parts, 'unsafe authored source path')
                    source_raw = base.git_file(story, a.story_candidate, filename)
                    require(sha(source_raw) == digest and source_raw == (story/filename).read_bytes(), 'authored migration source drifted: '+filename)
            latest[key] = 'latest/' + key + '.json'; put(latest[key], raw)
    relations = None
    if getattr(a, 'relations_package', None):
        require(not managed_methods and not latest, 'unified relationship release owns its exact method/data transaction')
        relative = Path(a.relations_package).as_posix()
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'relationship package must be project relative')
        raw = base.git_file(story, a.story_candidate, relative)
        require(raw == (story / relative).read_bytes(), 'relationship package differs from candidate')
        document = json.loads(raw)
        require(document.get('format') == 'unified-relation-release-v1', 'wrong relationship package')
        put('relations/' + relative, raw)
        for item in document['files'].values():
            name = item['file']
            require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'relationship input path escaped')
            value = base.git_file(story, a.story_candidate, name)
            require(sha(value) == item['sha256'] and value == (story/name).read_bytes(), 'relationship input differs: ' + name)
            put('relations/' + name, value)
        relations = {'root':'relations', 'package':'relations/' + relative}
    retirement = None
    if getattr(a, 'review_retirement_package', None):
        require(not managed_methods and not latest and not relations, 'review retirement owns its exact method/data transaction')
        relative = Path(a.review_retirement_package).as_posix()
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'retirement package must be project relative')
        raw = base.git_file(story, a.story_candidate, relative)
        require(raw == (story/relative).read_bytes(), 'retirement package differs from candidate')
        document = json.loads(raw)
        require(document.get('format') == 'comment-review-release-v1', 'wrong retirement package')
        put('retirement/'+relative, raw)
        for item in document['files'].values():
            name = item['file']
            require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'retirement input escaped')
            value = base.git_file(story, a.story_candidate, name)
            require(sha(value) == item['sha256'] and value == (story/name).read_bytes(), 'retirement input differs: '+name)
            put('retirement/'+name, value)
        retirement = {'root':'retirement', 'package':'retirement/'+relative}
    method_media=method_media_files(read(root/'instance/content/production-approach.json'))
    for name,digest in method_media.items():
        raw=base.git_file(story,a.story_candidate,name)
        require(sha(raw)==digest,'method media differs from declared version: '+name)
        put('instance/'+name,raw)
    cfg=read(root/'instance/config/instance.json');require(cfg['review_desk_commit']==a.system_candidate,'candidate instance pin differs')
    current_files={name:sha(Path(mounts['/instance/'+name]['Source']).read_bytes()) for name in base.INSTANCE_FILES}
    if task in {'task-20261010-0001', 'task-20261010-0022', 'task-20261010-0023'}:
        raw = base.git_file(story, a.story_candidate, 'production/system-vision.md')
        require(raw == (story/'production/system-vision.md').read_bytes(), 'vision source differs from candidate')
        check_vision_change(read(mounts['/instance/content/production-approach.json']['Source']),
                            read(root/'instance/content/production-approach.json'), raw)
        put('instance/production/system-vision.md', raw)
    else:
        require(task in {'task-20261005-0007','task-20261006-0006','task-20261008-0001','task-20261008-0002','task-20261008-0006','task-20261008-0004','task-20261009-0004','task-20261010-0019'} or current_files['content/production-approach.json']==hashes['instance/content/production-approach.json'],'approach content change is outside this release')
    source={}
    for line in git(system,'ls-tree','-r',a.system_candidate,'--','review_desk').splitlines():
        header,name=line.split('\t',1);require(header.split()[0] in ('100644','100755'),'special source file')
        raw=base.git_file(system,a.system_candidate,name);put('build/'+name,raw);source[name]=sha(raw)
    policy=base.stable_image_policy(app['Image'])
    tag=policy['base_image_tag']
    put('build/Dockerfile',('FROM '+tag+'\nRUN rm -rf /app/review_desk\nCOPY review_desk /app/review_desk\nLABEL org.opencontainers.image.revision='+a.system_candidate+'\n').encode())
    helpers=['material_review_release.py','autonomous_optimization_release.py','integrate_generation_review_system.py']
    if managed_methods:helpers.append('method_migration.py')
    if native:helpers.append('task_repository_delivery.py')
    if latest:helpers.extend(['latest_state_migration.py','audiovisual_publication.py','generation_workspace.py','method_migration.py'])
    if relations:helpers.extend(['unified_relation_migration.py','method_migration.py'])
    if retirement:helpers.extend(['review_retirement_release.py','unified_relation_migration.py','method_migration.py'])
    for helper in helpers:
        raw=base.git_file(story,a.story_candidate,'scripts/'+helper);require(raw==(story/'scripts'/helper).read_bytes(),'helper differs from committed candidate');put('helpers/'+helper,raw)
    files=old['config_files'].split(',');require(files==proxy['config_files'].split(','),'compose sets differ')
    plan={'format':'generation-system-delivery-v1','task':task,'push':bool(upstream),'system_main_from_story_main':os.path.relpath(gm,sm),'system_worktree':os.path.relpath(system,story),'expected_target':a.system_target,'candidate':a.system_candidate}
    if native:plan['task_delivery']=native
    put('system-delivery.json',json.dumps(plan,ensure_ascii=False,indent=2).encode()+b'\n')
    m={**policy,'format':'material-review-release-v1','task':task,'push':False,'story_worktree':str(story),'system_worktree':str(system),'story_main':str(sm),'system_main':str(gm),'story_candidate':a.story_candidate,'story_target':a.story_target,'system_candidate':a.system_candidate,'system_target':a.system_target,'system_upstream':upstream,'release_name':release_id,'hashes':hashes,'source_hashes':source,'base_image_tag':tag,'previous_app':old,'previous_nginx':proxy,'previous_compose_hashes':{f:sha(Path(f).read_bytes()) for f in files},'previous_instance_hashes':current_files,'ca_sha256':sha(Path(mounts['/run/local-ca/cacert.pem']['Source']).read_bytes()),'prepared_at':datetime.now(timezone.utc).isoformat()}
    m['delivery_backend']='codex.task' if native else 'legacy'
    if method_media:m['method_media']=method_media
    if media_mount:m['previous_method_media']=method_directory_hashes(media_mount['Source'])
    if native:m['task_delivery']=native
    if managed_methods:m['managed_methods']=managed_methods
    if latest:m['latest_state_migration']=latest
    if relations:m['unified_relation_migration']=relations
    if retirement:m['review_retirement']=retirement
    if task=='task-20261006-0005':
        m['database_changes']={'format':'transactional-read-cache-v1','journal_mode':'delete','journal_mode_changed':False,
                               'auxiliary_table':'read_generations','business_rows':'preserve',
                               'recovery':'retain current DELETE journal and business rows; disable or clear the disposable cache; never restore an old business snapshot'}
    save(root/'manifest.json',m);print(json.dumps({'bundle':str(root),'manifest_sha256':sha((root/'manifest.json').read_bytes()),'formal_writes':False,'business_delta':None if managed_methods or latest or relations or retirement else 0}))


def load_bundle(path):
    root=path.resolve();m=read(root/'manifest.json');require(m.get('format')=='material-review-release-v1' and (m.get('task') in RELEASE_PREFIXES or m.get('task_delivery',{}).get('backend')=='codex.task' or (m.get('delivery_backend')=='legacy' and re.fullmatch(r'task-[0-9]{8}-[0-9]{4}',m.get('task','')))) and m.get('push') is False,'wrong bundle')
    require(m.get('release_name')==release_name(m['task'],m['story_candidate'],m['system_candidate']),'release task or name differs')
    for rel,value in m['hashes'].items():
        require(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'invalid package path');require(sha((root/rel).read_bytes())==value,'bundle changed: '+rel)
    require(sha(Path(__file__).read_bytes())==m['hashes']['helpers/material_review_release.py'],'wrapper changed')
    require(sha(Path(base.__file__).read_bytes())==m['hashes']['helpers/autonomous_optimization_release.py'],'runtime helper changed')
    if m.get('task_delivery'):
        import task_repository_delivery
        require(sha(Path(task_repository_delivery.__file__).read_bytes())==m['hashes']['helpers/task_repository_delivery.py'],'task adapter changed')
    return root,m


def build(a):
    root,m=load_bundle(a.bundle);require(not (root/'image.json').exists(),'immutable image already prepared')
    if m.get('image_policy')==base.IMAGE_POLICY:
        image=base.build_stable_image(root,m)
        save(root/'image.json',{'image':image,'publish_tag':base.IMAGE_CURRENT,'source_verified':True,'manifest_sha256':sha((root/'manifest.json').read_bytes())})
        print(json.dumps({'image':image,'image_receipt_sha256':sha((root/'image.json').read_bytes()),'formal_writes':False}));return
    base.pin_base_image(m['previous_app']['image'],m['base_image_tag'])
    tag='story-review-desk:materials-'+m['system_candidate'][:12]+'-'+m['story_candidate'][:12]
    run([base.DOCKER,'build','--pull=false','--network=none','-t',tag,root/'build'])
    image=inspect(tag,image=True)['Id'];base.source_check(image,m['source_hashes'])
    save(root/'image.json',{'image':image,'tag':tag,'source_verified':True,'manifest_sha256':sha((root/'manifest.json').read_bytes())})
    print(json.dumps({'image':image,'image_receipt_sha256':sha((root/'image.json').read_bytes()),'formal_writes':False}))


def checks(root,m,live=True):
    # Breakdown and small-card releases use the approved two-stage integration:
    # code first, data/service next, task completion after formal page acceptance.
    base.repo_check(m['story_worktree'],m['story_main'],m['story_candidate'],m['story_target'],system=bool(m.get('task_delivery')) or m['task'] in ('task-20261004-0007','task-20261005-0003','task-20261005-0004','task-20261005-0005','task-20261005-0006','task-20261005-0007','task-20261006-0001','task-20261006-0002','task-20261006-0003'))
    base.repo_check(m['system_worktree'],m['system_main'],m['system_candidate'],m['system_target'],system=True)
    for path,value in m['previous_compose_hashes'].items():require(sha(Path(path).read_bytes())==value,'compose input drifted')
    ca=next(x['Source'] for x in m['previous_app']['mounts'] if x['Destination']=='/run/local-ca/cacert.pem');require(sha(Path(ca).read_bytes())==m['ca_sha256'],'CA drifted')
    image=read(root/'image.json');require(image['manifest_sha256']==sha((root/'manifest.json').read_bytes()),'image manifest differs');base.source_check(image['image'],m['source_hashes'])
    if live:
        require(base.safe_container(inspect(base.APP))==m['previous_app'] and base.safe_container(inspect(base.NGINX))==m['previous_nginx'],'formal service drifted')
        for name,value in m['previous_instance_hashes'].items():
            path=next(x['Source'] for x in m['previous_app']['mounts'] if x['Destination']=='/instance/'+name);require(sha(Path(path).read_bytes())==value,'formal overlay drifted')
        if 'previous_method_media' in m:
            path=next(x['Source'] for x in m['previous_app']['mounts'] if x['Destination']=='/instance/'+METHOD_MEDIA_DIRECTORY)
            require(method_directory_hashes(path)==m['previous_method_media'],'formal method media drifted')
    return image


def preflight(a):
    root,m=load_bundle(a.bundle);image=checks(root,m)
    result=json.loads(run([sys.executable,root/'helpers/integrate_generation_review_system.py','--plan',root/'system-delivery.json','--system-main',m['system_main'],'--system-worktree',m['system_worktree']]))
    require(result['preflight_only'],'unexpected integrator action')
    print(json.dumps({'preflight_only':True,'manifest_sha256':sha((root/'manifest.json').read_bytes()),'image_receipt_sha256':sha((root/'image.json').read_bytes()),'image':image['image']}))


def read_generation_schema(db, schemas):
    """Only the reviewed disposable invalidation journal may be added."""
    name='read_generations'
    if name not in schemas:return
    require(schemas[name]=='CREATE TABLE read_generations (name TEXT PRIMARY KEY, token TEXT NOT NULL)',
            'unexpected read generation schema')
    values=dict(db.execute('SELECT name,token FROM read_generations'))
    require(set(values)==set(schemas)-{name},'incomplete read generation table coverage')
    require(all(re.fullmatch('[0-9a-f]{32}',v or '') for v in values.values()),'invalid read generation token')
    triggers=dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger' AND name LIKE 'read_generation_%'"))
    expected={}
    for table in values:
        quoted='"'+table.replace('"','""')+'"';literal="'"+table.replace("'","''")+"'"
        for operation in ('INSERT','UPDATE','DELETE'):
            key='read_generation_'+hashlib.sha256((table+operation).encode()).hexdigest()[:24]
            expected[key]=f'CREATE TRIGGER "{key}" AFTER {operation} ON {quoted} BEGIN UPDATE read_generations SET token=lower(hex(randomblob(16))) WHERE name={literal}; END'
    require(triggers==expected,'read generation triggers differ from approved migration')


def preserved(before,after,*,allow_read_generations=False,allow_cache_token_updates=False):
    # The live instance contains a large content-addressed history. Keep only
    # one row in Python; the exact multiset comparison lives in a disk index.
    mutable={'objects':('id','kind','created_at'),
             'comments':('id','target_object_id','target_revision_id','anchor','created_at'),
             'sources':('id',),'configurations':('scope',),
             'material_rounds':('material_id','number','created_at'),
             'material_members':('material_id','number','revision_id')}
    with ExitStack() as stack:
        databases=[]
        for path in (before,after):
            db=stack.enter_context(closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)))
            db.row_factory=sqlite3.Row;db.execute('PRAGMA cache_size=-4096');db.execute('PRAGMA temp_store=FILE')
            db.execute('BEGIN');databases.append(db)
        schemas=[dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")) for db in databases]
        if allow_read_generations:
            require('read_generations' in schemas[1],'approved read generation migration missing')
            for db,schema in zip(databases,schemas):
                read_generation_schema(db,schema)
                schema.pop('read_generations',None)
        require(schemas[0].keys()==schemas[1].keys(),'database table set changed')
        temporary=stack.enter_context(tempfile.TemporaryDirectory(prefix='review-release-history-'))
        index=stack.enter_context(closing(sqlite3.connect(Path(temporary)/'counts.sqlite3')))
        index.execute('PRAGMA cache_size=-4096');index.execute('PRAGMA temp_store=FILE')
        index.execute('CREATE TABLE counts(side INTEGER,digest TEXT,n INTEGER,PRIMARY KEY(side,digest)) WITHOUT ROWID')
        evidence={}
        for table,schema in schemas[0].items():
            require(schema==schemas[1][table],'business table schema changed')
            if table == 'read_generations' and allow_cache_token_updates:
                for db, schema_set in zip(databases, schemas):
                    read_generation_schema(db, schema_set)
                counts=[db.execute('SELECT COUNT(*) FROM read_generations').fetchone()[0] for db in databases]
                evidence[table]={'before':counts[0],'after':counts[1],'disposable_tokens_only':True}
                continue
            quoted='"'+table.replace('"','""')+'"'
            columns={row['name'] for row in databases[0].execute('PRAGMA table_info('+quoted+')')}
            keys=tuple(k for k in mutable.get(table,()) if k in columns)
            counts=[]
            index.execute('DELETE FROM counts')
            for side,db in enumerate(databases):
                count=0
                for row in db.execute('SELECT * FROM '+quoted):
                    value=dict(row)
                    require(all(not isinstance(v,bytes) for v in value.values()),'unexpected BLOB history; review serializer')
                    # A current head/status may advance, but its original
                    # identity and every immutable historical row must remain.
                    identity=tuple(value[k] for k in keys) if table in mutable else value
                    digest=sha(base.canonical(identity))
                    index.execute('INSERT INTO counts VALUES (?,?,1) ON CONFLICT(side,digest) DO UPDATE SET n=n+1',(side,digest))
                    count+=1
                counts.append(count)
            missing=index.execute('SELECT 1 FROM counts a LEFT JOIN counts b ON b.side=1 AND b.digest=a.digest '
                'WHERE a.side=0 AND (b.digest IS NULL'+('' if table in mutable else ' OR b.n<a.n')+') LIMIT 1').fetchone()
            require(missing is None,('current identities lost: ' if table in mutable else 'immutable history lost: ')+table)
            evidence[table]={'before':counts[0],'after':counts[1],'preserved':True}
        return evidence


def file_sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def install(root,m,image):
    release=Path(m['story_main'])/'.runtime/service-releases'/m['release_name']
    require(not release.is_symlink(),'release must not be symlink')
    for name in (*base.INSTANCE_FILES,*m.get('method_media',{})):base.write_once(release/'instance'/name,(root/'instance'/name).read_bytes())
    for name in ('manifest.json','image.json'):base.write_once(release/name,(root/name).read_bytes())
    for name in ('material_review_release.py','autonomous_optimization_release.py'):base.write_once(release/name,(root/'helpers'/name).read_bytes())
    save(release/'compose.release.json',base.compose_definition(m,image,release))
    save(release/'README.json',{'purpose':'Permanent immutable config and approach mounts; live DB/assets stay on /instance. Never restore the before database.','restart':['python3','material_review_release.py','restart','--release','.','--apply']})
    return release


def authorized(a):
    require(a.apply,'--apply is required and does not replace user confirmation');root,m=load_bundle(a.bundle)
    require(sha((root/'manifest.json').read_bytes())==a.manifest_sha256 and sha((root/'image.json').read_bytes())==a.image_receipt_sha256,'confirmed bundle digest differs')
    return root,m


def apply(a):
    root,m=authorized(a)
    with base.publication_locks(m):
        image=checks(root,m,live=False);receipt=root/'run';receipt.mkdir(exist_ok=True)
        release=Path(m['story_main'])/'.runtime/service-releases'/m['release_name']
        current=inspect(base.APP);candidate_mounts={v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}
        exact_candidate=current['Image']==image['image'] and {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']}==candidate_mounts
        proxy=base.safe_container(inspect(base.NGINX));expected_proxy={**m['previous_nginx'],'config_files':str(release/'compose.release.json')}
        require(proxy in (m['previous_nginx'],expected_proxy),'another proxy runtime is active')
        before=receipt/'before.sqlite3'
        method_change = m.get('managed_methods')
        if method_change:
            import method_migration
            require(sha(Path(method_migration.__file__).read_bytes()) == m['hashes']['helpers/method_migration.py'], 'method migration helper changed')
            method_migration.check_cutover(Path(m['story_main']), read(root/method_change['audit']))
            # The previous release may not know the HTTP maintenance lock.
            # Stop the exact verified application, then take the cutoff snapshot.
            # Accepted writes before this stop are included; no old DB is restored.
            require(exact_candidate or base.safe_container(current)==m['previous_app'], 'another app is active')
            if current['State']['Running']:run([base.DOCKER, 'stop', '--time', '30', current['Id']])
            require(not inspect(current['Id'])['State']['Running'], 'application still accepting writes')
            save(receipt/'write-window.json', {'container_id': current['Id'], 'stopped': True,
                                              'surfaces': ['comments','acceptance','configuration','content','uploads'],
                                              'ingress': method_migration.stopped_api(application_stopped=True),
                                              'at': datetime.now(timezone.utc).isoformat()})
        # Integrator receipt root is task runtime, irrespective of copied helper.
        integration=json.loads(run([sys.executable,Path(m['story_worktree'])/'scripts/integrate_generation_review_system.py','--plan',root/'system-delivery.json','--apply','--receipt',receipt/'system-integration.json']))
        require(integration['target_after']==m['system_candidate'],'system integration mismatch')
        if m.get('latest_state_migration'):
            import latest_state_migration
            for helper in ('latest_state_migration.py','audiovisual_publication.py','generation_workspace.py','method_migration.py'):
                require(sha((Path(m['story_worktree'])/'scripts'/helper).read_bytes()) == m['hashes']['helpers/'+helper], 'latest migration helper drifted')
            require(exact_candidate or base.safe_container(current)==m['previous_app'], 'another app is active')
            if current['State']['Running']:run([base.DOCKER, 'stop', '--time', '30', current['Id']])
            require(not inspect(current['Id'])['State']['Running'], 'application still writing')
            save(receipt/'latest-write-window.json', {'container_id':current['Id'], 'stopped':True,
                 'ingress':__import__('method_migration').stopped_api(application_stopped=True)})
            latest_state_migration.apply(root,m)
        if m.get('unified_relation_migration'):
            import unified_relation_migration
            for helper in ('unified_relation_migration.py','method_migration.py'):
                require(sha((Path(m['story_worktree'])/'scripts'/helper).read_bytes()) == m['hashes']['helpers/'+helper], 'relationship migration helper drifted')
            require(exact_candidate or base.safe_container(current)==m['previous_app'], 'another app is active')
            if current['State']['Running']:run([base.DOCKER, 'stop', '--time', '30', current['Id']])
            require(not inspect(current['Id'])['State']['Running'], 'application still writing')
            save(receipt/'relations-write-window.json', {'container_id':current['Id'], 'stopped':True,
                 'ingress':__import__('method_migration').stopped_api(application_stopped=True)})
            unified_relation_migration.apply(root,m)
        if m.get('review_retirement'):
            import review_retirement_release
            for helper in ('review_retirement_release.py','unified_relation_migration.py','method_migration.py'):
                require(sha((Path(m['story_worktree'])/'scripts'/helper).read_bytes()) == m['hashes']['helpers/'+helper], 'retirement helper drifted')
            require(exact_candidate or base.safe_container(current)==m['previous_app'], 'another app is active')
            if current['State']['Running']:run([base.DOCKER, 'stop', '--time', '30', current['Id']])
            require(not inspect(current['Id'])['State']['Running'], 'application still writing')
            save(receipt/'review-write-window.json', {'container_id':current['Id'], 'stopped':True,
                 'ingress':__import__('method_migration').stopped_api(application_stopped=True)})
            review_retirement_release.apply(root,m)
        if not before.exists():
            checks(root,m);base.snapshot(Path(m['story_main'])/'.runtime/review.sqlite3',before);save(receipt/'before.json',{'sha256':file_sha256(before)})
        else:
            require(file_sha256(before)==read(receipt/'before.json')['sha256'],'before snapshot changed')
            require(exact_candidate or base.safe_container(current)==m['previous_app'],'another runtime is active; recover or prepare again')
        if method_change:
            cutoff=receipt/('method-cutoff-'+str(time.time_ns())+'.sqlite3')
            base.snapshot(Path(m['story_main'])/'.runtime/review.sqlite3',cutoff)
            result = json.loads(run([sys.executable, root/'helpers/method_migration.py', '--system', m['system_main'],
                                     'apply', '--database', Path(m['story_main'])/'.runtime/review.sqlite3',
                                     '--registry', root/method_change['registry'], '--activate-media']))
            save(receipt/'method-migration.json', result)
            migrated=receipt/('methods-'+str(time.time_ns())+'.sqlite3')
            base.snapshot(Path(m['story_main'])/'.runtime/review.sqlite3',migrated)
            evidence = method_migration.compare(cutoff,migrated,read(root/method_change['registry']))
            save(receipt/'method-preservation.json',evidence)
        release=install(root,m,image);environment=base.env_values(inspect(base.APP))
        if not exact_candidate or not inspect(base.APP)['State']['Running']:base.compose_up(m,[release/'compose.release.json'],environment,release=True)
        service=base.verify_service(m,image,release)
        after=receipt/('after-'+str(time.time_ns())+'.sqlite3');base.snapshot(Path(m['story_main'])/'.runtime/review.sqlite3',after)
        cache_migration=m.get('database_changes',{}).get('format')=='transactional-read-cache-v1'
        require(not cache_migration or m['task']=='task-20261006-0005','unexpected database migration task')
        evidence=preserved(before,after,allow_read_generations=cache_migration,allow_cache_token_updates=bool(method_change or m.get('latest_state_migration') or m.get('unified_relation_migration') or m.get('review_retirement')))
        database_runtime=None
        if cache_migration:
            live_db=(Path(m['story_main'])/'.runtime/review.sqlite3').resolve()
            with closing(sqlite3.connect(live_db.as_uri()+'?mode=ro',uri=True)) as db:
                database_runtime={'journal_mode':db.execute('PRAGMA journal_mode').fetchone()[0]}
            require(database_runtime['journal_mode']=='delete','reviewed DELETE journal mode changed')
        base.update_image_aliases(m,image)
        result={'status':'formal_browser_pending','service':service,'release':str(release),'rows':evidence,'business_delta':None if method_change or m.get('latest_state_migration') or m.get('unified_relation_migration') or m.get('review_retirement') else 0,'method_migration':read(receipt/'method-migration.json') if method_change else None,'system_candidate':m['system_candidate'],'push':False,'complete_invoked':False,
                'database_changes':m.get('database_changes'),'database_runtime':database_runtime}
        save(receipt/('service-'+str(time.time_ns())+'.json'),result);print(json.dumps(result,ensure_ascii=False))


def recover(a):
    root,m=authorized(a);image=read(root/'image.json');release=Path(m['story_main'])/'.runtime/service-releases'/m['release_name']
    with base.publication_locks(m):
        require(not m.get('latest_state_migration'), 'latest data contract applied: recover forward with the exact current package; never restore an old database or incompatible image')
        require(not m.get('review_retirement'), 'approval retirement: recover forward with this exact package; never restore an old approval database or incompatible image')
        require(not m.get('unified_relation_migration'), 'unified relationship contract: recover forward with this exact package; never restore an old database or incompatible image')
        if m.get('managed_methods'):
            # The pre-cutover image cannot enforce the newly active contract.
            # Keep the database and require a compatible runtime repair instead.
            database=Path(m['story_main'])/'.runtime/review.sqlite3'
            with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
                active=db.execute("SELECT 1 FROM objects WHERE id='method.activation.media-plan'").fetchone()
            require(not active,'方法约束已启用，不能回退到切换前镜像；请重启当前兼容版本或发布兼容修复，不要回灌旧数据库')
        current=inspect(base.APP);known_mounts=[{v['Destination']:(v['Source'],v['RW']) for v in m['previous_app']['mounts']},{v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}];require(current['Image'] in (image['image'],m['previous_app']['image']) and {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']} in known_mounts,'another release is active')
        proxy=base.safe_container(inspect(base.NGINX));expected_proxy={**m['previous_nginx'],'config_files':str(release/'compose.release.json')};recovered_proxy={**m['previous_nginx'],'config_files':str(root/'compose.previous.json')}
        require(proxy in (m['previous_nginx'],expected_proxy,recovered_proxy),'another proxy runtime is active')
        previous=base.compose_definition(m,{'image':m['previous_app']['image']},release)
        previous['services']['app']['volumes']=[{'type':'bind','source':v['Source'],'target':v['Destination'],'read_only':not v['RW']} for v in m['previous_app']['mounts']]
        path=root/'compose.previous.json';save(path,previous);base.compose_up(m,[path],base.env_values(current),release=True);base.wait_healthy()
        require(inspect(base.APP)['Image']==m['previous_app']['image'],'recovery image differs')
        base.update_image_aliases(m,image,recovered=True)
        print(json.dumps({'runtime_recovered':True,'database_restored':False,'git_reset':False}))


def system_upstream(worktree,target,candidate,expected=None):
    """Freeze or recheck one exact upstream; no force push and no remote guessing."""
    remote=git(worktree,'config','--get','branch.main.remote')
    ref=git(worktree,'config','--get','branch.main.merge')
    require(remote and remote!='.' and ref=='refs/heads/main','system main needs one named upstream')
    urls=git(worktree,'remote','get-url','--push','--all',remote).splitlines()
    require(len(urls)==1,'system push needs one destination')
    value={'remote':remote,'ref':ref,'url':urls[0],'expected_target':target}
    require(expected is None or value==expected,'system upstream changed')
    current=git(worktree,'ls-remote','--exit-code',remote,ref).splitlines()
    require(len(current)==1 and current[0].split()[1]==ref,'system upstream identity differs')
    head=current[0].split()[0]
    require(head in (target,candidate),'system remote changed; prepare and verify again')
    return value


def publish_system(a):
    root,m=authorized(a)
    if m.get('task_delivery'):
        import task_repository_delivery
        result=task_repository_delivery.push_receipt(m['task_delivery'])
        save(root/'run/system-push.json',result);print(json.dumps(result));return
    require(m.get('system_upstream'),'system push was not prepared')
    base.repo_check(m['system_worktree'],m['system_main'],m['system_candidate'],m['system_target'],system=True)
    require(git(m['system_main'],'rev-parse','HEAD')==m['system_candidate'],'system must be integrated before push')
    upstream=system_upstream(m['system_worktree'],m['system_target'],m['system_candidate'],m['system_upstream'])
    # A concurrent divergence is rejected by ordinary Git fast-forward rules.
    run(['git','-C',m['system_worktree'],'push',upstream['remote'],m['system_candidate']+':'+upstream['ref']])
    head=git(m['system_worktree'],'ls-remote','--exit-code',upstream['remote'],upstream['ref']).split()[0]
    require(head==m['system_candidate'],'system remote verification failed')
    result={'system_candidate':head,'remote':upstream['remote'],'ref':upstream['ref'],'remote_verified':True,'force':False}
    save(root/'run/system-push.json',result);print(json.dumps(result))


def restart(a):
    require(a.apply,'restart requires --apply');root=a.release.resolve();m=read(root/'manifest.json');image=read(root/'image.json')
    require(m['format']=='material-review-release-v1','not this release');expected=base.compose_definition(m,image,root)
    for name in (base.APP,base.NGINX):
        current=inspect(name);require(current['Image']==expected['services']['app' if name==base.APP else 'nginx']['image'],'another image is active')
    require({v['Destination']:(v['Source'],v['RW']) for v in inspect(base.APP)['Mounts']}=={v['target']:(v['source'],not v['read_only']) for v in expected['services']['app']['volumes']},'another mount is active')
    run([base.DOCKER,'restart',base.APP,base.NGINX]);base.verify_service(m,image,root);print(json.dumps({'restarted':True,'recreated':False}))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare');q.add_argument('--story-worktree',type=Path,default=Path(__file__).resolve().parents[1]);q.add_argument('--system-worktree',type=Path,required=True);q.add_argument('--bundle',type=Path,required=True)
    q.add_argument('--task',default=TASK);q.add_argument('--push-system',action='store_true')
    q.add_argument('--audiovisual-package',type=Path);q.add_argument('--latest-registry',type=Path)
    q.add_argument('--relations-package',type=Path)
    q.add_argument('--review-retirement-package',type=Path)
    q.add_argument('--method-registry',type=Path);q.add_argument('--method-audit',type=Path)
    for name in ('story-candidate','system-candidate','story-target','system-target'):q.add_argument('--'+name,required=True)
    for cmd in ('build','preflight','apply','recover','publish-system'):
        q=sub.add_parser(cmd);q.add_argument('--bundle',type=Path,required=True)
        if cmd in ('apply','recover','publish-system'):
            q.add_argument('--apply',action='store_true');q.add_argument('--manifest-sha256',required=True);q.add_argument('--image-receipt-sha256',required=True)
    q=sub.add_parser('restart');q.add_argument('--release',type=Path,required=True);q.add_argument('--apply',action='store_true')
    a=p.parse_args();globals()[a.command.replace('-','_')](a)

if __name__=='__main__':main()
