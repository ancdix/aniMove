"""Append generic two- and four-arm humanoids without replacing existing targets."""
import json, shutil
import numpy as np
from prepare_assets import Rig, export, OUT

def humanoid(four_arms=False):
    r=Rig();a=r.add
    for name,parent,p in [
        ('Hips',None,(0,.95,0)),('Spine','Hips',(0,1.09,0)),
        ('Spine Middle','Spine',(0,1.25,0)),('Chest','Spine Middle',(0,1.45,0)),
        ('Neck','Chest',(0,1.60,0)),('Head','Neck',(0,1.73,0)),
        ('Head Tip','Head',(0,1.87,0))]:a(name,parent,p,'head' if name.startswith('Head') else 'body')
    for side,sign in [('Left',1),('Right',-1)]:
        prev='Hips'
        for part,p in [('Thigh',(.13,.91,0)),('Shin',(.14,.50,.035)),
                       ('Foot',(.14,.08,0)),('Toe',(.14,0,.20))]:
            prev=a(side+' '+part,prev,(sign*p[0],p[1],p[2]),side.lower()+'_leg')
        pairs=[('', 'Chest',[(.18,1.48,0),(.26,1.45,0),(.52,1.25,.015),(.72,1.05,.025)],side.lower()+'_front')]
        if four_arms:
            pairs.append(('Secondary ','Spine Middle',[(.18,1.25,.015),(.25,1.20,.02),(.44,.96,.05),(.58,.73,.07)],side.lower()+'_middle'))
        for prefix,parent,points,group in pairs:
            prev=parent
            for part,p in zip(['Shoulder','Upper Arm','Forearm','Hand'],points):
                prev=a(side+' '+prefix+part,prev,(sign*p[0],p[1],p[2]),group)
            x,y,z=points[-1]
            for digit,dz in [('Thumb',.05),('Index',0),('Little',-.05)]:
                r.chain(side+' '+prefix+digit+' ',prev,
                        [(sign*(x+.035),y-.055,z+dz),(sign*(x+.065),y-.105,z+dz)],group)
    assert len(r.nodes)==(55 if four_arms else 35)
    return r

def main():
    path=OUT/'targets.json';targets=json.loads(path.read_text())
    backup=OUT/'targets_before_humanoids.json'
    if not backup.exists():shutil.copy2(path,backup)
    for key,title,four in [('Humanoid','Humanoid',False),('Humanoid4Arm','Humanoid · four arms',True)]:
        if any(t['id']==key for t in targets):continue
        t=export(humanoid(four),key,title,'An object walks forward.' if not four else 'An object raises its arms.')
        # Unique rig identifiers; both pairs receive familiar arm/hand semantic labels.
        labels=[n.replace('Secondary ','') for n in t['names']]
        payload=np.load(t['condition'],allow_pickle=True).item();payload[key]['clean_joint_names']=labels
        np.save(t['condition'],payload);t['clean_joint_names']=labels
        t['source']='Authored humanoid with '+('four' if four else 'two')+' arms, two legs and simplified three-digit hands; static registration only'
        targets.append(t)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(targets,indent=2)+'\n');temp.replace(path)
    print(json.dumps([{'id':t['id'],'joints':t['joints'],'depth':t.get('max_depth')} for t in targets]))

if __name__=='__main__':main()
