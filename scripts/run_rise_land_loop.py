"""Paired sparse-window experiment: rise, descend, free landing, closed rest seam."""
import argparse, json, os, sys, time, subprocess
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial.transform import Rotation
from run_inbetween_experiment import (ROOT,ASSETS,SOURCE,digest,torch,edit_args,get_opt,dist_util,
    create_model_and_diffusion_general_skeleton,load_model,T5Conditioner,prepare_inpainting_inputs,
    recover_from_bvh_ric_np,get_bvh_cont6d_params,get_rifke,animation_from_positions,Animation,fixseed)


def fabrik(points,goal,lengths):
    points=points.copy();root=points[0].copy()
    for _ in range(50):
        points[-1]=goal
        for j in range(len(points)-2,-1,-1):
            d=points[j]-points[j+1];points[j]=points[j+1]+d/max(np.linalg.norm(d),1e-9)*lengths[j]
        points[0]=root
        for j in range(1,len(points)):
            d=points[j]-points[j-1];points[j]=points[j-1]+d/max(np.linalg.norm(d),1e-9)*lengths[j-1]
    return points


def make_guide(original,cond):
    xyz=recover_from_bvh_ric_np(original);base=xyz[10].copy();base[:,[0,2]]-=base[0,[0,2]]
    core=(base[0]+base[17])/2;initial_pitch=np.arctan2((base[17]-base[0])[1],np.linalg.norm((base[17]-base[0])[[0,2]]))
    # Target key poses define context only; unknown frames are discarded by the mask.
    phase=PchipInterpolator([0,10,27,47,58,79,101,110,120],[0,0,.45,1,1,.45,0,0,0])(np.arange(121))
    targets=[]
    for w in phase:
        rot=Rotation.from_euler('x',-w*(np.deg2rad(70)-initial_pitch)).as_matrix()
        desired_core=(1-w)*core+w*np.array([0,1.25,-.14])
        pose=(base-core)@rot.T+desired_core
        for chain in [[9,10,11,12,13,14],[3,4,5,6,7,8]]:
            anchor=base[chain[-1]].copy();anchor[1]=.03
            lengths=np.linalg.norm(np.diff(base[chain],axis=0),axis=-1)
            pose[chain]=fabrik(pose[chain],anchor,lengths)
        targets.append(pose)
    targets=np.array(targets)
    anim,order,_=animation_from_positions(targets,cond['parents'],cond['offsets'],iterations=150)
    assert np.array_equal(order,np.arange(len(cond['parents']))),'Guide joint order changed'
    rot6,_,_,rrot,positions=get_bvh_cont6d_params(anim,'Hound')
    ric=get_rifke(positions,rrot)
    local_vel=np.repeat(rrot[1:,None],positions.shape[1],axis=1)*(positions[1:]-positions[:-1])
    contacts=np.zeros(positions[:-1].shape[:2]+(1,))
    contacts[:,[8,14]]=1;contacts[phase[:-1]<.01,29,0]=1;contacts[phase[:-1]<.01,23,0]=1
    features=np.concatenate([ric[:-1],rot6[:-1],local_vel,contacts],axis=-1)
    # Both rest windows are identical; this is an authored rest-to-rest loop boundary.
    features[:10]=features[0];features[110:]=features[0];features[:10,:,9:12]=0;features[110:,:,9:12]=0
    decoded=recover_from_bvh_ric_np(features)
    return features,dict(pitch_goal_degrees=70,fit_mean_error=float(np.linalg.norm(positions-targets,axis=-1).mean()),fit_max_error=float(np.linalg.norm(positions-targets,axis=-1).max()),guide_endpoint_position_error=float(np.linalg.norm(decoded[-1]-decoded[0],axis=-1).max()))


