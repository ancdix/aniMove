import sys
import unittest
from pathlib import Path
import numpy as np
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collision import segment_distance, segment_box_distance, audit, clean_bend_planes
from retarget_motion import solve


class CollisionTests(unittest.TestCase):
    def test_crossing_parallel_and_degenerate_segments(self):
        self.assertAlmostEqual(segment_distance([-1,0,0],[1,0,0],[0,-1,0],[0,1,0]),0)
        self.assertAlmostEqual(segment_distance([0,0,0],[1,0,0],[0,.2,0],[1,.2,0]),.2)
        self.assertAlmostEqual(segment_distance([0,0,0],[0,0,0],[2,0,0],[2,1,0]),2)
        self.assertAlmostEqual(segment_distance([0,0,0],[1,0,0],[2,1,0],[3,1,0]),np.sqrt(2))

    def test_segment_box_interior_corner_and_rotated_equivalent(self):
        box = np.array([1.,1.,1.]);zero=np.zeros(3)
        self.assertEqual(segment_box_distance([-2,0,0],[2,0,0],zero,box),0)
        self.assertAlmostEqual(segment_box_distance([2,2,-2],[2,2,2],zero,box),np.sqrt(2))
        self.assertAlmostEqual(segment_box_distance([2,0,0],[2,0,0],zero,box),1)
        self.assertAlmostEqual(segment_box_distance([-3,2,0],[3,2,0],zero,box),1)

    def test_bend_cleanup_removes_intersections_without_moving_feet(self):
        config=json.loads((Path(__file__).resolve().parents[1]/'configs/hound_robot.json').read_text())
        for key,limb in config['limbs'].items():limb['hip'][0]=.35 if key in 'AC' else -.35
        core=np.array([[0.,0.,1.]])
        rotation=np.eye(3)[None]
        feet=np.array([[[.55,-.45,.035],[-.55,-.45,.035],[.55,.45,.035],[-.55,.45,.035]]])
        bends=np.zeros_like(feet)+[0,0,.6]
        head=np.array([[0.,-1.,0.]])
        before=solve(core,rotation,feet,bends,np.ones((1,4),bool),config,True)
        self.assertGreater(audit(before['joints'],core,rotation,head)['intersection_count'],0)
        after=clean_bend_planes(before,feet,rotation,head,config)
        self.assertEqual(audit(after['joints'],core,rotation,head)['margin_violation_count'],0)
        np.testing.assert_allclose(after['joints'][:,:,2],feet,atol=1e-12)


if __name__ == '__main__':
    unittest.main()
