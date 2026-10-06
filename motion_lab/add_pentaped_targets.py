"""Add two five-contact morphology experiments with low-poly display metadata."""
import json,math,shutil
from prepare_assets import Rig,export,OUT

def radial():
    r=Rig();a=r.add
    for name,parent,y in [('Hips',None,.80),('Spine','Hips',.94),('Chest','Spine',1.05),('Neck','Chest',1.21),('Head','Neck',1.36),('Head Tip','Head',1.48)]:
        a(name,parent,(0,y,0),'head' if name.startswith('Head') else 'body')
    for index,(label,group) in enumerate([('Center Front','center_leg'),('Left Front','left_front'),('Left Hind','left_hind'),('Right Hind','right_hind'),('Right Front','right_front')]):
        angle=math.radians(index*72);prev='Hips'
        for part,radius,y in [('Upper Leg',.27,.79),('Knee',.63,.73),('Ankle',.88,.24),('Foot',1.0,.055),('Toe',1.15,0)]:
            prev=a(label+' '+part,prev,(math.sin(angle)*radius,y,math.cos(angle)*radius),group)
    return r

def tripod():
    r=Rig();a=r.add
    for name,parent,p in [('Hips',None,(0,.95,-.30)),('Spine','Hips',(0,1.05,0)),('Chest','Spine',(0,1.25,.38)),('Neck','Chest',(0,1.47,.50)),('Head','Neck',(0,1.64,.60)),('Head Tip','Head',(0,1.76,.65))]:
        a(name,parent,p,'head' if name.startswith('Head') else 'body')
    for side,sign in [('Left',1),('Right',-1)]:
        prev='Hips'
        for part,p in [('Upper Leg',(.30,.94,-.28)),('Knee',(.56,.56,-.23)),('Ankle',(.63,.17,-.50)),('Foot',(.66,.055,-.42)),('Toe',(.66,0,-.24))]:
            prev=a(side+' Hind '+part,prev,(sign*p[0],p[1],p[2]),side.lower()+'_hind')
        prev='Chest'
        for part,p in [('Shoulder',(.27,1.23,.35)),('Upper Arm',(.40,1.14,.48)),('Forearm',(.53,.65,.66)),('Hand',(.60,.055,.90)),('Finger',(.60,0,1.08))]:
            prev=a(side+' '+part,prev,(sign*p[0],p[1],p[2]),side.lower()+'_front')
    prev='Hips'
    for part,p in [('Upper Leg',(0,.94,-.55)),('Knee',(0,.56,-.91)),('Ankle',(0,.16,-1.12)),('Foot',(0,.055,-1.17)),('Toe',(0,0,-1.34))]:
        prev=a('Center Hind '+part,prev,p,'center_leg')
    return r

def main():
    path=OUT/'targets.json';targets=json.loads(path.read_text());backup=OUT/'targets_before_pentapeds.json'
    if not backup.exists():shutil.copy2(path,backup)
    for key,title,rig in [('PentapedRadial','Pentaped · radial',radial()),('PentapedTripod','Pentaped · rear tripod',tripod())]:
        if any(t['id']==key for t in targets):continue
        assert len(rig.nodes)==31
        t=export(rig,key,title,'An object walks forward on five legs.')
        t['source']='Authored five-limb experiment; '+('five radial legs spaced 72 degrees apart' if key=='PentapedRadial' else 'three rear support legs and two longer front arms')+'; static registration only'
        volumes=[('Chest',(.16,.16,.13)),('Head',(.13,.15,.12))] if key=='PentapedRadial' else [('Hips',(.30,.29,.18)),('Spine',(.21,.25,.18)),('Chest',(.30,.23,.22)),('Head',(.14,.20,.14))]
        for n in t['names']:
            if n.endswith(('Foot','Hand')):volumes.append((n,(.12,.12,.05)))
            elif n.endswith(('Knee','Ankle','Forearm','Upper Arm')):volumes.append((n,(.065,.065,.065)))
        t['body_volumes']=volumes;t['low_poly']=True;t['limb_radius']=.055
        if key=='PentapedRadial':t['body_shell']={'bone':'Hips','radius':.37,'depth':.22,'vertices':5}
        targets.append(t)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(targets,indent=2)+'\n');temp.replace(path)
    print(json.dumps([{'id':t['id'],'joints':t['joints']} for t in targets]))

if __name__=='__main__':main()
