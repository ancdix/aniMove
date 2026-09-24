"""Matched raw sampling of upright and quadrupedal reference frames."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
from run_unimate_known_test import ROOT,UPSTREAM,sha
repo=Path(__file__).resolve().parents[1];out=ROOT/'pilgrim_stance_001';assert json.loads((out/'stance_validation.json').read_text())['status']=='passed';assert not (out/'run.json').exists()
prompts=json.loads((repo/'configs/unimate_support_short_prompts.json').read_text());cases=out/'cases.json';cases.write_text(json.dumps({'Pilgrim-'+k:v for k,v in prompts.items()},indent=2)+'\n');prior=json.loads((ROOT/'pilgrim_support_short_001/run.json').read_text());checkpoint=ROOT/'weights/checkpoints/checkpoint_step_120000.pt'
m=dict(status='running',object='Pilgrim',frames=60,fps=30,cfg=3.0,seeds=[9700,9701,9702],prompts=prompts,variants=['upright','quadruped'],checkpoint_sha256=prior['checkpoint_sha256'],source_revision=prior['source_revision'],raw_only=True,reference_note='Authored static quadrupedal reference; no known animation frames or masks. Same front/hind labels, lengths, parents and scale. Both loader registration clips are static reference repeats.',runs=[],audits=[])
def save():(out/'run.json').write_text(json.dumps(m,indent=2)+'\n')
for variant in m['variants']:
    exp=out/'experiments'/variant;exp.mkdir(parents=True);c=json.loads((ROOT/'weights/config.json').read_text());c['dataset']['dataset_list']=['objaverse'];c['objaverse']['path']=str(out/'conditions'/variant);c['experiment']['output_dir']=str(exp);(exp/'config.json').write_text(json.dumps(c,indent=2)+'\n');shutil.copy2(ROOT/'weights/dataset_stats.npy',exp/'dataset_stats.npy')
env=dict(os.environ,HF_HOME=str(ROOT/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false');save()
for seed in m['seeds']:
    for variant in m['variants']:
        folder=out/'batches'/f'{variant}_{seed}';folder.mkdir(parents=True);env['UNIMATE_AUDIT']=str(folder/'audit.json');cmd=[sys.executable,str(repo/'scripts/unimate_condition_audit.py'),'--exp_dir',str(out/'experiments'/variant),'--model_path',str(checkpoint),'--test_cases_json',str(cases),'--num_repetitions','1','--batch_size','1','--seed',str(seed),'--cfg_scale','3.0','--output_dir',str(folder/'samples')];start=time.monotonic()
        with (folder/'sample.log').open('w') as log:r=subprocess.run(cmd,cwd=UPSTREAM,env=env,stdout=log,stderr=subprocess.STDOUT)
        m['audits'].append(dict(variant=variant,seed=seed,command=cmd,returncode=r.returncode,seconds=time.monotonic()-start));save()
        if r.returncode:m['status']='failed';save();raise RuntimeError(str(folder/'sample.log'))
        audit=json.loads((folder/'audit.json').read_text());assert len(audit['noise'])==len(audit['conditions'])==3
        for i,(pid,prompt) in enumerate(prompts.items()):
            dest=out/'clips'/f'{variant}_{pid}_{seed}';(dest/'samples/motions').mkdir(parents=True);(dest/'samples/animations').mkdir();f=next((folder/'samples/motions').glob(f'Pilgrim-{pid}-*.npy'));v=next((folder/'samples/animations').glob(f'Pilgrim-{pid}-*_fk.mp4'));shutil.copy2(f,dest/'samples/motions'/f.name);shutil.copy2(v,dest/'samples/animations'/v.name)
            record=dict(label='stance_'+variant+'_'+pid,variant=variant,prompt_id=pid,prompt=prompt,seed=seed,path=str(dest),cond_path=str(out/'conditions'/variant/'cond.npy'),feature_sha256=sha(f),noise=audit['noise'][i],condition=audit['conditions'][i]);assert record['condition']['x1_known'] is None and record['condition']['keep_mask'] is None
            if variant=='upright':
                old=next(x for x in prior['runs'] if x['seed']==seed and x['prompt_id']==pid);assert record['noise']==old['noise'];assert record['condition']==old['condition'];assert record['feature_sha256']==old['feature_sha256'],'Static registration must not change free generation';record['prior_baseline_exact_replay']=True
            else:
                b=next(x for x in m['runs'] if x['variant']=='upright' and x['seed']==seed and x['prompt_id']==pid);assert record['noise']==b['noise'];changed=[k for k,val in record['condition']['cond'].items() if val!=b['condition']['cond'][k]];assert set(changed)=={'tpos_first_frame','tpos_first_frame_parents','offsets'},changed;record['changed_model_fields']=changed
            m['runs'].append(record)
        save();print('GENERATED',variant,seed,len(m['runs']),flush=True)
m['status']='generated_requires_raw_support_review';save()
