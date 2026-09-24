"""Combine verified harvested scenes and all independent baked Actions."""
import bpy,json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--')+1]);out=p/'motion_harvest_master.blend';assert not out.exists();records=[]
for title in ['Orient','Listen','Unfold','Orient_Loop']:
 folder=p/title;v=json.loads((folder/'saved_validation.json').read_text());assert v['status']=='passed'
 names=['PILGRIM_'+title,'PILGRIM_'+title+'_Compare'];action='HARVEST_'+title.upper()+'_Final_FK_v001'
 with bpy.data.libraries.load(str(folder/'harvest_master.blend'),link=False) as (source,target):
  target.scenes=list(names);target.actions=[action];target.texts=[n for n in source.texts if n.startswith('README_') or n.endswith('CONTROL_UTILITIES.py')]
 assert action in bpy.data.actions
 bpy.data.actions[action].use_fake_user=True
 records.append(dict(title=title,scenes=names,baked_action=action,rig=bpy.data.scenes[names[0]]['rig']))
scene=bpy.data.scenes['PILGRIM_Orient_Loop'];bpy.context.window.scene=scene;scene.frame_set(1)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.region_3d.view_perspective='CAMERA';space.shading.type='SOLID';space.shading.color_type='MATERIAL';space.overlay.show_extras=False;space.overlay.show_bones=False
bpy.data.texts.new('README_MOTION_HARVEST_001').write('Three unguided discovered phrases: Orient, Listen and Unfold. Separate raw comparisons and independent FK Actions. Orient_Loop is six seconds at half speed with a measured boundary bridge. Raw body/head motion is preserved after fixed-length fitting; static limb clearance and inferred contacts are explicit production edits. No action storyboard was supplied to AnyTop. See docs/pilgrim_motion_harvest_001.md and the adjacent manifests. Detailed mesh remains deferred.')
bpy.ops.wm.save_as_mainfile(filepath=str(out));bpy.ops.wm.open_mainfile(filepath=str(out))
for r in records:
 assert all(n in bpy.data.scenes for n in r['scenes']);assert r['baked_action'] in bpy.data.actions
 assert bpy.data.scenes[r['scenes'][0]].objects[r['rig']]==bpy.data.scenes[r['scenes'][1]].objects[r['rig']]
(p/'package_validation.json').write_text(json.dumps(dict(status='passed',assets=records,master=str(out)),indent=2)+'\n');print('HARVEST_PACKAGE',json.dumps(records),flush=True)
