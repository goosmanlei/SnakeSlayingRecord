import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native_audio_workflow import obsolete
from seedance_preparation import validate_reference_budget

class NativeAudioTest(unittest.TestCase):
    def test_only_templates_survive_cleanup(self):
        row=lambda oid,slot,kind='REQUIREMENT':{'object_id':oid,'kind':kind,'payload':{'media_type':'audio','slot':slot}}
        self.assertTrue(obsolete(row('need-form-a-e01-line-001','e01-line-001')))
        self.assertTrue(obsolete(row('need-shot-e01-001-voice-01','voice-01')))
        self.assertTrue(obsolete(row('need-form-stage-drum-audible-overall','overall')))
        self.assertFalse(obsolete(row('need-form-boat-song-short-overall','overall')))
        self.assertFalse(obsolete(row('need-form-a-voice','voice')))
        self.assertFalse(obsolete(row('asset-a','voice-01','ASSET')))

    def test_reference_budget_is_not_full_master_length_or_line_count(self):
        clip=lambda a,b:{'range':{'start_seconds':a,'end_seconds':b}}
        validate_reference_budget([clip(4,9),clip(6,11),clip(2,7)],9)
        for refs,images in [([clip(0,17)],0),([clip(0,1)],0),([clip(0,6)]*3,0),([clip(0,3)]*4,0),([],10)]:
            with self.assertRaises(ValueError):validate_reference_budget(refs,images)

if __name__=='__main__':unittest.main()
