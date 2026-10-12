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
        self.assertEqual(nodes['shot']['title'],'镜头实体 · ASH')

    def test_flow_does_not_invent_skills_and_follows_new_bound_identity(self):
        catalog={'skill':[{'object_id':'method.skill.changed','payload':{'title':'New'}}],
                 'binding':[{'object_id':'method.binding.media-plan','payload':{'work_type':'media-plan','rules':[{'object_id':'method.skill.changed','when':{'media_type':'video'}}]}}]}
        flow=load_flow(ROOT,catalog)
        selected=[m for stage in flow['stages'] for m in stage['methods']]
        self.assertEqual(selected,[{'object_id':'method.skill.changed','title':'视频方案'}])
        self.assertFalse(flow['stages'][0]['methods'])
        self.assertEqual(len(flow['stages']),11)
