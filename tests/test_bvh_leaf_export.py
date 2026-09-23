"""Regression test for retaining multiple named leaf joints through BVH export."""
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'external' / 'Motion'))
import BVH
import Animation
from Quaternions import Quaternions


class NamedLeafExportTest(unittest.TestCase):
    def test_named_leaves_timing_and_transforms_survive_roundtrip(self):
        parents = np.array([-1, 0, 1, 1])
        offsets = np.array([[0., 0., 0.], [0., 2., 0.], [-1., 1., 0.], [1., 1., 0.]])
        positions = np.tile(offsets, (12, 1, 1))
        positions[:, 0, 0] = np.linspace(0, 2, 12)
        angles = np.zeros((12, 4, 3))
        angles[:, 1, 2] = np.linspace(0, .8, 12)
        animation = Animation.Animation(Quaternions.from_euler(angles), positions,
                                        Quaternions.id(4), offsets, parents)
        names = ['Root', 'Branch', 'LeftTip', 'RightTip']
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'motion.bvh')
            BVH.save(path, animation, names, frametime=.05, leaf_joints=True)
            decoded, decoded_names, interval = BVH.load(path)
        self.assertEqual(decoded_names, names)
        self.assertEqual(interval, .05)
        np.testing.assert_array_equal(decoded.parents, parents)
        np.testing.assert_allclose(Animation.positions_global(decoded),
                                   Animation.positions_global(animation), atol=1e-6)


if __name__ == '__main__':
    unittest.main()
