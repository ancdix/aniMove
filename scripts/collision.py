"""Conservative capsule/box robot collision checks and bend-plane cleanup.

Each limb segment has radius 0.075, enclosing the 0.043 beams and joint balls.
Adjacent segments in the same mechanical joint and intended hip mounts are
excluded; independent limbs, torso, head and ground are checked.
"""
import numpy as np
from motion_lab import normalize, two_bone


def segment_distance(p, q, a, b):
    p, q, a, b = [np.asarray(x, dtype=float) for x in (p, q, a, b)]
    u, v, w = q - p, b - a, p - a
    aa, bb, cc = np.dot(u, u), np.dot(u, v), np.dot(v, v)
    dd, ee = np.dot(u, w), np.dot(v, w)
    if aa < 1e-16 and cc < 1e-16:
        return float(np.linalg.norm(w))
    if aa < 1e-16:
        s, t = 0., np.clip(ee / cc, 0, 1)
    elif cc < 1e-16:
        s, t = np.clip(-dd / aa, 0, 1), 0.
    else:
        denominator = aa * cc - bb * bb
        s = np.clip((bb * ee - cc * dd) / denominator, 0, 1) if denominator > 1e-16 else 0.
        t = (bb * s + ee) / cc
        if t < 0:
            t, s = 0., np.clip(-dd / aa, 0, 1)
        elif t > 1:
            t, s = 1., np.clip((bb - dd) / aa, 0, 1)
    return float(np.linalg.norm(w + s * u - t * v))


def segment_box_distance(p, q, center, half):
    """Exact segment-to-axis-aligned-box distance via piecewise quadratics."""
    p = np.asarray(p) - center
    d = np.asarray(q) - center - p
    half = np.asarray(half)
    breaks = [0., 1.]
    for axis in range(3):
        if abs(d[axis]) > 1e-12:
            breaks.extend(t for t in ((-half[axis] - p[axis]) / d[axis], (half[axis] - p[axis]) / d[axis]) if 0 < t < 1)
    breaks = sorted(breaks)
    candidates = list(breaks)
    for start, stop in zip(breaks[:-1], breaks[1:]):
        midpoint = p + d * (start + stop) / 2
        active = abs(midpoint) > half
        if active.any():
            boundary = np.sign(midpoint[active]) * half[active]
            denominator = np.dot(d[active], d[active])
            if denominator > 1e-16:
                candidates.append(np.clip(-np.dot(d[active], p[active] - boundary) / denominator, start, stop))
    points = p[None] + np.array(candidates)[:, None] * d
    return float(np.min(np.linalg.norm(np.maximum(abs(points) - half, 0), axis=-1)))


def head_box(core, rotation, heading):
    y = normalize(heading, (0, -1, 0))
    x = normalize(np.cross(y, [0, 0, 1]), (-1, 0, 0))
    z = normalize(np.cross(x, y))
    orientation = np.column_stack((-x, -y, z))
    origin = core + rotation @ np.array([0, -.5, .12])
    return origin + orientation @ np.array([0, -.1395, 0]), orientation, np.array([.18, .1595, .095])


def frame_clearances(joints, core, rotation, heading, radius=.075, mount_exclusion=.18):
    checks = []
    for i in range(4):
        for j in range(i + 1, 4):
            for a in range(2):
                for b in range(2):
                    clearance = segment_distance(*joints[i, a:a+2], *joints[j, b:b+2]) - 2 * radius
                    checks.append(('limb_%s%d_%s%d' % ('ABCD'[i], a, 'ABCD'[j], b), clearance))
    center, orient, half = head_box(core, rotation, heading)
    for i in range(4):
        for segment in range(2):
            p, q = joints[i, segment:segment+2].copy()
            if segment == 0:
                p += normalize(q-p) * mount_exclusion
            local_p, local_q = (p-core) @ rotation, (q-core) @ rotation
            clearance = segment_box_distance(local_p, local_q, np.array([0, 0, .0375]), np.array([.255, .48, .1275])) - radius
            checks.append(('torso_%s%d' % ('ABCD'[i], segment), clearance))
            # Head is not part of the hip mount and receives no mount exclusion.
            p, q = joints[i, segment:segment+2]
            clearance = segment_box_distance((p-center) @ orient, (q-center) @ orient, np.zeros(3), half) - radius
            checks.append(('head_%s%d' % ('ABCD'[i], segment), clearance))
    return checks


