"""Unconditional AnyTop sampling directly on the Pilgrim graph, with controls."""
import argparse, contextlib, gc, json, os, sys, time, subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];ASSETS=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove');SOURCE=ROOT/'external/AnyTop'
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',HF_HOME=str(ASSETS/'cache/huggingface'),MPLCONFIGDIR='/tmp/pilgrim_mpl')
sys.path.insert(0,str(SOURCE));os.chdir(SOURCE)
import torch, Animation, BVH
from utils.parser_util import generate_args
from utils.model_util import create_model_and_diffusion_general_skeleton,load_model
from utils.fixseed import fixseed
from utils import dist_util
from sample.generate import create_condition
from model.conditioners import T5Conditioner
from data_loaders.truebones.truebones_utils.get_opt import get_opt
from data_loaders.truebones.truebones_utils.motion_process import recover_from_bvh_ric_np
from InverseKinematics import animation_from_positions
from generate_batch import sha256


def main():
    p=argparse.ArgumentParser();p.add_argument('condition',type=Path);p.add_argument('--name',default='pilot_v001');p.add_argument('--families',nargs='+',default=['all','quadropeds','bipeds']);p.add_argument('--seeds',type=int,nargs='+',default=[5100,5101,5102,5103]);cli=p.parse_args()
    cm=json.loads((cli.condition/'condition_manifest.json').read_text());out=cli.condition.parent/cli.name;out.mkdir(exist_ok=False)
    cond=np.load(cm['condition'],allow_pickle=True).item();cond['Hound']=np.load(ASSETS/'AnyTop/dataset/truebones/zoo/truebones_processed/cond.npy',allow_pickle=True).item()['Hound']
    run=dict(status='running',condition_manifest=str(cli.condition/'condition_manifest.json'),condition_sha256=sha256(cm['condition']),
             guidance='None: no keyframes, inpainting, contact constraints, prescribed paths or procedural guide motion.',
             calibration_caveat=cm['caveat'],fps=20,frames=120,seeds=cli.seeds,clips=[],checkpoints={},source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             source_diff=subprocess.check_output(['git','diff'],text=True),normalized_units_per_design_meter=cm['normalized_units_per_design_meter'])
    def save(): (out/'run.json').write_text(json.dumps(run,indent=2)+'\n')
    save();t5=None
    for family in cli.families:
        checkpoint=next((ASSETS/'AnyTop/checkpoints').glob(family+'_model_*/model*.pt'));run['checkpoints'][family]=dict(path=str(checkpoint),sha256=sha256(checkpoint))
        sys.argv=['generate','--model_path',str(checkpoint),'--object_type','Pilgrim','--cond_path',cm['condition'],'--motion_length','6']
        args=generate_args();opt=get_opt(args.device);dist_util.setup_dist(args.device)
        model,diffusion=create_model_and_diffusion_general_skeleton(args);load_model(model,torch.load(checkpoint,map_location='cpu'));model.to(dist_util.dev());model.eval()
        if t5 is None:t5=T5Conditioner(name=args.t5_name,finetune=False,word_dropout=0.,normalize_text=False,device='cuda')
        for object_type,seeds in [('Pilgrim',cli.seeds),('Hound',cli.seeds[:1])]:
            c=cond[object_type];_,kwargs=create_condition([object_type],cond,120,args.temporal_window,t5,opt.max_joints,opt.feature_len)
            for seed in seeds:
                fixseed(seed);start=time.monotonic()
                with torch.no_grad():sample=diffusion.p_sample_loop(model,(1,opt.max_joints,model.feature_len,120),clip_denoised=False,model_kwargs=kwargs,skip_timesteps=0,init_image=None,progress=True)
                features=sample[0,:len(c['parents'])].cpu().permute(2,0,1).numpy()*c['std'][None]+c['mean'][None]
                xyz=recover_from_bvh_ric_np(features);assert np.isfinite(xyz).all()
                name=object_type+'_'+family+'_seed'+str(seed);np.save(out/(name+'.npy'),features);np.save(out/(name+'.xyz.npy'),xyz)
                with open(out/(name+'.fit.log'),'w') as log,contextlib.redirect_stdout(log):fitted,order,_=animation_from_positions(xyz,c['parents'],c['offsets'],iterations=150)
                assert np.array_equal(order,np.arange(len(c['parents'])))
                fitted_xyz=Animation.positions_global(fitted);np.save(out/(name+'.fitted.xyz.npy'),fitted_xyz)
                BVH.save(str(out/(name+'.bvh')),fitted,c['joints_names'],frametime=.05,leaf_joints=True)
                check,check_names,dt=BVH.load(str(out/(name+'.bvh')));assert list(check_names)==list(c['joints_names']);assert abs(dt-.05)<1e-8
                err=np.linalg.norm(fitted_xyz-xyz,axis=-1);scale=cm['normalized_units_per_design_meter'] if object_type=='Pilgrim' else 1
                step=np.linalg.norm(np.diff(xyz,axis=0),axis=-1)/scale
                parents=np.array(c['parents']);raw_lengths=np.linalg.norm(xyz[:,1:]-xyz[:,parents[1:]],axis=-1);rest_lengths=np.linalg.norm(c['offsets'][1:],axis=-1)
                ratio=raw_lengths/rest_lengths
                entry=dict(name=name,object=object_type,family=family,seed=seed,seconds=time.monotonic()-start,fit_rms_design_units=float(np.sqrt(np.mean(err**2))/scale),
                    fit_max_design_units=float(err.max()/scale),max_frame_step_design_units=float(step.max()),p95_frame_step_design_units=float(np.percentile(step,95)),
                    bone_length_ratio_p05=float(np.percentile(ratio,5)),bone_length_ratio_p95=float(np.percentile(ratio,95)),
                    min_raw_height_design_units=float(xyz[...,1].min()/scale),min_fitted_height_design_units=float(fitted_xyz[...,1].min()/scale),
                    bvh_reload_error=float(np.linalg.norm(Animation.positions_global(check)-fitted_xyz,axis=-1).max()),parents=parents.tolist(),names=c['joints_names'],
                    feature_sha256=sha256(out/(name+'.npy')),xyz_sha256=sha256(out/(name+'.xyz.npy')))
                run['clips'].append(entry);save();print('PILGRIM_SAMPLE',json.dumps({k:v for k,v in entry.items() if k not in ['parents','names']}),flush=True)
        del model,diffusion;gc.collect();torch.cuda.empty_cache()
    run['status']='generated';save();print('PILGRIM_PILOT_COMPLETE',out,flush=True)


if __name__=='__main__':main()
