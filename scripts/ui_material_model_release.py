#!/usr/bin/env python3
"""Prepare and apply the reviewed task-0009 database and service transition.

Preparation reads the live database only through SQLite's read-only backup API.
Apply/recover require the exact approved bundle digests. Neither action pushes,
merges the story repository, invokes task completion, nor restores a DB snapshot.
"""
import argparse
import json
from pathlib import Path
import sys
import time

import material_review_release as service

base = service.base
TASK = 'task-20261004-0009'
PACKAGE = 'production/ui-material-model/migration.json'


def model_api(m):
    system = str(Path(m['system_worktree']))
    if system not in sys.path:
        sys.path.insert(0, system)
    from review_desk.store import Store
    from review_desk import material_model
    return Store, material_model


def prepare(a):
    a.task = TASK
    service.prepare(a)
    root, m = service.load_bundle(a.bundle)
    story = Path(m['story_worktree'])
    Store, model = model_api(m)
    package = story / PACKAGE
    doc = model.load_migration(package)
    base.require(doc.get('system_head') == m['system_candidate'], 'migration system candidate differs')
    envelope = base.read(package)
    graph = (package.parent / envelope['content_source']).resolve()
    relative = graph.relative_to(story).as_posix()
    paths = [PACKAGE, relative, 'scripts/ui_material_model_release.py']
    hashes = {}
    for path in paths:
        raw = base.git_file(story, m['story_candidate'], path)
        base.require(raw == (story / path).read_bytes(), 'uncommitted model delivery file: ' + path)
        hashes[path] = base.sha(raw)
    # The raw formal archives remain readable until the final story integration.
    # Only the approved candidate contains the reference containers at that point.
    for item in doc['archives']:
        path = item.get('path', 'export/assets/' + item['file'])
        raw = base.git_file(story, m['story_candidate'], path)
        base.require(json.loads(raw) == item['container'], 'candidate archive differs: ' + path)
        hashes[path] = base.sha(raw)
    model_manifest = {'format': 'ui-material-model-release-v1', 'task': TASK,
                      'service_manifest_sha256': base.sha((root / 'manifest.json').read_bytes()),
                      'migration_id': doc['id'], 'package': PACKAGE, 'hashes': hashes,
                      'formal_archives_deferred_until_story_complete': True}
    base.save(root / 'model-manifest.json', model_manifest)
    print(json.dumps({'model_manifest_sha256': base.sha((root / 'model-manifest.json').read_bytes()),
                      'migration_id': doc['id'], 'formal_writes': False}))


def load(path):
    root, m = service.load_bundle(path)
    model_manifest = base.read(root / 'model-manifest.json')
    base.require(m['task'] == TASK and model_manifest['format'] == 'ui-material-model-release-v1', 'wrong model release')
    base.require(model_manifest['service_manifest_sha256'] == base.sha((root / 'manifest.json').read_bytes()), 'service manifest changed')
    story = Path(m['story_worktree'])
    for path, sha in model_manifest['hashes'].items():
        base.require(not Path(path).is_absolute() and '..' not in Path(path).parts, 'invalid model path')
        base.require(base.sha((story / path).read_bytes()) == sha, 'model delivery changed: ' + path)
    base.require(base.sha(Path(__file__).read_bytes()) == model_manifest['hashes']['scripts/ui_material_model_release.py'], 'release helper changed')
    Store, model = model_api(m)
    doc = model.load_migration(story / model_manifest['package'])
    base.require(doc['id'] == model_manifest['migration_id'], 'migration changed')
    return root, m, Store, model, doc


def shadow_validate(root, m, Store, model, doc):
    snapshot = root / 'run' / ('preflight-' + str(time.time_ns()) + '.sqlite3')
    live = Path(m['story_main']) / '.runtime/review.sqlite3'
    base.snapshot(live, snapshot)
    store = Store(snapshot)
    try:
        # Connection remains the isolated snapshot. This path is only the base
        # for read-only checks of current archive/media files before rollback.
        store.db_path = live
        return model.migrate(store, doc, validate_only=True,
                             system_head=m['system_candidate'], apply_archives=False)
    finally:
        store.db.close()


