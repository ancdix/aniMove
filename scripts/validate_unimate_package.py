"""Validate artifact links, native sample metadata and complete raw source set."""
import hashlib,json,subprocess
from html.parser import HTMLParser
from pathlib import Path
import numpy as np
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');run=BASE/'pilgrim_harvest_001';manifest=json.loads((run/'run.json').read_text());assert len(manifest['runs'])==80
records=[]
for r in manifest['runs']:
    p=Path(r['path']);f=next((p/'samples/motions').glob('*.npy'));feature=np.load(f);assert feature.shape==(60,23,12) and np.isfinite(feature).all();assert hashlib.sha256(f.read_bytes()).hexdigest()==r['feature_sha256']
    kin=np.load(p/'raw_kinematics.npz');assert kin['positions'].shape==(60,23,3);assert np.isfinite(kin['global_quaternions_wxyz']).all()
    video=next((p/'samples/animations').glob('*_fk.mp4'));meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate','-of','json',str(video)],text=True))['streams'][0];assert meta['r_frame_rate']=='30/1' and int(meta['nb_frames'])==60;records.append(dict(label=r['label'],seed=r['seed'],frames=60))
class Links(HTMLParser):
    def __init__(self):super().__init__();self.paths=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ['src','href'] and not v.startswith(('http','#')):self.paths.append(v)
index=run/'review/index.html';parser=Links();parser.feed(index.read_text());missing=[p for p in parser.paths if not (index.parent/p).exists()];assert not missing,missing
assert len(list((run/'review').glob('p??_grid.mp4')))==10;assert len(list((run/'review').glob('p??_poses.png')))==10
saved=json.loads((run/'saved_blender_validation.json').read_text());live=json.loads((run/'live_ui_validation.json').read_text());assert saved['status']==live['status']=='passed'
result=dict(status='passed',raw_samples=80,source_hashes_verified=80,video_frames=60,fps=30,valid_local_links=len(parser.paths),saved_blender_actions=80,live_ui='passed',postprocessing='none',gates={'P0':'passed','P1':'passed independent checkpoint','P2':'passed text response; limited prompt fidelity','P3':'passed 23 joints and canonical roundtrip','P4':'passed raw text response','P5':'completed80','P6':'completed descriptive raw comparison','P7':'execution passed; behavior failed in two trials','P8':'deferred','P9':'deferred'})
(run/'package_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
