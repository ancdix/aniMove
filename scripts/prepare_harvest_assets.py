"""Package curated discovered phrases, then test a source-preserving loop seam."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from optimize_harvest_clearance import apply
from clean_pilgrim_harvest import cleanup
from pilgrim_skeleton import audit
from prepare_pilgrim_loop import periodic_bridge,stats
from analyze_pilgrim_harvest import contacts

def make(p):
    screen={x['name']:x for x in json.loads((p/'clearance_screen.json').read_text())['results']};d=json.loads((p/'skeleton.json').read_text());d['ring'].update(carrier='SPINE_02',axial_offset=-.05,limb_capsule_radius=.095);d['geometry']={'upper_shell_proximal_inset_fraction':.10};out=p/'curated_v004';out.mkdir(exist_ok=False)
    choices=[('Orient','Pilgrim_bipeds_seed7120','Torso turns while the neck lifts; two nearly stationary lower endpoints.'),('Listen','Pilgrim_bipeds_seed7132','Head dips sideways and recovers, with an asymmetric free-hand response.'),('Unfold','Pilgrim_all_seed7120','A forward-curled upper body extends upward, with slight lower-support adjustment.')]
    manifest=[]
    for title,name,note in choices:
        r=screen[name];assert r['accepted'];path=out/title;path.mkdir();m=np.load(p/'clearance_candidates'/(name+'.npz'));base,po,w,a,episodes,reach=cleanup(m['fitted'],d,m['source_contact_mask']);clean,po,reach=apply(m['fitted'],base,d,np.array(r['parameters']));data={k:m[k] for k in m.files};data.update(clean=clean,poles=po);r=dict(r,cleanup=stats(clean-m['fitted']),total=stats(clean-m['raw']),reach=reach,minimum_flexion_degrees=2);np.savez_compressed(path/'motion.npz',**data);(path/'skeleton.json').write_text(json.dumps(d,indent=2)+'\n');info=dict(title=title,source=name,source_directory=str(p),fps=20,frames=60,cyclic=False,description=note,authorship='Unguided AnyTop phrase. Fitted body/head trajectory retained exactly; inferred contacts plus constant clearance edits only.',corrections=r,body_preserved_frames=[1,60]);(path/'motion.json').write_text(json.dumps(info,indent=2)+'\n');manifest.append(info)
    # Seek a low-edit closing bridge on the strongest stationary-support phrase.
    name=choices[0][1];r=screen[name];m=np.load(p/'clearance_candidates'/(name+'.npz'));fit=m['fitted'];raw=m['raw'];rest=np.array(d['rest']);parents=d['parents'];length=np.linalg.norm(np.array(d['offsets']),axis=-1);options=[]
    for window in [6,8,10,12]:
        bridged=periodic_bridge(fit,window);normalized=bridged.copy()
        for j,pa in enumerate(parents):
            if pa>=0:
                vec=bridged[:,j]-bridged[:,pa];vec/=np.linalg.norm(vec,axis=-1)[:,None];normalized[:,j]=normalized[:,pa]+vec*length[j]
        co=m['source_contact_mask'];base,po,w,a,episodes,reach=cleanup(normalized,d,co);clean,poles,reach=apply(normalized,base,d,np.array(r['parameters']));proxy=audit(d,clean)
        for li in range(2):a[:,li]+=[r['parameters'][2*li],0,r['parameters'][2*li+1]]
        rec=dict(window=window,bridge=stats(bridged-fit),cleanup=stats(clean-normalized),total_from_fitted=stats(clean-fit),total_from_raw=stats(clean-raw),proxy=proxy,reach=reach,interior_body_max_change=float(np.linalg.norm(clean[window:61-window,:7]-fit[window:61-window,:7],axis=-1).max()))
        print('LOOP_GATE',rec,flush=True)
        ok=reach<.005 and proxy['min_interlimb_capsule_clearance']>0 and proxy['min_ring_limb_capsule_clearance']>0
        if ok:options.append((rec['bridge']['rms'],rec,clean,poles,w,a,bridged,normalized))
    assert options,'No low-edit loop candidate clears numerical gates';best=min(options,key=lambda x:x[0]);_,rec,clean,poles,w,a,bridge,normalized=best
    path=out/'Orient_Loop';path.mkdir();close=lambda x:np.concatenate([x,x[:1]])
    np.savez_compressed(path/'motion.npz',raw=raw,fitted=fit,clean=close(clean),poles=close(poles),contacts=close(w),anchor_paths=close(a),bridged=bridge,normalized=normalized,source_contact_mask=m['source_contact_mask'])
    (path/'skeleton.json').write_text(json.dumps(d,indent=2)+'\n');info=dict(title='Orient_Loop',source=name,source_directory=str(p),fps=10,source_fps=20,frames=60,cyclic=True,description='Orient phrase with a measured boundary bridge, played uniformly at half speed as a six-second ritual loop.',authorship='No new choreography: generated motion retained in the interior; authored boundary interpolation, contact/clearance edits, and uniform half-speed presentation.',corrections=rec,constant_clearance=r['parameters'],retiming='Uniform 2x duration; raw comparison uses identical timing',body_preserved_frames=[rec['window']+1,61-rec['window']]);(path/'motion.json').write_text(json.dumps(info,indent=2)+'\n');manifest.append(info)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory',type=Path);make(a.parse_args().directory)
