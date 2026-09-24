"""Raw biped/quadruped feasibility test with matched name-variant noise."""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
from run_unimate_known_test import ROOT,UPSTREAM,sha
p=argparse.ArgumentParser();p.add_argument('--name',default='pilgrim_support_001');p.add_argument('--seeds',type=int,nargs='+',default=[9700,9701,9702]);p.add_argument('--prompts-file',type=Path,default=Path(__file__).resolve().parents[1]/'configs/unimate_support_prompts.json');p.add_argument('--variants',nargs='+',choices=['arms_legs','front_hind'],default=['arms_legs','front_hind']);args=p.parse_args()
repo=Path(__file__).resolve().parents[1];out=ROOT/args.name;out.mkdir(exist_ok=False)
prompts=json.loads(args.prompts_file.read_text());cases=out/'cases.json';cases.write_text(json.dumps({'Pilgrim-'+k:v for k,v in prompts.items()},indent=2)+'\n')
previous=json.loads((ROOT/'pilgrim_labels_001/run.json').read_text());manifest=dict(status='running',object='Pilgrim',frames=60,fps=30,cfg=3.0,seeds=args.seeds,prompts=prompts,checkpoint_sha256=previous['checkpoint_sha256'],source_revision=previous['source_revision'],raw_only=True,geometry='Existing upright Pilgrim reference; no changed lengths, topology, rest pose, or imposed animation poses.',variants=args.variants,runs=[],audits=[])
def save():(out/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
checkpoint=ROOT/'weights/checkpoints/checkpoint_step_120000.pt';env=dict(os.environ,HF_HOME=str(ROOT/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false')
for variant in manifest['variants']:
    features=out/'conditions'/variant;shutil.copytree(ROOT/'pilgrim_labels_001/conditions'/variant,features)
    exp=out/'experiments'/variant;exp.mkdir(parents=True);c=json.loads((ROOT/'weights/config.json').read_text());c['dataset']['dataset_list']=['objaverse'];c['objaverse']['path']=str(features);c['experiment']['output_dir']=str(exp);(exp/'config.json').write_text(json.dumps(c,indent=2)+'\n');shutil.copy2(ROOT/'weights/dataset_stats.npy',exp/'dataset_stats.npy')
save()
for seed in args.seeds:
    for variant in manifest['variants']:
        folder=out/'batches'/f'{variant}_{seed}';folder.mkdir(parents=True);env['UNIMATE_AUDIT']=str(folder/'audit.json');cmd=[sys.executable,str(repo/'scripts/unimate_condition_audit.py'),'--exp_dir',str(out/'experiments'/variant),'--model_path',str(checkpoint),'--test_cases_json',str(cases),'--num_repetitions','1','--batch_size','1','--seed',str(seed),'--cfg_scale','3.0','--output_dir',str(folder/'samples')];start=time.monotonic()
        with (folder/'sample.log').open('w') as log:r=subprocess.run(cmd,cwd=UPSTREAM,env=env,stdout=log,stderr=subprocess.STDOUT)
        manifest['audits'].append(dict(variant=variant,seed=seed,command=cmd,returncode=r.returncode,seconds=time.monotonic()-start));save()
        if r.returncode:manifest['status']='failed';save();raise RuntimeError(str(folder/'sample.log'))
        audit=json.loads((folder/'audit.json').read_text());assert len(audit['noise'])==len(audit['conditions'])==3
        for i,(pid,prompt) in enumerate(prompts.items()):
            dest=out/'clips'/f'{variant}_{pid}_{seed}';(dest/'samples/motions').mkdir(parents=True);(dest/'samples/animations').mkdir()
            f=next((folder/'samples/motions').glob(f'Pilgrim-{pid}-*.npy'));v=next((folder/'samples/animations').glob(f'Pilgrim-{pid}-*_fk.mp4'));shutil.copy2(f,dest/'samples/motions'/f.name);shutil.copy2(v,dest/'samples/animations'/v.name)
            record=dict(label=('support' if args.name=='pilgrim_support_001' else args.name)+'_'+variant+'_'+pid,variant=variant,prompt_id=pid,prompt=prompt,seed=seed,path=str(dest),feature_sha256=sha(f),noise=audit['noise'][i],condition=audit['conditions'][i]);assert record['condition']['x1_known'] is None and record['condition']['keep_mask'] is None
            if variant=='front_hind' and 'arms_legs' in args.variants:
                b=next(x for x in manifest['runs'] if x['variant']=='arms_legs' and x['seed']==seed and x['prompt_id']==pid);assert record['noise']==b['noise'];assert all(value==b['condition']['cond'][key] for key,value in record['condition']['cond'].items() if key!='joint_names_emb')
            manifest['runs'].append(record)
        save();print('GENERATED',variant,seed,len(manifest['runs']),flush=True)
manifest['status']='generated_requires_support_review';save()
