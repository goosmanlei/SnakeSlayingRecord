import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from review_desk.store import Store
from scripts.publish_song_stage import KEYS, apply
from scripts.publish_generation import copy_media
from generation_fixtures import make_worktree


class SongPublicationTest(unittest.TestCase):
    """Exercise data loss and concurrency boundaries, never the formal instance."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='song-publication-')
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'review.sqlite3')
        self.db = self.store.db
        self.db.execute('PRAGMA foreign_keys=ON')
        self.head = dict(id='entity-boat-song', kind='ENTITY', current_revision='old',
                         version=1, created_at='before', updated_at='before')
        self.reference = dict(id='old', object_id='entity-boat-song', version=1,
                              payload='{}', created_at='before')
        with self.db:
            self.insert('objects', self.head)
            self.insert('revisions', self.reference)
            self.insert('objects', dict(id='entity-unrelated', kind='ENTITY',
                        current_revision='other', version=1,
                        created_at='before', updated_at='before'))
            self.insert('revisions', dict(id='other', object_id='entity-unrelated',
                        version=1, payload='{}', created_at='before'))
            self.insert('comments', self.comment('history', 'entity-unrelated', 'other'))
            self.insert('comment_events', dict(id=1, comment_id='history',
                        action='created', body='old opinion', at='before'))
        self.plan = dict(format='songs-current-stage-publication-v1',
            scope=['entity-boat-song'], expected_heads={'entity-boat-song': self.head},
            expected_references={'old': self.reference},
            objects=[dict(self.head, current_revision='new', version=2, updated_at='after')],
            insert={t: [] for t in KEYS if t != 'objects'}, comment_events=[], media=[])
        self.plan['insert']['revisions'] = [dict(self.reference, id='new', version=2,
                                               created_at='after')]
        self.plan['insert']['dependencies'] = [dict(from_revision='new',
                                                   to_revision='old', role='source')]
        self.plan['insert']['comments'] = [self.comment('new-opinion', 'entity-boat-song', 'new')]
        # The isolated source event ID collides with the unrelated formal event.
        self.plan['comment_events'] = [dict(id=1, comment_id='new-opinion',
                                           action='created', body='still wrong', at='after')]

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def insert(self, table, row):
        self.db.execute('INSERT INTO ' + table + ' (' + ','.join(row) + ') VALUES (' +
                        ','.join('?' for _ in row) + ')', tuple(row.values()))

    def comment(self, cid, oid, rid):
        return dict(id=cid, source_id=None, target_object_id=oid,
                    target_revision_id=rid, anchor=json.dumps({}), body='actual feedback',
                    status='open', version=1, created_at='before', updated_at='before')

    def dump(self):
        return '\n'.join(self.db.iterdump())

    def test_preserves_unrelated_rows_and_allocates_event_ids(self):
        old = dict(self.db.execute("SELECT * FROM objects WHERE id='entity-unrelated'").fetchone())
        result = apply(self.db, self.plan)
        self.assertEqual(result['comment_events'][0]['published_id'], 2)
        self.assertEqual(self.db.execute('SELECT comment_id FROM comment_events WHERE id=1').fetchone()[0], 'history')
        self.assertEqual(dict(self.db.execute("SELECT * FROM objects WHERE id='entity-unrelated'").fetchone()), old)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 3)
        self.assertFalse(result['audio_quality_accepted'])

    def test_changed_head_refuses_before_mutation(self):
        with self.db:
            self.db.execute("UPDATE objects SET updated_at='concurrent' WHERE id='entity-boat-song'")
        before = self.dump()
        with self.assertRaisesRegex(ValueError, 'head changed'):
            apply(self.db, self.plan)
        self.assertEqual(self.dump(), before)

    def test_failed_dependency_rolls_back_head_revision_and_comments(self):
        plan = copy.deepcopy(self.plan)
        plan['insert']['dependencies'][0]['to_revision'] = 'missing'
        before = self.dump()
        with self.assertRaises((sqlite3.IntegrityError, ValueError)):
            apply(self.db, plan)
        self.assertEqual(self.dump(), before)

    def test_repeated_apply_does_not_duplicate_history(self):
        apply(self.db, self.plan)
        before = self.dump()
        self.assertTrue(apply(self.db, self.plan)['already_published'])
        self.assertEqual(self.dump(), before)

    def test_non_song_scope_refused(self):
        plan = copy.deepcopy(self.plan)
        plan['scope'].append('entity-unrelated')
        before = self.dump()
        with self.assertRaises(ValueError):
            apply(self.db, plan)
        self.assertEqual(self.dump(), before)

    def test_existing_original_never_overwritten(self):
        source, target = self.root / 'source', self.root / 'target'
        (source / 'export/assets').mkdir(parents=True); (target / 'export/assets').mkdir(parents=True)
        digest = hashlib.sha256(b'original').hexdigest()
        name = digest + '.mp3'
        (source / 'export/assets' / name).write_bytes(b'original')
        (target / 'export/assets' / name).write_bytes(b'different-existing-original')
        plan = {'media': [dict(file=name, bytes=8, sha256=digest)]}
        with self.assertRaisesRegex(ValueError, 'existing original differs'):
            copy_media(source, target, plan['media'])
        self.assertEqual((target / 'export/assets' / name).read_bytes(), b'different-existing-original')

    def test_real_cli_preflight_apply_and_retry_preserve_history(self):
        main, task = make_worktree(self.root / 'workspace')
        target = task / '.runtime/target'
        database = target / '.runtime/review.sqlite3'
        database.parent.mkdir(parents=True)
        with sqlite3.connect(database) as destination:
            self.db.backup(destination)
        package = task / 'production/song-stage/publication-plan.json'
        package.parent.mkdir(parents=True)
        package.write_text(json.dumps(self.plan))
        (task / 'export/assets').mkdir(parents=True)
        script = Path(__file__).resolve().parents[1] / 'scripts/publish_song_stage.py'

        def cli(name, apply=False):
            command = [sys.executable, str(script), '--workspace', str(task),
                       '--instance', '.runtime/target', '--run-name', name]
            if apply:
                command.append('--apply')
            result = subprocess.run(command, cwd=self.root, capture_output=True,
                                    text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        def dump():
            with sqlite3.connect(database) as db:
                return '\n'.join(db.iterdump())

        before = dump()
        self.assertFalse(cli('preflight')['applied'])
        self.assertEqual(dump(), before)
        applied = cli('apply', apply=True)
        self.assertTrue(applied['applied'])
        self.assertEqual(applied['scope']['comment_events'][0]['published_id'], 2)
        with sqlite3.connect(database) as db:
            self.assertEqual(db.execute("SELECT body FROM comment_events WHERE id=1").fetchone()[0],
                             'old opinion')
            self.assertEqual(db.execute("SELECT current_revision FROM objects WHERE id='entity-unrelated'").fetchone()[0],
                             'other')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 3)
        after = dump()
        self.assertTrue(cli('retry', apply=True)['already_published'])
        self.assertEqual(dump(), after)
        self.assertFalse((main / 'export').exists())


if __name__ == '__main__':
    unittest.main()
