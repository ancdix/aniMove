import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from motion_lab import detect_contacts, pin_contacts, reach_bounds, runs, slip_speed, two_bone


class MotionLabTests(unittest.TestCase):
    def test_hysteresis_and_short_contact_rejection(self):
        feet = np.zeros((13, 1, 3))
        feet[:, 0, 2] = [.2, .05, .09, .12, .09, .14, .17, .2, .05, .2, .2, .2, .2]
        settings = dict(height_on=.1, height_off=.16, speed_on=100, speed_off=200, minimum_frames=3)
        mask, _, _ = detect_contacts(feet, 20, 1, 0, settings)
        self.assertEqual(runs(mask[:, 0]), [(1, 6)])

    def test_world_pin_and_swing_preservation(self):
        feet = np.zeros((15, 1, 3))
        feet[:, 0, 0] = np.arange(15) * .01
        feet[:, 0, 2] = .01
        mask = np.zeros((15, 1), bool)
        mask[2:13] = True
        clean, weights, anchors = pin_contacts(feet, mask, 0, 3)
        np.testing.assert_array_equal(clean[[0, 1, 13, 14]], feet[[0, 1, 13, 14]])
        self.assertLess(slip_speed(clean, weights == 1, 20), 1e-12)
        self.assertGreater(slip_speed(feet, weights == 1, 20), 0)
        np.testing.assert_allclose(clean[4:11, 0, 2], 0)
        self.assertTrue(np.isnan(anchors[0]).all())

    def test_ik_lengths_reach_and_degenerate_pole(self):
        for target in [np.array([.3, .2, -.8]), np.array([0., 0., -4.]), np.zeros(3)]:
            elbow, tip, _, error, flexion = two_bone(np.zeros(3), target, target, .7, .6)
            self.assertAlmostEqual(np.linalg.norm(elbow), .7)
            self.assertAlmostEqual(np.linalg.norm(tip - elbow), .6)
            self.assertTrue(np.isfinite(elbow).all())
            self.assertGreaterEqual(flexion, 8 - 1e-8)
            self.assertLessEqual(flexion, 160 + 1e-8)
            self.assertAlmostEqual(np.linalg.norm(tip - target), error)


if __name__ == '__main__':
    unittest.main()
