"""Render saved Pilgrim scenes without altering the saved assets."""
import bpy,sys,subprocess,json
from pathlib import Path
from mathutils import Vector
p=Path(sys.argv[sys.argv.index('--')+1]);scene_name=sys.argv[sys.argv.index('--')+2];out=Path(sys.argv[sys.argv.index('--')+3]);out.mkdir(exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(p));scene=bpy.data.scenes[scene_name];bpy.context.window.scene=scene
if scene_name=='PILGRIM_Blockout':
    for text,y,size in [('PILGRIM / BLOCKOUT',1.85,.15),('Authored rig checks - not AnyTop motion',-1.98,.085)]:
        c=bpy.data.curves.new(text,'FONT');c.body=text;c.size=size;obj=bpy.data.objects.new(text,c);scene.collection.objects.link(obj);obj.parent=scene.camera;obj.location=(-1.94,y,-5)
        mat=bpy.data.materials.new(text);mat.diffuse_color=(.95,.95,.88,1);c.materials.append(mat)
scene.render.filepath=str(out/'frames/frame_');scene.render.image_settings.file_format='PNG';bpy.ops.render.render(animation=True)
subprocess.run(['/usr/bin/ffmpeg','-v','error','-n','-framerate',str(scene.render.fps),'-i',str(out/'frames/frame_%04d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'preview.mp4')],check=True)
if scene_name=='PILGRIM_Blockout':
    scene.frame_set(1)
    for name,pos in [('front',(0,-8,1.5)),('side',(8,0,1.5))]:
        scene.camera.location=pos;scene.camera.rotation_euler=(Vector((0,0,1.5))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
print('PILGRIM_PREVIEW',str(out/'preview.mp4'),flush=True)
