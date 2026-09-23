"""Blender --background --factory-startup --python this.py -- ROBOT_OUTPUT_DIR.

Build editable IK/FK robots, preserve separately baked Actions, verify evaluated
endpoints against the numerical solution, and render an inspection image.
"""
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector


def bone_matrix(head, tail, pole=(0, 1, 0)):
    y = Vector(tail) - Vector(head)
    y.normalize()
    x = y.cross(Vector(pole))
    if x.length < 1e-6:
        x = y.cross(Vector((1, 0, 0)))
    x.normalize()
    z = x.cross(y).normalized()
    matrix = Matrix((x, y, z)).transposed().to_4x4()
    matrix.translation = Vector(head)
    return matrix


def material(name, color, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = .3
    return mat


def relocate(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def linear_keys(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:
                        point.interpolation = 'LINEAR'


def primitive(name, kind, center, scale, mat, collection, rig=None, bone=None, rotation=None):
    if kind == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8)
    elif kind == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(vertices=16)
    else:
        bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    relocate(obj, collection)
    transform = Matrix.Translation(Vector(center))
    if rotation is not None:
        transform = transform @ rotation.to_matrix().to_4x4()
    transform = transform @ Matrix.Diagonal((*scale, 1))
    obj.data.transform(transform)
    obj.data.materials.append(mat)
    if rig:
        group = obj.vertex_groups.new(name=bone)
        group.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
        modifier = obj.modifiers.new('Rigid segment skin', 'ARMATURE')
        modifier.object = rig
        obj.location = rig.location
    if kind != 'sphere':
        bevel = obj.modifiers.new('Machined edges', 'BEVEL')
        bevel.width = .015
        bevel.segments = 2
    for polygon in obj.data.polygons:
        polygon.use_smooth = kind == 'sphere'
    return obj


def empty(name, collection, display='SPHERE', size=.07):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.empty_display_type = display
    obj.empty_display_size = size
    return obj


def build_rig(prefix, mode, x_offset, motion, record, collections, mats):
    config = record['config']
    frames, fps = record['frames'], record['fps']
    chain = motion[mode + '_joints']
    roots, rotations = motion[mode + '_core'], motion['rotation']
    pole_points = motion[mode + '_poles']
    rig_data = bpy.data.armatures.new(prefix)
    rig = bpy.data.objects.new(prefix, rig_data)
    collections['ROBOT_RIG'].objects.link(rig)
    rig.location.x = x_offset
    rig.show_in_front = False
    rig_data.display_type = 'STICK'
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def add_bone(name, head, tail, parent=None, pole=(0, 1, 0), connected=False):
        bone = rig_data.edit_bones.new(name)
        # A fresh edit bone has zero length; assigning its matrix before head/tail
        # does not establish its axis. Set the endpoints, then the roll.
        bone.head, bone.tail = Vector(head), Vector(tail)
        bone.align_roll(bone_matrix(head, tail, pole).to_3x3().col[2])
        if parent:
            bone.parent = rig_data.edit_bones[parent]
            bone.use_connect = connected
        return bone
    add_bone('ROOT', (0, 0, 0), (0, 0, .2))
    add_bone('CORE', (0, 0, 0), (0, -.2, 0), 'ROOT')
    add_bone('SPINE', (0, -.2, 0), (0, -.45, 0), 'CORE', connected=True)
    add_bone('HEAD', (0, -.5, .12), (0, -.75, .12), 'SPINE', pole=(0, 0, 1))
    rest = (chain[0] - roots[0]) @ rotations[0]
    rest_poles = (pole_points[0] - roots[0]) @ rotations[0]
    for i, key in enumerate(config['limbs']):
        hip, elbow, tip = rest[i]
        bend = rest_poles[i] - hip
        add_bone('LIMB_' + key + '_0', hip, elbow, 'CORE', bend)
        add_bone('LIMB_' + key + '_1', elbow, tip, 'LIMB_' + key + '_0', bend, True)
        add_bone('EE_' + key, tip, tip + np.array([0, 0, -.08]), 'LIMB_' + key + '_1', connected=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    rig['ik_fk'] = 0.0
    rig.id_properties_ui('ik_fk').update(min=0, max=1, description='0 = baked FK Action; 1 = editable target and pole IK')
    rig['source_manifest'] = record['source']['source']
    rig['role_mapping'] = json.dumps({key: value['role'] for key, value in config['limbs'].items()})
    rig['units'] = record['units']
    rig['limits_note'] = 'Baked flexion 8–160 degrees; live IK bend X +/-160 degrees, free Y/Z for robot articulation. Disable use_ik_limit_x for experimental poses.'
    for pose in rig.pose.bones:
        pose.rotation_mode = 'QUATERNION'
    for i, key in enumerate(config['limbs']):
        rig.pose.bones['LIMB_' + key + '_0']['role'] = config['limbs'][key]['role']
        for segment in (0, 1):
            rig.pose.bones['LIMB_' + key + '_' + str(segment)].ik_stretch = 0
    # Bake the independent numerical solve into its own Action, frame by frame.
    previous_quaternions = {}
    for frame in range(frames):
        bpy.context.scene.frame_set(frame + 1)
        matrix = Matrix(rotations[frame].tolist()).to_4x4()
        matrix.translation = Vector(roots[frame])
        rig.pose.bones['ROOT'].matrix = matrix @ rig.data.bones['ROOT'].matrix_local
        bpy.context.view_layer.update()
        for segment in (0, 1):
            for i, key in enumerate(config['limbs']):
                hip, elbow, tip = chain[frame, i]
                points = (hip, elbow, tip)
                rig.pose.bones['LIMB_' + key + '_' + str(segment)].matrix = bone_matrix(points[segment], points[segment + 1], pole_points[frame, i] - hip)
            bpy.context.view_layer.update()
        head = roots[frame] + rotations[frame] @ np.array([0, -.5, .12])
        rig.pose.bones['HEAD'].matrix = bone_matrix(head, head + motion['head_direction'][frame] * .25, (0, 0, 1))
        bpy.context.view_layer.update()
        for pose in rig.pose.bones:
            # Adjacent quaternion signs must agree for sensible subframe interpolation.
            if pose.name in previous_quaternions and pose.rotation_quaternion.dot(previous_quaternions[pose.name]) < 0:
                pose.rotation_quaternion.negate()
            previous_quaternions[pose.name] = pose.rotation_quaternion.copy()
            pose.keyframe_insert('location', frame=frame + 1, group=pose.name)
            pose.keyframe_insert('rotation_quaternion', frame=frame + 1, group=pose.name)
    rig.animation_data.action.name = prefix
    rig.animation_data.action.use_fake_user = True
    linear_keys(rig)
    targets, poles, constraints = [], [], []
    for i, key in enumerate(config['limbs']):
        target = empty('IK_' + prefix + '_' + key, collections['IK_TARGETS'])
        pole = empty('CTRL_POLE_' + prefix + '_' + key, collections['IK_TARGETS'], 'PLAIN_AXES', .12)
        marker = primitive('CONTACT_' + prefix + '_' + key, 'cylinder', (0, 0, 0), (.10, .10, .003), mats['green'], collections['DEBUG_CONTACTS'])
        for frame in range(frames):
            target.location = chain[frame, i, 2] + [x_offset, 0, 0]
            pole.location = pole_points[frame, i] + [x_offset, 0, 0]
            target.keyframe_insert('location', frame=frame + 1)
            pole.keyframe_insert('location', frame=frame + 1)
            marker.location = chain[frame, i, 2] + [x_offset, 0, 0]
            marker.location.z = .007
            marker.scale = (1, 1, 1) if motion['contacts'][frame, i] else (.001, .001, .001)
            marker.keyframe_insert('location', frame=frame + 1)
            marker.keyframe_insert('scale', frame=frame + 1)
        for obj in (target, pole, marker):
            linear_keys(obj)
        lower = rig.pose.bones['LIMB_' + key + '_1']
        ik = lower.constraints.new('IK')
        ik.name = 'Editable two-bone IK ' + key
        ik.target, ik.pole_target, ik.chain_count = target, pole, 2
        ik.use_stretch = False
        ik.iterations = 1000
        lower.use_ik_limit_x = True
        lower.ik_min_x = -math.radians(config['robot']['flexion_max_degrees'])
        lower.ik_max_x = math.radians(config['robot']['flexion_max_degrees'])
        ik.influence = 0
        curve = ik.driver_add('influence')
        variable = curve.driver.variables.new()
        variable.name = 'blend'
        variable.targets[0].id = rig
        variable.targets[0].data_path = '["ik_fk"]'
        curve.driver.expression = 'blend'
        targets.append(target)
        poles.append(pole)
        constraints.append(ik)
    # Mechanical preview mesh; each piece is rigidly weighted to one bone.
    accent = mats['amber'] if mode == 'retarget' else mats['blue']
    primitive(prefix + '_core_shell', 'cube', (0, 0, .02), (.255, .48, .11), mats['silver'], collections['ROBOT_RIG'], rig, 'CORE')
    primitive(prefix + '_core_panel', 'cube', (0, 0, .14), (.19, .35, .025), accent, collections['ROBOT_RIG'], rig, 'CORE')
    primitive(prefix + '_head', 'cube', (0, -.63, .12), (.18, .15, .095), mats['dark'], collections['ROBOT_RIG'], rig, 'HEAD')
    primitive(prefix + '_visor', 'cube', (0, -.785, .12), (.14, .014, .045), accent, collections['ROBOT_RIG'], rig, 'HEAD')
    for i, key in enumerate(config['limbs']):
        for segment in (0, 1):
            a, b = rest[i, segment:segment + 2]
            length = np.linalg.norm(b - a)
            rotation = Vector(b - a).to_track_quat('Z', 'Y')
            primitive(prefix + '_' + key + '_beam' + str(segment), 'cylinder', (a + b) / 2, (.043, .043, length / 2), accent, collections['ROBOT_RIG'], rig, 'LIMB_' + key + '_' + str(segment), rotation)
            primitive(prefix + '_' + key + '_joint' + str(segment), 'sphere', a, (.075, .075, .075), mats['dark'], collections['ROBOT_RIG'], rig, 'LIMB_' + key + '_' + str(segment))
        primitive(prefix + '_' + key + '_foot', 'sphere', rest[i, 2], (config['robot']['foot_radius'],) * 3, mats['silver'], collections['ROBOT_RIG'], rig, 'EE_' + key)
    # Verify baked FK and live IK separately against the independent solver.
    validation = {}
    for blend in (0.0, 1.0):
        rig['ik_fk'] = blend
        rig.update_tag()
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        if blend == 1:
            for i, constraint in enumerate(constraints):
                best = (float('inf'), 0)
                for angle in (0, math.pi / 2, -math.pi / 2, math.pi):
                    constraint.pole_angle = angle
                    bpy.context.view_layer.update()
                    error = (rig.pose.bones['LIMB_' + list(config['limbs'])[i] + '_1'].head - Vector(chain[0, i, 1])).length
                    if error < best[0]:
                        best = (error, angle)
                constraint.pole_angle = best[1]
                bpy.context.view_layer.update()
        errors, bend_errors = [], []
        for frame in range(frames):
            bpy.context.scene.frame_set(frame + 1)
            bpy.context.view_layer.update()
            if blend == 1:
                # Blender's pole angle is relative to the FK chain's roll. The
                # baked source bend plane changes that roll over time, so store
                # a per-frame compensation rather than allowing IK/FK elbow pops.
                for i, (key, constraint) in enumerate(zip(config['limbs'], constraints)):
                    hip, desired, tip = map(Vector, chain[frame, i])
                    axis = (tip - hip).normalized()
                    def radial(point):
                        delta = point - hip
                        return (delta - axis * delta.dot(axis)).normalized()
                    def angle(a, b):
                        return math.atan2(axis.dot(a.cross(b)), a.dot(b))
                    wanted = radial(desired)
                    for _ in range(8):
                        current = radial(rig.pose.bones['LIMB_' + key + '_1'].head)
                        error_angle = angle(current, wanted)
                        if abs(error_angle) < 1e-6:
                            break
                        initial = constraint.pole_angle
                        step = -.01 if initial > 3.1 else .01
                        constraint.pole_angle = initial + step
                        bpy.context.view_layer.update()
                        probe = radial(rig.pose.bones['LIMB_' + key + '_1'].head)
                        derivative = angle(current, probe) / step
                        assert abs(derivative) > .1, 'Degenerate pole-angle calibration'
                        corrected = initial + error_angle / derivative
                        constraint.pole_angle = math.atan2(math.sin(corrected), math.cos(corrected))
                        bpy.context.view_layer.update()
                    constraint.keyframe_insert('pole_angle', frame=frame + 1)
            evaluated = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
            for i, key in enumerate(config['limbs']):
                bone = evaluated.pose.bones['LIMB_' + key + '_1']
                errors.append((bone.tail - Vector(chain[frame, i, 2])).length)
                bend_errors.append((bone.head - Vector(chain[frame, i, 1])).length)
        validation['FK' if blend == 0 else 'IK'] = dict(max_endpoint_error=max(errors), max_bend_error=max(bend_errors))
    print('RIG_VALIDATION', prefix, validation, flush=True)
    assert validation['FK']['max_endpoint_error'] < 1e-4, validation
    assert validation['IK']['max_endpoint_error'] < 1e-3, validation
    assert validation['IK']['max_bend_error'] < 1e-3, validation
    rig['ik_fk'] = 0.0
    rig.update_tag()
    linear_keys(rig)
    mesh_errors = []
    for frame in (0, 39, 69, frames - 1):
        bpy.context.scene.frame_set(frame + 1)
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        for i, key in enumerate(config['limbs']):
            for part, expected in [('beam0', chain[frame, i, :2].mean(axis=0)), ('beam1', chain[frame, i, 1:].mean(axis=0)), ('foot', chain[frame, i, 2])]:
                obj = bpy.data.objects[prefix + '_' + key + '_' + part].evaluated_get(graph)
                center = np.mean([obj.matrix_world @ vertex.co for vertex in obj.data.vertices], axis=0)
                mesh_errors.append(float(np.linalg.norm(center - expected - [x_offset, 0, 0])))
        obj = bpy.data.objects[prefix + '_core_shell'].evaluated_get(graph)
        center = np.mean([obj.matrix_world @ vertex.co for vertex in obj.data.vertices], axis=0)
        mesh_errors.append(float(np.linalg.norm(center - roots[frame] - rotations[frame] @ [0, 0, .02] - [x_offset, 0, 0])))
    validation['mesh_max_center_error'] = max(mesh_errors)
    assert max(mesh_errors) < 1e-4, validation
    rig.select_set(False)
    return rig, validation


def main():
    directory = Path(sys.argv[sys.argv.index('--') + 1])
    destination = directory / 'robot_contact_comparison.blend'
    assert not destination.exists() or '--replace' in sys.argv, 'Refusing to overwrite ' + str(destination)
    record = json.loads((directory / 'retarget.json').read_text())
    motion = np.load(directory / 'motion.npz')
    scene = bpy.data.scenes.new('LAB_Contact_Comparison')
    bpy.context.window.scene = scene
    scene.render.fps, scene.render.fps_base = record['fps'], 1
    scene.frame_start, scene.frame_end = 1, record['frames']
    scene['experiment_manifest'] = str(directory / 'retarget.json')
    scene['instructions'] = 'Left: transferred smoothed source targets. Right: contact-cleaned. Space to play. Select CLEAN rig; custom property ik_fk: 0 baked FK, 1 editable IK targets/poles. Frames 1–120, not a seamless loop.'
    collections = {}
    for name in ['ROBOT_RIG', 'IK_TARGETS', 'DEBUG_CONTACTS', 'CAMERA_LIGHTS', 'STAGE']:
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
        collections[name] = collection
    mats = {name: material(name, color, .65 if name in ('silver', 'dark') else .3) for name, color in dict(silver=(.52, .62, .69), dark=(.035, .055, .075), amber=(.95, .38, .06), blue=(.035, .51, .8), green=(.12, .65, .25), floor=(.065, .085, .115), white=(.75, .85, .9)).items()}
    reports, rigs = {}, []
    for prefix, mode, x in [('RETARGET_', 'retarget', -1.65), ('CLEAN_', 'clean', 1.65)]:
        rig, validation = build_rig(prefix + record['source']['id'], mode, x, motion, record, collections, mats)
        rigs.append(rig)
        reports[mode] = validation
    primitive('Stage', 'cube', (0, 0, -.13), (5, 4, .08), mats['floor'], collections['STAGE'])
    for x in (-1.65, 1.65):
        primitive('Inspection platform', 'cube', (x, -.4, -.015), (1.45, 1.9, .015), mats['dark'], collections['STAGE'])
    bpy.ops.object.camera_add(location=(4.6, -7.8, 5.0))
    camera = bpy.context.object
    relocate(camera, collections['CAMERA_LIGHTS'])
    camera.rotation_euler = (Vector((0, -.4, .55)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type, camera.data.ortho_scale = 'ORTHO', 7.8
    scene.camera = camera
    def overlay(text, x, y, size, mat):
        overlay_mat = mat.copy()
        overlay_mat.name = 'Label ' + mat.name
        overlay_mat.node_tree.nodes.clear()
        output = overlay_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        shader = overlay_mat.node_tree.nodes.new('ShaderNodeEmission')
        shader.inputs['Color'].default_value = mat.diffuse_color
        overlay_mat.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
        data = bpy.data.curves.new(text, 'FONT')
        data.body, data.size = text, size
        obj = bpy.data.objects.new(text, data)
        collections['CAMERA_LIGHTS'].objects.link(obj)
        obj.parent = camera
        obj.location = (x, y, -6)
        obj.data.materials.append(overlay_mat)
    overlay('ANYTOP  /  FOUR-LIMB ROBOT', -3.55, 1.75, .21, mats['white'])
    overlay('Supported weight shift   |   Hound 100 / 01   |   120 frames @ 20 fps', -3.55, 1.48, .11, mats['white'])
    overlay('TRANSFERRED', -3.4, -1.60, .17, mats['amber'])
    overlay('CONTACT CLEANED', .45, -1.60, .17, mats['blue'])
    overlay('Same source timing and body motion. Green markers: estimated ground contacts.', -3.4, -1.89, .105, mats['white'])
    for name, position, energy, size in [('Key', (1, -3, 6), 1400, 5), ('Fill', (-4, -1, 3), 900, 4), ('Rim', (1, 4, 5), 1700, 3)]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.shape, data.size = energy, 'DISK', size
        light = bpy.data.objects.new(name, data)
        collections['CAMERA_LIGHTS'].objects.link(light)
        light.location = position
        light.rotation_euler = (Vector((0, -.4, .5)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    scene.world = bpy.data.worlds.new('Lab world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.065, .085, .12, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1280, 720, 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(directory / 'comparison.png')
    scene.frame_set(70)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = rigs[1]
    rigs[1].select_set(True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.color_type = 'MATERIAL'
    text = bpy.data.texts.new('README_MOTION_LAB')
    text.write(scene['instructions'] + '\n\n' + json.dumps(record, indent=2))
    validation = dict(status='passed', frames=record['frames'], fps=record['fps'], rigs=reports, metrics=record['metrics'])
    (directory / 'blender_validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    bpy.ops.render.render(write_still=True)
    print('ROBOT_BASELINE_VALIDATED', json.dumps(validation))


if __name__ == '__main__':
    main()
