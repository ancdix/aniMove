"""Invoke unchanged upstream sampling, recording initial noise without modifying it."""
import hashlib,json,os,runpy,sys
from pathlib import Path
import torch

sys.path.insert(0,'/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/UniMate')
original_randn=torch.randn
records=[]
destination=Path(os.environ['UNIMATE_NOISE_AUDIT'])

def observed_randn(*args,**kwargs):
    value=original_randn(*args,**kwargs)
    if value.ndim==4 and value.shape[-2:]==(12,60):
        records.append(dict(shape=list(value.shape),sha256=hashlib.sha256(value.detach().cpu().numpy().tobytes()).hexdigest()))
        destination.write_text(json.dumps(dict(scope='Observation only; random draws are returned unchanged.',draws=records),indent=2)+'\n')
    return value

torch.randn=observed_randn
try:runpy.run_module('unimate.inference.sample',run_name='__main__')
finally:torch.randn=original_randn
