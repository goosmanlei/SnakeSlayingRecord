import tempfile
import unittest
from pathlib import Path
from scripts.screenplay_writing import Run


class ScreenplayWritingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run = Run(Path(self.temp.name)/'work.sqlite3')

    def tearDown(self):
        self.run.close()
        self.temp.cleanup()

    def scene(self, id):
        return dict(id=id, episode=1, episode_title='一', heading='门口', location='家', time='日',
                    seconds=100, chapters=['novel-c01'], design='说明人物选择', text='她把门打开。')

    def adopt(self, id):
        self.run.save(self.scene(id)); self.run.read()
        self.run.accept({'assessment':'动作可辨', 'continuity':'门已打开'})

    def test_candidate_must_be_read_and_finished_before_next_scene(self):
        self.run.save(self.scene('a'))
        with self.assertRaises(ValueError):
            self.run.accept({'assessment':'没有读过', 'continuity':'未知'})
        with self.assertRaises(ValueError):
            self.run.save(self.scene('b'))
        self.run.read()
        self.run.accept({'assessment':'回读完成', 'continuity':'门已打开'})
        self.adopt('b')
        self.assertEqual([s['id'] for s in self.run.current()[1]['scenes']], ['a','b'])

    def test_recovery_and_revision_preserve_prior_checkpoints(self):
        self.adopt('a'); old = self.run.current()[0]
        changed = {**self.scene('a'), 'text':'她停了一下，把门打开。'}
        self.run.save(changed)
        self.run.close(); self.run = Run(Path(self.temp.name)/'work.sqlite3')
        self.assertEqual(self.run.read(), changed)
        self.run.accept({'assessment':'停顿有依据', 'continuity':'门已打开'})
        self.assertNotEqual(self.run.current()[0], old)
        self.assertIn('她把门打开', self.run.db.execute('SELECT payload FROM checkpoints WHERE hash=?',(old,)).fetchone()[0])

    def test_arrangement_requires_complete_explicit_scope_and_final_review(self):
        self.adopt('a'); self.adopt('b')
        with self.assertRaises(ValueError):
            self.run.arrange({'order':['a'], 'reason':'不能静默丢场'})
        self.run.arrange({'order':['b','a'], 'episodes':{'a':[2,'二']}, 'reason':'调整断点'})
        head,state=self.run.current()
        with self.assertRaises(ValueError):
            self.run.finalize({'revision':head,'scene_ids':['a'],'assessment':'漏读'})
        self.run.finalize({'revision':head,'scene_ids':['b','a'],'assessment':'按新顺序通读'})
        self.assertTrue(self.run.current()[1]['reviewed'])


if __name__ == '__main__':
    unittest.main()
