"""Matched-noise label-only ablation; original topology and raw rig names unchanged."""
import copy,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from run_unimate_known_test import ROOT,UPSTREAM,sha
repo=Path(__file__).resolve().parents[1];out=ROOT/'pilgrim_labels_001';out.mkdir(exist_ok=False);original=ROOT/'pilgrim_canonical_v002';conditions=np.load(original/'cond.npy',allow_pickle=True).item();base=conditions['Pilgrim'];raw=list(base['joint_names']);clean=list(base['clean_joint_names']);variants={'arms_legs':clean.copy(),'front_hind':clean.copy(),'neutral_limbs':clean.copy()}
for side in ['Left','Right']:
    for old,new in zip(['UpperArm','Forearm','Hand','Fingers'],['Front Leg','Front Knee','Front Ankle','Front Foot']):
        i=raw.index(side+old);variants['front_hind'][i]=side+' '+new;variants['neutral_limbs'][i]='Bone'
    for old,new in zip(['Thigh','Shin','Foot','Toes'],['Hind Leg','Hind Knee','Hind Ankle','Hind Foot']):
        i=raw.index(side+old);variants['front_hind'][i]=side+' '+new;variants['neutral_limbs'][i]='Bone'
prompts_all=json.loads((repo/'configs/unimate_pilgrim_prompts.json').read_text());prompts={k:prompts_all[k] for k in ['p07','p03','p05']};cases=out/'cases.json';cases.write_text(json.dumps({'Pilgrim-'+k:v for k,v in prompts.items()},indent=2)+'\n')
base_manifest=json.loads((ROOT/'pilgrim_harvest_001/run.json').read_text());manifest=dict(status='running',object='Pilgrim',frames=60,fps=30,cfg=3.0,seeds=[9600,9601,9602],prompts=prompts,variants=variants,raw_joint_names=raw,only_changed_field='cond.npy Pilgrim.clean_joint_names (16 limb entries only)',unchanged='All other cond fields, raw bone names, source registration motion, T-pose, parents, facing, joint order, scale, statistics, checkpoint, prompts, CFG and matched seeds.',neutral_note='Bone on all 16 limb joints removes side/segment semantics too; core labels retained. Not zero embeddings.',checkpoint_sha256=base_manifest['checkpoint_sha256'],source_revision=base_manifest['source_revision'],runs=[],audits=[])
(out/'variant_labels.json').write_text(json.dumps({'raw_joint_names':raw,'variants':variants},indent=2)+'\n')
def save():(out/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
def identical(a,b):
    if isinstance(a,np.ndarray):return np.array_equal(a,b)
    if isinstance(a,dict):return a.keys()==b.keys() and all(identical(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return len(a)==len(b) and all(identical(x,y) for x,y in zip(a,b))
    return a==b
for variant,labelnames in variants.items():
    features=out/'conditions'/variant;features.mkdir(parents=True);d=copy.deepcopy(conditions);d['Pilgrim']['clean_joint_names']=labelnames;np.save(features/'cond.npy',d);shutil.copytree(original/'motions',features/'motions')
    check=np.load(features/'cond.npy',allow_pickle=True).item()['Pilgrim'];assert all(identical(base[k],check[k]) for k in base if k!='clean_joint_names')
    assert all(sha(p)==sha(features/'motions'/p.name) for p in (original/'motions').iterdir())
    exp=out/'experiments'/variant;exp.mkdir(parents=True);config=json.loads((ROOT/'weights/config.json').read_text());config['dataset']['dataset_list']=['objaverse'];config['objaverse']['path']=str(features);config['experiment']['output_dir']=str(exp);(exp/'config.json').write_text(json.dumps(config,indent=2)+'\n');shutil.copy2(ROOT/'weights/dataset_stats.npy',exp/'dataset_stats.npy')
checkpoint=ROOT/'weights/checkpoints/checkpoint_step_120000.pt';env=dict(os.environ,HF_HOME=str(ROOT/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false');save()
jobs=[(variant,seed,False) for seed in manifest['seeds'] for variant in variants]+[('arms_legs',9600,True)]
for variant,seed,repeat in jobs:
    label=variant+('_repeat' if repeat else '');folder=out/'batches'/f'{label}_{seed}';folder.mkdir(parents=True);env['UNIMATE_AUDIT']=str(folder/'audit.json');cmd=[sys.executable,str(repo/'scripts/unimate_condition_audit.py'),'--exp_dir',str(out/'experiments'/variant),'--model_path',str(checkpoint),'--test_cases_json',str(cases),'--num_repetitions','1','--batch_size','1','--seed',str(seed),'--cfg_scale','3.0','--output_dir',str(folder/'samples')];start=time.monotonic()
    with (folder/'sample.log').open('w') as log:r=subprocess.run(cmd,cwd=UPSTREAM,env=env,stdout=log,stderr=subprocess.STDOUT)
    manifest['audits'].append(dict(variant=label,seed=seed,path=str(folder/'audit.json'),command=cmd,returncode=r.returncode,seconds=time.monotonic()-start));save()
    if r.returncode:manifest['status']='failed';save();raise RuntimeError('See '+str(folder/'sample.log'))
    audit=json.loads((folder/'audit.json').read_text());assert len(audit['conditions'])==len(audit['noise'])==3
    for i,(prompt_id,prompt) in enumerate(prompts.items()):
        dest=out/'clips'/f'{label}_{prompt_id}_{seed}';(dest/'samples/motions').mkdir(parents=True);(dest/'samples/animations').mkdir();feature=next((folder/'samples/motions').glob(f'Pilgrim-{prompt_id}-*.npy'));video=next((folder/'samples/animations').glob(f'Pilgrim-{prompt_id}-*_fk.mp4'));shutil.copy2(feature,dest/'samples/motions'/feature.name);shutil.copy2(video,dest/'samples/animations'/video.name)
        manifest['runs'].append(dict(label=label+'_'+prompt_id,variant=label,prompt_id=prompt_id,prompt=prompt,seed=seed,path=str(dest),feature_sha256=sha(feature),noise=audit['noise'][i],condition=audit['conditions'][i],repeat_control=repeat))
    save();print('GENERATED',label,seed,len(manifest['runs']),flush=True)
    # Reject a confounded comparison as soon as all variants of a seed exist.
    for prompt_id in prompts:
        selected=[r for r in manifest['runs'] if r['seed']==seed and r['prompt_id']==prompt_id];baseline=next((r for r in selected if r['variant']=='arms_legs'),None)
        if baseline:
            for entry in selected:
                assert entry['noise']==baseline['noise'],('noise mismatch',entry['label'])
                for k,val in baseline['condition']['cond'].items():
                    if k!='joint_names_emb':assert entry['condition']['cond'][k]==val,('non-name condition changed',k,entry['label'])
                assert entry['condition']['x1_known'] is None and entry['condition']['keep_mask'] is None
                if entry['repeat_control']:assert entry['feature_sha256']==baseline['feature_sha256'],('baseline replay differs',prompt_id)
manifest['status']='generated_verified_label_only_requires_visual_review';manifest['verification']='Exact equality of initial noise and all non-name model conditioning fields per seed/prompt. Baseline replay feature hashes identical.';save()
