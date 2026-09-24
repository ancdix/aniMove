import bpy,json
from pathlib import Path
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001');pending=json.loads((BASE/'ui_test_pending.json').read_text());ns=bpy.app.driver_namespace['motion_lab_ui'];s=bpy.data.scenes['UNIMATE_Motion_Lab'];state=json.loads((BASE/'jobs'/pending['job']/'status.json').read_text());print('STATE',state,'PANEL',s.get('status'),'JOB_ACTIVE',ns['JOB'] is not None)
if state['status']=='complete' and ns['JOB'] is None:
    assert s['active_result']==pending['job'] and s.frame_end==120
    assert bpy.context.screen.is_animation_playing
    assert json.loads((BASE/'jobs'/pending['cancelled_job']/'status.json').read_text())['status']=='cancelled'
    assert bpy.ops.motion_lab.save()=={'FINISHED'}
    for key in ns['TARGETS']:
        s.ml_target=key;assert s['active_target']==key
        visible=[k for k in ns['TARGETS'] if not bpy.data.collections['ML_TARGET_'+k].hide_viewport];assert visible==[key]
    s.ml_history=pending['job'];assert bpy.ops.motion_lab.load()=={'FINISHED'}
    result=dict(status='passed',generated_from_ui=pending['job'],frames=s.frame_end,cancel=True,history_reload=True,target_visibility=True,autoplay=True,saved_animation=str(BASE/'jobs'/pending['job']/'animation.blend'))
    (BASE/'ui_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
