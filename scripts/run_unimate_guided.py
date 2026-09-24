"""Three seeds, matched free / sparse poses / sparse poses plus root path."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
from run_unimate_known_test import ROOT,UPSTREAM,sha
repo=Path(__file__).resolve().parents[1];out=ROOT/'pilgrim_guided_001';assert json.loads((out/'guide_validation.json').read_text())['status']=='passed';assert not (out/'run.json').exists();exp=out/'experiment';exp.mkdir();c=json.loads((ROOT/'weights/config.json').read_text());c['dataset']['dataset_list']=['objaverse'];c['objaverse']['path']=str(out/'condition');c['experiment']['output_dir']=str(exp);(exp/'config.json').write_text(json.dumps(c,indent=2));shutil.copy2(ROOT/'weights/dataset_stats.npy',exp/'dataset_stats.npy');prompt='The creature walks forward slowly.';(out/'cases.json').write_text(json.dumps({'Pilgrim-walk':prompt}));checkpoint=ROOT/'weights/checkpoints/checkpoint_step_120000.pt'
m=dict(status='running',object='Pilgrim',frames=60,fps=30,cfg=3.,seeds=[9700,9701,9702],variants=['euler_free','poses','poses_root'],prompt=prompt,runs=[],checkpoint_sha256=sha(checkpoint),source_revision='9f3076e1db482883edb6f6a37a67f521c3853278');env=dict(os.environ,HF_HOME=str(ROOT/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false')
for seed in m['seeds']:
    folder=out/'batches'/str(seed);folder.mkdir(parents=True);env['UNIMATE_GUIDED_OUTPUT']=str(folder);cmd=[sys.executable,str(repo/'scripts/unimate_guided_sample.py'),'--exp_dir',str(exp),'--model_path',str(checkpoint),'--test_cases_json',str(out/'cases.json'),'--num_repetitions','1','--batch_size','1','--seed',str(seed),'--cfg_scale','3','--only_save_motion','--output_dir',str(folder/'stock_save')];start=time.monotonic()
    with (folder/'sample.log').open('w') as log:r=subprocess.run(cmd,cwd=UPSTREAM,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0,str(folder/'sample.log');audit=json.loads((folder/'audit.json').read_text())
    for record in audit['records']:
        variant=record['mode'];clip=out/'clips'/f'{variant}_{seed}';(clip/'samples/motions').mkdir(parents=True);f=clip/'samples/motions/motion.npy';shutil.copy2(folder/(variant+'.npy'),f);m['runs'].append(dict(label='guided_'+variant,variant=variant,seed=seed,prompt=prompt,prompt_id='walk',path=str(clip),cond_path=str(out/'condition/cond.npy'),feature_sha256=sha(f),audit=record))
    (out/'run.json').write_text(json.dumps(m,indent=2)+'\n');print('GENERATED',seed,'seconds',time.monotonic()-start,flush=True)
m['status']='generated_requires_review';(out/'run.json').write_text(json.dumps(m,indent=2)+'\n')
