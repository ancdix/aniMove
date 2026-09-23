"""Reload a saved robot baseline and independently verify playback and IK editing."""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector


def main():
    directory = Path(sys.argv[sys.argv.index('--') + 1])
    bpy.ops.wm.open_mainfile(filepath=str(directory / 'robot_contact_comparison.blend'))
    scene = bpy.data.scenes['LAB_Contact_Comparison']
    bpy.context.window.scene = scene
    motion = np.load(directory / 'motion.npz')
    record = json.loads((directory / 'retarget.json').read_text())
    reports = {}
    assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, record['frames'], record['fps'])
    for prefix, mode in [('RETARGET_', 'retarget'), ('CLEAN_', 'clean')]:
        rig = bpy.data.objects[prefix + record['source']['id']]
        report = {}
        for blend in (0.0, 1.0):
            rig['ik_fk'] = blend
            rig.update_tag()
            errors, lengths, roll_jumps = [], [], []
            previous_angles = None
            for frame in range(record['frames']):
                scene.frame_set(frame + 1)
                bpy.context.view_layer.update()
                evaluated = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
                angles = []
                for i, key in enumerate(record['config']['limbs']):
                    for segment in (0, 1):
                        bone = evaluated.pose.bones['LIMB_' + key + '_' + str(segment)]
                        errors.append((bone.head - Vector(motion[mode + '_joints'][frame, i, segment])).length)
                        errors.append((bone.tail - Vector(motion[mode + '_joints'][frame, i, segment + 1])).length)
                        expected_length = record['config']['robot']['upper_length' if segment == 0 else 'lower_length']
                        lengths.append(abs((bone.tail - bone.head).length - expected_length))
                    angles.append(rig.pose.bones['LIMB_' + key + '_1'].constraints[0].pole_angle)
                if previous_angles is not None:
                    roll_jumps.append(float(np.max(abs(np.array(angles) - previous_angles))))
                previous_angles = np.array(angles)
            report['FK' if blend == 0 else 'IK'] = dict(max_joint_error=max(errors), max_length_error=max(lengths), max_pole_angle_step=max(roll_jumps))
            assert max(errors) < 1e-3, report
            assert max(lengths) < 1e-5, report
            assert max(roll_jumps) < np.pi, 'Pole-angle wrap would cause subframe flipping'
        # Demonstrate actual editing, beyond replaying baked targets.
        scene.frame_set(20)
        target = bpy.data.objects['IK_' + prefix + record['source']['id'] + '_A']
        target.location.x += .03
        bpy.context.view_layer.update()
        tip = rig.matrix_world @ rig.pose.bones['LIMB_A_1'].tail
        error = (tip - target.location).length
        assert error < 1e-3, error
        report['interactive_target_move_error'] = error
        reports[mode] = report
    (directory / 'reload_validation.json').write_text(json.dumps(dict(status='passed', rigs=reports), indent=2) + '\n')
    print('SAVED_ROBOT_VALIDATED', json.dumps(reports))


if __name__ == '__main__':
    main()
