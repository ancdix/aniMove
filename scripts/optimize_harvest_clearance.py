"""Find constant clearance edits without changing the discovered body trajectory."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from analyze_pilgrim_harvest import contacts
from clean_pilgrim_harvest import cleanup
from motion_lab import normalize,two_bone
from pilgrim_skeleton import audit
from prepare_pilgrim_loop import stats

def segment_distances(a,b,c,d):
    u=b-a;v=d-c;w=a-c;dot=lambda x,y:np.sum(x*y,axis=-1);aa=dot(u,u);bb=dot(u,v);cc=dot(v,v);dd=dot(u,w);ee=dot(v,w);den=aa*cc-bb*bb
    s=(bb*ee-cc*dd)/np.maximum(den,1e-12);t=(aa*ee-bb*dd)/np.maximum(den,1e-12);inter=np.linalg.norm(w+s[...,None]*u-t[...,None]*v,axis=-1);inter=np.where((den>1e-12)&(s>=0)&(s<=1)&(t>=0)&(t<=1),inter,1e5)
    def pt(p,a,b):
        v=b-a;t=np.clip(dot(p-a,v)/np.maximum(dot(v,v),1e-12),0,1);return np.linalg.norm(p-a-t[...,None]*v,axis=-1)
    return np.minimum.reduce([inter,pt(a,c,d),pt(b,c,d),pt(c,a,b),pt(d,a,b)])

def pairs(d):
    ix={n:i for i,n in enumerate(d['names'])};out=[]
    for i,k in enumerate('ABCD'):
        for q in 'ABCD'[i+1:]:
            for s in range(3):
                for t in range(3):out.append([ix[k+'_'+str(s)],ix[k+'_'+str(s+1)],ix[q+'_'+str(t)],ix[q+'_'+str(t+1)]])
    return np.array(out).T

def apply(x,base,d,params):
    ix={n:i for i,n in enumerate(d['names'])};rest=np.array(d['rest']);out=base.copy();poles=[];reach=[]
    offsets=np.array([[params[0],0,params[1]],[params[2],0,params[3]],[0,0,0],[0,0,0]])
    for f in range(len(x)):
        fp=[];fr=[]
        for li,k in enumerate('ABCD'):
            js=[ix[k+'_'+str(j)] for j in range(4)];lengths=np.linalg.norm(np.diff(rest[js],axis=0),axis=-1);a=x[f,js[0]];dist=normalize(x[f,js[3]]-x[f,js[2]])*lengths[2];tip=base[f,js[3]]+offsets[li];axis=normalize(tip-dist-a);rad=normalize(x[f,js[1]]-a-axis*np.dot(x[f,js[1]]-a,axis));theta=params[4+li];bend=rad*np.cos(theta)+np.cross(axis,rad)*np.sin(theta)
            e,w,b,error,_=two_bone(a,tip-dist,bend,*lengths[:2],(2,175));out[f,js[1]]=e;out[f,js[2]]=w;out[f,js[3]]=w+dist;fp.append(a+b*.85);fr.append(error)
        poles.append(fp);reach.append(fr)
    return out,np.array(poles),float(np.max(reach))

def main(p,count):
    run=json.loads((p/'run.json').read_text());d=json.loads((p/'skeleton.json').read_text());d['ring'].update(carrier='SPINE_02',axial_offset=-.05,limb_capsule_radius=.095);d['geometry']={'upper_shell_proximal_inset_fraction':.10};scale=run['normalized_units_per_design_meter'];screen=json.loads((p/'cleanup_screen.json').read_text())['results'];order=[r for r in screen if r['support_fraction']>=.7 and r['total']['rms']<.19 and r['proxy']['min_ring_limb_capsule_clearance']>0 and r['reach']<.005];results=[];ab,ae,bb,be=pairs(d);dest=p/'clearance_candidates';dest.mkdir(exist_ok=True)
    for r in order[:count]:
        name=r['name'];raw=np.load(p/(name+'.xyz.npy'))/scale+[0,.06,0];x=np.load(p/(name+'.fitted.xyz.npy'))/scale+[0,.06,0];co,_=contacts(raw,d['contact_joints']);base,po,w,anchors,episodes,reach=cleanup(x,d,co);idx=np.unique(np.r_[np.arange(0,len(x),6),len(x)-1]);xx=x[idx];bc=base[idx]
        def residual(params):
            q,_,reach=apply(xx,bc,d,params);dist=segment_distances(q[:,ab],q[:,ae],q[:,bb],q[:,be]);pen=np.maximum(0,.215-dist)*12
            return np.r_[(q-xx).flatten(),pen.flatten(),reach*50]
        bounds=([0,0,-.40,0,-.65,-.65,-.65,-.65],[.40,.40,0,.40,.65,.65,.65,.65]);initial=np.array([.02,.02,-.02,.02,0,0,0,0]);result=least_squares(residual,initial,bounds=bounds,max_nfev=55,diff_step=1e-3,ftol=1e-5)
        clean,poles,reach=apply(x,base,d,result.x);proxy=audit(d,clean);corr=stats(clean-x);total=stats(clean-raw);good=reach<.005 and proxy['min_interlimb_capsule_clearance']>=0 and proxy['min_ring_limb_capsule_clearance']>=0 and proxy['min_joint_height']>=.025 and corr['rms']<.08 and total['rms']<.18
        rec=dict(name=name,accepted=bool(good),parameters=result.x.tolist(),cleanup=corr,total=total,reach=reach,proxy=proxy,cost=total['rms']+corr['rms'],support_fraction=r['support_fraction'],body_change=float(np.linalg.norm(clean[:,:7]-x[:,:7],axis=-1).max()),evaluations=result.nfev)
        for li in range(2):anchors[:,li]+=[result.x[li*2],0,result.x[li*2+1]]
        np.savez_compressed(dest/(name+'.npz'),raw=raw,fitted=x,clean=clean,poles=poles,contacts=w,anchor_paths=anchors,source_contact_mask=co)
        results.append(rec);(p/'clearance_screen.json').write_text(json.dumps(dict(scope='Constant upper-palm translations and per-limb bend rotations chosen solely for clearance; no body/head trajectory edits.',parameter_order=['A_dx','A_dz','B_dx','B_dz','A_bend_radians','B_bend_radians','C_bend_radians','D_bend_radians'],results=results),indent=2)+'\n');print('CLEARANCE',name,good,'rms',round(corr['rms'],3),'total',round(total['rms'],3),'min',round(proxy['min_interlimb_capsule_clearance'],3),'params',np.round(result.x,3),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory',type=Path);a.add_argument('--count',type=int,default=18);v=a.parse_args();main(v.directory,v.count)
