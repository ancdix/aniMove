#!/usr/bin/env python3
"""Controlled walking with explicit stance anchors and bounded AnyTop body detail.

This is a procedural locomotion controller, not a claim of direct diffusion walk
generation. Source provenance and the controlled contributions remain explicit.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from motion_lab import normalize, smooth, to_blender, slip_speed
from retarget_motion import solve
from collision import audit, clean_bend_planes


def footstep_targets(time, period=1.6, speed=.38, duty=.75, height=.16, radius=.035):
    phases = np.array([.25, .75, 0., .5])
    nominal = np.array([[.55,-.45,0],[-.55,-.45,0],[.55,.45,0],[-.55,.45,0]])
    feet, contacts = [], []
    for t in time:
        phase = t / period + phases
        cycle, local = np.floor(phase), phase % 1
        start_time = (cycle - phases) * period
        row = nominal.copy()
        row[:, 1] -= speed * start_time + speed * duty * period / 2
        row[:, 2] = radius
        stance = local < duty
        for limb in range(4):
            if not stance[limb]:
                u = (local[limb] - duty) / (1 - duty)
                progress = u**3 * (10 - 15*u + 6*u*u)
                row[limb, 1] -= speed * period * progress
                row[limb, 2] += height * 64 * u**3 * (1-u)**3
        feet.append(row)
        contacts.append(stance)
    return np.array(feet), np.array(contacts)


def build_motion(source, base_config, fps=30, seconds=8):
    metadata = json.loads(source.read_text())
    xyz = smooth(to_blender(np.load(source.parent / metadata['xyz'])), passes=4)
    names = metadata['joint_names']
    config = copy.deepcopy(base_config)
    for key, limb in config['limbs'].items():
        limb['hip'][0] = .35 if key in ('A','C') else -.35
    count = int(fps * seconds)
    time = np.arange(count) / fps
    feet, contacts = footstep_targets(time)
    idx = lambda name: names.index(base_config[name])
    body = xyz[:, idx('chest')] - xyz[:, idx('root')]
    center = (xyz[:, idx('root')] + xyz[:, idx('chest')]) / 2
    head = xyz[:, idx('nose')] - xyz[:, idx('head')]
    def sample(value):
        return np.interp(np.linspace(0, len(value)-1, count), np.arange(len(value)), value)
    source_yaw = np.unwrap(np.arctan2(body[:,0], -body[:,1]))
    source_yaw -= source_yaw[0]
    source_pitch = np.arctan2(body[:,2], np.linalg.norm(body[:,:2], axis=1))
    yaw = .035 * np.tanh(sample(source_yaw) / .1)
    pitch = -.04 * np.tanh(sample(source_pitch) / .15)
    bob = .02 * np.tanh(sample(center[:,2]-np.median(center[:,2])) / .05)
    core = np.column_stack((.012*np.sin(2*np.pi*time/1.6), -.38*time, 1.02+bob+.008*np.cos(4*np.pi*time/1.6)))
    rotation = []
    headings = []
    head_pitch = .18 * np.tanh(sample(np.arctan2(head[:,2], np.linalg.norm(head[:,:2], axis=1))) / .5)
    for y, p, h in zip(yaw, pitch, head_pitch):
        rz=np.array([[np.cos(y),-np.sin(y),0],[np.sin(y),np.cos(y),0],[0,0,1]])
        rx=np.array([[1,0,0],[0,np.cos(p),-np.sin(p)],[0,np.sin(p),np.cos(p)]])
        rotation.append(rz@rx)
        headings.append(rz@np.array([0,-np.cos(h),np.sin(h)]))
    rotation, headings = np.array(rotation), np.array(headings)
    # A naive inward-pole walk is retained only as an explicitly labelled control.
    bends = np.empty_like(feet)
    for limb in range(4):
        local = np.array([-.15 if limb in (0,2) else .15, 0, -.4])
        bends[:,limb] = core + np.einsum('fij,j->fi',rotation,local)
    before = solve(core, rotation, feet, bends, contacts, config, True)
    after = clean_bend_planes(before, feet, rotation, headings, config)
    collision_before = audit(before['joints'], before['core'], rotation, headings)
    collision_after = audit(after['joints'], after['core'], rotation, headings)
    assert collision_after['margin_violation_count'] == 0, collision_after['worst']
    assert after['projection'].max() < 1e-6
    assert slip_speed(after['joints'][:,:,2], contacts, fps) < 1e-6
    result = dict(rotation=rotation, head_direction=headings, contacts=contacts, contact_weights=contacts.astype(float),
                  anchors=np.where(contacts[:,:,None], feet, np.nan), raw_targets=feet, clean_targets=feet,
                  local_targets=np.einsum('fji,flj->fli',rotation, feet-core[:,None]))
    for label, data in [('retarget',before),('clean',after)]:
        result.update({label+'_'+key:value for key,value in data.items()})
    metrics={}
    for label, data in [('retarget',before),('clean',after)]:
        tips=data['joints'][:,:,2]
        metrics[label]=dict(contact_slip=slip_speed(tips,contacts,fps),fully_pinned_slip=slip_speed(tips,contacts,fps),
                           max_foot_penetration=float(np.maximum(0,.035-tips[...,2]).max()),max_target_projection=float(data['projection'].max()),
                           maximum_root_correction=float(np.linalg.norm(data['root_correction'],axis=1).max()),
                           flexion_range_degrees=[float(data['flexions'].min()),float(data['flexions'].max())])
    record=dict(schema=2,source=dict(id='Controlled_Walk_AnyTop_Hound100_01',source=str(source)), config=config, fps=fps,frames=count,
                units='robot design units, not calibrated physical meters', metrics=metrics,
                construction='Procedural four-beat footstep controller + bounded AnyTop torso/head variation. Not a diffusion-generated walking gait.',
                gait=dict(period_seconds=1.6,speed=.38,stance_fraction=.75,swing_height=.16,phase_offsets=[.25,.75,0,.5],
                          forward_distance=float(core[0,1]-core[-1,1]),support_count_range=[int(contacts.sum(1).min()),int(contacts.sum(1).max())]),
                collision_before=collision_before,collision_after=collision_after,
                collision_before_description='Naive inward-pole IK control on the same walking targets; not an AnyTop-generated walk.',
                character='Three feet support while one swings; fixed world-space stance points and continuous swing position/velocity/acceleration.')
    return result, record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    config=json.loads(Path('configs/hound_robot.json').read_text())
    arrays,record=build_motion(args.source,config)
    args.output.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(args.output/'motion.npz',**arrays)
    (args.output/'retarget.json').write_text(json.dumps(record,indent=2)+'\n')
    compact={key:record[key] for key in ['construction','gait','metrics']}
    compact['collisions']={label:{key:value for key,value in record['collision_'+label].items() if key!='violations'} for label in ['before','after']}
    print(json.dumps(compact,indent=2))


if __name__=='__main__':
    main()
