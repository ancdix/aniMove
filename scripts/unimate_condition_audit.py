"""Observe stock sampler noise and conditioning; return all values unchanged."""
import hashlib,json,os,runpy,sys
from pathlib import Path
import torch,numpy as np
sys.path.insert(0,'/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/UniMate')
import unimate.inference.generate as generate_module
randn=torch.randn;generate=generate_module.generate_samples;out=Path(os.environ['UNIMATE_AUDIT']);records={'noise':[],'conditions':[],'scope':'Observation only: tensors are hashed and returned unchanged. No random draws added.'}
def save():out.write_text(json.dumps(records,indent=2)+'\n')
def digest(v):
    if torch.is_tensor(v):
        a=v.detach().cpu().numpy();return {'shape':list(a.shape),'dtype':str(a.dtype),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
    if isinstance(v,(list,tuple)):return [digest(x) for x in v]
    if isinstance(v,dict):return {str(k):digest(x) for k,x in v.items()}
    if isinstance(v,np.ndarray):return {'shape':list(v.shape),'dtype':str(v.dtype),'sha256':hashlib.sha256(v.tobytes()).hexdigest()}
    if isinstance(v,np.generic):return v.item()
    return v

def observed_randn(*args,**kwargs):
    x=randn(*args,**kwargs)
    if x.ndim==4 and x.shape[-2:]==(12,60):records['noise'].append(digest(x));save()
    return x

def observed_generate(*args,**kwargs):
    assert not args,'Expected stock keyword call'
    records['conditions'].append({'cond':digest(kwargs['cond']),'x1_known':digest(kwargs.get('x1_known')),'keep_mask':digest(kwargs.get('keep_mask'))});save()
    return generate(*args,**kwargs)
torch.randn=observed_randn;generate_module.generate_samples=observed_generate
try:runpy.run_module('unimate.inference.sample',run_name='__main__')
finally:torch.randn=randn;generate_module.generate_samples=generate
