#!/usr/bin/env python3
"""Validate numeric motion, BVH reconstruction, duration, and output provenance."""
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import BVH
import Animation
from generate_batch import sha256


def main():
    root = Path(sys.argv[1])
    run = json.loads((root / 'run.json').read_text())
    reports = []
    for sidecar in sorted(root.glob('*_rep_*.json')):
        item = json.loads(sidecar.read_text())
        features = np.load(root / item['features'])
        xyz = np.load(root / item['xyz'])
        frames, joints, channels = features.shape
        assert (frames, channels) == (120, 13), features.shape
        assert xyz.shape == (frames, joints, 3), xyz.shape
        assert np.isfinite(features).all() and np.isfinite(xyz).all(), 'Nonfinite motion'
        animation, names, interval = BVH.load(str(root / item['bvh']))
        bvh_xyz = Animation.positions_global(animation)
        assert bvh_xyz.shape == xyz.shape, (bvh_xyz.shape, xyz.shape)
        assert list(names) == item['joint_names'], 'BVH joint order changed'
        assert np.isfinite(bvh_xyz).all(), 'Nonfinite BVH transforms'
        assert abs(interval - 1 / item['fps']) < 1e-6, interval
        video = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_read_frames,r_frame_rate,duration', '-of', 'json',
            str(root / item['preview'])], text=True))['streams'][0]
        assert int(video['nb_read_frames']) == frames, video
        numerator, denominator = map(int, video['r_frame_rate'].split('/'))
        assert numerator / denominator == item['fps'], video
        assert abs(float(video['duration']) - frames * interval) < 0.01, video
        assert np.max(np.ptp(xyz, axis=0)) > 0.01, 'Static motion'
        reference = root / 'bvh_reference'
        reference.mkdir(exist_ok=True)
        np.save(reference / (sidecar.stem + '.npy'), bvh_xyz)
        error = np.linalg.norm(bvh_xyz - xyz, axis=-1)
        report = dict(clip=sidecar.stem, frames=frames, joints=joints, fps=item['fps'],
                      duration_seconds=frames * interval,
                      bvh_fit_mean_error=float(error.mean()), bvh_fit_max_error=float(error.max()),
                      xyz_bounds_min=xyz.min(axis=(0, 1)).tolist(),
                      xyz_bounds_max=xyz.max(axis=(0, 1)).tolist(),
                      diffusion_seconds=item['diffusion_seconds'], export_seconds=item['export_seconds'],
                      files={item[k]: sha256(root / item[k]) for k in ['features', 'xyz', 'bvh', 'preview']})
        reports.append(report)
    assert len(reports) == run['repetitions'], (len(reports), run['repetitions'])
    result = dict(status='passed', checks='finite arrays, shapes, joint order, motion, BVH/MP4 timing; fit errors reported, not quality-gated', clips=reports)
    (root / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
