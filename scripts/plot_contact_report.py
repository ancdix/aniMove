#!/usr/bin/env python3
"""Render source-quality and robot-contact diagnostics using recorded arrays."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Registers projection on upstream-pinned Matplotlib 3.1.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis', type=Path)
    parser.add_argument('robot', type=Path)
    args = parser.parse_args()
    report = json.loads(args.analysis.read_text())
    record = json.loads((args.robot / 'retarget.json').read_text())
    arrays = np.load(args.robot / 'motion.npz')
    plt.rcParams.update({'figure.facecolor': '#f5f7fa', 'axes.facecolor': '#ffffff', 'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 10})
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    clips = report['clips']
    labels = [item['id'].replace('Hound_seed0', '').replace('_rep', '/') for item in clips]
    colors = ['#168776' if item['accepted_for_prototype'] else '#c56b51' for item in clips]
    axes[0, 0].barh(labels[::-1], [item['rank_score'] for item in clips][::-1], color=colors[::-1])
    count = sum(item['accepted_for_prototype'] for item in clips)
    axes[0, 0].set(title='Heuristic screening: %d candidates / %d clips' % (count, len(clips)), xlabel='Rank score (lower is better; green passes prototype gates)')
    time = np.arange(record['frames']) / record['fps']
    for i, key in enumerate(record['config']['limbs']):
        axes[0, 1].fill_between(time, i - .35, i + .35, where=arrays['contacts'][:, i], step='mid', color='#168776')
    axes[0, 1].set(yticks=range(4), yticklabels=['A · front left', 'B · front right', 'C · rear left', 'D · rear right'], xlabel='Time (seconds)', title='Selected source: estimated stance intervals', ylim=(-.6, 3.6))
    for mode, color in [('retarget', '#d78028'), ('clean', '#1682b2')]:
        feet = arrays[mode + '_joints'][:, :, 2]
        speed = np.linalg.norm(np.diff(feet, axis=0), axis=-1) * record['fps']
        pairs = arrays['contacts'][1:] & arrays['contacts'][:-1]
        mean = np.array([s[m].mean() if m.any() else np.nan for s, m in zip(speed, pairs)])
        axes[1, 0].plot(time[1:], mean, label=mode, color=color)
        minimum = feet[..., 2].min(axis=1) - record['config']['robot']['foot_radius']
        axes[1, 1].plot(time, minimum, label=mode, color=color)
    axes[1, 0].set(title='Sliding during estimated stance (includes blends)', xlabel='Time (seconds)', ylabel='Mean endpoint speed (robot units / second)')
    axes[1, 1].axhline(0, color='#555555', linewidth=.7, linestyle='--')
    axes[1, 1].set(title='Lowest foot surface relative to estimated floor', xlabel='Time (seconds)', ylabel='Height (robot design units)')
    for ax in axes[1]:
        ax.legend()
    fig.suptitle('AnyTop → tetrapod: contact baseline\nHound seed 100 / repetition 1 · supported weight shift, not a validated walking gait', fontsize=16)
    fig.savefig(args.robot / 'contact_report.png', dpi=150)
    plt.close(fig)
    # Compare raw proposal and fitted BVH at the selected and globally worst clips.
    selected = next(clip for clip in clips if clip['id'] == record['source']['id'])
    worst = max(clips, key=lambda clip: clip['worst_fit']['error'])
    fig = plt.figure(figsize=(13, 6), constrained_layout=True)
    for column, clip in enumerate([selected, worst]):
        data = np.load(args.analysis.parent / (clip['id'] + '.npz'))
        source = json.loads(Path(clip['source']).read_text())
        frame = clip['worst_fit']['frame'] - 1
        ax = fig.add_subplot(1, 2, column + 1, projection='3d')
        for key, color, label in [('xyz', '#1682b2', 'Raw XYZ'), ('fitted_xyz', '#d78028', 'Fitted BVH')]:
            points = data[key][frame]
            for j, parent in enumerate(source['parents']):
                if parent < 0:
                    continue
                edge = points[[parent, j]]
                ax.plot(*edge.T, color=color, linewidth=1.2, alpha=.8)
            ax.scatter(*points.T, s=6, color=color, label=label)
        extent = np.concatenate([data['xyz'][frame], data['fitted_xyz'][frame]])
        center = (extent.min(axis=0) + extent.max(axis=0)) / 2
        radius = np.ptp(extent, axis=0).max() * .55
        ax.set(xlim=(center[0]-radius, center[0]+radius), ylim=(center[1]-radius, center[1]+radius), zlim=(center[2]-radius, center[2]+radius), xlabel='X', ylabel='Y', zlabel='Z')
        if hasattr(ax, 'set_box_aspect'):
            ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=20, azim=-60)
        ax.set_title('%s · frame %d\nWorst joint error %.3f source units' % (clip['id'], frame + 1, clip['worst_fit']['error']))
        ax.legend(loc='upper left')
    fig.suptitle('Separate diffusion-position distortion from BVH fitting error', fontsize=15)
    fig.savefig(args.robot / 'source_fit_diagnostics.png', dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    main()