def preflight(a):
    root, m, Store, model, doc = load(a.bundle)
    service.preflight(a)
    result = shadow_validate(root, m, Store, model, doc)
    print(json.dumps({'preflight_only': True, 'migration': result, 'formal_writes': False}))


def authorized(a):
    base.require(a.apply, '--apply is required and does not replace user confirmation')
    root, m, Store, model, doc = load(a.bundle)
    for path, expected in [('manifest.json', a.manifest_sha256),
                           ('image.json', a.image_receipt_sha256),
                           ('model-manifest.json', a.model_manifest_sha256)]:
        base.require(base.sha((root / path).read_bytes()) == expected, 'approved digest differs: ' + path)
    return root, m, Store, model, doc


def restore_runtime(root, m, environment):
    previous = base.compose_definition(m, {'image': m['previous_app']['image']}, root)
    previous['services']['app']['volumes'] = [
        {'type': 'bind', 'source': v['Source'], 'target': v['Destination'], 'read_only': not v['RW']}
        for v in m['previous_app']['mounts']]
    path = root / 'compose.previous.json'
    base.save(path, previous)
    base.compose_up(m, [path], environment, release=True)
    base.wait_healthy()
    base.require(base.inspect(base.APP)['Image'] == m['previous_app']['image'], 'previous image not restored')


def apply(a):
    root, m, Store, model, doc = authorized(a)
    with base.publication_locks(m):
        image = service.checks(root, m, live=False)
        receipt = root / 'run'
        receipt.mkdir(exist_ok=True)
        release = Path(m['story_main']) / '.runtime/service-releases' / m['release_name']
        current = base.inspect(base.APP)
        expected = {v['target']: (v['source'], not v['read_only']) for v in base.compose_definition(m, image, release)['services']['app']['volumes']}
        actual = {v['Destination']: (v['Source'], v['RW']) for v in current['Mounts']}
        already_running = current['Image'] == image['image'] and actual == expected
        base.require(already_running or base.safe_container(current) == m['previous_app'], 'another service is active')
        proxy=base.safe_container(base.inspect(base.NGINX))
        expected_proxy={**m['previous_nginx'],'config_files':str(release/'compose.release.json')}
        base.require(proxy in (m['previous_nginx'],expected_proxy),'another proxy runtime is active')
        if not already_running:
            service.checks(root, m)
            shadow_validate(root, m, Store, model, doc)
        integration = json.loads(base.run([sys.executable, Path(m['story_worktree']) / 'scripts/integrate_generation_review_system.py',
                         '--plan', root / 'system-delivery.json', '--apply', '--receipt', receipt / 'system-integration.json']))
        base.require(integration['target_after'] == m['system_candidate'], 'system integration differs')
        environment = base.env_values(current)
        # Stop the old reader before changing physical payloads. The new reader
        # supports both raw JSON and references, including this deferred window.
        if not already_running:
            base.run([base.DOCKER, 'stop', '--time', '20', base.APP])
        store = None
        try:
            store = Store(Path(m['story_main']) / '.runtime/review.sqlite3')
            delta = model.migrate(store, doc, system_head=m['system_candidate'], apply_archives=False)
            checkpoint_row = store.db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
            checkpoint = dict(zip(('busy', 'log_frames', 'checkpointed_frames'), checkpoint_row))
            base.require(checkpoint['busy'] == 0, 'WAL checkpoint busy; migration recovery required')
            verification = model.verify(store)
            release = service.install(root, m, image)
            if not already_running:
                base.compose_up(m, [release / 'compose.release.json'], environment, release=True)
            running = base.verify_service(m, image, release)
        except BaseException:
            if store is None and already_running:
                raise
            # Exact inverse delta only; it refuses to erase any changed material.
            # If refusal occurs, leave the database intact for forward recovery.
            try:
                base.run([base.DOCKER, 'stop', '--time', '20', base.APP])
                inverse = model.rollback(store, doc, require_legacy=True) if store is not None else model.prepare_legacy_runtime(Path(m['story_main']) / '.runtime/review.sqlite3')
                restore_runtime(root, m, environment)
                base.save(receipt / ('recovery-' + str(time.time_ns()) + '.json'), inverse)
            except BaseException as recovery_error:
                base.save(receipt / ('recovery-blocked-' + str(time.time_ns()) + '.json'),
                          {'status': 'manual_forward_recovery_required', 'error_type': type(recovery_error).__name__,
                           'database_snapshot_restored': False, 'git_reset': False})
                raise RuntimeError('release failed and exact inverse recovery was refused; inspect runtime receipt; live DB was not replaced') from recovery_error
            raise
        finally:
            if store is not None:store.db.close()
        result = {'status': 'formal_browser_pending', 'migration': delta, 'checkpoint': checkpoint, 'verification': verification,
                  'service': running, 'release': str(release), 'archives': 'deferred_until_story_complete',
                  'push': False, 'complete_invoked': False}
        base.save(receipt / ('service-' + str(time.time_ns()) + '.json'), result)
        print(json.dumps(result, ensure_ascii=False))


