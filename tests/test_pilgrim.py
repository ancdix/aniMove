"""Pose-envelope invariants guarding against unreachable targets and limb crossing."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pilgrim_skeleton import definition,pose,audit

class PilgrimGeometryTests(unittest.TestCase):
    def test_pose_envelope_reach_lengths_and_clearance(self):
        d=definition();poses=[]
        for lower,pitch,yaw,a,b in [(0,0,0,0,0),(.2,25,0,0,0),(.45,40,0,1,0),(.55,50,0,1,1),(.55,48,12,1,1),(.25,20,-8,0,0)]:
            xyz,_,error=pose(d,lower,pitch,yaw,a,b);self.assertLess(error.max(),1e-9);poses.append(xyz)
        r=audit(d,np.array(poses));self.assertLess(r['max_bone_length_error'],1e-9);self.assertGreater(r['min_interlimb_capsule_clearance'],.1);self.assertGreater(r['min_ring_limb_capsule_clearance'],.1)

    def test_contact_pose_preserves_four_support_anchors(self):
        d=definition();a,_,_=pose(d,.55,50,0,1,1);b,_,_=pose(d,.55,48,12,1,1)
        np.testing.assert_allclose(a[d['contact_joints']],b[d['contact_joints']],atol=1e-9)
        np.testing.assert_allclose(a[d['contact_joints'],1],.06,atol=1e-9)

if __name__=='__main__':unittest.main()
