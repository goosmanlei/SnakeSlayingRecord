import tempfile
import unittest
from pathlib import Path
from scripts.screenplay_writing import Run


class ScreenplayWritingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        from method_client_fixture import Client
        self.client = Client()
        self.run = Run(Path(self.temp.name)/'work.sqlite3', self.client)
        self.number = 0

    def tearDown(self):
        self.run.close()
        self.temp.cleanup()

    def scene(self, id):
        return dict(id=id, episode=1, episode_title='一', heading='门口', location='家', time='日',
                    seconds=100, chapters=['novel-c01'], design='说明人物选择', text='她把门打开。')

    def adopt(self, id):
        self.begin(id)
        self.run.save(self.scene(id)); self.run.read()
        self.run.accept({'assessment':'动作可辨', 'continuity':'门已打开'})

    def begin(self, id):
        self.number += 1
        spec = {'step_id': 'step-' + str(self.number), 'scene_id': id,
                'base_revision': self.run.context()['revision'], 'context': {'source': '她回到家，在门口停下。'}}
        self.run.begin(spec)
        return spec

    def test_candidate_must_be_read_and_finished_before_next_scene(self):
        self.begin('a')
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
        spec = self.begin('a')
        self.run.save(changed)
        self.run.close(); self.run = Run(Path(self.temp.name)/'work.sqlite3', self.client)
        original = self.run.begin(spec)
        self.assertEqual(original['payload']['inputs']['context']['spec'], spec)
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

    def test_missing_method_wrong_scene_and_changed_restore_cannot_bypass(self):
        with self.assertRaisesRegex(ValueError, '缺少方法'):
            self.run.save(self.scene('a'))
        spec = self.begin('a')
        with self.assertRaisesRegex(ValueError, '不一致'):
            self.run.save(self.scene('b'))
        with self.assertRaisesRegex(ValueError, 'different inputs'):
            self.run.begin({**spec, 'context': {'source': 'changed'}})
        self.run.save(self.scene('a'))
        self.run.close(); self.run = Run(Path(self.temp.name)/'work.sqlite3')
        self.assertEqual(self.run.read()['id'], 'a')
        with self.assertRaisesRegex(ValueError, '准确方法'):
            self.run.accept({'assessment': '动作可辨', 'continuity': '门开着'})
        self.assertEqual(self.run.current()[1]['scenes'], [])

    def test_legacy_candidate_readable_but_method_history_not_invented(self):
        import json
        with self.run.db:
            self.run.db.execute('INSERT INTO pending VALUES (1,?,?,NULL)', (self.run.current()[0], json.dumps(self.scene('old'))))
        self.assertIsNone(self.run.context()['method_execution'])
        self.run.read()
        with self.assertRaisesRegex(ValueError, '缺少方法'):
            self.run.accept({'assessment': '历史阅读', 'continuity': '保持未知'})
        self.run.reject('原候选保留在原来源；新步骤重新修订')
        self.begin('new')

    def test_lost_prepare_response_reuses_persisted_run_identity(self):
        original = self.client.prepare
        calls = []
        def interrupted(request):
            calls.append(request['run_id'])
            result = original(request)
            if len(calls) == 1:
                raise OSError('response lost after remote commit')
            return result
        self.client.prepare = interrupted
        spec = {'step_id': 'recover', 'scene_id': 'a', 'base_revision': self.run.context()['revision'],
                'context': {'source': '她走到门口。'}}
        with self.assertRaises(OSError):
            self.run.begin(spec)
        self.run.close(); self.run = Run(Path(self.temp.name)/'work.sqlite3', self.client)
        self.run.begin(spec)
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(len(self.client.executions), 1)


if __name__ == '__main__':
    unittest.main()