def recover(a):
    root, m, Store, model, doc = authorized(a)
    # This command is a pre-completion recovery. After story integration, use a
    # separately reviewed forward/revert task so tracked archives stay coherent.
    base.require(base.git(m['story_main'], 'rev-parse', 'HEAD') == m['story_target'], 'story already integrated; prepare a new recovery task')
    with base.publication_locks(m):
        current = base.inspect(base.APP)
        image = base.read(root / 'image.json')
        release = Path(m['story_main']) / '.runtime/service-releases' / m['release_name']
        known_mounts=[{v['Destination']:(v['Source'],v['RW']) for v in m['previous_app']['mounts']},{v['target']:(v['source'],not v['read_only']) for v in base.compose_definition(m,image,release)['services']['app']['volumes']}]
        base.require(current['Image'] in (m['previous_app']['image'], image['image']) and {v['Destination']:(v['Source'],v['RW']) for v in current['Mounts']} in known_mounts, 'another runtime or mount is active')
        proxy=base.safe_container(base.inspect(base.NGINX));expected_proxy={**m['previous_nginx'],'config_files':str(release/'compose.release.json')};recovered_proxy={**m['previous_nginx'],'config_files':str(root/'compose.previous.json')}
        base.require(proxy in (m['previous_nginx'],expected_proxy,recovered_proxy),'another proxy runtime is active')
        environment = base.env_values(current)
        store = Store(Path(m['story_main']) / '.runtime/review.sqlite3')
        try:
            model.rollback(store, doc, validate_only=True, require_legacy=True)
            base.run([base.DOCKER, 'stop', '--time', '20', base.APP])
            result = model.rollback(store, doc, require_legacy=True)
            restore_runtime(root, m, environment)
        finally:
            store.db.close()
        print(json.dumps({'inverse_delta': result, 'runtime_recovered': True,
                          'database_snapshot_restored': False, 'git_reset': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    q = sub.add_parser('prepare')
    q.add_argument('--story-worktree', type=Path, default=Path(__file__).resolve().parents[1])
    q.add_argument('--system-worktree', type=Path, required=True)
    q.add_argument('--bundle', type=Path, required=True)
    for key in ('story-candidate', 'system-candidate', 'story-target', 'system-target'):
        q.add_argument('--' + key, required=True)
    for command in ('build', 'preflight', 'apply', 'recover'):
        q = sub.add_parser(command)
        q.add_argument('--bundle', type=Path, required=True)
        if command in ('apply', 'recover'):
            q.add_argument('--apply', action='store_true')
            for key in ('manifest-sha256', 'image-receipt-sha256', 'model-manifest-sha256'):
                q.add_argument('--' + key, required=True)
    a = parser.parse_args()
    if a.command == 'build':
        load(a.bundle)
        service.build(a)
    else:
        globals()[a.command](a)


if __name__ == '__main__':
    main()