def create_mask(shape,windows):
    mask=torch.zeros(shape,dtype=torch.bool,device=dist_util.dev())
    for start,stop in windows:mask[:,:,:,start:stop]=True
    # Shared authored root yaw and horizontal velocity; vertical root motion is free.
    mask[:,0,3:9,:]=True;mask[:,0,9,:]=True;mask[:,0,11,:]=True
    return mask


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);parser.add_argument('--body-guided',action='store_true');parser.add_argument('--family',choices=['quadropeds','all','bipeds'],default='quadropeds');parser.add_argument('--seeds',type=int,nargs='+',default=[4200,4201,4202,4203]);cli=parser.parse_args()
    if Path(cli.name).name!=cli.name:raise ValueError('Use one new folder name')
    out=ASSETS/'generated'/cli.name;out.mkdir(exist_ok=False)
    checkpoint=next((ASSETS/'AnyTop/checkpoints').glob(cli.family+'_model_*/model*.pt'))
    cond=np.load(ASSETS/'AnyTop/dataset/truebones/zoo/truebones_processed/cond.npy',allow_pickle=True).item()['Hound']
    source=ASSETS/'generated/hound_seed100_batch8/Hound_rep_1_#0.npy';metadata=json.loads(source.with_suffix('.json').read_text())
    guide,guide_report=make_guide(np.load(source),cond);np.save(out/'guide.npy',guide);np.save(out/'guide.xyz.npy',recover_from_bvh_ric_np(guide))
    sys.argv=['edit','--model_path',str(checkpoint),'--object_type','Hound','--samples',str(source),'--num_samples','1']
    args=edit_args();opt=get_opt(args.device);dist_util.setup_dist(args.device)
    model,diffusion=create_model_and_diffusion_general_skeleton(args);load_model(model,torch.load(checkpoint,map_location='cpu'));model.to(dist_util.dev());model.eval()
    t5=T5Conditioner(name=args.t5_name,finetune=False,word_dropout=0.,normalize_text=False,device='cuda')
    motion,kwargs=prepare_inpainting_inputs([guide],'Hound',cond,args.temporal_window,t5,opt.max_joints,opt.feature_len);motion=motion.to(dist_util.dev())
    definitions={'endpoints':[[0,10],[48,59],[110,120]],'waypoints':[[0,10],[24,30],[48,59],[77,83],[110,120]]}
    if cli.body_guided:definitions={'body_guided':definitions['waypoints']}
    report=dict(schema=1,status='running',family=cli.family,checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),source=str(source),source_sha256=digest(source),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_diff=subprocess.check_output(['git','diff'],text=True),fps=20,frames=120,joint_names=metadata['joint_names'],parents=metadata['parents'],guide=guide_report,masks=definitions,shared_root_constraints='Root orientation features 3:9 and horizontal velocity features 9,11 held for entire clip. Root height, contact features and limb/body motion free outside pose windows.',landing_probe_frames=[84,110],body_guidance='Root height and spine joint positions held through frame 83, free again at 84' if cli.body_guided else None,clips=[])
    (out/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    for kind,windows in definitions.items():
        mask=create_mask(motion.shape,windows)
        if kind=='body_guided':
            # Explicit stronger control, released BEFORE the free landing probe.
            mask[:,[0,2,15,16,17],:3,:83]=True
        kwargs['y']['inpainting_mask']=mask;kwargs['y']['inpainted_motion']=motion
        np.save(out/(kind+'_mask.npy'),mask[0,:len(cond['parents'])].cpu().permute(2,0,1).numpy())
        for seed in cli.seeds:
            fixseed(seed);start=time.monotonic()
            with torch.no_grad():sample=diffusion.p_sample_loop(model,motion.shape,clip_denoised=False,model_kwargs=kwargs,skip_timesteps=0,init_image=None,progress=True)
            fixed_error=float((sample[mask]-motion[mask]).abs().max());assert fixed_error<1e-6
            entry=dict(name=kind+'_seed'+str(seed),kind=kind,seed=seed,seconds=time.monotonic()-start,max_fixed_normalized_feature_error=fixed_error)
            if not report['clips']:
                # Prove unknown procedural guide values cannot leak through the mask.
                altered=motion.clone();altered[~mask]=123.456;kwargs['y']['inpainted_motion']=altered;fixseed(seed)
                with torch.no_grad():probe=diffusion.p_sample_loop(model,motion.shape,clip_denoised=False,model_kwargs=kwargs,skip_timesteps=0,init_image=None,progress=False)
                entry['unknown_guide_perturbation_output_error']=float((sample-probe).abs().max());assert entry['unknown_guide_perturbation_output_error']==0
                kwargs['y']['inpainted_motion']=motion
            features=sample[0,:len(cond['parents'])].cpu().permute(2,0,1).numpy()*(cond['std'][None]+1e-6)+cond['mean'][None]
            xyz=recover_from_bvh_ric_np(features);assert np.isfinite(xyz).all()
            entry['raw_loop_position_error']=float(np.linalg.norm(xyz[-1]-xyz[0],axis=-1).max())
            entry['raw_loop_velocity_error']=float(np.linalg.norm((xyz[1]-xyz[0])-(xyz[-1]-xyz[-2]),axis=-1).max()*20)
            assert entry['raw_loop_position_error']<1e-4
            np.save(out/(entry['name']+'.npy'),features);np.save(out/(entry['name']+'.xyz.npy'),xyz)
            report['clips'].append(entry);(out/'run.json').write_text(json.dumps(report,indent=2)+'\n');print('LOOP_SAMPLE',json.dumps(entry),flush=True)
    report['status']='generated';(out/'run.json').write_text(json.dumps(report,indent=2)+'\n');print('LOOP_COMPLETE',out,flush=True)

if __name__=='__main__':main()
