"""Bounded direct-Pilgrim inpainting for an authored ceremonial storyboard."""
import argparse,contextlib,json,os,sys,time,subprocess
from pathlib import Path
import numpy as np
from pilgrim_skeleton import pose,audit
from prepare_pilgrim_loop import stats
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine')

def guide(d):
    times=np.array([0,24,56,78,100,132,160,176,196,220,240])
    values=np.array([[0,0,0,0,0],[0,0,0,0,0],[.2,25,0,0,0],[.45,40,0,1,0],[.55,50,0,1,1],[.55,50,0,1,1],[.55,48,12,1,1],[.50,42,12,1,1],[.40,30,-8,1,0],[0,0,0,0,0],[0,0,0,0,0]])
    xyz=[];poles=[];params=[];errors=[]
    for f in range(241):
        i=min(np.searchsorted(times,f,side='right')-1,len(times)-2);u=(f-times[i])/(times[i+1]-times[i]);w=u*u*u*(10+u*(-15+6*u));v=values[i]*(1-w)+values[i+1]*w
        x,p,e=pose(d,*v);xyz.append(x);poles.append(p);params.append(v);errors.append(e)
    return np.array(xyz),np.array(poles),np.array(params),np.array(errors)

def main():
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--families',nargs='+',default=['all','bipeds']);p.add_argument('--seeds',nargs='+',type=int,default=[6100,6101]);p.add_argument('--body-guided',action='store_true');p.add_argument('--denser-context',action='store_true');cli=p.parse_args();assert Path(cli.name).name==cli.name
    out=BASE/cli.name;out.mkdir(exist_ok=False)
    d=json.loads((BASE/'devotional_loop_v003/skeleton.json').read_text());xyz,poles,params,reach=guide(d)
    np.savez_compressed(out/'authored_guide.npz',xyz=xyz,poles=poles,parameters=params);(out/'skeleton.json').write_text(json.dumps(d,indent=2)+'\n')
    # Existing, patched upstream input preparation keeps free guide values out of diffusion.
    from run_inbetween_experiment import (ASSETS,SOURCE,digest,torch,edit_args,get_opt,dist_util,create_model_and_diffusion_general_skeleton,load_model,T5Conditioner,prepare_inpainting_inputs,recover_from_bvh_ric_np,get_bvh_cont6d_params,get_rifke,animation_from_positions,Animation,fixseed)
    cm=json.loads((BASE/'condition_v002/condition_manifest.json').read_text());c=np.load(cm['condition'],allow_pickle=True).item()['Pilgrim'];scale=cm['normalized_units_per_design_meter']
    target=xyz.copy();target[:,:,1]-=.06;target*=scale
    with open(out/'guide_fit.log','w') as log,contextlib.redirect_stdout(log):anim,order,_=animation_from_positions(target,c['parents'],c['offsets'],iterations=150)
    assert np.array_equal(order,np.arange(len(d['names'])))
    rot6,_,_,rrot,positions=get_bvh_cont6d_params(anim,'Pilgrim',face_joints=d['face_joints']);ric=get_rifke(positions,rrot)
    vel=np.repeat(rrot[1:,None],len(d['names']),axis=1)*(positions[1:]-positions[:-1]);contacts=np.zeros((240,len(d['names']),1))
    contacts[:,d['contact_joints'],0]=np.c_[params[:240,3:5],np.ones((240,2))]
    features=np.concatenate([ric[:-1],rot6[:-1],vel,contacts],axis=-1);np.save(out/'guide_features.npy',features)
    windows=[[[0,16],[72,84],[104,120]],[[0,16],[36,44],[96,120]]]
    if cli.denser_context:windows=[[[0,16],[40,48],[72,84],[96,120]],[[0,16],[36,44],[64,72],[96,120]]]
    report=dict(status='running',fps=20,frames=240,source_condition=cm['condition'],condition_sha256=digest(cm['condition']),scale=scale,calibration_caveat=cm['caveat'],source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_diff=subprocess.check_output(['git','diff'],text=True),guide_fit=stats((positions-target)/scale),guide_reach_max=float(reach.max()),guidance=dict(full_pose_windows_local_zero_based=windows,shared='Root orientation 3:9 and horizontal velocity 9,11 throughout; root height and all remaining channels free outside full-pose windows.',body_guided=cli.body_guided),clips=[])
    def save():(out/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    save();t5=None
    for family in cli.families:
        ck=next((ASSETS/'AnyTop/checkpoints').glob(family+'_model_*/model*.pt'))
        sys.argv=['edit','--model_path',str(ck),'--object_type','Pilgrim','--cond_path',cm['condition'],'--samples',str(out/'guide_features.npy'),'--num_samples','1']
        args=edit_args();opt=get_opt(args.device);dist_util.setup_dist(args.device);model,diff=create_model_and_diffusion_general_skeleton(args);load_model(model,torch.load(ck,map_location='cpu'));model.to(dist_util.dev());model.eval()
        if t5 is None:t5=T5Conditioner(name=args.t5_name,finetune=False,word_dropout=0.,normalize_text=False,device='cuda')
        for half in range(2):
            start=half*120;part=features[start:start+120];motion,kw=prepare_inpainting_inputs([part],'Pilgrim',c,args.temporal_window,t5,opt.max_joints,opt.feature_len);motion=motion.to(dist_util.dev());mask=torch.zeros_like(motion,dtype=torch.bool)
            for a,b in windows[half]:mask[:,:,:,a:b]=True
            mask[:,0,3:9,:]=True;mask[:,0,9,:]=True;mask[:,0,11,:]=True
            if cli.body_guided:mask[:,[0,1,2,3],:3,:]=True
            kw['y']['inpainted_motion']=motion;kw['y']['inpainting_mask']=mask
            np.save(out/('mask_half'+str(half)+'.npy'),mask[0,:len(d['names'])].cpu().permute(2,0,1).numpy())
            for seed in cli.seeds:
                fixseed(seed+half*10);t=time.monotonic()
                with torch.no_grad():sample=diff.p_sample_loop(model,motion.shape,clip_denoised=False,model_kwargs=kw,progress=False)
                fixed=float((sample[mask]-motion[mask]).abs().max());assert fixed<1e-6
                probe_error=None
                if not report['clips']:
                    altered=motion.clone();altered[~mask]=123.456;kw['y']['inpainted_motion']=altered;fixseed(seed+half*10)
                    with torch.no_grad():probe=diff.p_sample_loop(model,motion.shape,clip_denoised=False,model_kwargs=kw,progress=False)
                    probe_error=float((sample-probe).abs().max());assert probe_error==0.;kw['y']['inpainted_motion']=motion
                f=sample[0,:len(d['names'])].cpu().permute(2,0,1).numpy()*(c['std'][None]+1e-6)+c['mean'][None];raw=recover_from_bvh_ric_np(f)
                # Upstream decoding integrates root XZ from zero per window.
                raw[:,:,[0,2]]+=positions[start,0,[0,2]]
                name=f'{family}_half{half}_seed{seed}';np.save(out/(name+'.npy'),f);np.save(out/(name+'.raw.xyz.npy'),raw/scale+[0,.06,0])
                with open(out/(name+'.fit.log'),'w') as log,contextlib.redirect_stdout(log):fitted,order,_=animation_from_positions(raw,c['parents'],c['offsets'],iterations=150)
                fitted=Animation.positions_global(fitted)/scale+[0,.06,0];np.save(out/(name+'.fitted.xyz.npy'),fitted)
                entry=dict(name=name,half=half,seed=seed+half*10,family=family,seconds=time.monotonic()-t,checkpoint=str(ck),checkpoint_sha256=digest(ck),fixed_normalized_error=fixed,unknown_guide_perturbation_error=probe_error,fit=stats(fitted-(raw/scale+[0,.06,0])),guide_difference=stats(fitted-xyz[start:start+120]),root_height_range=[float(fitted[:,0,1].min()),float(fitted[:,0,1].max())],raw_sha256=digest(out/(name+'.raw.xyz.npy')))
                report['clips'].append(entry);save();print('GENUFLECTION_SAMPLE',json.dumps(entry),flush=True)
        del model,diff;torch.cuda.empty_cache()
    report['status']='generated';save();print('GENUFLECTION_COMPLETE',out,flush=True)
if __name__=='__main__':main()
