"""Apply reviewed presentation layout and validated continuous IK playback."""
import json,sys,subprocess
from pathlib import Path
import bpy
from mathutils import Vector
p=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(p/'inbetween_experiments.blend'))
scene=bpy.data.scenes['ANYTOP_Inbetween_Variations'];bpy.context.window.scene=scene
positions={'ORIGINAL':(-4.6,1.95),'VARIATION 1':(-1,1.95),'VARIATION 2':(2.6,1.95),'VARIATION 3':(-2.8,-.60),'VARIATION 4':(.8,-.60)}
for o in list(scene.objects):
    if o.type=='FONT' and o.data.body in positions:o.location.x,o.location.y=positions[o.data.body]
    if o.type=='FONT' and o.data.body.startswith('0 s '):
        template=o
        for fraction,label in [(0,'0 s'),(.25,'1.5 s'),(.75,'4.5 s'),(1,'6 s')]:
            n=template.copy();n.data=template.data.copy();n.data.body=label;template.users_collection[0].objects.link(n);n.location.x=-5.2+10.4*fraction-.06
        bpy.data.objects.remove(template,do_unlink=True)
scene=bpy.data.scenes['ANYTOP_Extreme_Four_to_Two'];bpy.context.window.scene=scene
scene.camera.rotation_euler=(Vector((0,-.1,.75))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
for o in scene.objects:
    if o.type=='FONT':
        if o.data.body in ['RAW ANYTOP OUTPUT','CONTACT-CORRECTED ROBOT']:o.location.y=-1.48
        if o.data.body in ['Boundary snap and foot drift visible','Rear feet pinned / body repositioned']:o.location.y=-1.60
rig=bpy.data.objects['EDIT_EXTREME_ROBOT'];rig['ik_fk']=1.;rig.update_tag();scene.frame_set(105)
assert json.loads((p/'saved_animation_validation.json').read_text())['status']=='passed'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p/'inbetween_experiments.blend'))
for name,stem in [('ANYTOP_Inbetween_Variations','variations'),('ANYTOP_Extreme_Four_to_Two','extreme')]:
    if '--extreme-only' in sys.argv and stem!='extreme':continue
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene;scene.frame_set(105 if stem=='extreme' else 60);scene.render.filepath=str(p/(stem+'.png'));bpy.ops.render.render(write_still=True)
    scene.render.filepath=str(p/(stem+'_frames')/'frame_');bpy.ops.render.render(animation=True)
    subprocess.run(['/usr/bin/ffmpeg','-v','error','-y','-framerate','20','-i',str(p/(stem+'_frames')/'frame_%04d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(p/(stem+'.mp4'))],check=True)
print('POLISHED_AND_SAVED')
