"""Ten requested prompts x eight seeds, through stock UniMate inference, raw only."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
from run_unimate_known_test import ROOT,UPSTREAM,sha

repo=Path(__file__).resolve().parents[1];out=ROOT/'pilgrim_harvest_001';out.mkdir(exist_ok=False)
features=ROOT/'pilgrim_canonical_v002';assert json.loads((features/'asset_validation.json').read_text())['status']=='passed'
prompts=json.loads((repo/'configs/unimate_pilgrim_prompts.json').read_text());exp=out/'experiment';exp.mkdir()
config=json.loads((ROOT/'weights/config.json').read_text());config['dataset']['dataset_list']=['objaverse'];config['objaverse']['path']=str(features);config['experiment']['output_dir']=str(exp)
(exp/'config.json').write_text(json.dumps(config,indent=2)+'\n');shutil.copy2(ROOT/'weights/dataset_stats.npy',exp/'dataset_stats.npy')
cases=out/'cases.json';cases.write_text(json.dumps({'Pilgrim-'+k:v for k,v in prompts.items()},indent=2)+'\n')
checkpoint=ROOT/'weights/checkpoints/checkpoint_step_120000.pt';env=dict(os.environ,HF_HOME=str(ROOT/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false')
manifest=dict(status='running',object='Pilgrim',frames=60,fps=30,cfg=3.0,seeds=list(range(9400,9408)),prompts=prompts,raw_only=True,checkpoint_sha256=sha(checkpoint),cond_sha256=sha(features/'cond.npy'),stats_sha256=sha(exp/'dataset_stats.npy'),config_sha256=sha(exp/'config.json'),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=UPSTREAM,text=True).strip(),noise_note='Each seed initializes a stock run over ten prompts; each prompt consumes its own successive noise draw. Hash and draw index are recorded. This harvest is not a matched-noise prompt test; the separate six-sample probe is.',runs=[],commands=[])
def save():(out/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
save()
for seed in manifest['seeds']:
    batch=out/('seed_'+str(seed));batch.mkdir();env['UNIMATE_NOISE_AUDIT']=str(batch/'noise_audit.json')
    cmd=[sys.executable,str(repo/'scripts/unimate_sample_audit.py'),'--exp_dir',str(exp),'--model_path',str(checkpoint),'--test_cases_json',str(cases),'--num_repetitions','1','--batch_size','1','--seed',str(seed),'--cfg_scale','3.0','--output_dir',str(batch/'samples')]
    start=time.monotonic()
    with (batch/'sample.log').open('w') as log:result=subprocess.run(cmd,cwd=UPSTREAM,env=env,stdout=log,stderr=subprocess.STDOUT)
    manifest['commands'].append(dict(seed=seed,command=cmd,returncode=result.returncode,seconds=time.monotonic()-start));save()
    if result.returncode:manifest['status']='failed';save();raise RuntimeError('Failed seed '+str(seed))
    draws=json.loads((batch/'noise_audit.json').read_text())['draws'];assert len(draws)==10
    for i,(label,prompt) in enumerate(prompts.items()):
        folder=out/(label+'_'+str(seed));(folder/'samples/motions').mkdir(parents=True);(folder/'samples/animations').mkdir()
        f=next((batch/'samples/motions').glob('Pilgrim-'+label+'-*.npy'));v=next((batch/'samples/animations').glob('Pilgrim-'+label+'-*_fk.mp4'))
        shutil.copy2(f,folder/'samples/motions'/f.name);shutil.copy2(v,folder/'samples/animations'/v.name)
        manifest['runs'].append(dict(label=label,prompt=prompt,seed=seed,path=str(folder),original_feature=str(f),feature_sha256=sha(f),noise_draw_index=i,noise_sha256=draws[i]['sha256']))
    save();print('HARVEST',seed,len(manifest['runs']),flush=True)
manifest['status']='generated_requires_raw_review';save()
