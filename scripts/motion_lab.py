"""Numerical motion tools, independent of Blender and AnyTop's Python runtime."""
import numpy as np


def smooth(values, passes=2):
    result = np.asarray(values, dtype=float).copy()
    for _ in range(passes):
        padded = np.pad(result, [(1, 1)] + [(0, 0)] * (result.ndim - 1), mode='edge')
        result = (padded[:-2] + 2 * padded[1:-1] + padded[2:]) / 4
    return result


def normalize(value, fallback=(1, 0, 0)):
    length = np.linalg.norm(value)
    return np.asarray(value) / length if length > 1e-9 else np.asarray(fallback, dtype=float)


def runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def detect_contacts(feet, fps, body_length, ground, settings):
    """Feet are F,L,3, Z-up. Contact uses smoothed height and full 3D speed."""
    velocity = np.linalg.norm(np.gradient(feet, 1 / fps, axis=0), axis=-1) / body_length
    height = (feet[..., 2] - ground) / body_length
    contacts = np.zeros(height.shape, dtype=bool)
    for limb in range(feet.shape[1]):
        active = False
        for frame in range(len(feet)):
            h, v = height[frame, limb], velocity[frame, limb]
            if active:
                active = h <= settings['height_off'] and v <= settings['speed_off']
            else:
                active = h <= settings['height_on'] and v <= settings['speed_on']
            contacts[frame, limb] = active
        for start, stop in runs(contacts[:, limb]):
            if stop - start < settings['minimum_frames']:
                contacts[start:stop, limb] = False
    return contacts, velocity, height


def pin_contacts(feet, contacts, ground, blend_frames):
    """World anchors, zero slip in fully pinned interiors, eased stance edges."""
    clean = feet.copy()
    clean[..., 2] = np.maximum(clean[..., 2], ground)
    weights = np.zeros(contacts.shape)
    anchors = np.full(feet.shape, np.nan)
    for limb in range(feet.shape[1]):
        for start, stop in runs(contacts[:, limb]):
            anchor = feet[start, limb].copy()
            anchor[2] = ground
            for frame in range(start, stop):
                # Contacts extending beyond a clip edge have no within-clip entry/exit.
                entering = 1 if start == 0 else min(1, (frame - start + 1) / blend_frames)
                leaving = 1 if stop == len(feet) else min(1, (stop - frame) / blend_frames)
                w = min(entering, leaving)
                w = w * w * (3 - 2 * w)
                weights[frame, limb] = w
                anchors[frame, limb] = anchor
                clean[frame, limb] = clean[frame, limb] * (1 - w) + anchor * w
    return clean, weights, anchors


def slip_speed(feet, mask, fps):
    pairs = mask[1:] & mask[:-1]
    speeds = np.linalg.norm(np.diff(feet, axis=0), axis=-1) * fps
    return float(speeds[pairs].mean()) if pairs.any() else None


def to_blender(xyz):
    result = xyz[..., [0, 2, 1]].astype(float).copy()
    result[..., 1] *= -1
    return result


def reach_bounds(upper, lower, minimum_flexion, maximum_flexion):
    # Flexion is 0 at a straight knee/elbow, 180 at a fully folded chain.
    def distance(angle):
        return np.sqrt(upper**2 + lower**2 + 2 * upper * lower * np.cos(np.radians(angle)))
    return distance(maximum_flexion), distance(minimum_flexion)


def two_bone(hip, target, pole_direction, upper, lower, limits=(8, 160)):
    """Analytic task-space IK with explicit reach/limit projection diagnostics."""
    offset = target - hip
    distance = np.linalg.norm(offset)
    direction = normalize(offset, (0, 0, -1))
    lo, hi = reach_bounds(upper, lower, *limits)
    actual = np.clip(distance, lo, hi)
    endpoint = hip + actual * direction
    perpendicular = pole_direction - np.dot(pole_direction, direction) * direction
    if np.linalg.norm(perpendicular) < 1e-8:
        axis = np.eye(3)[np.argmin(abs(direction))]
        perpendicular = np.cross(direction, axis)
    perpendicular = normalize(perpendicular)
    along = (upper**2 - lower**2 + actual**2) / (2 * actual)
    elbow = hip + along * direction + np.sqrt(max(0, upper**2 - along**2)) * perpendicular
    flexion = np.degrees(np.arccos(np.clip((actual**2 - upper**2 - lower**2) / (2 * upper * lower), -1, 1)))
    return elbow, endpoint, perpendicular, float(abs(actual - distance)), float(flexion)
