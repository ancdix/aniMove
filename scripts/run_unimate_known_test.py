"""Run the stock sampler on one known rig with matched seeds across prompts."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
UPSTREAM=ROOT/'UniMate'
UID='4798d8c87a0e4ad8835217fe93ddf67b'
PROMPTS={'still':'An object stands still.', 'walk':'An object walks in place.', 'lower':'An object lowers its head to its front legs.'}

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',default='known_text_001');parser.add_argument('--seeds',type=int,nargs='+',default=[9200,9201,9202,9203]);parser.add_argument('--prompts',nargs='+');parser.add_argument('--stock',action='store_true');parser.add_argument('--object',default=UID);parser.add_argument('--features',type=Path,default=ROOT/'known/features');parser.add_argument('--prompts-file',type=Path);a=parser.parse_args()
    prompts=json.loads(a.prompts_file.read_text()) if a.prompts_file else PROMPTS
    labels=a.prompts or list(prompts)
    assert all(label in prompts for label in labels)
    out=ROOT/a.name;out.mkdir(exist_ok=False)
    exp=out/'experiment';exp.mkdir()
    config=json.loads((ROOT/'weights/config.json').read_text())
    config['dataset']['dataset_list']=['objaverse'];config['objaverse']['path']=str(a.features)
    config['experiment']['output_dir']=str(exp)
    (exp/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    shutil.copy2(ROOT/'weights/dataset_stats.npy',exp/'dataset_stats.npy')
    checkpoint=ROOT/'weights/checkpoints/checkpoint_step_120000.pt'
    assert checkpoint.exists() and (a.features/'cond.npy').exists()
    env=dict(os.environ,HF_HOME=str(ROOT/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false')
    manifest=dict(status='running',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=UPSTREAM,text=True).strip(),checkpoint_sha256=sha(checkpoint),cond_sha256=sha(a.features/'cond.npy'),stats_sha256=sha(exp/'dataset_stats.npy'),config_sha256=sha(exp/'config.json'),cfg=3.0,frames=60,fps=30,seeds=a.seeds,object=a.object,raw_only=True,model_changes='none',config_changes=['dataset subset/path and output path only'],runs=[])
    def save(): (out/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    for seed in a.seeds:
        for label in labels:
            prompt=prompts[label]
            folder=out/(label+'_'+str(seed));folder.mkdir();case=folder/'cases.json';case.write_text(json.dumps({a.object+'-'+label:prompt},indent=2)+'\n')
            cmd=[sys.executable,str(Path(__file__).resolve().with_name('unimate_sample_audit.py')),'--exp_dir',str(exp),'--model_path',str(checkpoint),'--test_cases_json',str(case),'--num_repetitions','1','--batch_size','1','--seed',str(seed),'--cfg_scale','3.0','--output_dir',str(folder/'samples')]
            env['UNIMATE_NOISE_AUDIT']=str(folder/'noise_audit.json')
            if a.stock:cmd=[sys.executable,'-m','unimate.inference.sample']+cmd[2:]
            start=time.monotonic()
            with (folder/'sample.log').open('w') as log:result=subprocess.run(cmd,cwd=UPSTREAM,env=env,stdout=log,stderr=subprocess.STDOUT)
            manifest['runs'].append(dict(label=label,prompt=prompt,seed=seed,command=cmd,seconds=time.monotonic()-start,returncode=result.returncode,path=str(folder)))
            save()
            if result.returncode:
                manifest['status']='failed';save();raise RuntimeError('Stock sampling failed; inspect '+str(folder/'sample.log'))
            print('GENERATED',label,seed,flush=True)
    for seed in ([] if a.stock else a.seeds):
        hashes=[]
        for label in labels:
            audit=json.loads((out/(label+'_'+str(seed))/'noise_audit.json').read_text())
            assert len(audit['draws'])==1,audit
            hashes.append(audit['draws'][0]['sha256'])
        assert len(set(hashes))==1,('Prompts did not receive matched noise',seed,hashes)
    manifest['noise_matching']='Not audited (stock smoke test)' if a.stock else 'Verified identical initial noise across prompts for each seed; observation-only wrapper, unchanged stock sampler.'
    manifest['status']='generated_requires_text_response_review';save()

if __name__=='__main__':main()
