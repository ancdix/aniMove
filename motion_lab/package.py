"""Archive the shipped interface and verify saved results without changing motion."""
import hashlib,json,shutil
from pathlib import Path
import numpy as np
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001');REPO=Path(__file__).resolve().parents[1];targets=json.loads((BASE/'targets.json').read_text());counts={t['id']:t['joints'] for t in targets};assert counts==dict(Mammal=48,Bird=49,Insect=43,Pilgrim=23,PilgrimQuad=23)
for filename in ['blender_validation.json','saved_validation.json','live_validation.json','ui_validation.json','camera_validation.json']:assert json.loads((BASE/filename).read_text())['status']=='passed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();installed=Path(json.loads((BASE/'live_validation.json').read_text())['installed_addon']);assert sha(installed)==sha(REPO/'motion_lab/blender_ui.py')
results=[]
for file in (BASE/'jobs').glob('*/result.json'):
    r=json.loads(file.read_text());x=np.load(file.parent/'motion.npy');d=np.load(file.parent/'kinematics.npz');assert x.shape==(r['frames'],r['joints'],12) and np.isfinite(x).all();assert d['positions'].shape==(r['frames'],r['joints'],3);assert sha(file.parent/'motion.npy')==r['feature_sha256'];results.append(r['id'])
archive=BASE/'reproduction';archive.mkdir(exist_ok=False)
for folder in ['motion_lab']:
    for file in (REPO/folder).glob('*.py'):
        dest=archive/folder/file.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
for name in ['docs/unimate_motion_lab.md','tests/test_motion_lab_requests.py']:
    dest=archive/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,dest)
report=dict(status='passed',targets=counts,completed_results=results,interface='Installed Blender add-on, local GPU subprocess worker',duration_range_seconds=[2,12],native_frames=60,fps=30,longer_generation_tested_seconds=4,raw_only=True)
(BASE/'package_validation.json').write_text(json.dumps(report,indent=2)+'\n');checks={str(p.relative_to(BASE)):sha(p) for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='checksums.json'};(archive/'checksums.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(dict(**report,hashed_files=len(checks))))
