"""Archive experiment scripts/configs, pinned encoder metadata and output checksums."""
import hashlib,json,shutil,subprocess
from pathlib import Path
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');repo=Path(__file__).resolve().parents[1];out=BASE/'reproduction_001';out.mkdir(exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
records=[]
files=list((repo/'scripts').glob('*unimate*.py'))+list((repo/'scripts').glob('*unimate*.sh'))+list((repo/'configs').glob('unimate*'))+list((repo/'docs').glob('unimate*'))+[repo/'docs/reference/unimate_bringup_request.txt']
for f in files:
    dest=out/f.relative_to(repo);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);records.append(dict(path=str(dest),sha256=sha(dest)))
encoder=BASE/'cache/huggingface/hub/models--google--flan-t5-base/snapshots/7bcac572ce56db69c1ea7c8af255c5d7c9672fc2';enc=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(encoder.iterdir()) if p.is_file()]
(BASE/'text_encoder_manifest.json').write_text(json.dumps(dict(repo='google/flan-t5-base',revision=encoder.name,files=enc),indent=2)+'\n')
for root in [BASE/'pilgrim_harvest_001',BASE/'pilgrim_expansion_001']:
    checks=[]
    for f in sorted(root.rglob('*')):
        if f.is_file() and f.name!='checksums.json':checks.append(dict(path=str(f.relative_to(root)),bytes=f.stat().st_size,sha256=sha(f)))
    (root/'checksums.json').write_text(json.dumps(checks,indent=2)+'\n')
(out/'manifest.json').write_text(json.dumps(dict(files=records,upstream_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE/'UniMate',text=True).strip(),upstream_diff=subprocess.check_output(['git','diff','--stat'],cwd=BASE/'UniMate',text=True)),indent=2)+'\n');print('ARCHIVED',len(records))
