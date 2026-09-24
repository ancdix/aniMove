"""Archive raw support evidence and make a labeled three-way preview."""
import hashlib,json,re,shutil,subprocess
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[1];base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=base/'pilgrim_support_review_001';m=json.loads((out/'run.json').read_text());a=json.loads((base/'pilgrim_support_001/run.json').read_text());b=json.loads((base/'pilgrim_support_short_001/run.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in m['runs']:
    files=list((Path(r['path'])/'samples/motions').glob('*.npy'));assert len(files)==1 and sha(files[0])==r['feature_sha256']
    x=np.load(Path(r['path'])/'raw_fk.xyz.npy');assert x.shape==(60,23,3) and np.isfinite(x).all()
    video=next((Path(r['path'])/'samples/animations').glob('*_fk.mp4'))
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,nb_frames:format=duration','-of','json',str(video)],text=True));assert info['streams'][0]['avg_frame_rate']=='30/1' and int(info['streams'][0]['nb_frames'])==60 and abs(float(info['format']['duration'])-2)<.02
for r in a['runs']:
    if r['variant']!='front_hind':continue
    q=next(q for q in a['runs'] if q['variant']=='arms_legs' and q['seed']==r['seed'] and q['prompt_id']==r['prompt_id']);assert r['noise']==q['noise'];assert all(val==q['condition']['cond'][k] for k,val in r['condition']['cond'].items() if k!='joint_names_emb')
for r in b['runs']:
    q=next(q for q in a['runs'] if q['variant']==r['variant'] and q['seed']==r['seed'] and q['prompt_id']=={'walk':'biped','quad':'quad','crawl':'crawl'}[r['prompt_id']]);assert r['noise']==q['noise'];assert all(val==q['condition']['cond'][k] for k,val in r['condition']['cond'].items() if k not in ['caption','caption_emb','caption_tokens','caption_mask'])
for r in a['runs']+b['runs']:assert r['condition']['x1_known'] is None and r['condition']['keep_mask'] is None
for filename in ['saved_blender_validation.json','live_session.json']:assert json.loads((out/filename).read_text())['status']=='passed'
for folder,index in [(out,'index.html'),(base/'pilgrim_support_001/review','index.html'),(base/'pilgrim_support_short_001/review','index.html')]:
    for target in re.findall(r'(?:href|src)="([^"]+)"',(folder/index).read_text()):assert (folder/target).is_file(),target
chosen=[('walk',9701,'WALK - BIPEDAL'),('quad',9701,'ALL FOURS - REJECTED'),('crawl',9702,'CRAWL - REJECTED')];cmd=['ffmpeg','-y','-v','error'];filters=[]
for i,(pid,seed,title) in enumerate(chosen):
    r=next(r for r in b['runs'] if r['prompt_id']==pid and r['seed']==seed);video=next((Path(r['path'])/'samples/animations').glob('*_fk.mp4'));cmd+=['-i',str(video)];filters.append(f'[{i}:v]scale=480:480:force_original_aspect_ratio=decrease,pad=480:514:(ow-iw)/2:34,drawtext=text={title}:fontcolor=white:fontsize=20:x=8:y=5[v{i}]')
filters.append('[v0][v1][v2]hstack=inputs=3[v]');cmd+=['-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[v]','-an','-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p',str(out/'support_comparison.mp4')];subprocess.run(cmd,check=True)
index=out/'index.html';page=index.read_text().replace('</body>','<h2>Illustrative short-prompt results</h2><p>Different seeds/noise between columns; selected examples, not a paired prompt comparison. All raw, no corrections.</p><video controls loop muted src="support_comparison.mp4"></video></body>');index.write_text(page)
result=dict(status='passed',raw_samples_verified=28,new_samples=27,requested_quad_or_crawl_samples=18,visually_accepted_quadrupedal_phrases=0,permissive_screen_false_positives=1,matched_name_pairs=9,matched_detailed_vs_short_prompt_pairs=9,saved_actions=28,visual_review='All 27 six-pose/contact sheets and saved Blender render inspected. Four-limb gait gate unmet. No transitions assembled.',postprocessing='none',preview_selection=chosen)
(out/'package_validation.json').write_text(json.dumps(result,indent=2)+'\n')
archive=out/'reproduction';archive.mkdir(exist_ok=False)
files=['scripts/run_unimate_support_probe.py','scripts/review_unimate_support.py','scripts/combine_unimate_support.py','scripts/finalize_unimate_support_blender.py','scripts/verify_unimate_support.py','scripts/append_unimate_support_live.py','scripts/package_unimate_support.py','scripts/unimate_condition_audit.py','scripts/run_unimate_known_test.py','scripts/analyze_unimate_raw.py','scripts/compare_unimate_anytop.py','scripts/build_unimate_review.py','scripts/unimate_review_ui.py','configs/unimate_support_prompts.json','configs/unimate_support_short_prompts.json','docs/unimate_support_transition_plan.md','docs/unimate_support_transition_results.md']
for name in files:
    target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/name,target)
checks={}
for folder in [base/'pilgrim_support_001',base/'pilgrim_support_short_001',out]:
    for p in sorted(folder.rglob('*')):
        if p.is_file() and p.name!='checksums.json':checks[str(p.relative_to(base))]=sha(p)
(archive/'checksums.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(dict(**result,files_hashed=len(checks))))
