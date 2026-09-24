"""Preserve a direct AnyTop phrase; close its boundary and solve explicit contacts."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from motion_lab import normalize,two_bone
from collision import segment_distance
from pilgrim_skeleton import audit


def periodic_bridge(values,window=12):
    """Replace only the boundary neighborhood with a C1 Hermite bridge."""
    x=np.array(values,dtype=float,copy=True);n=len(x);a=n-window;b=window
    if window<2 or 2*window>=n:raise ValueError('Boundary window must be at least 2 and less than half the clip')
    va=(x[a+1]-x[a-1])/2;vb=(x[b+1]-x[b-1])/2;pa=x[a].copy();pb=x[b].copy();span=2*window
    for t in range(1,span):
        u=t/span
        x[(a+t)%n]=(2*u**3-3*u**2+1)*pa+(u**3-2*u**2+u)*span*va+(-2*u**3+3*u**2)*pb+(u**3-u**2)*span*vb
    return x


def stats(delta):
    e=np.linalg.norm(delta,axis=-1)
    return dict(rms=float(np.sqrt(np.mean(e**2))),p95=float(np.percentile(e,95)),max=float(e.max()))


def prepare(pilot,blockout,output,hand_offset=.34):
    run=json.loads((pilot/'run.json').read_text());d=json.loads((blockout/'skeleton.json').read_text());ix={n:i for i,n in enumerate(d['names'])}
    name='Pilgrim_bipeds_seed5100';scale=run['normalized_units_per_design_meter'];parents=np.array(d['parents']);rest=np.array(d['rest']);lengths=np.linalg.norm(np.array(d['offsets']),axis=-1)
    d['ring']['axial_offset']=-.05;d['ring']['limb_capsule_radius']=.095;d['ring']['carrier']='SPINE_02'
    raw=np.load(pilot/(name+'.xyz.npy'))/scale;fitted=np.load(pilot/(name+'.fitted.xyz.npy'))/scale
    raw[:,:,1]+=.06;fitted[:,:,1]+=.06
    loop=periodic_bridge(fitted);normalized=loop.copy()
    for j,p in enumerate(parents):
        if p>=0:
            v=loop[:,j]-loop[:,p];v/=np.linalg.norm(v,axis=-1)[:,None];normalized[:,j]=normalized[:,p]+v*lengths[j]
    clean=normalized.copy();anchors=np.median(loop[:,d['contact_joints']],axis=0);anchors[:,1]=.06
    targets=normalized[:,d['contact_joints']].copy();targets[:,2:]=anchors[None,2:]
    # A static lane offset retains the free hand's learned time variation.
    targets[:,1,0]-=hand_offset
    targets[:,1,1]+=.085
    poles=[];reach=[];bend_changes=[]
    for f,frame in enumerate(clean):
        fp=[];fr=[];fb=[]
        for li,key in enumerate('ABCD'):
            js=[ix[key+'_'+str(k)] for k in range(4)];sign=1 if key in 'AC' else -1
            upper,lower,dist=np.linalg.norm(np.diff(rest[js],axis=0),axis=-1)
            # Editable distal orientation starts at the rest direction; ground pads are flat.
            distal=normalize(rest[js[3]]-rest[js[2]])*dist
            wrist=targets[f,li]-distal;hip=frame[js[0]]
            source_bend=normalize(normalized[f,js[1]]-hip)
            preferred=normalize([sign*(1.0 if key in 'AB' else .22),.05,.2 if key in 'AB' else 1.0])
            # Preserve source bend when it remains separated; rear source bends are retained initially.
            direction=normalize(source_bend+(.5*preferred if key=='B' else 0))
            e,w,bend,error,_=two_bone(hip,wrist,direction,upper,lower,(2,165))
            frame[js[1]]=e;frame[js[2]]=w;frame[js[3]]=w+distal
            fp.append(hip+bend*.85);fr.append(error);fb.append(np.linalg.norm(e-normalized[f,js[1]]))
        poles.append(fp);reach.append(fr);bend_changes.append(fb)
    collision=audit(d,clean)
    metrics=dict(fitting=stats(fitted-raw),boundary_bridge=stats(loop-fitted),fixed_length_after_bridge=stats(normalized-loop),contact_and_lane_cleanup=stats(clean-normalized),total_from_fitted=stats(clean-fitted),total_from_raw=stats(clean-raw),
                 root_change=stats(clean[:,0]-fitted[:,0]),max_reach_projection=float(np.max(reach)),collision=collision,
                 max_frame_step=float(np.linalg.norm(np.roll(clean,-1,axis=0)-clean,axis=-1).max()))
    output.mkdir(parents=True,exist_ok=False)
    (output/'skeleton.json').write_text(json.dumps(d,indent=2)+'\n')
    contacts=np.tile([0.,0.,1.,1.],(len(clean),1))
    # Frame 121 is a closing interpolation key; playback/export uses frames 1..120.
    np.savez_compressed(output/'motion.npz',raw=raw,fitted=fitted,bridged=loop,normalized=normalized,clean=np.concatenate([clean,clean[:1]]),poles=np.concatenate([poles,np.array(poles)[:1]]),contacts=np.concatenate([contacts,contacts[:1]]),anchors=anchors,requested_targets=targets)
    record=dict(schema=1,source=str(pilot/(name+'.xyz.npy')),source_sha256=hashlib.sha256((pilot/(name+'.xyz.npy')).read_bytes()).hexdigest(),fitted_source=str(pilot/(name+'.fitted.xyz.npy')),source_run=str(pilot/'run.json'),skeleton=str(blockout/'skeleton.json'),fps=20,frames=120,closing_key=121,units='design meters',
                corrections=dict(boundary_window_frames=12,bridge='C1 Hermite interpolation over original end/start boundary; interior indices 12..108 retained before length/contact correction',contacts='C/D authored as constant supports at median source horizontal positions, y=.06; A/B free',free_hand_B_static_offset=[-hand_offset,.085,0],B_bend_bias='Source direction plus 0.5 times outward preferred vector, renormalized',ring_visual_axial_offset=-.05,ring_carrier='SPINE_02 chest, independent of neck hinge',distal_orientation='Rest direction for all limbs; contact pads world-flat. Source bend directions used for upper/lower solve, with recorded B bias.'),metrics=metrics)
    (output/'loop.json').write_text(json.dumps(record,indent=2)+'\n');(output/'contacts.json').write_text(json.dumps(dict(fps=20,frame_start=1,frame_end=121,contacts=dict(A=0,B=0,C=1,D=1),anchors=anchors.tolist(),provenance='Authored cleanup schedule for a two-support settling loop, not inferred model contact truth.'),indent=2)+'\n')
    print(json.dumps(metrics,indent=2));return clean,d


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pilot',type=Path);p.add_argument('blockout',type=Path);p.add_argument('output',type=Path);p.add_argument('--hand-offset',type=float,default=.34);a=p.parse_args();prepare(a.pilot,a.blockout,a.output,a.hand_offset)
