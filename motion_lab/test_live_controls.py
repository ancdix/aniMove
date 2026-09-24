"""Exercise the actual Blender operators: cancellation, async generation and history."""
import bpy,json,time
from pathlib import Path
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001');ns=bpy.app.driver_namespace['motion_lab_ui'];s=bpy.data.scenes['UNIMATE_Motion_Lab'];assert ns['JOB'] is None,'Leave an existing user generation alone';bpy.context.window.scene=s
s.ml_target='Mammal';s.ml_prompt='A dog walks forward.';s.ml_seconds=2;s.ml_seed=9801
assert bpy.ops.motion_lab.generate()=={'FINISHED'};cancelled=ns['JOB'][1].name;assert bpy.ops.motion_lab.cancel()=={'FINISHED'};assert ns['JOB'] is None
s.ml_seconds=4;assert bpy.ops.motion_lab.generate()=={'FINISHED'};job=ns['JOB'][1];(BASE/'ui_test_pending.json').write_text(json.dumps(dict(cancelled_job=cancelled,job=job.name,started=time.time()),indent=2)+'\n');print('ASYNC_UI_TEST',job.name)
