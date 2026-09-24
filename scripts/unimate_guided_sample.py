"""Inject explicit guides through stock replacement sampling, with matched Euler control."""
import os,sys,runpy,json,hashlib
from pathlib import Path
import numpy as np
import torch
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');sys.path.insert(0,str(BASE/'UniMate'))
import unimate.inference.generate as gm
original=gm.generate_samples;randn=torch.randn;out=Path(os.environ['UNIMATE_GUIDED_OUTPUT']);source=BASE/'pilgrim_guided_001';records=[];noise=[]
def digest(t):
    a=t.detach().cpu().numpy();return hashlib.sha256(a.tobytes()).hexdigest()
def observed_randn(*args,**kwargs):
    value=randn(*args,**kwargs)
    if value.ndim==4 and value.shape[-2:]==(12,60):noise.append(digest(value))
    return value
def generate(**kw):
    assert kw['x1_known'] is None and kw['keep_mask'] is None
    cond=kw['cond'];device=kw['device'];shape=kw['motion_shape'];assert shape[0]==1
    feature=np.load(source/'authored_features.npy');mean=cond['mean'][0,:23].cpu().numpy();std=cond['std'][0,:23].cpu().numpy();normalized=(feature-mean[None])/std[None]
    known=torch.zeros(shape,device=device);known[0,:23]=torch.as_tensor(normalized.transpose(1,2,0),device=device,dtype=known.dtype)
    cpu=torch.get_rng_state();gpu=torch.cuda.get_rng_state_all();last=None
    for mode in ['euler_free','poses','poses_root']:
        torch.set_rng_state(cpu);torch.cuda.set_rng_state_all(gpu)
        mask=torch.zeros(shape,device=device,dtype=torch.bool);mask[0,:23]=torch.as_tensor(np.load(source/(mode+'_mask.npy')).transpose(1,2,0),device=device)
        last=original(**dict(kw,x1_known=known,keep_mask=mask))
        raw=last[0,:23].detach().cpu().permute(2,0,1).numpy()*std[None]+mean[None];np.save(out/(mode+'.npy'),raw)
        delta=(last-known)[mask];records.append(dict(mode=mode,noise_sha256=noise[-1],constrained_normalized_max_error=float(delta.abs().max()) if delta.numel() else 0.,finite=bool(torch.isfinite(last).all()),condition_hashes={k:digest(v) for k,v in cond.items() if torch.is_tensor(v)}))
    assert len(set(r['noise_sha256'] for r in records))==1
    (out/'audit.json').write_text(json.dumps(dict(solver='Unmodified stock replacement Euler, 50 steps; all-false mask for unguided control',records=records),indent=2)+'\n')
    return last
gm.generate_samples=generate;torch.randn=observed_randn
try:runpy.run_module('unimate.inference.sample',run_name='__main__')
finally:gm.generate_samples=original;torch.randn=randn
