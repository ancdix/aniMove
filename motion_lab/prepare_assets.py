"""Canonical, meaningful generic motion rigs; no controls or decorative bones."""
import json,sys,copy,shutil
from collections import deque
from pathlib import Path
import numpy as np
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');OUT=BASE/'motion_lab_v001';sys.path.insert(0,str(BASE/'UniMate'))
from Animation import offsets_from_positions
from Quaternions import Quaternions
from unimate.utils.topology_utils import compute_edge_indexs,compute_joint_depths,compute_edge_relations_and_distances,compute_laplacian_eigenvectors
from unimate.utils.motion_utils import compute_unimate_motion_feats,recover_unimate_joint_pos_from_rot
class Rig:
    def __init__(self):self.nodes=[]
    def add(self,name,parent,p,group='body'):
        assert name not in [n['name'] for n in self.nodes];self.nodes.append(dict(name=name,parent=parent,position=list(p),group=group));return name
    def chain(self,prefix,parent,points,group):
        for i,p in enumerate(points):parent=self.add(prefix+str(i+1),parent,p,group)
        return parent

def mammal():
    r=Rig();a=r.add
    a('Hips',None,(0,1.05,-.50));a('Spine','Hips',(0,1.09,-.20));a('Spine Middle','Spine',(0,1.12,.12));a('Chest','Spine Middle',(0,1.14,.50));a('Neck','Chest',(0,1.35,.72));a('Head','Neck',(0,1.48,.94));a('Muzzle','Head',(0,1.39,1.15));a('Nose','Muzzle',(0,1.38,1.30))
    for side,sign in [('Left',1),('Right',-1)]:a(side+' Ear','Head',(sign*.15,1.72,.89),'head')
    r.chain('Tail ','Hips',[(0,1.13,-.76),(0,1.14,-1.02),(0,1.10,-1.25),(0,1.01,-1.44),(0,.88,-1.59),(0,.73,-1.66)],'tail')
    for side,sign in [('Left',1),('Right',-1)]:
        for kind,parent,pts in [('Front','Chest',[(.30,1.03,.48),(.34,.59,.45),(.34,.18,.65),(.34,.07,.83)]),('Hind','Hips',[(.30,1.0,-.50),(.36,.61,-.25),(.36,.20,-.62),(.36,.07,-.42)])]:
            prev=parent;group=side.lower()+'_'+kind.lower()
            for part,p in zip(['Upper Leg','Knee','Ankle','Paw'],pts):prev=a(side+' '+kind+' '+part,prev,(sign*p[0],p[1],p[2]),group)
            for digit,dx in [('Inner',-.055),('Outer',.055)]:r.chain(side+' '+kind+' '+digit+' Toe ',prev,[(sign*(pts[-1][0]+dx),.035,pts[-1][2]+.09),(sign*(pts[-1][0]+dx),0,pts[-1][2]+.18)],group)
    assert len(r.nodes)==48;return r

