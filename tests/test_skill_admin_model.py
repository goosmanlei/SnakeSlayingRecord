"""Instance models stay declarative and use the real live bindings."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
# Task test runner supplies the exact registered system through PYTHONPATH.
from review_desk.data_model import load as load_model
from review_desk.skill_flow import load as load_flow


class ModelTest(unittest.TestCase):
    def test_instance_relations_cover_the_current_business_contract(self):
        value=load_model(ROOT)
        nodes={n['id']:n for d in value['diagrams'] for n in d['nodes']}
        self.assertIn('三者择一',nodes['requirement']['text'])
        self.assertIn('至少拥有一项真实素材需求',nodes['state']['text'])
        self.assertIn('以后改方案不改写候选',nodes['candidate']['text'])
        self.assertEqual(len(value['examples']),2)
        expected={'episode':'E','scene':'S','av-episode':'AE','av-scene':'AS','shot':'ASH',
                  'entity':'EN','state':'ST','requirement':'M','candidate':'MC','relation':'R','legacy':'MV','comment':'C'}
        for identity,prefix in expected.items():
            self.assertIn('· '+prefix,nodes[identity]['title'])
            self.assertTrue(nodes[identity]['version'])
            self.assertTrue(nodes[identity]['comments'])
        for identity in ('entity','state','shot','av-episode','av-scene','requirement','relation'):
            self.assertIn('仅当前内容',nodes[identity]['version'])
        for identity in ('episode','scene'):
            self.assertIn('随所属剧本版本',nodes[identity]['version'])
        self.assertIn('每个文件独立版本',nodes['file']['version'])
        self.assertIn('没有独立评论入口',nodes['execution']['comments'])

    def test_flow_does_not_invent_skills_and_follows_new_bound_identity(self):
        catalog={'skill':[{'object_id':'method.skill.changed','payload':{'title':'New'}}],
                 'binding':[{'object_id':'method.binding.media-plan','payload':{'work_type':'media-plan','rules':[{'object_id':'method.skill.changed','when':{'media_type':'video'}}]}}]}
        flow=load_flow(ROOT,catalog)
        selected=[m for stage in flow['stages'] for m in stage['methods']]
        self.assertEqual(selected,[{'object_id':'method.skill.changed','title':'视频方案'}])
        self.assertFalse(flow['stages'][0]['methods'])
        self.assertEqual(len(flow['stages']),11)
        stages={s['id']:s for s in flow['stages']}
        self.assertIn('剧本集 E',stages['screenplay']['output'])
        self.assertIn('角色、场景、道具、歌曲',stages['extraction']['output'])
        self.assertIn('实体状态 ST',stages['extraction']['output'])
        self.assertTrue(all(s['output'] for s in flow['stages']))
