"""Verify that displayed source and rig still match the saved direct model outputs."""
import bpy,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from motion_lab import to_blender
p=Path(sys.argv[sys.argv.index('--')+1]);block=Path(sys.argv[sys.argv.index('--')+2]);out=p/'comparison'
bpy.ops.wm.open_mainfile(filepath=str(out/'pilgrim_direct_anytop.blend'));scene=bpy.data.scenes['PILGRIM_Direct_AnyTop'];bpy.context.window.scene=scene
r=json.loads((p/'run.json').read_text());d=json.loads((block/'skeleton.json').read_text());name=scene['clip'];scale=r['normalized_units_per_design_meter']
raw=to_blender(np.load(p/(name+'.xyz.npy'))/scale);fit=to_blender(np.load(p/(name+'.fitted.xyz.npy'))/scale);raw+=np.array([-1.8,0,.06]);fit+=np.array([1.8,0,.06]);rig=bpy.data.objects['PILGRIM_DIRECT_RIG']
report=dict(frames=120,max_raw_display_error=0.,max_rig_display_error=0.,source='unconditional direct Pilgrim AnyTop; fixed-length fit only')
for f in range(120):
    scene.frame_set(f+1);dg=bpy.context.evaluated_depsgraph_get();er=rig.evaluated_get(dg)
    actual=np.array([(er.matrix_world@er.pose.bones[n].head)[:] for n in d['names']]);report['max_rig_display_error']=max(report['max_rig_display_error'],float(np.linalg.norm(actual-fit[f],axis=-1).max()))
    actual=np.array([bpy.data.objects['PILGRIM_RAW_'+n].matrix_world.translation[:] for n in d['names']]);report['max_raw_display_error']=max(report['max_raw_display_error'],float(np.linalg.norm(actual-raw[f],axis=-1).max()))
report['status']='passed' if max(report['max_raw_display_error'],report['max_rig_display_error'])<1e-4 else 'needs_fix'
(out/'saved_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('DIRECT_VALIDATION',json.dumps(report))
