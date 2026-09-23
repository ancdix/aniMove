#!/usr/bin/env python3
"""Score unique raw clips and export reproducible source contact diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_lab import detect_contacts, runs, slip_speed, smooth, to_blender


def analyze(sidecar, config):
    metadata = json.loads(sidecar.read_text())
    names = metadata['joint_names']
    raw = np.load(sidecar.parent / metadata['xyz'])
    xyz = to_blender(raw)
    fitted = to_blender(np.load(sidecar.parent / 'bvh_reference' / (sidecar.stem + '.npy')))
    idx = lambda name: names.index(name)
    endpoints = [idx(limb['endpoint']) for limb in config['limbs'].values()]
    major = [idx(config['root']), idx(config['chest'])] + endpoints + [idx(limb['bend']) for limb in config['limbs'].values()]
    body = float(np.median(np.linalg.norm(xyz[:, idx(config['chest'])] - xyz[:, idx(config['root'])], axis=-1)))
    stable = smooth(xyz)
    feet = stable[:, endpoints]
    ground = float(np.percentile(feet[..., 2], config['contact']['ground_percentile']))
    contacts, speed, height = detect_contacts(feet, metadata['fps'], body, ground, config['contact'])
    errors = np.linalg.norm(xyz - fitted, axis=-1)
    parents = np.asarray(metadata['parents'])
    lengths = np.linalg.norm(xyz[:, 1:] - xyz[:, parents[1:]], axis=-1)
    fitted_lengths = np.linalg.norm(fitted[:, 1:] - fitted[:, parents[1:]], axis=-1)
    worst = np.unravel_index(errors.argmax(), errors.shape)
    jerk = np.linalg.norm(np.diff(xyz[:, major], n=3, axis=0), axis=-1) * metadata['fps']**3 / body
    q = config['quality']
    scores = dict(endpoint_fit_mean=float(errors[:, endpoints].mean() / body),
                  collapsed_fraction=float(np.mean((xyz[:, idx(config['root']), 2] - ground) / body < q['minimum_root_height'])),
                  jerk_p95=float(np.percentile(jerk, 95)),
                  supported_fraction=float(contacts.any(axis=1).mean()),
                  contact_slip_body_lengths_per_second=slip_speed(feet / body, contacts, metadata['fps']),
                  penetration_p95_body_lengths=float(np.percentile(np.maximum(0, ground - feet[..., 2]) / body, 95)),
                  bone_length_error_p95_body_lengths=float(np.percentile(abs(lengths - fitted_lengths), 95) / body),
                  body_length_variation=float(np.std(np.linalg.norm(xyz[:, idx(config['chest'])] - xyz[:, idx(config['root'])], axis=-1)) / body),
                  endpoint_loop_seam_body_lengths=float(np.mean(np.linalg.norm((feet[-1] - xyz[-1, 0]) - (feet[0] - xyz[0, 0]), axis=-1)) / body))
    failures = []
    for score, threshold in [('collapsed_fraction', 'maximum_collapsed_fraction'), ('endpoint_fit_mean', 'maximum_endpoint_fit_mean'), ('jerk_p95', 'maximum_jerk_p95')]:
        if scores[score] > q[threshold]:
            failures.append('%s %.4f > %.4f' % (score, scores[score], q[threshold]))
    if scores['supported_fraction'] < q['minimum_supported_fraction']:
        failures.append('insufficient detected ground support')
    # Rank only gate-passing candidates: lower fit error, jitter and stance slip win.
    score = scores['endpoint_fit_mean'] + scores['jerk_p95'] / 1000 + (scores['contact_slip_body_lengths_per_second'] or 0) / 4
    report = dict(id='Hound_seed%04d_rep%02d' % (metadata['seed'], metadata['repetition']), source=str(sidecar),
                  xyz_sha256=hashlib.sha256((sidecar.parent / metadata['xyz']).read_bytes()).hexdigest(),
                  frames=metadata['frames'], fps=metadata['fps'], body_length=body, estimated_ground=ground,
                  accepted_for_prototype=not failures, rejection_reasons=failures, rank_score=score, scores=scores,
                  worst_fit=dict(frame=int(worst[0] + 1), joint=names[worst[1]], error=float(errors[worst])),
                  contact_intervals={key: [[int(start + 1), int(stop)] for start, stop in runs(contacts[:, i])] for i, key in enumerate(config['limbs'])})
    return report, dict(xyz=xyz, smoothed_xyz=stable, feet=feet, contacts=contacts, speed=speed, height=height, fitted_xyz=fitted)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('configs/hound_robot.json'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('runs', nargs='+', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    reports, hashes = [], set()
    for directory in args.runs:
        for sidecar in sorted(directory.glob('*_rep_*.json')):
            report, arrays = analyze(sidecar, config)
            if report['xyz_sha256'] in hashes:
                continue
            hashes.add(report['xyz_sha256'])
            np.savez_compressed(args.output / (report['id'] + '.npz'), **arrays)
            reports.append(report)
    reports.sort(key=lambda item: (not item['accepted_for_prototype'], item['rank_score']))
    candidates = [report for report in reports if report['accepted_for_prototype']]
    result = dict(schema=1, config=config, selected=candidates[0]['id'] if candidates else None, clips=reports,
                  interpretation='Heuristic screening for a ground-support prototype, not biological or physical validation. Ground estimated from endpoint height; contacts are hypotheses. No loop acceptance implied.')
    (args.output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
