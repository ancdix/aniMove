"""Render a fast workbench movie from the saved comparison without editing it."""
from pathlib import Path
import subprocess
import sys
import bpy


directory = Path(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=str(directory / 'robot_contact_comparison.blend'))
scene = bpy.data.scenes['LAB_Contact_Comparison']
bpy.context.window.scene = scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.studio_light = 'paint.sl'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = False  # Prevent camera-facing labels casting floor text.
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.background_type = 'WORLD'
scene.render.resolution_percentage = 75
scene.render.image_settings.file_format = 'PNG'
frames = directory / 'preview_frames'
frames.mkdir(exist_ok=True)
scene.render.filepath = str(frames / 'frame_')
bpy.ops.render.render(animation=True)
subprocess.run(['/usr/bin/ffmpeg', '-v', 'error', '-y', '-framerate', str(scene.render.fps), '-i', str(frames / 'frame_%04d.png'), '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(directory / 'comparison.mp4')], check=True)
print('ROBOT_PREVIEW_SAVED', directory / 'comparison.mp4')