def audit(joints, cores, rotations, headings, clearance=.015):
    minimum, worst, violations = float('inf'), None, []
    categories = dict(limb=float('inf'), torso=float('inf'), head=float('inf'))
    for frame, (pose, core, rot, head) in enumerate(zip(joints, cores, rotations, headings)):
        for name, value in frame_clearances(pose, core, rot, head):
            category = name.split('_')[0]
            categories[category] = min(categories[category], value)
            if value < minimum:
                minimum, worst = value, dict(frame=frame + 1, pair=name, clearance=value)
            if value < clearance - 1e-7:
                violations.append(dict(frame=frame + 1, pair=name, clearance=value))
    return dict(proxy='0.075-radius limb capsules; oriented torso/head boxes; intended hip mounts and adjacent same-limb joints excluded', required_clearance=clearance,
                minimum_clearance=minimum, minimum_by_category=categories, worst=worst,
                intersection_count=sum(item['clearance'] < 0 for item in violations), margin_violation_count=len(violations), violations=violations)


def clean_bend_planes(solution, targets, rotations, headings, config, clearance=.015):
    """Search bend planes jointly, leaving feet and core trajectories unchanged."""
    result = {key: value.copy() for key, value in solution.items()}
    radius = .075
    robot = config['robot']
    lengths = robot['upper_length'], robot['lower_length']
    limits = robot['flexion_min_degrees'], robot['flexion_max_degrees']
    previous = None
    for frame, pose in enumerate(result['joints']):
        preferred = []
        candidates = []
        for limb in range(4):
            hip = pose[limb, 0]
            axis = normalize(targets[frame, limb] - hip)
            # Outboard knees keep left/right and front/rear chains in separate lanes.
            desired = rotations[frame] @ np.array([1 if limb in (0, 2) else -1, -.45 if limb < 2 else .45, 0])
            u = normalize(desired - np.dot(desired, axis) * axis)
            v = normalize(np.cross(axis, u))
            preferred.append(u)
            angles = np.linspace(-np.pi, np.pi, 32, endpoint=False)
            directions = [np.cos(angle)*u + np.sin(angle)*v for angle in angles]
            if previous is not None:
                directions.insert(0, previous[limb])
            directions.insert(0, u)
            choices = []
            for direction in directions:
                elbow, endpoint, plane, error, flexion = two_bone(hip, targets[frame, limb], direction, *lengths, limits)
                choices.append((np.array([hip, elbow, endpoint]), plane))
            candidates.append(choices)
            pose[limb] = choices[0][0]
        selected = np.array(preferred)
        initial_checks = frame_clearances(pose, result['core'][frame], rotations[frame], headings[frame], radius)
        already_clear = min(value for _, value in initial_checks) >= clearance
        # Coordinate descent considers collisions with all three other chains.
        for _ in range(0 if already_clear else 2):
            for limb in range(4):
                best = (float('inf'), None, None)
                for points, direction in candidates[limb]:
                    proposal = pose.copy()
                    proposal[limb] = points
                    checks = frame_clearances(proposal, result['core'][frame], rotations[frame], headings[frame], radius)
                    deficits = np.maximum(0, clearance - np.array([value for _, value in checks]))
                    cost = 100000 * np.dot(deficits, deficits) + .1 * (1 - np.dot(direction, preferred[limb]))
                    if previous is not None:
                        cost += 2 * (1 - np.dot(direction, previous[limb]))
                    if cost < best[0]:
                        best = (cost, points, direction)
                pose[limb], selected[limb] = best[1], best[2]
        for limb in range(4):
            result['poles'][frame, limb] = pose[limb, 0] + selected[limb] * 1.2
        previous = selected
    return result
