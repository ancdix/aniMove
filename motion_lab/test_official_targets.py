"""Run real official-v2 GPU generation on all Motion Lab targets."""
import json,subprocess,sys,time,uuid
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
records=[]
for target,prompt in [('Mammal','An object walks forward on all fours.'),('Bird','An object flaps its wings.'),('Insect','An object walks forward on six legs.'),('Pilgrim','An object walks forward slowly.'),('PilgrimQuad','An object walks forward on all fours.')]:
    job=BASE/'jobs'/(time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]);job.mkdir()
    seconds=4 if target=='Mammal' else 2
    (job/'request.json').write_text(json.dumps(dict(target=target,prompt=prompt,seconds=seconds,seed=9801),indent=2))
    subprocess.run([sys.executable,str(REPO/'motion_lab/worker.py'),str(job/'request.json')],check=True,cwd=REPO)
    result=json.loads((job/'result.json').read_text());assert result['model_repository']=='Linzhan/UniMate' and result['frames']==seconds*30 and result['device']=='cuda'
    records.append(job.name);print('PASSED',target,job.name,flush=True)
(BASE/'official_v2_target_jobs.json').write_text(json.dumps(records,indent=2)+'\n')
