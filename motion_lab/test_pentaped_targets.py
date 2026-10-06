"""Run two short official-v2 GPU samples per five-limbed target."""
import json,subprocess,sys,time,uuid
from pathlib import Path
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
REPO=Path(__file__).resolve().parents[1]
jobs=[]
for key in ['PentapedRadial','PentapedTripod']:
    for prompt in ['An object walks forward on five legs.','An object lowers its body while spreading its legs.']:
        job=BASE/'jobs'/(time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]);job.mkdir()
        (job/'request.json').write_text(json.dumps(dict(target=key,prompt=prompt,seconds=2,seed=9811)))
        subprocess.run([sys.executable,str(REPO/'motion_lab/worker.py'),str(job/'request.json')],check=True,cwd=REPO)
        jobs.append(job.name);print(key,prompt,job.name,flush=True)
(BASE/'pentaped_target_jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
