"""Two raw stock text-sequence expansion tests; no authored clamp motion."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
from run_unimate_known_test import ROOT,UPSTREAM,sha
out=ROOT/'pilgrim_expansion_001';out.mkdir(exist_ok=False);exp=out/'experiment';shutil.copytree(ROOT/'pilgrim_harvest_001/experiment',exp)
prompts=['The creature stands still.','The creature slowly lowers its body.','The creature moves forward on all four limbs.','The creature slowly rises.'];case=out/'cases.json';case.write_text(json.dumps({'Pilgrim-ritual01':prompts},indent=2)+'\n');checkpoint=ROOT/'weights/checkpoints/checkpoint_step_120000.pt'
env=dict(os.environ,HF_HOME=str(ROOT/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false');manifest=dict(status='running',object='Pilgrim',cfg=3.0,fps=30,frames=210,overlap=10,prompts=prompts,postprocessing='none; stock generated-tail overlap conditioning only',checkpoint_sha256=sha(checkpoint),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=UPSTREAM,text=True).strip(),runs=[])
for seed in [9500,9501]:
    folder=out/('ritual01_'+str(seed));folder.mkdir();cmd=[sys.executable,'-m','unimate.inference.sample','--exp_dir',str(exp),'--model_path',str(checkpoint),'--test_cases_json',str(case),'--num_repetitions','1','--batch_size','1','--seed',str(seed),'--cfg_scale','3.0','--motion_expand','--expand_overlap','10','--output_dir',str(folder/'samples')];start=time.monotonic()
    with (folder/'sample.log').open('w') as log:r=subprocess.run(cmd,cwd=UPSTREAM,env=env,stdout=log,stderr=subprocess.STDOUT)
    manifest['runs'].append(dict(label='ritual01',seed=seed,prompt=' | '.join(prompts),path=str(folder),command=cmd,returncode=r.returncode,seconds=time.monotonic()-start));(out/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if r.returncode:raise RuntimeError('Expansion failed; '+str(folder/'sample.log'))
    for kind in ['motions','animations']:
        source=folder/'samples/motion_expand'/kind;target=folder/'samples'/kind;shutil.copytree(source,target)
    feature=next((folder/'samples/motions').glob('*.npy'));manifest['runs'][-1]['feature_sha256']=sha(feature);print('EXPANSION',seed,flush=True)
manifest['status']='generated_requires_review';(out/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
