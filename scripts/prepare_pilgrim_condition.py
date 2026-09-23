"""Direct custom condition with documented Hound-derived calibration statistics."""
import argparse, contextlib, hashlib, json, os, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ASSETS=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove')
sys.path.insert(0,str(ROOT/'external/AnyTop'))
os.environ.update(MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/pilgrim_mpl',OMP_NUM_THREADS='4')
import Animation, BVH
from Quaternions import Quaternions
from InverseKinematics import animation_from_positions
from data_loaders.truebones.truebones_utils import motion_process as mp


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    pa=argparse.ArgumentParser();pa.add_argument('blockout',type=Path);pa.add_argument('--name',default='condition_v001');pa.add_argument('--filter-calibration',action='store_true');a=pa.parse_args()
    out=a.blockout.parent/a.name;out.mkdir(exist_ok=False);bvhs=out/'calibration_bvhs';bvhs.mkdir()
    d=json.loads((a.blockout/'skeleton.json').read_text());rest=np.array(d['rest']);parents=np.array(d['parents']);offsets=np.array(d['offsets']);mapped=np.array(d['source_hound_indices'])
    anim,order,_=Animation.animation_from_offsets(offsets,parents,(2,len(parents),3));assert np.array_equal(order,np.arange(len(parents)))
    anim.positions[:,0]=rest[0]
    restpath=bvhs/'Pilgrim_rest.bvh';BVH.save(str(restpath),anim,names=d['model_names'],frametime=.05,leaf_joints=True)
    report=dict(status='preparing',skeleton=str(a.blockout/'skeleton.json'),skeleton_sha256=sha(a.blockout/'skeleton.json'),
                method='Global source bone-direction changes relative to each source first frame applied to Pilgrim rest vectors; fixed-length IK fit; official process_skeleton feature/statistics preprocessing.',
                caveat='Hound-derived calibration supplies motion statistics and biases posture distribution. No claim of morphology-only behavior or independence from those statistics.',calibration=[],rejected_calibration=[],calibration_filter={'rms_max':.06,'max_max':.18} if a.filter_calibration else None)
    sources=sorted((ASSETS/'generated/hound_seed100_batch8').glob('Hound_rep_*.xyz.npy'))
    assert len(sources)==8
    for i,src in enumerate(sources):
        original=np.load(src);source=original[:,mapped];xyz=np.zeros((len(source),len(parents),3))
        xyz[:,0]=rest[0]+(original[:,0]-original[0,0])*.95
        for j,p in enumerate(parents):
            if p<0:continue
            vec=source[:,j]-source[:,p]
            q=Quaternions.between(np.repeat(vec[:1],len(vec),axis=0),vec)
            xyz[:,j]=xyz[:,p]+q*np.repeat((rest[j]-rest[p])[None],len(vec),axis=0)
        with open(out/('fit_'+str(i)+'.log'),'w') as log,contextlib.redirect_stdout(log):
            fitted,order,_=animation_from_positions(xyz,parents,offsets,iterations=150)
        assert np.array_equal(order,np.arange(len(parents)))
        actual=Animation.positions_global(fitted);error=np.linalg.norm(actual-xyz,axis=-1)
        if a.filter_calibration and (np.sqrt(np.mean(error**2))>.06 or error.max()>.18):
            report['rejected_calibration'].append(dict(source=str(src),source_sha256=sha(src),fit_rms=float(np.sqrt(np.mean(error**2))),fit_max=float(error.max())))
            continue
        path=bvhs/('Pilgrim_calibration_'+str(i)+'.bvh');BVH.save(str(path),fitted,d['model_names'],frametime=.05,leaf_joints=True)
        np.save(out/('calibration_'+str(i)+'.xyz.npy'),actual)
        report['calibration'].append(dict(source=str(src),source_sha256=sha(src),bvh_sha256=sha(path),fit_rms=float(np.sqrt(np.mean(error**2))),fit_max=float(error.max())))
    processed=out/'processed'
    # Replace only optional Matplotlib/FFmpeg previews; raw/calibration XYZ and Blender previews are retained.
    mp.plot_general_skeleton_3d_motion=lambda *args,**kwargs:None
    with open(out/'preprocess.log','w') as log,contextlib.redirect_stdout(log):
        mp.process_skeleton('Pilgrim',str(bvhs),[d['model_names'][i] for i in d['face_joints']],str(processed),str(restpath))
    condpath=processed/'cond.npy';c=np.load(condpath,allow_pickle=True).item()['Pilgrim']
    assert list(c['joints_names'])==d['model_names'];assert np.array_equal(c['parents'],parents)
    for k in ['mean','std','tpos_first_frame','offsets','joint_relations','joints_graph_dist']:assert np.isfinite(c[k]).all(),k
    assert c['mean'].shape==(len(parents),13);assert (c['std'][:,:12]>1e-8).all(),'Degenerate calibration motion statistics'
    normalized=(c['tpos_first_frame']-c['mean'])/(c['std']+1e-6)
    scales=np.linalg.norm(c['offsets'][1:],axis=-1)/np.linalg.norm(offsets[1:],axis=-1)
    assert np.ptp(scales)<1e-5
    report.update(status='validated',condition=str(condpath),condition_sha256=sha(condpath),joints=len(parents),normalization_max_abs_rest=float(abs(normalized).max()),
                  normalized_units_per_design_meter=float(scales.mean()),contact_zero_std_joints=np.where(c['std'][:,12]==0)[0].tolist(),
                  model_names=d['model_names'],parents=parents.tolist(),optional_upstream_video_previews='Skipped; XYZ and separate Blender previews retained')
    (out/'condition_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