def bird():
    r=Rig();a=r.add
    a('Hips',None,(0,.90,-.15));a('Spine','Hips',(0,1.03,0));a('Chest','Spine',(0,1.15,.20));a('Neck Lower','Chest',(0,1.36,.30));a('Neck','Neck Lower',(0,1.60,.34));a('Head','Neck',(0,1.75,.42));a('Beak','Head',(0,1.70,.58));a('Beak Tip','Beak',(0,1.69,.77));a('Tail','Hips',(0,.95,-.48));a('Tail Tip','Tail',(0,1.0,-.82));a('Tail Center Feather','Tail Tip',(0,1.02,-1.04))
    for side,sign in [('Left',1),('Right',-1)]:
        a(side+' Tail Feather','Tail Tip',(sign*.18,1.0,-1.0),'tail')
        group=side.lower()+'_wing';shoulder=a(side+' Wing Shoulder','Chest',(sign*.20,1.17,.16),group);elbow=a(side+' Wing Elbow',shoulder,(sign*.64,1.20,.06),group);wrist=a(side+' Wing Wrist',elbow,(sign*1.04,1.22,.22),group);hand=a(side+' Wing Hand',wrist,(sign*1.33,1.21,.19),group);a(side+' Wing Tip',hand,(sign*1.66,1.18,.02),group)
        for label,parent,p in [('Primary Feather',hand,(1.48,1.16,-.24)),('Secondary Feather',wrist,(1.01,1.13,-.31)),('Inner Feather',elbow,(.63,1.11,-.32))]:a(side+' '+label,parent,(sign*p[0],p[1],p[2]),group)
        group=side.lower()+'_leg';prev='Hips'
        for part,p in [('Thigh',(.17,.86,-.13)),('Knee',(.21,.57,.05)),('Ankle',(.21,.22,-.15)),('Foot',(.21,.07,.02))]:prev=a(side+' '+part,prev,(sign*p[0],p[1],p[2]),group)
        for label,dx,z in [('Inner',-.09,.25),('Outer',.09,.25),('Back',0,-.20)]:r.chain(side+' '+label+' Toe ',prev,[(sign*(.21+dx*.5),.025,z*.5),(sign*(.21+dx),0,z)],group)
    assert len(r.nodes)==49;return r

def insect():
    r=Rig();a=r.add
    a('Thorax',None,(0,.48,0));a('Thorax Front','Thorax',(0,.49,.28));a('Head','Thorax Front',(0,.48,.51));a('Head Tip','Head',(0,.46,.67));a('Left Mandible','Head Tip',(.12,.40,.73),'head');a('Right Mandible','Head Tip',(-.12,.40,.73),'head');a('Abdomen','Thorax',(0,.46,-.28));a('Abdomen Middle','Abdomen',(0,.43,-.56));a('Abdomen Tip','Abdomen Middle',(0,.37,-.81))
    for side,sign in [('Left',1),('Right',-1)]:
        r.chain(side+' Antenna ','Head',[(sign*.16,.63,.78),(sign*.28,.69,1.05)],'head')
        for label,z in [('Front',.26),('Middle',0),('Hind',-.24)]:
            group=side.lower()+'_'+label.lower();prev='Thorax Front' if label=='Front' else 'Thorax';sweep={'Front':.20,'Middle':0,'Hind':-.20}[label]
            for part,p in [('Coxa',(.17,.47,z)),('Femur',(.45,.53,z+sweep*.5)),('Tibia',(.70,.21,z+sweep)),('Tarsus',(.78,.025,z+sweep+.08)),('Claw',(.86,0,z+sweep+.13))]:prev=a(side+' '+label+' '+part,prev,(sign*p[0],p[1],p[2]),group)
    assert len(r.nodes)==43;return r

