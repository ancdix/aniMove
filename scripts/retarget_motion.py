#!/usr/bin/env python3
"""Build a reproducible four-chain task-space baseline from screened raw XYZ."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_lab import normalize, pin_contacts, reach_bounds, slip_speed, smooth, two_bone


def solve(core, rotation, targets, source_bends, contacts, config, correct_root):
    robot = config['robot']
    upper, lower = robot['upper_length'], robot['lower_length']
    limits = (robot['flexion_min_degrees'], robot['flexion_max_degrees'])
    _, max_reach = reach_bounds(upper, lower, *limits)
    attachment = np.array([limb['hip'] for limb in config['limbs'].values()])
    roots = core.copy()
    joints = np.empty((len(core), 4, 3, 3))
    poles = np.empty((len(core), 4, 3))
    projection = np.zeros((len(core), 4))
    flexions = np.zeros_like(projection)
    previous = [None] * 4
    for frame in range(len(core)):
        offsets = attachment @ rotation[frame].T
        if correct_root:
            # Project the core into the intersection of support-limb reach balls.
            # Residual infeasibility is retained in projection, never silently hidden.
            for _ in range(40):
                largest = 0
                for limb in np.flatnonzero(contacts[frame]):
                    delta = roots[frame] + offsets[limb] - targets[frame, limb]
                    distance = np.linalg.norm(delta)
                    excess = max(0, distance - max_reach * 0.98)
                    roots[frame] -= normalize(delta) * excess
                    largest = max(largest, excess)
                if largest < 1e-7:
                    break
        for limb in range(4):
            hip = roots[frame] + offsets[limb]
            direction = normalize(targets[frame, limb] - hip, (0, 0, -1))
            bend = source_bends[frame, limb] - hip
            bend -= np.dot(bend, direction) * direction
            if np.linalg.norm(bend) < 0.03:
                bend = previous[limb] if previous[limb] is not None else rotation[frame, :, 1]
            bend = normalize(bend)
            if previous[limb] is not None:
                if np.dot(bend, previous[limb]) < 0:
                    bend *= -1
                bend = normalize(0.75 * previous[limb] + 0.25 * bend)
            elbow, endpoint, plane, error, flexion = two_bone(hip, targets[frame, limb], bend, upper, lower, limits)
            previous[limb] = plane
            joints[frame, limb] = [hip, elbow, endpoint]
            poles[frame, limb] = hip + plane * 1.2
            projection[frame, limb], flexions[frame, limb] = error, flexion
    return dict(core=roots, joints=joints, poles=poles, projection=projection, flexions=flexions,
                root_correction=roots - core)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis', type=Path)
    parser.add_argument('--clip')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    analysis = json.loads(args.analysis.read_text())
    selected = args.clip or analysis['selected']
    report = next(item for item in analysis['clips'] if item['id'] == selected)
    if not report['accepted_for_prototype']:
        raise ValueError('Source clip failed screening: ' + str(report['rejection_reasons']))
    config = analysis['config']
    metadata = json.loads(Path(report['source']).read_text())
    arrays = np.load(args.analysis.parent / (selected + '.npz'))
    xyz = arrays['smoothed_xyz'].copy()
    names = metadata['joint_names']
    idx = lambda key: names.index(config[key])
    scale = config['robot']['body_length'] / report['body_length']
    origin = xyz[0, idx('root')].copy()
    origin[2] = report['estimated_ground']
    xyz = (xyz - origin) * scale
    # Foot sphere centers, rather than their bottoms, are the end-effector targets.
    radius = config['robot']['foot_radius']
    xyz[..., 2] += radius
    core = (xyz[:, idx('root')] + xyz[:, idx('chest')]) / 2
    rotation = []
    for backward in xyz[:, idx('root')] - xyz[:, idx('chest')]:
        y = normalize(backward, (0, 1, 0))
        x = normalize(np.cross(y, [0, 0, 1]))
        z = normalize(np.cross(x, y))
        rotation.append(np.column_stack((x, y, z)))
    rotation = np.asarray(rotation)
    feet = xyz[:, [names.index(limb['endpoint']) for limb in config['limbs'].values()]]
    bends = xyz[:, [names.index(limb['bend']) for limb in config['limbs'].values()]]
    contacts = arrays['contacts']
    clean, weights, anchors = pin_contacts(feet, contacts, radius, config['contact']['blend_frames'])
    result = dict(rotation=rotation, contacts=contacts, contact_weights=weights, anchors=anchors,
                  raw_targets=feet, clean_targets=clean,
                  local_targets=np.einsum('fji,flj->fli', rotation, feet - core[:, None]),
                  head_direction=np.array([normalize(v, (0, -1, 0)) for v in xyz[:, idx('nose')] - xyz[:, idx('head')]]))
    metrics = {}
    for name, targets in [('retarget', feet), ('clean', clean)]:
        solved = solve(core, rotation, targets, bends, contacts, config, name == 'clean')
        result.update({name + '_' + key: value for key, value in solved.items()})
        tips = solved['joints'][:, :, 2]
        metrics[name] = dict(
            contact_slip=slip_speed(tips, contacts, metadata['fps']),
            fully_pinned_slip=slip_speed(tips, weights >= 1 - 1e-9, metadata['fps']),
            max_foot_penetration=float(np.maximum(0, radius - tips[..., 2]).max()),
            max_target_projection=float(solved['projection'].max()),
            projected_frames_limbs=np.argwhere(solved['projection'] > 1e-6).tolist(),
            maximum_root_correction=float(np.linalg.norm(solved['root_correction'], axis=-1).max()),
            flexion_range_degrees=[float(solved['flexions'].min()), float(solved['flexions'].max())],
            minimum_reach_margin=float(1 - np.linalg.norm(tips - solved['joints'][:, :, 0], axis=-1).max() / (config['robot']['upper_length'] + config['robot']['lower_length'])))
    assert np.isfinite(result['clean_joints']).all()
    assert metrics['clean']['max_target_projection'] < 1e-5, 'Unreachable clean targets; inspect root/scale'
    assert metrics['clean']['fully_pinned_slip'] < 1e-6, 'Pinning did not hold'
    assert metrics['clean']['max_foot_penetration'] < 1e-6
    args.output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(args.output / 'motion.npz', **result)
    record = dict(schema=1, source=report, config=config, fps=metadata['fps'], frames=metadata['frames'],
                  source_to_robot_scale=scale, origin_blender_units=origin.tolist(),
                  units='robot design units; body length 0.9, not a physical calibration',
                  analysis_sha256=hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
                  filtering='Two binomial smoothing passes (five-frame support); no temporal resampling',
                  metrics=metrics, contact_interpretation='Estimated flat-ground stance, not measured forces. This selected clip is a supported weight shift, not an accepted walking gait.')
    (args.output / 'retarget.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
