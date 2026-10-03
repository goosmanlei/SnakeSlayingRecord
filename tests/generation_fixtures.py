from pathlib import Path
import subprocess


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()


def make_worktree(directory):
    base = Path(directory).resolve()
    main = base / 'main'
    subprocess.run(['git', 'init', '-qb', 'main', str(main)], check=True, capture_output=True)
    git(main, 'config', 'user.name', 'Generation Test')
    git(main, 'config', 'user.email', 'test@example.invalid')
    (main / '.gitignore').write_text('.runtime/\n')
    git(main, 'add', '.gitignore')
    git(main, 'commit', '-qm', 'baseline')
    worktree = base / 'task'
    git(main, 'worktree', 'add', '-qb', 'generation', str(worktree))
    return main, worktree
