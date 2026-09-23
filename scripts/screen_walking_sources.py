#!/usr/bin/env python3
"""Screen raw AnyTop output for travel plus repeated ground-supported steps."""
import argparse
import json
from pathlib import Path
import numpy as np
from motion_lab import to_blender, smooth, detect_contacts, runs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('directories',nargs='+',type=Path)
    args=parser.parse_args()
    config=json.loads(Path('configs/hound_robot.json').read_text())
    reports=[]
    for directory in args.directories:
        for sidecar in sorted(directory.glob('*_rep_*.json')):
            metadata=json.loads(sidecar.read_text());names=metadata['joint_names']
            xyz=to_blender(np.load(directory/metadata['xyz']))
            root=names.index('Bip01_Pelvis');chest=names.index('Bip01_Neck')
            scale=float(np.median(np.linalg.norm(xyz[:,chest]-xyz[:,root],axis=-1)))
            feet=smooth(xyz[:,[names.index(limb['endpoint']) for limb in config['limbs'].values()]])
            ground=float(np.percentile(feet[...,2],5))
            contacts,_,_=detect_contacts(feet,metadata['fps'],scale,ground,config['contact'])
            travel=float(np.linalg.norm((xyz[-1,root]-xyz[0,root])[:2])/scale)
            height=float(np.percentile(xyz[:,root,2]-ground,10)/scale)
            episodes=[len(runs(contacts[:,i])) for i in range(4)]
            fractions=contacts.mean(0)
            reasons=[]
            if travel<1:reasons.append('less than one body length of travel')
            if height<.45:reasons.append('body is too low/collapsed')
            if min(episodes)<2:reasons.append('fewer than two stance episodes on each limb')
            if (fractions<.25).any() or (fractions>.9).any():reasons.append('stance fractions outside 0.25–0.90')
            reports.append(dict(source=str(sidecar),skeleton=metadata['source_skeleton'],seed=metadata['seed'],repetition=metadata['repetition'],
                                travel_body_lengths=travel,root_height_p10_body_lengths=height,stance_episodes=episodes,
                                stance_fractions=fractions.tolist(),accepted=not reasons,reasons=reasons))
    report=dict(interpretation='Heuristic acceptance for direct forward-walking transfer; failure does not establish that the model cannot generate walks.',
                thresholds=dict(minimum_travel_body_lengths=1,minimum_root_height_p10=.45,minimum_stance_episodes_per_limb=2,stance_fraction_range=[.25,.9]),
                clips=reports,accepted_count=sum(item['accepted'] for item in reports))
    assert not args.output.exists()
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(clips=len(reports),accepted=report['accepted_count'],max_travel=max(item['travel_body_lengths'] for item in reports))))


if __name__=='__main__':main()
