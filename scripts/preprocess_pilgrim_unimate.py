"""Run upstream custom-asset processing on an explicitly selected motion skeleton."""
import sys,functools,json
from pathlib import Path
p=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
sys.path.insert(0,'/home/ipsedesktop/Documents/GitHub/aniMove/.cache/unimate-blender313')
sys.path.insert(0,str(p/'UniMate'))
from data_process.mesh_animation import preprocess_char as upstream
from data_process.utils import blender_export

def pose_action(action):
    if action is None:return False
    if hasattr(action,'fcurves'):curves=action.fcurves
    else:curves=[fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    return any(fc.data_path.startswith('pose.bones[') for fc in curves)
blender_export.action_is_relevant_pose=pose_action

# A quiet loader-registration clip must not redefine the selected morphology.
# These are existing export/extraction parameters, not generation changes.
upstream.export_asset=functools.partial(upstream.export_asset,prune=False)
upstream.process_object=functools.partial(upstream.process_object,activity_threshold=0.0)
out=p/'pilgrim_canonical_v002';assert not out.exists()
upstream.preprocess_asset(char_path=str(p/'pilgrim_registration_v001/Pilgrim.glb'),output_dir=str(out),face_r='RightThigh',face_l='LeftThigh',formats=('glb','fbx'),keep_intermediate=True)
(out/'adapter.json').write_text(json.dumps(dict(upstream_file_changes='none',compatibility='Read Blender 5 layered Action channels when discovering pose animation.',export_overrides={'prune':False},feature_overrides={'activity_threshold':0.0},reason='Preserve explicitly selected 23 motion joints and retain innocuous loader-registration clip; no generated motion or model changes.'),indent=2)+'\n')
