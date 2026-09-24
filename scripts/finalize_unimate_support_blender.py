"""Give the standalone support review its own scene, UI and verification."""
import bpy,json
from pathlib import Path
out=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_review_001');s=bpy.context.scene;s.name='PILGRIM_UniMate_SUPPORT'
rig=s.objects[s['rig']];rig.name='PILGRIM_UniMate_SUPPORT_Rig';s['rig']=rig.name
util=bpy.data.texts['UNIMATE_REVIEW_UTILITIES.py'];util.name='UNIMATE_SUPPORT_UTILITIES.py';code=util.as_string().replace('PILGRIM_UniMate_RAW','PILGRIM_UniMate_SUPPORT');util.clear();util.write(code)
ui=bpy.data.texts['UNIMATE_REVIEW_UI.py'];ui.name='UNIMATE_SUPPORT_UI.py';code=ui.as_string()
for a,b in [('UNIMATE_REVIEW_UTILITIES.py','UNIMATE_SUPPORT_UTILITIES.py'),('UNIMATE_OT_step','UNIMATE_OT_support_step'),('UNIMATE_PT_raw_review','UNIMATE_PT_support_review'),('unimate_raw_clip','unimate_support_clip'),('unimate.step_clip','unimate.support_step'),('PILGRIM_UniMate_RAW','PILGRIM_UniMate_SUPPORT'),('UniMate — raw review','UniMate — support feasibility')]:code=code.replace(a,b)
code=code.replace("layout.separator();layout.label(text='Raw • 30 fps • CFG 3')", "layout.separator();layout.label(text='Raw • 30 fps • CFG 3');layout.label(text='Four-limb gait gate: NOT MET')")
ui.clear();ui.write(code);ns={'__name__':'support_ui'};exec(code,ns);bpy.app.driver_namespace['unimate_support_ui']=ns
selected=json.loads((out/'selection.json').read_text())['action'];s.unimate_support_clip=selected
readme=bpy.data.texts['README_UNIMATE_RAW'];readme.name='README_UNIMATE_SUPPORT';readme.clear();readme.write('Raw support feasibility: explicit biped / four-legged / hands-and-feet crawling prompts on the same upright Pilgrim skeleton. 27 new clips across detailed/short prompts, plus one earlier bipedal walking reference. No correction or transition assembly. See support_analysis.json and results report. Run UNIMATE_SUPPORT_UI.py to restore selector after reopening. Playback wrap is a hard reset.\n')
s['support_analysis']=str(out/'support_analysis.json');s['selection_note']=json.loads((out/'selection.json').read_text())['note']
bpy.ops.wm.save_as_mainfile(filepath=str(out/'support_review.blend'));s.render.filepath=str(out/'support_blender_preview.png');bpy.ops.render.render(write_still=True)
