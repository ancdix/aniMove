"""Four natural inbetweens plus four authored-rearing boundary stress tests."""
import argparse,hashlib,json,os,sys,time,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ASSETS=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove')
SOURCE=ROOT/'external/AnyTop'
for k,v in dict(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLBACKEND='Agg',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',HF_HOME=str(ASSETS/'cache/huggingface'),MPLCONFIGDIR=str(ASSETS/'cache/matplotlib')).items():os.environ[k]=v
sys.path.insert(0,str(SOURCE));os.chdir(SOURCE)
import torch
from utils.parser_util import edit_args
from utils.model_util import create_model_and_diffusion_general_skeleton,load_model
from utils.fixseed import fixseed
from utils import dist_util
from model.conditioners import T5Conditioner
from sample.edit import prepare_inpainting_inputs
from data_loaders.truebones.truebones_utils.get_opt import get_opt
from data_loaders.truebones.truebones_utils.motion_process import recover_from_bvh_ric_np,get_bvh_cont6d_params,get_rifke
from InverseKinematics import animation_from_positions
import Animation

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def end_pose(xyz,cond):
    from scipy.spatial.transform import Rotation
    base=xyz[10].copy();core=(base[0]+base[17])/2
    rear=base[[14,8]].mean(axis=0);ground=float(base[[29,23,14,8],1].min())
    rear[1]=ground
    # Approximate 70-degree upright body: rear feet remain planted, front feet lift.
    spine=base[17]-base[0];pitch=np.arctan2(spine[1],np.linalg.norm(spine[[0,2]]))
    rot=Rotation.from_euler('x',-(np.deg2rad(70)-pitch)).as_matrix()
    target=(base-core)@rot.T+rear+[0,1.25,0]
    for chain in [[9,10,11,12,13,14],[3,4,5,6,7,8]]:
        points=target[chain].copy();root=points[0].copy();goal=base[chain[-1]].copy();goal[1]=ground
        lengths=np.linalg.norm(np.diff(base[chain],axis=0),axis=-1)
        for _ in range(100):
            points[-1]=goal
            for j in range(len(points)-2,-1,-1):
                d=points[j]-points[j+1];points[j]=points[j+1]+d/max(np.linalg.norm(d),1e-9)*lengths[j]
            points[0]=root
            for j in range(1,len(points)):
                d=points[j]-points[j-1];points[j]=points[j-1]+d/max(np.linalg.norm(d),1e-9)*lengths[j-1]
        target[chain]=points
    # Fit a consistent source skeleton and encode with upstream feature routines.
    anim,_,_=animation_from_positions(target[None],cond['parents'],cond['offsets'],iterations=150)
    positions=Animation.positions_global(anim)
    rot6,_,_,rrot,positions=get_bvh_cont6d_params(anim,'Hound')
    ric=get_rifke(positions,rrot)
    features=np.concatenate([ric,rot6,np.zeros_like(positions),np.zeros(positions.shape[:2]+(1,))],axis=-1)[0]
    for j in [8,14]:features[j,12]=1
    return features,positions[0],dict(authored_body_pitch_degrees=70,fit_mean_error=float(np.linalg.norm(positions[0]-target,axis=-1).mean()),fit_max_error=float(np.linalg.norm(positions[0]-target,axis=-1).max()),note='Authored goal pose, fitted to Hound bone lengths. Middle guide values are masked out, never interpolated into the model output.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);parser.add_argument('--seeds',type=int,nargs='+',default=[3100,3101,3102,3103]);parser.add_argument('--kinds',nargs='+',choices=['natural','rear_up'],default=['natural','rear_up']);cli=parser.parse_args()
    out=ASSETS/'generated'/cli.name;out.mkdir(exist_ok=False)
    checkpoint=next((ASSETS/'AnyTop/checkpoints').glob('quadropeds_model_*/model*.pt'))
    condpath=ASSETS/'AnyTop/dataset/truebones/zoo/truebones_processed/cond.npy'
    cond=np.load(condpath,allow_pickle=True).item()['Hound']
    originalpath=ASSETS/'generated/hound_seed100_batch8/Hound_rep_1_#0.npy'
    original=np.load(originalpath);xyz=recover_from_bvh_ric_np(original)
    ending,ending_xyz,guide_info=end_pose(xyz,cond)
    extreme=original.copy();extreme[90:]=ending
    # The middle is an explicit unknown region, not a procedural transition.
    guides={'natural':original,'rear_up':extreme}
    for name,guide in guides.items():np.save(out/(name+'_guide.npy'),guide);np.save(out/(name+'_guide.xyz.npy'),recover_from_bvh_ric_np(guide))
    np.save(out/'authored_end_pose.xyz.npy',ending_xyz)
    sys.argv=['edit','--model_path',str(checkpoint),'--object_type','Hound','--samples',str(originalpath),'--num_samples','1']
    args=edit_args();opt=get_opt(args.device);dist_util.setup_dist(args.device)
    model,diffusion=create_model_and_diffusion_general_skeleton(args);load_model(model,torch.load(checkpoint,map_location='cpu'));model.to(dist_util.dev());model.eval()
    t5=T5Conditioner(name=args.t5_name,finetune=False,word_dropout=0.,normalize_text=False,device='cuda')
    metadata=json.loads(originalpath.with_suffix('.json').read_text())
    report=dict(schema=1,status='running',source_features=str(originalpath),source_sha256=digest(originalpath),checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_diff=subprocess.check_output(['git','diff'],text=True),frames=120,fps=20,fixed_frames=[[1,30],[91,120]],generated_frames=[31,90],guide=guide_info,joint_names=metadata['joint_names'],parents=metadata['parents'],clips=[])
    (out/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    for kind,guide in guides.items():
        if kind not in cli.kinds:continue
        motion,kwargs=prepare_inpainting_inputs([guide],'Hound',cond,args.temporal_window,t5,opt.max_joints,opt.feature_len)
        motion=motion.to(dist_util.dev());mask=torch.ones_like(motion,dtype=torch.bool);mask[:,:,:,30:90]=False
        kwargs['y']['inpainted_motion']=motion;kwargs['y']['inpainting_mask']=mask
        for seed in cli.seeds:
            fixseed(seed);start=time.monotonic()
            with torch.no_grad():sample=diffusion.p_sample_loop(model,motion.shape,clip_denoised=False,model_kwargs=kwargs,skip_timesteps=0,init_image=None,progress=True)
            fixed_error=float((sample[mask]-motion[mask]).abs().max());assert fixed_error<1e-5,fixed_error
            features=sample[0,:len(cond['parents'])].cpu().permute(2,0,1).numpy()*(cond['std'][None]+1e-6)+cond['mean'][None]
            output_xyz=recover_from_bvh_ric_np(features);assert np.isfinite(output_xyz).all()
            guide_xyz=recover_from_bvh_ric_np(guide)
            suffix_delta=output_xyz[90:]-guide_xyz[90:]
            # Root integration allows suffix translation even when suffix features are fixed.
            relative=suffix_delta-suffix_delta[:,0:1]
            name=kind+'_seed'+str(seed);np.save(out/(name+'.npy'),features);np.save(out/(name+'.xyz.npy'),output_xyz)
            entry=dict(name=name,kind=kind,seed=seed,seconds=time.monotonic()-start,max_fixed_normalized_feature_error=fixed_error,max_fixed_feature_error=float(abs(features[np.r_[0:30,90:120]]-guide[np.r_[0:30,90:120]]).max()),prefix_xyz_error=float(abs(output_xyz[:30]-guide_xyz[:30]).max()),suffix_root_offset= suffix_delta[0,0].tolist(),suffix_relative_pose_error=float(abs(relative).max()),middle_difference_rms=float(np.sqrt(np.mean((output_xyz[30:90]-guide_xyz[30:90])**2))))
            report['clips'].append(entry);(out/'run.json').write_text(json.dumps(report,indent=2)+'\n');print('EDIT_RESULT',json.dumps(entry),flush=True)
    report['status']='generated';(out/'run.json').write_text(json.dumps(report,indent=2)+'\n');print('EDIT_COMPLETE',out,flush=True)

if __name__=='__main__':main()
