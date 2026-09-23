"""Fast 30-fps walking preview from the saved file, without altering that file."""
from pathlib import Path
import subprocess
import sys
import bpy

directory=Path(sys.argv[sys.argv.index('--')+1])
bpy.ops.wm.open_mainfile(filepath=str(directory/'robot_walk.blend'))
scene=bpy.data.scenes['WALK_Collision_Checked'];bpy.context.window.scene=scene
scene.render.engine='BLENDER_WORKBENCH'
shading=scene.display.shading
shading.light='STUDIO';shading.studio_light='paint.sl';shading.color_type='MATERIAL'
shading.show_shadows=False;shading.show_cavity=True;shading.cavity_type='BOTH'
scene.render.resolution_percentage=100
frames=directory/'preview_frames';frames.mkdir(exist_ok=True)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(frames/'frame_')
bpy.ops.render.render(animation=True)
subprocess.run(['/usr/bin/ffmpeg','-v','error','-y','-framerate',str(scene.render.fps),'-i',str(frames/'frame_%04d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(directory/'walking.mp4')],check=True)
print('WALK_PREVIEW_SAVED',directory/'walking.mp4')