def export(rig,key,title,prompt):
    nodes=rig.nodes;order=[];q=deque([n for n in nodes if n['parent'] is None])
    while q:
        n=q.popleft();order.append(n);q.extend(v for v in nodes if v['parent']==n['name'])
    names=[n['name'] for n in order];parents=[-1 if n['parent'] is None else names.index(n['parent']) for n in order];pos=np.array([n['position'] for n in order]);pos[:,[0,2]]-=pos[0,[0,2]];leaves=[i for i in range(len(names)) if i not in parents];diameter=np.linalg.norm(pos[leaves,None]-pos[None,leaves],axis=-1).max();scale=2/diameter;rest=pos*scale;off=offsets_from_positions(rest,np.array(parents));relations,dists=compute_edge_relations_and_distances(parents);spectral=compute_laplacian_eigenvectors(parents,max_freqs=8);depth=compute_joint_depths(parents)
    if isinstance(spectral,tuple):spectral=spectral[0]
    c=dict(object_type=key,parents=parents,offsets=off,tpos_offsets=off.copy(),joint_names=names,clean_joint_names=names,tpos_first_frame=rest,tpos_local_rotations=Quaternions.id(len(names)).qs,tpos_global_rotations=Quaternions.id(len(names)).qs,joint_relations=relations,joint_graph_dists=dists,joint_depths=depth,edge_indexs=compute_edge_indexs(parents),spectral_feats=spectral,kinematic_chains=[],scale_factor=scale,ground_height=None,ground_height_mode='per_motion',face_joint_idxs={'r_hip':next(i for i,n in enumerate(names) if n.startswith('Right') and ('Leg' in n or 'Thigh' in n or 'Coxa' in n)),'l_hip':next(i for i,n in enumerate(names) if n.startswith('Left') and ('Leg' in n or 'Thigh' in n or 'Coxa' in n)),'body_axis':False})
    for leaf in leaves:
        chain=[leaf]
        while parents[chain[-1]]>=0:chain.append(parents[chain[-1]])
        c['kinematic_chains'].append(chain[::-1])
    folder=OUT/'targets'/key;(folder/'motions').mkdir(parents=True,exist_ok=True);np.save(folder/'cond.npy',{key:c});p=np.repeat(rest[None],90,axis=0);local=Quaternions.id((90,len(names)));facing=Quaternions.id(90);features=compute_unimate_motion_feats(p,local,np.array(parents),facing);decoded=recover_unimate_joint_pos_from_rot(features,np.array(parents),off);assert np.max(abs(decoded-p[:-1]))<1e-8
    np.savez_compressed(folder/'motions'/f'{key}-Registration-000.npz',global_positions=p,local_rotations=local.qs,root_facing_quat=facing.qs,fps=30)
    assert len(names)<=61 and max(depth)<19 and all(parents[i]<i for i in range(1,len(names))) and min(np.linalg.norm(off[1:],axis=-1))>1e-5
    result=dict(id=key,title=title,object_type=key,condition=str(folder/'cond.npy'),features=str(folder),names=names,parents=parents,rest=pos.tolist(),groups=[n['group'] for n in order],scale=float(scale),joints=len(names),max_depth=int(max(depth)),default_prompt=prompt,source='Authored generic motion skeleton; static registration only; no motion guidance',identity_fk_error=float(np.max(abs(decoded-p[:-1]))));return result

def main():
    OUT.mkdir(exist_ok=True);assert not (OUT/'targets.json').exists(),'Versioned targets already prepared'
    targets=[export(mammal(),'Mammal','Mammal quadruped','A dog walks forward.'),export(bird(),'Bird','Winged bird','A bird flaps its wings.'),export(insect(),'Insect','Six-legged insect','An insect walks forward.')]
    for key,title,path in [('Pilgrim','Pilgrim · upright',BASE/'pilgrim_canonical_v002'),('PilgrimQuad','Pilgrim · quadrupedal',BASE/'pilgrim_stance_001/conditions/quadruped')]:
        folder=OUT/'targets'/key;shutil.copytree(path/'motions',folder/'motions');d=np.load(path/'cond.npy',allow_pickle=True).item();c=d['Pilgrim'];np.save(folder/'cond.npy',d);names=list(c['joint_names']);mapping=json.loads((BASE/'pilgrim_canonical_v002/asset_validation.json').read_text())['canonical_to_original'];groups=[mapping[n].split('_')[0] for n in names];targets.append(dict(id=key,title=title,object_type='Pilgrim',condition=str(folder/'cond.npy'),features=str(folder),names=names,parents=c['parents'],rest=(np.asarray(c['tpos_first_frame'])/c['scale_factor']).tolist(),groups=groups,scale=float(c['scale_factor']),joints=len(names),default_prompt='The creature walks forward slowly.',source='Existing verified Pilgrim reference; copied without geometry changes'))
    (OUT/'targets.json').write_text(json.dumps(targets,indent=2)+'\n');print(json.dumps([dict(id=t['id'],joints=t['joints'],depth=t.get('max_depth')) for t in targets]))
if __name__=='__main__':main()
