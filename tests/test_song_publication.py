import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from review_desk.store import Store
from scripts.publish_song_stage import KEYS, apply, copy_media


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
        source.mkdir(); target.mkdir()
        digest = hashlib.sha256(b'original').hexdigest()
        name = digest + '.mp3'
        (source / name).write_bytes(b'original')
        (target / name).write_bytes(b'different-existing-original')
        plan = {'media': [dict(file=name, bytes=8, sha256=digest)]}
        with self.assertRaisesRegex(ValueError, 'existing file conflict'):
            copy_media(plan, source, target)
        self.assertEqual((target / name).read_bytes(), b'different-existing-original')


if __name__ == '__main__':
    unittest.main()
