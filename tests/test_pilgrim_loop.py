"""Guard that closing a phrase only replaces its boundary neighborhood."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_pilgrim_loop import periodic_bridge

class PilgrimLoopTests(unittest.TestCase):
    def test_retains_interior_and_does_not_reverse_motion(self):
        t=np.arange(120,dtype=float);source=np.stack([.01*t,np.sin(t/30),np.cos(t/20)],axis=1)
        result=periodic_bridge(source,12)
        np.testing.assert_array_equal(result[12:109],source[12:109])
        self.assertGreater(np.linalg.norm(result[:12]-source[:12]),0)
        self.assertLess(np.linalg.norm(result[0]-result[-1]),np.linalg.norm(source[0]-source[-1]))

    def test_preserves_constant_channels(self):
        source=np.ones((120,23,3))*3.14
        np.testing.assert_allclose(periodic_bridge(source),source,atol=1e-12)

    def test_rejects_window_that_erases_interior(self):
        with self.assertRaises(ValueError):periodic_bridge(np.zeros((20,3)),12)

if __name__=='__main__':unittest.main()
