"""Validate and archive the reference-stance experiment without altering raw motion."""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
import numpy as np

repo = Path(__file__).resolve().parents[1]
base = Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
out = base / 'pilgrim_stance_001'
manifest = json.loads((out / 'run.json').read_text())
prior = json.loads((base / 'pilgrim_support_short_001/run.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert len(manifest['runs']) == 18
for r in manifest['runs']:
    folder = Path(r['path'])
    features = list((folder / 'samples/motions').glob('*.npy'))
    assert len(features) == 1 and sha(features[0]) == r['feature_sha256']
    x = np.load(folder / 'raw_fk.xyz.npy')
    assert x.shape == (60, 23, 3) and np.isfinite(x).all()
    assert r['condition']['x1_known'] is None and r['condition']['keep_mask'] is None
    if r['variant'] == 'upright':
        old = next(q for q in prior['runs'] if q['seed'] == r['seed'] and q['prompt_id'] == r['prompt_id'])
        assert all(r[k] == old[k] for k in ['feature_sha256', 'noise', 'condition'])
    else:
        control = next(q for q in manifest['runs'] if q['variant'] == 'upright' and q['seed'] == r['seed'] and q['prompt_id'] == r['prompt_id'])
        assert r['noise'] == control['noise']
        changed = {k for k, v in r['condition']['cond'].items() if v != control['condition']['cond'][k]}
        assert changed == {'tpos_first_frame', 'tpos_first_frame_parents', 'offsets'}

conds = {v: np.load(out / 'conditions' / v / 'cond.npy', allow_pickle=True).item()['Pilgrim'] for v in manifest['variants']}
for key in ['parents', 'joint_names', 'clean_joint_names']:
    assert np.array_equal(conds['upright'][key], conds['quadruped'][key])
lengths = []
for c in conds.values():
    pos = np.asarray(c['tpos_first_frame'])
    lengths.append(np.linalg.norm(pos[1:] - pos[np.asarray(c['parents'])[1:]], axis=-1))
assert np.max(np.abs(lengths[0] - lengths[1])) < 1e-12

videos = list((out / 'review').glob('*.mp4'))
assert len(videos) == 9
for video in videos:
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=avg_frame_rate,nb_frames:format=duration', '-of', 'json', str(video)], text=True))
    assert info['streams'][0]['avg_frame_rate'] == '30/1'
    assert int(info['streams'][0]['nb_frames']) == 60
    assert abs(float(info['format']['duration']) - 2) < .02
for target in re.findall(r'(?:href|src)="([^"]+)"', (out / 'review/index.html').read_text()):
    assert (out / 'review' / target).is_file(), target
for filename in ['stance_validation.json', 'saved_blender_validation.json', 'live_session.json']:
    assert json.loads((out / filename).read_text())['status'] == 'passed'
result = dict(status='passed', raw_samples_verified=18, exact_baseline_replays=9,
              matched_reference_pairs=9, paired_videos_verified=9,
              visually_accepted_quadrupedal_walks=0,
              useful_partial_cases=['quadruped_walk_9700', 'quadruped_crawl_9701'],
              visual_review='All nine paired six-pose/contact sheets and Blender reference render inspected.',
              postprocessing='none', full_transition_assembled=False)
(out / 'package_validation.json').write_text(json.dumps(result, indent=2) + '\n')
archive = out / 'reproduction'
archive.mkdir(exist_ok=False)
scripts = ['prepare_unimate_stance', 'run_unimate_stance', 'analyze_unimate_stance',
           'preview_unimate_stance', 'build_unimate_stance_review', 'unimate_stance_ui',
           'verify_unimate_stance', 'append_unimate_stance_live', 'package_unimate_stance',
           'analyze_unimate_raw', 'compare_unimate_anytop', 'run_unimate_known_test',
           'unimate_condition_audit', 'unimate_sample_audit', 'test_unimate_decoding']
files = [f'scripts/{s}.py' for s in scripts] + ['configs/unimate_support_short_prompts.json',
         'docs/unimate_stance_results.md', 'docs/unimate_support_transition_plan.md', 'docs/unimate_pilgrim_plan.md']
for name in files:
    target = archive / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / name, target)
checks = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'checksums.json'}
(archive / 'checksums.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps(dict(**result, files_hashed=len(checks))))
