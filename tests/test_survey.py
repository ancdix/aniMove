"""Survey coverage, crash recovery and bounded unattended retries."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('survey',ROOT/'motion_lab/survey.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class SurveyTests(unittest.TestCase):
    def test_full_cross_product_and_round_order(self):
        c=s.read(ROOT/'configs/essential_motion_survey_001.json');e=s.make_entries(c)
        self.assertEqual(len(e),1440);self.assertEqual(len({x['id'] for x in e}),1440)
        self.assertEqual({x['seed'] for x in e[:360]},{c['seeds'][0]})
        for t in c['targets']:
            for p in c['prompts']:
                pair=[x for x in e if x['target']==t and x['prompt_id']==p['id']]
                self.assertEqual({x['seed'] for x in pair},set(c['seeds']))
                self.assertEqual({x['experimental'] for x in pair},{t not in p['intended_targets']})
    def test_resume_recovers_completed_child(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);jobs=root/'jobs';job=jobs/'saved';job.mkdir(parents=True);s.write(job/'result.json',{})
            state={'entries':[dict(id='x',status='running',attempts=[{'job':'saved'}])]}
            def export(root,e,job,m):e['status']='complete'
            with patch.object(s,'LAB',root),patch.object(s,'export_clip',export):s.reconcile(root,{'config':{'max_attempts':2}},state)
            self.assertEqual(state['entries'][0]['status'],'complete')
    def test_failure_retries_and_completed_run_does_not_regenerate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'jobs').mkdir();(root/'web').mkdir();(root/'runtime/motion_lab').mkdir(parents=True)
            worker=root/'runtime/motion_lab/worker.py'
            worker.write_text("import sys,json\nfrom pathlib import Path\np=Path(sys.argv[1]).parent\nif p.name.endswith('_a1'):\n (p/'status.json').write_text(json.dumps({'error':'intentional test failure'}))\n sys.exit(1)\n(p/'result.json').write_text('{}')\n")
            config={'seeds':[1],'targets':['Test'],'seconds':2,'max_attempts':2,'id':'test','title':'Test','prompts':[{'id':'G01','text':'An object walks.','intended_targets':['Test']}]}
            s.write(root/'targets.json',[])
            manifest={'config':config,'targets':[],'targets_sha256':s.sha(root/'targets.json'),'condition_sha256':{},'worker_sha256':s.sha(worker)}
            s.write(root/'manifest.json',manifest);s.write(root/'state.json',{'entries':s.make_entries(config)})
            def export(root,e,job,m):e.update(status='complete',job=job.name,elapsed_seconds=.1)
            with patch.object(s,'LAB',root),patch.object(s,'export_clip',export):
                s.run(root);first=s.read(root/'state.json');s.run(root);second=s.read(root/'state.json')
            self.assertEqual(first['status'],'complete');self.assertEqual(first['completed'],1)
            self.assertEqual(len(first['entries'][0]['attempts']),2);self.assertEqual(len(second['entries'][0]['attempts']),2)
            self.assertEqual(len(list((root/'jobs').iterdir())),2)
if __name__=='__main__':unittest.main()
