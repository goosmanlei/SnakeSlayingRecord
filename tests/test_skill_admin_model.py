"""Instance models stay declarative and use the real live bindings."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
# Task test runner supplies the exact registered system through PYTHONPATH.
from review_desk.data_model import load as load_model
from review_desk.skill_flow import load as load_flow


class ModelTest(unittest.TestCase):
    def test_five_material_skills_have_concrete_independent_bindings(self):
        registry=json.loads((ROOT/'content/managed-method-registry.json').read_text())
        current={}
        for row in registry['records']:
            if row['version'] > current.get(row['object_id'],{}).get('version',0):
                current[row['object_id']]=row
        catalog={kind:[r for r in current.values() if r['payload']['format']=='managed-method-'+kind+'-v1']
                 for kind in ('skill','binding')}
        plans=next(s for s in load_flow(ROOT,catalog)['stages'] if s['id']=='plans')
        self.assertEqual([m['title'] for m in plans['methods']],['图像方案','音色方案','演唱方案','视频方案','字层方案'])
        self.assertEqual(len({m['object_id'] for m in plans['methods']}),5)
        rules=current['method.binding.media-plan']['payload']['rules']
        self.assertTrue(all(rule['when'] for rule in rules))
        voice=next(r for r in rules if r['when']=={'media_type':'audio','audio_type':'voice'})
        song=next(r for r in rules if r['when']=={'media_type':'audio','audio_type':'song'})
        self.assertNotEqual(voice['object_id'],song['object_id'])

    def test_instance_relations_cover_the_current_business_contract(self):
        value=load_model(ROOT)
        nodes={n['id']:n for d in value['diagrams'] for n in d['nodes']}
        self.assertIn('三者择一',nodes['requirement']['text'])
        self.assertIn('至少拥有一项真实素材需求',nodes['state']['text'])
        self.assertIn('以后改方案不改写候选',nodes['candidate']['text'])
        self.assertEqual(len(value['examples']),2)
        expected={'episode':'E','scene':'S','av-episode':'AE','av-scene':'AS','shot':'ASH',
                  'entity':'EN','state':'ST','requirement':'M','candidate':'MC','relation':'R','comment':'C'}
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

    def test_reader_is_shared_in_both_creation_loops_and_polish_is_comment_assistance(self):
        catalog={'skill':[{'object_id':'reader','payload':{'title':'独立读者'}},{'object_id':'polish','payload':{'title':'审阅意见措辞'}}],
                 'binding':[{'object_id':'b-reader','payload':{'work_type':'reader-review','rules':[{'object_id':'reader','when':{}}]}},
                            {'object_id':'b-polish','payload':{'work_type':'comment-polish','rules':[{'object_id':'polish','when':{}}]}}]}
        flow=load_flow(ROOT,catalog)
        for stage in flow['stages']:
            if stage['id'] in ('novel','screenplay'):
                self.assertEqual(stage['repeat']['methods'][0]['object_id'],'reader')
                self.assertIn('修订 → 再读',stage['repeat']['label'])
        feedback=next(b for b in flow['branches'] if b['id']=='feedback')
        self.assertEqual(feedback['methods'],[{'object_id':'polish','title':'评论 AI 润色'}])
        self.assertIn('用户采用',feedback['output'])
