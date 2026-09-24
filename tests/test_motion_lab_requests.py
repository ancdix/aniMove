"""Input and duration checks that prevent invalid GPU work from the UI boundary."""
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('lab_worker',Path(__file__).parents[1]/'motion_lab/worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
class RequestTests(unittest.TestCase):
    def test_valid_prompt_preserves_literal_shell_characters(self):
        r=worker.validate_request(dict(target='Mammal',prompt='  A dog walks; $(nothing)  ',seconds=4,seed=32),{'Mammal':{}})
        self.assertEqual(r['prompt'],'A dog walks; $(nothing)');self.assertEqual(r['seconds'],4)
    def test_invalid_requests(self):
        base=dict(target='Mammal',prompt='Walk',seconds=2,seed=0)
        for patch in [dict(target='../x'),dict(prompt=' '),dict(seconds=float('nan')),dict(seconds=13),dict(seconds=True),dict(seed=-1),dict(seed=True),dict(prompt='x'*1501)]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):worker.validate_request(dict(base,**patch),{'Mammal':{}})
if __name__=='__main__':unittest.main()
