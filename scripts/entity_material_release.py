#!/usr/bin/env python3
"""Freeze, rehearse and apply the explicitly reviewed explanation cleanup.

prepare/build/preflight never write the formal database. apply requires three
reviewed package digests. Recovery resumes the same sanitized database and new
reader; it never restores old prose or overwrites business data with a snapshot.
Story integration/task completion remain the launcher's separate final step.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

import material_review_release as service
from entity_material_cleanup import compact

base = service.base
TASK = 'task-20261005-0002'
PACKAGE = 'production/entity-material/cleanup-plan.json'
NEW_TABLES = {'business_codes', 'business_candidates', 'business_comments',
              'relation_explanation_policy', 'relation_explanation_redactions',
              'relation_redacted_comments'}


def fingerprint(path):
    """Hash rows without retaining their original explanation text."""
    result = {}
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for name, sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
            quoted = '"' + name.replace('"', '""') + '"'
            hashes = sorted(base.sha(base.canonical(dict(row))) for row in db.execute('SELECT * FROM ' + quoted))
            result[name] = {'schema':base.sha(sql.encode()), 'count':len(hashes), 'rows_sha256':base.sha(base.canonical(hashes))}
    return result


def readers(path, directory=False):
    """Reject application readers; report only known read-only macOS VM handles.

    The platform VM caches files from the workspace. It must not be stopped to
    clean an unused task file. An unknown process or writable handle still stops
    deletion. This exception never permits removing a Git worktree or mount.
    """
    args=['lsof','-Fpcfa'] + (['+D',str(path)] if directory else [str(path)])
    result=subprocess.run(args,capture_output=True,text=True)
    base.require(result.returncode in (0,1), 'cannot inspect file readers')
    holders=[]
    for line in result.stdout.splitlines():
        if line.startswith('p'):holders.append({'pid':int(line[1:]),'access':[]})
        elif line.startswith('a') and holders:holders[-1]['access'].append(line[1:])
    expected='/System/Library/Frameworks/Virtualization.framework/Versions/A/XPCServices/com.apple.Virtualization.VirtualMachine.xpc/Contents/MacOS/com.apple.Virtualization.VirtualMachine'
    for holder in holders:
        process=subprocess.run(['ps','-p',str(holder['pid']),'-o','comm='],capture_output=True,text=True)
        base.require(process.returncode==0 and process.stdout.strip()==expected
                     and holder['access'] and set(holder['access'])=={'r'}, 'task resource still used by an application')
    return [{'pid':h['pid'],'read_only_handles':len(h['access'])} for h in holders]


def tree_hashes(path):
    values={};sidecars={'.runtime/'+name+suffix for name in ('review.sqlite3','generation-base.sqlite3') for suffix in ('-wal','-shm')}
    for p in sorted(path.rglob('*')):
        base.require(not p.is_symlink(), 'task cleanup tree contains a symbolic link')
        if p.is_file() and p.relative_to(path).as_posix() not in sidecars:
            values[p.relative_to(path).as_posix()]=base.sha(p.read_bytes())
    return values


def api(m):
    sys.path.insert(0, str(Path(m['system_worktree'])))
    from review_desk.store import Store
    from review_desk import relation_explanations as cleanup, material_model, bundle
    return Store, cleanup, material_model, bundle


def prepare(a):
    a.task = TASK
    service.prepare(a)
    root, m = service.load_bundle(a.bundle)
    story = Path(m['story_worktree'])
    hashes = {}
    for name in (PACKAGE, 'scripts/entity_material_release.py', 'scripts/entity_material_cleanup.py',
                 'export/objects.json', 'export/manifest.json', 'export/comments.json'):
        raw = base.git_file(story, m['story_candidate'], name)
        base.require(raw == (story / name).read_bytes(), 'candidate file differs: ' + name)
        hashes[name] = base.sha(raw)
    package = base.read(story / PACKAGE)
    for item in package['archives']:
        hashes[item['path']] = item['after_sha256']
        base.require(base.sha(base.git_file(story, m['story_candidate'], item['path'])) == item['after_sha256'], 'candidate archive differs')
    live = Path(m['story_main']) / '.runtime/review.sqlite3'
    baseline = story / '.runtime/entity-material/delivery/.runtime/generation-base.sqlite3'
    guard = fingerprint(baseline)
    base.require(fingerprint(live) == guard, 'formal data changed since delivery rehearsal; refresh the candidate')
    after = fingerprint(story / '.runtime/entity-material/delivery/.runtime/review.sqlite3')
    before_review = story / '.runtime/entity-material/relationship-before-review.json'
    own_old = [before_review, baseline, story / '.runtime/entity-material/review/.runtime/generation-base.sqlite3']
    own_old += [story / '.runtime/entity-material/review/.runtime/review.sqlite3']
    own_old += [story / '.runtime/entity-material/review/export/objects.json']
    old_copies = [{'path':p.relative_to(story).as_posix(), 'sha256':base.sha(p.read_bytes())}
                  for p in own_old if p.exists()]
    manifest = {'format':'entity-material-release-v1', 'task':TASK, 'hashes':hashes,
                'service_manifest_sha256':base.sha((root / 'manifest.json').read_bytes()),
                'before':guard, 'after':after, 'package':PACKAGE,
                'old_task_copies':old_copies,
                'retired_task_trees':[{ 'path':'.runtime/entity-material/'+name,
                                        'files':tree_hashes(story/'.runtime/entity-material'/name)}
                                       for name in ('review','delivery')],
                'archives':'candidate export enters main through task _complete after formal browser acceptance',
                'recovery':'resume sanitized database with this candidate reader; never restore old explanations'}
    if a.push_system:
        system = Path(m['system_worktree'])
        remote = base.git(system, 'config', '--get', 'branch.main.remote')
        ref = base.git(system, 'config', '--get', 'branch.main.merge')
        base.require(remote and remote != '.' and ref == 'refs/heads/main', 'unique system main upstream required')
        urls = base.git(system, 'remote', 'get-url', '--push', '--all', remote).splitlines()
        base.require(len(urls) == 1, 'one system push target required')
        head = remote_head(system, remote, ref)
        base.require(head == m['system_target'], 'system remote moved; prepare a new candidate')
        manifest['system_upstream'] = {'remote':remote, 'ref':ref, 'url':urls[0], 'expected':head}
    base.save(root / 'cleanup-manifest.json', manifest)
    print(json.dumps({'cleanup_manifest_sha256':base.sha((root / 'cleanup-manifest.json').read_bytes()),
                      'old_explanations':len(package['relationships']['revisions']), 'formal_writes':False}))


def load(a):
    root, m = service.load_bundle(a.bundle)
    c = base.read(root / 'cleanup-manifest.json')
    base.require(m['task'] == TASK and c['format'] == 'entity-material-release-v1', 'wrong cleanup release')
    base.require(c['service_manifest_sha256'] == base.sha((root / 'manifest.json').read_bytes()), 'service manifest differs')
    story = Path(m['story_worktree'])
    for name, sha in c['hashes'].items():
        base.require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe cleanup path')
        base.require(base.sha((story / name).read_bytes()) == sha, 'reviewed cleanup file changed: ' + name)
    base.require(base.sha(Path(__file__).read_bytes()) == c['hashes']['scripts/entity_material_release.py'], 'cleanup helper changed')
    return root, m, c, base.read(story / c['package'])


def validate_database(root, m, c, package):
    live = Path(m['story_main']) / '.runtime/review.sqlite3'
    base.require(fingerprint(live) == c['before'], 'formal data drifted; prepare and review a new candidate')
    path = root / 'run' / ('shadow-' + str(time.time_ns()) + '.sqlite3')
    base.snapshot(live, path)
    Store, cleanup, model, _ = api(m)
    store = Store(path)
    try:
        result = cleanup.apply(store, package['relationships'])
        compact(store)
        model.verify(store)
        base.require(fingerprint(path) == c['after'], 'rehearsed database differs from approved delivery')
        return result
    finally:
        store.close()
        for suffix in ('', '-wal', '-shm'):
            Path(str(path) + suffix).unlink(missing_ok=True)


def preflight(a):
    root, m, c, package = load(a)
    service.preflight(a)
    result = validate_database(root, m, c, package)
    for item in package['archives']:
        raw = Path(m['story_main']) / item['path']
        base.require(base.sha(raw.read_bytes()) == item['before_sha256'], 'formal archive drifted')
    print(json.dumps({'preflight_only':True, 'cleanup':result, 'formal_writes':False}))


def authorized(a):
    base.require(a.apply, '--apply is required and does not replace user confirmation')
    root, m, c, package = load(a)
    for name, sha in (('manifest.json', a.manifest_sha256), ('image.json', a.image_receipt_sha256),
                      ('cleanup-manifest.json', a.cleanup_manifest_sha256)):
        base.require(base.sha((root / name).read_bytes()) == sha, 'approved digest differs: ' + name)
    return root, m, c, package


def remote_head(system, remote, ref):
    lines = base.git(system, 'ls-remote', remote, ref).splitlines()
    base.require(len(lines) == 1 and lines[0].split()[1] == ref, 'ambiguous remote target')
    return lines[0].split()[0]


def publish_system(a):
    root, m, c, _ = authorized(a)
    upstream = c.get('system_upstream')
    base.require(upstream is not None, 'system push was not included in reviewed package')
    system = Path(m['system_worktree'])
    base.repo_check(system, m['system_main'], m['system_candidate'], m['system_target'], system=True)
    base.require(base.git(m['system_main'],'rev-parse','HEAD') == m['system_candidate'], 'integrate before push')
    base.require(base.git(system,'remote','get-url','--push','--all',upstream['remote']).splitlines() == [upstream['url']], 'push destination changed')
    head = remote_head(system,upstream['remote'],upstream['ref'])
    base.require(head in (upstream['expected'],m['system_candidate']), 'system upstream changed; do not overwrite')
    if head != m['system_candidate']:
        base.run(['git','-C',system,'push','--porcelain',
                  '--force-with-lease='+upstream['ref']+':'+head,upstream['remote'],
                  m['system_candidate']+':'+upstream['ref']])
    after = remote_head(system,upstream['remote'],upstream['ref'])
    base.require(after == m['system_candidate'], 'system remote verification failed')
    result = {'system_candidate':after,'remote':upstream['remote'],'ref':upstream['ref'],'push_verified':True}
    base.save(root/'run/system-push.json',result)
    print(json.dumps(result))


def purge(a):
    root,m,c,_ = authorized(a)
    base.require(base.git(m['story_main'],'rev-parse','HEAD') == m['story_candidate'], 'finish controlled story integration first')
    base.require(fingerprint(Path(m['story_main'])/'.runtime/review.sqlite3') == c['after'], 'formal cleanup not verified')
    base.require((root/'run/sanitized-recovery/export/manifest.json').is_file(), 'sanitized recovery missing')
    story = Path(m['story_worktree'])
    removed = [];cached=[]
    trees=[]
    for item in c['retired_task_trees']:
        path=story/item['path']
        base.require(path in (story/'.runtime/entity-material/review',story/'.runtime/entity-material/delivery'), 'unsafe retired task tree')
        if not path.exists():continue
        base.require(path.is_dir() and not path.is_symlink(), 'retired task tree changed')
        actual=tree_hashes(path)
        # The individual old copies may already have been purged on a retry.
        known_old={x['path'] for x in c['old_task_copies']}
        expected={name:sha for name,sha in item['files'].items()
                  if (path/name).exists() or (path/name).relative_to(story).as_posix() not in known_old}
        base.require(actual==expected, 'retired task tree changed; inspect before deleting')
        cached.extend(readers(path,directory=True));trees.append(path)
    containers=base.run([base.DOCKER,'ps','-aq']).splitlines()
    for container in containers:
        for mount in base.inspect(container)['Mounts']:
            source=Path(mount['Source'])
            base.require(not any(source==p or p in source.parents for p in trees), 'retired task tree is explicitly mounted')
    for item in c['old_task_copies']:
        path = story/item['path']
        base.require(path.resolve().is_relative_to(story/'.runtime/entity-material'), 'unsafe old copy path')
        if not path.exists():continue
        base.require(not path.is_symlink() and base.sha(path.read_bytes()) == item['sha256'], 'old task copy changed')
        # Stop the task preview first. Never stop a shared platform VM cache.
        cached.extend(readers(path))
    for item in c['old_task_copies']:
        path = story/item['path']
        for suffix in ('','-wal','-shm') if path.suffix == '.sqlite3' else ('',):
            target = Path(str(path)+suffix)
            if target.exists():target.unlink();removed.append(str(target.relative_to(story)))
    retired=[]
    for path in trees:
        count=sum(p.is_file() for p in path.rglob('*'))
        shutil.rmtree(path)
        retired.append({'path':path.relative_to(story).as_posix(),'files':count,'absent':not path.exists()})
    result = {'removed_files':removed,'count':len(removed),'all_listed_old_copies_absent':all(not (story/x['path']).exists() for x in c['old_task_copies']),
              'retired_task_trees':retired,'total_removed_files':len(removed)+sum(t['files'] for t in retired),
              'read_only_platform_handles':cached,'shared_vm_stopped':False}
    base.save(root/'run/old-task-copies-purged.json',result)
    print(json.dumps(result))


def apply(a):
    root, m, c, package = authorized(a)
    with base.publication_locks(m):
        image = service.checks(root, m, live=False)
        live = Path(m['story_main']) / '.runtime/review.sqlite3'
        current = base.inspect(base.APP)
        release = Path(m['story_main']) / '.runtime/service-releases' / m['release_name']
        expected = {v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}
        actual = {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']}
        candidate_running = current['Image'] == image['image'] and actual == expected
        base.require(candidate_running or base.safe_container(current) == m['previous_app'], 'another formal service is active')
        proxy = base.safe_container(base.inspect(base.NGINX))
        base.require(proxy in (m['previous_nginx'], {**m['previous_nginx'],'config_files':str(release / 'compose.release.json')}), 'another proxy is active')
        before = fingerprint(live)
        if before != c['after']:
            service.checks(root, m)
            validate_database(root, m, c, package)
        integration = json.loads(base.run([sys.executable, Path(m['story_worktree']) / 'scripts/integrate_generation_review_system.py',
            '--plan', root / 'system-delivery.json', '--apply', '--receipt', root / 'run/system-integration.json']))
        base.require(integration['target_after'] == m['system_candidate'], 'system integration differs')
        environment = base.env_values(current)
        base.run([base.DOCKER, 'stop', '--time', '20', base.APP])
        Store, cleanup, model, bundle = api(m)
        store = None
        try:
            # Stop the reader, then recheck inside the shared publication window.
            base.require(fingerprint(live) in (c['before'], c['after']), 'formal data changed before cleanup; no cleanup applied')
            store = Store(live)
            result = cleanup.apply(store, package['relationships'])
            compact(store)
            verification = model.verify(store)
            base.require(fingerprint(live) == c['after'], 'formal cleanup differs from approved rehearsal')
            # A sanitized recovery bundle is the only new recovery baseline.
            recovery = root / 'run/sanitized-recovery'
            recovered = recovery / 'export'
            if not recovered.exists():
                for name in ('config','content'):
                    shutil.copytree(Path(m['story_main']) / name, recovery / name)
                (recovery / 'config/instance.json').write_bytes((root / 'instance/config/instance.json').read_bytes())
                # Immutable originals share bytes; JSON archive containers are
                # replaced atomically by export, without changing those links.
                shutil.copytree(Path(m['story_main']) / 'export/assets', recovered / 'assets', copy_function=os.link)
            manifest = bundle.export(store, recovered)
            base.require(manifest['schema_version'] == 7, 'wrong recovery schema')
            base.require(fingerprint(live) == c['after'], 'export altered approved business data')
            release = service.install(root, m, image)
            base.compose_up(m, [release / 'compose.release.json'], environment, release=True)
            running = base.verify_service(m, image, release)
        except BaseException as error:
            # Do not restart an old reader over redacted payloads. A stopped
            # app is an explicit recovery state; apply can resume this bundle.
            base.save(root / 'run' / ('forward-recovery-' + str(time.time_ns()) + '.json'),
                {'status':'resume_approved_candidate', 'error_type':type(error).__name__,
                 'database_snapshot_restored':False, 'old_explanations_restored':False})
            raise
        finally:
            if store is not None: store.close()
        result = {'status':'formal_browser_pending', 'cleanup':result, 'verification':verification,
                  'service':running, 'archives':'deferred_until_story_complete',
                  'recovery_export':'run/sanitized-recovery/export', 'push':False, 'complete_invoked':False}
        base.save(root / 'run' / ('applied-' + str(time.time_ns()) + '.json'), result)
        print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    q = sub.add_parser('prepare')
    q.add_argument('--story-worktree', type=Path, default=Path(__file__).resolve().parents[1])
    q.add_argument('--system-worktree', type=Path, required=True)
    q.add_argument('--bundle', type=Path, required=True)
    q.add_argument('--push-system', action='store_true')
    for name in ('story-candidate','system-candidate','story-target','system-target'):
        q.add_argument('--' + name, required=True)
    for command in ('build','preflight','apply','publish-system','purge'):
        q = sub.add_parser(command)
        q.add_argument('--bundle', type=Path, required=True)
        if command in ('apply','publish-system','purge'):
            q.add_argument('--apply', action='store_true')
            for name in ('manifest-sha256','image-receipt-sha256','cleanup-manifest-sha256'):
                q.add_argument('--' + name, required=True)
    a = parser.parse_args()
    if a.command == 'build':
        load(a)
        service.build(a)
    else:
        globals()[a.command.replace('-','_')](a)


if __name__ == '__main__':
    main()
