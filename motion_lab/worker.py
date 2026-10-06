"""Isolated, offline UniMate job runner used by the Blender Motion Lab panel."""
import argparse,hashlib,json,math,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
LAB=BASE/'motion_lab_v001'
REPO=Path(__file__).resolve().parents[1]

def file_sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

def load_model_spec():
    spec=json.loads((REPO/'configs/motion_lab_model.json').read_text())
    weights=BASE/spec['weights_directory'];source=BASE/spec['source_directory']
    for filename,key in [(spec['checkpoint'],'checkpoint_sha256'),('config.json','config_sha256'),('dataset_stats.npy','stats_sha256')]:
        if file_sha256(weights/filename)!=spec[key]:raise ValueError('Model asset checksum mismatch: '+filename)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if revision!=spec['source_revision']:raise ValueError('UniMate source revision differs from the pinned model runtime')
    if subprocess.check_output(['git','diff','HEAD','--'],cwd=source):raise ValueError('Pinned UniMate runtime has modified tracked files')
    return spec,weights,source

def write_json(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def validate_request(r,targets):
    if r.get('target') not in targets:raise ValueError('Unknown target rig')
    prompt=r.get('prompt','').strip()
    if not prompt or len(prompt)>1500:raise ValueError('Enter a prompt between 1 and 1500 characters')
    seconds=r.get('seconds',2)
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 2<=seconds<=12:raise ValueError('Duration must be between 2 and 12 seconds')
    seed=r.get('seed',0)
    if isinstance(seed,bool) or not isinstance(seed,int) or not 0<=seed<=2147483647:raise ValueError('Seed must be an integer from 0 to 2147483647')
    return dict(target=r['target'],prompt=prompt,seconds=float(seconds),seed=seed)

def run(request_path):
    job=request_path.parent;start=time.time();state=dict(status='starting',started=start)
    def status(stage,**kwargs):state.update(status=stage,elapsed_seconds=time.time()-start,**kwargs);write_json(job/'status.json',state)
    try:
        targets={t['id']:t for t in json.loads((LAB/'targets.json').read_text())};r=validate_request(json.loads(request_path.read_text()),targets);t=targets[r['target']];frames=round(r['seconds']*30);segments=1 if frames<=60 else 1+math.ceil((frames-60)/50)
        status('verifying model');spec,weights,source=load_model_spec();config=json.loads((weights/'config.json').read_text())
        if config['dataset']['max_motion_length']!=60:raise ValueError('Motion Lab expects a 60-frame native checkpoint')
        if t['joints']>config['dataset']['max_joints']:raise ValueError('Target exceeds checkpoint joint capacity')
        import torch
        if not torch.cuda.is_available():raise RuntimeError('CUDA GPU unavailable. Motion Lab requires an NVIDIA GPU; check nvidia-smi and the driver before retrying.')
        device='cuda';gpu_name=torch.cuda.get_device_name(0)
        config['sampling']['device']=device
        exp=job/'experiment';exp.mkdir();config['dataset']['dataset_list']=['objaverse'];config['objaverse']['path']=t['features'];config['experiment']['output_dir']=str(exp);write_json(exp/'config.json',config);shutil.copy2(weights/'dataset_stats.npy',exp/'dataset_stats.npy');write_json(job/'model.json',spec)
        caption=r['prompt'] if segments==1 else [r['prompt']]*segments;write_json(job/'cases.json',{t['object_type']+'-interactive':caption});checkpoint=weights/spec['checkpoint']
        cmd=[sys.executable,'-m','unimate.inference.sample','--exp_dir',str(exp),'--model_path',str(checkpoint),'--test_cases_json',str(job/'cases.json'),'--num_repetitions','1','--batch_size','1','--seed',str(r['seed']),'--cfg_scale','3.0','--only_save_motion','--output_dir',str(job/'samples')]
        if segments>1:cmd+=['--motion_expand','--expand_overlap','10']
        env=dict(os.environ,HF_HOME=str(BASE/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',MPLBACKEND='Agg')
        status('generating',device=device,gpu_name=gpu_name,segments=segments,frames=frames,target=t['title'])
        with (job/'inference.log').open('w') as log:
            process=subprocess.run(cmd,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
        if process.returncode:raise RuntimeError('Generation failed. See inference.log: '+(job/'inference.log').read_text()[-1000:])
        status('decoding')
        import numpy as np
        sys.path.insert(0,str(source))
        from Animation import offsets_from_positions,rotations_global
        from unimate.utils.motion_utils import recover_unimate_anim_from_rot,recover_unimate_joint_pos_from_rot
        motion_dir=job/'samples'/('motion_expand/motions' if segments>1 else 'motions');files=list(motion_dir.glob('*.npy'));assert len(files)==1,files
        original=np.load(files[0]);feature=original[:frames];assert len(feature)==frames and feature.shape[1:]==(t['joints'],12) and np.isfinite(feature).all()
        cond=np.load(t['condition'],allow_pickle=True).item()[t['object_type']];parents=np.asarray(cond['parents']);off=offsets_from_positions(np.asarray(cond['tpos_first_frame']),parents);positions=recover_unimate_joint_pos_from_rot(feature,parents,off);anim=recover_unimate_anim_from_rot(feature,parents,off);quats=rotations_global(anim).qs
        assert np.isfinite(positions).all() and np.isfinite(quats).all()
        expected=np.linalg.norm(off[1:],axis=-1);actual=np.linalg.norm(positions[:,1:]-positions[:,parents[1:]],axis=-1);error=float(np.max(abs(actual-expected))/t['scale']);assert error<1e-5
        np.save(job/'motion.npy',feature);np.savez_compressed(job/'kinematics.npz',positions=positions/t['scale'],global_quaternions_wxyz=quats,names=t['names'],parents=parents,fps=30)
        manifest=dict(id=job.name,request=r,target=t['title'],joints=t['joints'],frames=frames,fps=30,seconds=frames/30,generated_frames=len(original),segments=segments,overlap_frames=10 if segments>1 else 0,seams_zero_based=[60+50*i for i in range(segments-1) if 60+50*i<frames],duration_mode='native' if segments==1 else 'stock overlapping continuation, cropped to requested length',postprocessing='FK and coordinate/scale conversion only; no IK, floor correction, smoothing or loop repair',condition_sha256=hashlib.sha256(Path(t['condition']).read_bytes()).hexdigest(),feature_sha256=hashlib.sha256((job/'motion.npy').read_bytes()).hexdigest(),bone_length_error_m=error,command=cmd,created=time.time(),elapsed_seconds=time.time()-start,kinematics=str(job/'kinematics.npz'))
        manifest.update(model_label=spec['label'],model_repository=spec['repository'],model_revision=spec['revision'],model_id=spec['model'],checkpoint_sha256=spec['checkpoint_sha256'],checkpoint_path=str(checkpoint),source_revision=spec['source_revision'],source_directory=str(source),model_config_sha256=spec['config_sha256'],dataset_stats_sha256=spec['stats_sha256'],experiment_config_sha256=file_sha256(exp/'config.json'),ema=True,device=device)
        manifest['gpu_name']=gpu_name
        write_json(job/'result.json',manifest);status('complete',result=str(job/'result.json'))
    except Exception as exc:
        (job/'error.log').write_text(traceback.format_exc());status('failed',error=str(exc));raise
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('request',type=Path);args=parser.parse_args();run(args.request.resolve())
