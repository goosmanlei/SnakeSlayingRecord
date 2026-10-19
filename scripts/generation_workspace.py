"""Filesystem and Git boundaries shared by this story's generation tools."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


try:
    from .material_model_io import logical_file_hash, logical_size
except ImportError:
    from material_model_io import logical_file_hash, logical_size


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError('Git validation failed: ' + result.stderr.decode().strip())
    return result.stdout


def primary_root(workspace):
    entries = git(workspace, 'worktree', 'list', '--porcelain', '-z').split(b'\0')
    return Path(os.fsdecode(next(x[9:] for x in entries if x.startswith(b'worktree ')))).resolve()


def workspace_root(path):
    root = Path(path).resolve(strict=True)
    actual = Path(os.fsdecode(git(root, 'rev-parse', '--show-toplevel')).strip()).resolve()
    if root != actual or root == primary_root(root):
        raise ValueError('generation requires an independent Git worktree, not the main directory')
    branch = git(root, 'symbolic-ref', '--quiet', 'HEAD').decode().strip()
    if branch == 'refs/heads/main':
        raise ValueError('generation cannot write the main branch')
    return root


def contained(root, path):
    """Check lexical and resolved containment, including every symlink component."""
    root = Path(root).resolve(strict=True)
    path = Path(os.path.abspath(path if Path(path).is_absolute() else root / path))
    # macOS /var and /tmp aliases may precede the worktree. Normalize that
    # prefix only; links inside the workspace still fail the checks below.
    for ancestor in reversed((path, *path.parents)):
        if ancestor.resolve() == root:
            path = root / path.relative_to(ancestor)
            break
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        raise ValueError('output must stay inside the selected worktree') from None
    current = root
    for part in parts:
        if part == '.git':
            raise ValueError('output cannot write Git metadata')
        current /= part
        if current.is_symlink():
            raise ValueError('output path cannot contain a symlink')
    if not path.resolve().is_relative_to(root):
        raise ValueError('output escapes the selected worktree')
    return path


def generation_root(path):
    root = workspace_root(path)
    # These are shared write boundaries, not just the last output filename.
    for relative in ('.runtime', 'export/assets', 'production/requests', 'production/receipts'):
        contained(root, relative)
    return root


def isolated_instance(root, path):
    root = generation_root(root)
    instance = contained(root, path)
    runtime = root / '.runtime'
    if instance == runtime or not instance.is_relative_to(runtime):
        raise ValueError('review instance must be below this worktree .runtime')
    for relative in ('.runtime/review.sqlite3', 'export/assets', 'config', 'content'):
        contained(root, instance / relative)
    return instance


def publication_target(root, target):
    root = generation_root(root)
    target = Path(target)
    target = (target if target.is_absolute() else root / target).resolve(strict=True)
    formal = target == primary_root(root)
    if not formal:
        isolated_instance(root, target)
    contained(target, '.runtime/review.sqlite3')
    contained(target, '.runtime/publication.lock')
    return target, formal


def media_entries(entries):
    found = {}
    for entry in entries:
        name, digest = entry['file'], entry['sha256']
        if not re.fullmatch(r'[a-f0-9]{64}\.[a-z0-9]+', name) or name.split('.')[0] != digest:
            raise ValueError('media must use its SHA-256 content-addressed basename')
        if name in found and found[name] != digest:
            raise ValueError('conflicting media hashes')
        found[name] = digest
    return found


def verify_media(root, entries):
    entries = list(entries)
    for name, digest in media_entries(entries).items():
        from review_desk.production_media import export_asset_path
        path = export_asset_path(root, name)
        if not path.is_file() or logical_file_hash(path) != digest:
            raise ValueError('missing or changed original: ' + name)
    for entry in entries:
        if (type(entry.get('bytes')) is not int or entry['bytes'] < 0
                or logical_size(export_asset_path(root, entry['file'])) != entry['bytes']):
            raise ValueError('original byte count differs: ' + entry['file'])


def matches_committed_file(path, blob):
    """Check hydrated LFS files and ordinary Git files with bounded reads."""
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        pointer = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\n'
                               rb'oid sha256:([a-f0-9]{64})\nsize ([0-9]+)\n', blob)
        if not pointer:
            raise ValueError('invalid committed Git LFS pointer')
        expected_hash, expected_size = pointer[1].decode(), int(pointer[2])
    else:
        expected_hash, expected_size = hashlib.sha256(blob).hexdigest(), len(blob)
    if path.stat().st_size != expected_size:
        return False
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest() == expected_hash


def verify_integrated(root, target, commit, package, entries):
    """Formal publication consumes merged files; it never copies missing media."""
    root = generation_root(root)
    target, formal = publication_target(root, target)
    if not formal:
        raise ValueError('integrated publication requires the primary worktree')
    if not commit or not re.fullmatch(r'[a-f0-9]{40,64}', commit):
        raise ValueError('--source-commit requires the full committed revision')
    if git(target, 'symbolic-ref', '--quiet', 'HEAD').decode().strip() != 'refs/heads/main':
        raise ValueError('formal target must have main checked out')
    if git(target, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('formal worktree must be clean before publication')
    result = subprocess.run(['git', '-C', str(target), 'merge-base', '--is-ancestor', commit, 'HEAD'])
    if result.returncode:
        raise ValueError('source commit has not been integrated into main')
    relative = contained(root, package).relative_to(root).as_posix()
    from review_desk import resources
    cloud = resources.settings(root)
    if cloud:
        try:from .check_resource_git import check
        except ImportError:from check_resource_git import check
        check(root, revision=commit)
        # Exact metadata/code must be integrated. Cloud bytes are verified by
        # version and SHA during preflight, never by presence in a Git tree.
        paths = ['config/resource-storage.json', 'config/resource-catalog.json']
        for logical in [relative, *('export/assets/'+name for name in media_entries(entries))]:
            try:
                spec = resources.descriptor(root, logical)
            except FileNotFoundError:
                if logical != relative: raise
                paths.append(logical)
                continue
            other = resources.descriptor(target, logical)
            if any(spec[k] != other[k] for k in ('sha256','bytes','key','version_id')):
                raise ValueError('integrated resource identity differs: '+logical)
            resources.verify_remote(target, other)
            resources.materialize(target, logical)
    else:
        paths = [relative, *('export/assets/' + name for name in media_entries(entries))]
    for name in paths:
        expected = git(root, 'show', commit + ':' + name)
        source = contained(root, name)
        destination = contained(target, name)
        if (not source.is_file() or not destination.is_file()
                or git(target, 'show', 'HEAD:' + name) != expected
                or not matches_committed_file(source, expected)
                or not matches_committed_file(destination, expected)):
            raise ValueError('publication file differs from integrated commit: ' + name)
    verify_media(target, entries)
    return commit


def write_json(root, path, value, *, replace=False):
    target = contained(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    relative=target.relative_to(root).as_posix()
    if not relative.startswith('.runtime/') and len(data.encode())>1024*1024 and (root/'config/resource-storage.json').is_file():
        import tempfile
        try:
            from .material_model_io import backend
        except ImportError:
            from material_model_io import backend
        resources=backend('resources')
        with tempfile.TemporaryDirectory(prefix='publication-',dir=root/'.runtime') as folder:
            source=Path(folder)/'package.json';source.write_text(data)
            spec=resources.publish_file(root,relative,source)
        resources.freeze_catalog(root,root/'config/resource-catalog.json')
        data=json.dumps({'format':'project-resource-reference-v1','path':relative,
                         'sha256':spec['sha256'],'bytes':spec['bytes']},ensure_ascii=False,indent=2)+'\n'
    if not replace:
        with target.open('x') as stream:
            stream.write(data)
    else:
        temporary = contained(root, target.with_name(target.name + '.tmp'))
        with temporary.open('x') as stream:
            stream.write(data)
        temporary.replace(target)
