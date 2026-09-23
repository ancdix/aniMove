import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from walking_motion import footstep_targets
from motion_lab import slip_speed


class WalkingTests(unittest.TestCase):
    def test_stance_points_are_fixed_with_separate_step_lanes(self):
        feet,contacts=footstep_targets(np.arange(240)/30)
        self.assertEqual(int(contacts.sum(1).min()),3)
        self.assertEqual(int(contacts.sum(1).max()),3)
        self.assertLess(slip_speed(feet,contacts,30),1e-12)
        self.assertGreater(float(feet[0,0,1]-feet[-1,0,1]),2.5)
        self.assertGreater(float(feet[...,2].max()),.18)
        self.assertGreaterEqual(float(feet[...,2].min()),.035)

    def test_step_boundary_position_and_velocity_continuity(self):
        delta=1e-5
        for time in [0.,.4,.8,1.2,1.6]:
            feet,_=footstep_targets(np.array([time-delta,time,time+delta]))
            np.testing.assert_allclose(feet[0],feet[2],atol=1e-8)
            np.testing.assert_allclose((feet[2]-feet[1])/delta,(feet[1]-feet[0])/delta,atol=1e-5)


if __name__=='__main__':unittest.main()
