"""Verify raw provenance, matched controls, constraints, previews and live review."""
import hashlib,json,re,shutil,subprocess
from pathlib import Path
import numpy as np
base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=base/'pilgrim_guided_001';repo=Path(__file__).resolve().parents[1];m=json.loads((out/'review_run.json').read_text());g=json.loads((out/'run.json').read_text());a=json.loads((out/'analysis.json').read_text());prior=json.loads((base/'pilgrim_stance_001/run.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len(m['runs'])==18 and len(g['runs'])==9
assert sha(out/'condition/cond.npy')==sha(base/'pilgrim_stance_001/conditions/quadruped/cond.npy')
for r in m['runs']:
    files=list((Path(r['source_path'])/'samples/motions').glob('*.npy'));assert len(files)==1 and sha(files[0])==r['feature_sha256'];x=np.load(Path(r['path'])/'raw_fk.xyz.npy');assert x.shape==(60,23,3) and np.isfinite(x).all()
for seed in g['seeds']:
    rs=[r for r in g['runs'] if r['seed']==seed];assert len(rs)==3
    assert len(set(r['audit']['noise_sha256'] for r in rs))==1
    assert all(r['audit']['condition_hashes']==rs[0]['audit']['condition_hashes'] for r in rs)
    old=next(r for r in prior['runs'] if r['variant']=='quadruped' and r['prompt_id']=='walk' and r['seed']==seed)
    assert rs[0]['audit']['noise_sha256']==old['noise']['sha256']
    for mode in ['dog','cat']:
        audit=json.loads((base/'pilgrim_animal_words_001'/f'{mode}_{seed}'/'noise_audit.json').read_text());assert audit['draws'][0]['sha256']==old['noise']['sha256']
known=np.load(out/'authored_features.npy')
for mode in g['variants']:
    mask=np.load(out/(mode+'_mask.npy'));assert mask.shape==(60,23,12)
    if mode=='euler_free':assert not mask.any()
    else:
        assert mask[[0,29,59],:,:9].all();assert not mask[:,1:,9:].any()
        free=mask.copy();free[[0,29,59],:,:9]=False
        if mode=='poses':assert not free.any()
        else:assert mask[:,0,:].all() and not free[:,1:].any()
for r in a['records']:
    if r['variant'] in ['poses','poses_root']:
        assert r['metrics']['constrained_feature_max_error']<1e-5
        assert r['metrics']['anchor_root_relative_max_error_m']<1e-4
        if r['variant']=='poses_root':assert r['metrics']['root_path_max_error_m']<1e-5
for name in ['guide_validation.json','saved_blender_validation.json','live_session.json']:assert json.loads((out/name).read_text())['status']=='passed'
videos=list((out/'review').glob('*.mp4'));assert len(videos)==6
for video in videos:
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,nb_frames:format=duration','-of','json',str(video)],text=True));assert p['streams'][0]['avg_frame_rate']=='30/1' and int(p['streams'][0]['nb_frames'])==60 and abs(float(p['format']['duration'])-2)<.02
for target in re.findall(r'(?:href|src)="([^"]+)"',(out/'review/index.html').read_text()):assert (out/'review'/target).is_file(),target
result=dict(status='passed',new_samples=15,reviewed_samples=18,wording_matched_seeds=3,guidance_matched_seeds=3,paired_videos=6,accepted_quadrupedal_walks=0,visual_review='All six three-way pose/contact sheets, authored poses and Blender render reviewed.',post_generation_cleanup='none',full_transition_assembled=False)
(out/'package_validation.json').write_text(json.dumps(result,indent=2)+'\n');archive=out/'reproduction';archive.mkdir(exist_ok=False)
names=['prepare_unimate_guided','unimate_guided_sample','run_unimate_guided','analyze_unimate_guided','preview_unimate_guided','build_unimate_guided_review','unimate_guided_ui','verify_unimate_guided','append_unimate_guided_live','package_unimate_guided','run_unimate_known_test','unimate_sample_audit','analyze_unimate_raw','compare_unimate_anytop']
for filename in [f'scripts/{n}.py' for n in names]+['configs/unimate_animal_walk_prompts.json','docs/unimate_guided_results.md','docs/unimate_pilgrim_plan.md','docs/unimate_support_transition_plan.md']:
    p=archive/filename;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/filename,p)
checks={}
for folder in [out,base/'pilgrim_animal_words_001']:
    for p in sorted(folder.rglob('*')):
        if p.is_file() and p.name!='checksums.json':checks[str(p.relative_to(base))]=sha(p)
(archive/'checksums.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(dict(**result,hashed_files=len(checks))))
