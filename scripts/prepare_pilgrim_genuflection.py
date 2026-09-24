"""Compose selected inpaints with measured mechanical/contact corrections."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from pilgrim_skeleton import audit
from motion_lab import normalize,two_bone
from prepare_pilgrim_loop import stats

def limited_direction(source,reference,degrees):
    a=normalize(reference);b=normalize(source);theta=np.arccos(np.clip(a@b,-1,1));limit=np.deg2rad(degrees)
    if theta<=limit:return b
    tangent=normalize(b-a*(a@b),[0,0,1]);return a*np.cos(limit)+tangent*np.sin(limit)

def clean_half(d,source,guide,params,half):
    ix={n:i for i,n in enumerate(d['names'])};rest=np.array(d['rest']);parents=d['parents'];length=np.linalg.norm(np.array(d['offsets']),axis=-1)
    smooth=gaussian_filter1d(source,1.5,axis=0,mode='nearest');out=guide.copy();poles=[];reach=[];angles=[]
    # Full context at clip edges provides still, identical joins; keep original guide there.
    envelope=np.ones(len(source));envelope[:16]=0;envelope[-16:]=0
    for a,b in [(16,24),(96,104)]:
        u=np.linspace(0,1,b-a);w=u*u*(3-2*u);envelope[a:b]=w if a==16 else 1-w
    for f in range(len(source)):
        w=envelope[f];out[f,0]=guide[f,0]+w*np.clip(smooth[f,0]-guide[f,0],[-.02,-.065,-.02],[.02,.065,.02])
        for j in range(1,len(rest)):
            p=parents[j];n=d['names'][j];ref=guide[f,j]-guide[f,p];src=smooth[f,j]-smooth[f,p]
            limit=10 if j<7 else 5
            if n=='SENSOR':direction=normalize(rest[j]-rest[p]) # Explicit stable world head orientation.
            else:direction=normalize((1-w)*normalize(ref)+w*limited_direction(src,ref,limit))
            out[f,j]=out[f,p]+direction*length[j]
        fp=[];fr=[]
        for li,key in enumerate('ABCD'):
            js=[ix[key+'_'+str(k)] for k in range(4)];sign=1 if key in 'AC' else -1;upper,lower,dist=np.linalg.norm(np.diff(rest[js],axis=0),axis=-1)
            tip=guide[f,js[3]].copy()
            if key in 'AB':
                contact=params[f,3+li]
                delta=smooth[f,js[3]]-guide[f,js[3]];delta*=min(1,.12/max(np.linalg.norm(delta),1e-9));tip+=w*(1-contact)*delta
                tip[0]=sign*max(sign*tip[0],.84);tip[1]=max(.06,tip[1])
            distal=normalize(rest[js[3]]-rest[js[2]])*dist
            preferred=normalize([sign*(1.0 if key in 'AB' else .22),.05,.2 if key in 'AB' else 1.0])
            # Preserve safe source bend variation inside a bounded outward sector.
            direction=limited_direction(smooth[f,js[1]]-smooth[f,js[0]],preferred,12)
            direction=normalize((1-w)*preferred+w*direction)
            e,wr,bend,err,_=two_bone(out[f,js[0]],tip-distal,direction,upper,lower,(2,165))
            out[f,js[1]]=e;out[f,js[2]]=wr;out[f,js[3]]=wr+distal;fp.append(out[f,js[0]]+bend*.85);fr.append(err)
        poles.append(fp);reach.append(fr)
    # Smooth bounded corrections after clipping to avoid abrupt motion at safety limits.
    preliminary=out.copy();residual=gaussian_filter1d(preliminary-guide,3.,axis=0,mode='nearest');body=guide+residual*envelope[:,None,None]
    bend_paths={k:gaussian_filter1d(preliminary[:,ix[k+'_1']]-preliminary[:,ix[k+'_0']],3.,axis=0,mode='nearest') for k in 'ABCD'}
    final=body.copy();poles=[];reach=[]
    for f in range(len(source)):
        for j in range(1,len(rest)):
            pa=parents[j]
            direction=normalize(body[f,j]-body[f,pa])
            if d['names'][j]=='SENSOR':direction=normalize(rest[j]-rest[pa])
            final[f,j]=final[f,pa]+direction*length[j]
        fp=[];fr=[]
        for li,key in enumerate('ABCD'):
            js=[ix[key+'_'+str(k)] for k in range(4)];lengths=np.linalg.norm(np.diff(rest[js],axis=0),axis=-1);distal=normalize(rest[js[3]]-rest[js[2]])*lengths[2]
            tip=guide[f,js[3]].copy()
            if key in 'AB':tip+=envelope[f]*(1-params[f,3+li])*residual[f,js[3]]
            e,wr,bend,error,_=two_bone(final[f,js[0]],tip-distal,bend_paths[key][f],*lengths[:2],(2,165))
            final[f,js[1]]=e;final[f,js[2]]=wr;final[f,js[3]]=wr+distal;fp.append(final[f,js[0]]+bend*.85);fr.append(error)
        poles.append(fp);reach.append(fr)
    return final,np.array(poles),float(np.max(reach))

def prepare(pilot,output):
    d=json.loads((pilot/'skeleton.json').read_text());d['geometry']={'upper_shell_proximal_inset_fraction':.10};g=np.load(pilot/'authored_guide.npz');guide=g['xyz'];params=g['parameters'];run=json.loads((pilot/'run.json').read_text());candidates=[];chosen=[]
    for half in range(2):
        opts=[]
        for entry in run['clips']:
            if entry['half']!=half:continue
            fitted=np.load(pilot/(entry['name']+'.fitted.xyz.npy'));clean,poles,reach=clean_half(d,fitted,guide[half*120:(half+1)*120],params[half*120:(half+1)*120],half)
            a=audit(d,clean);correction=stats(clean-fitted);acc=np.linalg.norm(np.diff(clean,n=2,axis=0),axis=-1);cost=correction['rms']+float(np.percentile(acc,95))*2+max(0,-a['min_interlimb_capsule_clearance'])*10+max(0,-a['min_ring_limb_capsule_clearance'])*10+reach*10
            record=dict(name=entry['name'],half=half,cost=cost,correction=correction,guide_difference=stats(clean-guide[half*120:(half+1)*120]),max_reach_projection=reach,audit=a);candidates.append(record);opts.append((cost,entry,clean,poles,record))
        chosen.append(min(opts,key=lambda x:x[0]));print('CHOSEN_HALF',half,chosen[-1][1]['name'],chosen[-1][-1],flush=True)
    clean=np.concatenate([x[2] for x in chosen]);poles=np.concatenate([x[3] for x in chosen]);raw=np.concatenate([np.load(pilot/(x[1]['name']+'.raw.xyz.npy')) for x in chosen]);fitted=np.concatenate([np.load(pilot/(x[1]['name']+'.fitted.xyz.npy')) for x in chosen]);mask=np.concatenate([np.load(pilot/('mask_half'+str(h)+'.npy')) for h in range(2)])
    # Motion remains on the anchors during fades, so changing contact weights cannot move pads.
    contacts=np.ones((241,4));contacts[:,:2]=0
    for li,start,end in [(0,78,196),(1,100,176)]:
        contacts[start:end+1,li]=1
        for t in range(7):
            u=t/6;w=u*u*(3-2*u);contacts[start+t,li]=w;contacts[end-t,li]=w
    anchors=guide[110,d['contact_joints']];output.mkdir(exist_ok=False)
    np.savez_compressed(output/'motion.npz',raw=raw,fitted=fitted,guide=guide,clean=np.concatenate([clean,clean[:1]]),poles=np.concatenate([poles,poles[:1]]),contacts=contacts,anchors=anchors,mask=mask)
    (output/'skeleton.json').write_text(json.dumps(d,indent=2)+'\n');(output/'selection.json').write_text(json.dumps(candidates,indent=2)+'\n')
    report=dict(status='prepared',pilot=str(pilot),selected=[x[1]['name'] for x in chosen],fps=20,frames=240,closing_key=241,contribution='Directed hybrid animation: authored choreography/contact goals and bounded AnyTop transition variation. Not raw learned choreography.',corrections=dict(upper_shell_proximal_inset_fraction=.10,gaussian_sigma_frames=1.5,post_limit_residual_sigma_frames=3.,root_deviation_limits=[.02,.065,.02],body_direction_cone_degrees=10,attachment_direction_cone_degrees=5,limb_bend_cone_degrees=12,free_hand_residual_max=.12,head='Sensor direction stabilized to rest world orientation',context_envelope='Original authored guide at each 16-frame endpoint; eight-frame fades'),metrics=dict(fitting=stats(fitted-raw),cleanup=stats(clean-fitted),total_from_raw=stats(clean-raw),final_vs_authored_guide=stats(clean-guide[:240]),root_aligned_cleanup=stats((clean-clean[:,:1])-(fitted-fitted[:,:1])),root_cleanup=stats(clean[:,0]-fitted[:,0]),audit=audit(d,clean),max_reach_projection=max(x[-1]['max_reach_projection'] for x in chosen)),events=dict(upright=1,bow=57,A_planted=79,B_planted=101,four_contact_pause=121,reorientation=161,B_release=177,A_release=197,returned=221))
    (output/'loop.json').write_text(json.dumps(report,indent=2)+'\n');(output/'contacts.json').write_text(json.dumps(dict(anchors=anchors.tolist(),support_intervals_zero_based=dict(A=[78,196],B=[100,176],C=[0,240],D=[0,240]),fade_frames=6,provenance='Authored schedule; both feet remain planted; B releases before A.'),indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pilot',type=Path);p.add_argument('output',type=Path);a=p.parse_args();prepare(a.pilot,a.output)
