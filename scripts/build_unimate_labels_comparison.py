"""Three exact-FK rigs, matched Actions and a comparison selector; no motion edits."""
import bpy,json
from pathlib import Path
from mathutils import Vector
import numpy as np
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=BASE/'pilgrim_labels_001';manifest=json.loads((out/'run.json').read_text());v=json.loads((BASE/'pilgrim_canonical_v002/asset_validation.json').read_text());scale=v['scale'];s=bpy.context.scene;s.name='PILGRIM_UniMate_LABELS';s.render.resolution_x=1680;s.render.resolution_y=760
rig=s.objects[s['rig']];links=[o for o in s.objects if any(mod.type=='ARMATURE' and mod.object==rig for mod in o.modifiers)];rigs={};variants=['arms_legs','front_hind','neutral_limbs']
for i,variant in enumerate(variants):
    if i==0:r=rig
    else:
        r=rig.copy();r.data=rig.data.copy();s.collection.objects.link(r)
        for src in links:
            o=src.copy();o.name='LABEL_'+variant+'_'+src.name;o.parent=r;s.collection.objects.link(o)
            for mod in o.modifiers:
                if mod.type=='ARMATURE':mod.object=r
    r.name='LABEL_RIG_'+variant;r.location=(5*(i-1),0,0);rigs[variant]=r.name
    font=bpy.data.curves.new('LABEL_FONT_'+variant,'FONT');font.body=['ARMS + LEGS','FRONT + HIND LEGS','GENERIC BONE'][i];font.align_x='CENTER';font.size=.22;o=bpy.data.objects.new('LABEL_TITLE_'+variant,font);s.collection.objects.link(o);mat=bpy.data.materials.new('LABEL_MAT_'+variant);mat.diffuse_color=(.95,.95,.95,1);font.materials.append(mat)
cases={f'{prompt}_{seed}':dict(prompt_id=prompt,seed=seed,prompt=text) for prompt,text in manifest['prompts'].items() for seed in manifest['seeds']};s['cases']=json.dumps(cases);s['rigs']=json.dumps(rigs);s['active_case']=next(iter(cases));s['comparison_note']='Only clean limb labels differ; identical morphology/prompts/noise verified. Rigs have constant X display offsets -5,0,+5m.'
code=(Path(__file__).parent/'unimate_labels_ui.py').read_text();t=bpy.data.texts.new('UNIMATE_LABELS_UI.py');t.write(code);namespace={'__name__':'unimate_labels_build'};exec(code,namespace);bpy.app.driver_namespace['unimate_labels_ui']=namespace
# Verify every source pose in each rig's local coordinates (display offsets excluded).
max_error=0.;checks=[]
for case_id,case in cases.items():
    namespace['select_case'](case_id)
    targets={var:np.load(out/'clips'/f"{var}_{case['prompt_id']}_{case['seed']}"/'raw_kinematics.npz') for var in variants}
    for frame in range(60):
        s.frame_set(frame+1);bpy.context.view_layer.update()
        for variant in variants:
            r=s.objects[rigs[variant]];data=targets[variant];x=data['positions'][frame]/scale
            for j,name in enumerate(data['names']):max_error=max(max_error,(r.pose.bones[name].head-Vector((x[j,0],-x[j,2],x[j,1]))).length)
    checks.append(case_id)
assert max_error<2e-4,max_error;namespace['select_case']('p07_9600');s.sync_mode='FRAME_DROP'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False
readme=bpy.data.texts.new('README_UNIMATE_LABELS');readme.write('Matched joint-name experiment. 27 raw clips and3 baseline replays. Same skeleton, parents, rest pose, root facing, registration clip, action text, noise and model. Only16 limb names differ. Left arms+legs; center front+hind legs; right generic Bone. The three rigs have constant X offsets only for display. Run UNIMATE_LABELS_UI.py to restore the optional selector after reopening. No IK, cleanup or physical validation. Native30fps,60frames; playback wraps abruptly. Data and audits: '+str(out))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'labels_comparison.blend'));s.render.filepath=str(out/'labels_blender_preview.png');bpy.ops.render.render(write_still=True);(out/'blender_comparison_validation.json').write_text(json.dumps(dict(status='passed',cases=checks,rigs=rigs,raw_actions=27,replay_actions=3,max_joint_error_design_m=max_error,display_offset_only=True),indent=2)+'\n');print('VERIFIED',max_error)
