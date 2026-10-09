#!/usr/bin/env python3
"""Prepare a consistent full VPS snapshot locally and drive its locked stages."""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import sqlite3
import subprocess
import tarfile

from vps_experience_remote import database, sha, portable_image

ROOT = Path(__file__).resolve().parent.parent


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def valid_identity(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', value):
        raise ValueError('publication identity must be a simple name')
    return value


def prepare(args):
    identity = valid_identity(args.publication)
    system = Path(args.desk).resolve(strict=True)
    formal = Path(args.formal).resolve(strict=True)
    output = ROOT/'.runtime/vps-experience'/identity
    if output.exists():
        raise ValueError('publication output already exists; verify or resume it rather than overwrite')
    config = json.loads((ROOT/'config/instance.json').read_text())
    commit = git(system, 'rev-parse', 'HEAD')
    if config['review_desk_commit'] != commit:
        raise ValueError('instance system pin differs from the system candidate')
    for path in [ROOT, system]:
        if git(path, 'status', '--porcelain', '--untracked-files=no'):
            raise ValueError('commit the candidate before preparing its package')
    output.mkdir(parents=True)
    instance = output/'instance'
    (instance/'.runtime').mkdir(parents=True)
    # Formal read and media copy share the existing project publication lock.
    # No formal database or export is written by this publisher.
    import fcntl
    with (formal/'.runtime/publication.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name in ['config', 'content']:
            shutil.copytree(ROOT/name, instance/name)
        shutil.copytree(formal/'export/assets', instance/'export/assets')
        source = sqlite3.connect((formal/'.runtime/review.sqlite3').as_uri()+'?mode=ro', uri=True)
        target = sqlite3.connect(instance/'.runtime/review.sqlite3')
        try:
            source.backup(target)
        finally:
            source.close(); target.close()
        snapshot = database(instance/'.runtime/review.sqlite3')
    image_tag = 'lijizhanshe-experience:'+identity
    build_args=[]
    if args.build_proxy:
        build_args=['--build-arg','HTTP_PROXY='+args.build_proxy,'--build-arg','HTTPS_PROXY='+args.build_proxy]
    run('docker', 'build', *build_args, '--platform', 'linux/amd64', '--label', 'org.leiguoguo.instance=lijizhanshe',
        '--label', 'org.opencontainers.image.revision='+commit, '-t', image_tag, str(system))
    image = json.loads(subprocess.check_output(['docker','image','inspect',image_tag], text=True))[0]
    if image['Architecture'] != 'amd64':
        raise ValueError('build did not produce amd64')
    image_archive = output/'image.tar.gz'
    with image_archive.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, compresslevel=1) as dst:
        process = subprocess.Popen(['docker', 'save', image_tag], stdout=subprocess.PIPE)
        try:
            shutil.copyfileobj(process.stdout, dst, 1024*1024)
        finally:
            process.stdout.close()
        if process.wait(): raise ValueError('docker save failed')
    image_id = portable_image(image_archive, image_tag, commit)
    manifest = {'format': 'lijizhanshe-experience-v1', 'publication_id': identity,
                'story_commit': git(ROOT,'rev-parse','HEAD'), 'desk_commit': commit,
                'formal_database': str(formal/'.runtime/review.sqlite3'),
                'image_id': image_id, 'build_image_id': image['Id'], 'image_tag': image_tag, 'architecture':'amd64',
                'database': snapshot, 'files': {}}
    for p in sorted(output.rglob('*')):
        if p.is_symlink(): raise ValueError('runtime input must not be a symlink')
        if p.is_file(): manifest['files'][str(p.relative_to(output))] = {'bytes':p.stat().st_size,'sha256':sha(p)}
    # Physical files and a complete DB include archive recipes without decoding
    # all historic metadata into additional copies in memory.
    manifest.pop('formal_database')
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    package = output/'bundle.tar'
    with tarfile.open(package, 'w') as archive:
        for rel in [*manifest['files'], 'manifest.json']:
            archive.add(output/rel, arcname=rel, recursive=False)
    receipt = {'publication_id':identity,'package_sha256':sha(package),'package_bytes':package.stat().st_size,
               'image_id':image_id,'build_image_id':image['Id'],'story_commit':manifest['story_commit'],'desk_commit':commit}
    (output/'prepare.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


def remote(command, *extra):
    # Use the configured SSH alias; no fixed host address or credentials.
    return run('ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','vps',
               shlex.join(['python3', 'lijizhanshe/deploy.py', command, *extra]))


def upload(args):
    identity = valid_identity(args.publication)
    output = ROOT/'.runtime/vps-experience'/identity
    receipt = json.loads((output/'prepare.json').read_text())
    if sha(output/'bundle.tar') != receipt['package_sha256']:
        raise ValueError('local package changed')
    run('ssh','-o','BatchMode=yes','vps', 'umask 077; mkdir -p lijizhanshe/incoming/'+identity)
    run('scp',str(ROOT/'scripts/vps_experience_remote.py'),'vps:lijizhanshe/deploy.py')
    run('scp',str(output/'bundle.tar'),'vps:lijizhanshe/incoming/'+identity+'/bundle.tar.part')
    run('ssh','-o','BatchMode=yes','vps','mv lijizhanshe/incoming/'+identity+'/bundle.tar.part lijizhanshe/incoming/'+identity+'/bundle.tar')
    remote('stage','--publication',identity,'--sha256',receipt['package_sha256'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare','upload','publish','maintain','replace','verify','open','cleanup','status'])
    p.add_argument('--publication'); p.add_argument('--desk'); p.add_argument('--formal'); p.add_argument('--build-proxy'); p.add_argument('--fail-after-clear',action='store_true')
    args = p.parse_args()
    if args.command == 'prepare': prepare(args)
    elif args.command == 'upload': upload(args)
    elif args.command == 'publish':
        upload(args)
        for step in ['maintain','replace','verify','open','cleanup']: remote(step)
    else:
        remote(args.command, *(['--fail-after-clear'] if args.fail_after_clear and args.command=='replace' else []))


if __name__ == '__main__': main()
