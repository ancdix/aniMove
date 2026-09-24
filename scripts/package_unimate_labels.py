"""Validate and archive the completed label experiment without touching older runs."""
import hashlib,json,re,shutil,subprocess
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[1];base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=base/'pilgrim_labels_001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((out/'run.json').read_text());assert len(m['runs'])==30
for r in m['runs']:
    files=list((Path(r['path'])/'samples/motions').glob('*.npy'));assert len(files)==1 and sha(files[0])==r['feature_sha256']
    x=np.load(Path(r['path'])/'raw_fk.xyz.npy');assert x.shape==(60,23,3) and np.isfinite(x).all()
    baseline=next(b for b in m['runs'] if b['variant']=='arms_legs' and b['seed']==r['seed'] and b['prompt_id']==r['prompt_id'])
    assert r['noise']==baseline['noise']
    assert all(value==baseline['condition']['cond'][key] for key,value in r['condition']['cond'].items() if key!='joint_names_emb')
    assert r['condition']['x1_known'] is None and r['condition']['keep_mask'] is None
    if r['repeat_control']:assert r['feature_sha256']==baseline['feature_sha256']
for f in ['blender_comparison_validation.json','saved_blender_validation.json','live_session.json']:assert json.loads((out/f).read_text())['status']=='passed'
videos=[]
for video in sorted((out/'review').glob('*.mp4')):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,nb_frames:format=duration','-of','json',str(video)],text=True))
    seconds=18 if video.stem=='all_pairs' else 2
    assert abs(float(info['format']['duration'])-seconds)<.02
    assert info['streams'][0]['avg_frame_rate']=='30/1'
    assert int(info['streams'][0]['nb_frames'])==seconds*30
    videos.append(dict(file=video.name,seconds=seconds,frames=seconds*30))
assert len(videos)==10
for target in re.findall(r'(?:href|src)="([^"]+)"',(out/'review/index.html').read_text()):
    assert (out/'review'/target).is_file(),target
assert len(list((out/'review').glob('p*.png')))==9
result=dict(status='passed',raw_clips=27,exact_baseline_replays=3,feature_hashes_verified=30,identical_noise_and_non_name_conditions=True,saved_blender_actions_verified=30,visual_review='All nine four-pose comparison sheets and Blender comparison render inspected; floor penetration and unreliable contact retained and documented.',videos=videos)
(out/'package_validation.json').write_text(json.dumps(result,indent=2)+'\n')
archive=out/'reproduction';archive.mkdir(exist_ok=False)
files=['unimate_condition_audit.py','run_unimate_label_ablation.py','inspect_unimate_labels.py','analyze_unimate_labels.py','preview_unimate_labels.py','unimate_labels_ui.py','build_unimate_labels_comparison.py','verify_unimate_labels.py','append_unimate_labels_live.py','package_unimate_labels.py','analyze_unimate_raw.py','build_unimate_review.py','compare_unimate_anytop.py','run_unimate_known_test.py','unimate_sample_audit.py','run_unimate_harvest.py','test_unimate_decoding.py']
for name in files:
    dest=archive/'scripts'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(repo/'scripts'/name,dest)
for relative in ['docs/unimate_joint_label_guide.md','docs/unimate_label_ablation_results.md','configs/unimate_pilgrim_prompts.json']:
    dest=archive/relative;dest.parent.mkdir(exist_ok=True);shutil.copy2(repo/relative,dest)
(archive/'README.txt').write_text('Existing completed run: '+str(out)+'\nGeneration script refuses to overwrite an existing experiment. Retain the recorded code/model/T5/dataset revisions and offline assets on ShareDrive.\nPipeline: run_unimate_label_ablation.py; inspect_unimate_labels.py; analyze_unimate_raw.py with --run; analyze_unimate_labels.py; preview_unimate_labels.py; build_unimate_review.py with --run; build_unimate_labels_comparison.py; verify_unimate_labels.py. See individual script arguments and run.json exact generation commands. Blender entry points use Blender Python. All other entry points use .venv-unimate/bin/python.\nNo post-generation motion correction.\n')
checks={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='checksums.json'}
(archive/'checksums.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(dict(status='passed',files_hashed=len(checks),clips=30,review_videos=len(videos))))
