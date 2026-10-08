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


class PublicationFixture:
    """Small synthetic revision and comment delta; no retired publication format."""

    def __init__(self):
        import tempfile
        from review_desk.store import Store
        self.temp = tempfile.TemporaryDirectory(prefix='publication-fixture-')
        self.store = Store(Path(self.temp.name) / 'review.sqlite3')
        self.db = self.store.db
        with self.db:
            for oid, rid in [('entity-boat-song', 'old'), ('entity-unrelated', 'other')]:
                self.insert('objects', dict(id=oid, kind='ENTITY', current_revision=rid,
                            version=1, created_at='before', updated_at='before'))
                self.insert('revisions', dict(id=rid, object_id=oid, version=1,
                            payload='{}', created_at='before'))
            self.insert('comments', self.comment('history', 'entity-unrelated', 'other'))
            self.insert('comment_events', dict(id=1, comment_id='history', action='created',
                        body='old opinion', at='before'))

    def insert(self, table, row):
        self.db.execute('INSERT INTO ' + table + ' (' + ','.join(row) + ') VALUES (' +
                        ','.join('?' for _ in row) + ')', tuple(row.values()))

    def comment(self, cid, oid, rid):
        return dict(id=cid, source_id=None, target_object_id=oid, target_revision_id=rid,
                    anchor='{}', body='actual feedback', status='open', version=1,
                    created_at='before', updated_at='before')

    def advance(self):
        with self.db:
            self.insert('revisions', dict(id='new', object_id='entity-boat-song', version=2,
                        payload='{}', created_at='after'))
            self.db.execute("UPDATE objects SET current_revision='new',version=2,updated_at='after' WHERE id='entity-boat-song'")
            self.insert('dependencies', dict(from_revision='new', to_revision='old', role='source'))
            self.insert('comments', self.comment('new-opinion', 'entity-boat-song', 'new'))
            self.insert('comment_events', dict(id=2, comment_id='new-opinion', action='created',
                        body='still wrong', at='after'))

    def close(self):
        self.store.close()
        self.temp.cleanup()
