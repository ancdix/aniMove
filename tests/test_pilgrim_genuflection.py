"""Regression gates for changing support roles during the ceremony."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pilgrim_skeleton import definition
from run_pilgrim_genuflection import guide

class GenuflectionTests(unittest.TestCase):
 def test_recovery_keeps_last_support_hand_reachable(self):
  d=definition();x,p,v,e=guide(d)
  self.assertLess(e.max(),1e-8)
  np.testing.assert_allclose(x[0],x[-1],atol=1e-12)
 def test_staggered_contacts_and_shared_hold_are_stationary(self):
  d=definition();x,p,v,e=guide(d);ix={n:i for i,n in enumerate(d['names'])}
  for k,a,b in [('A',78,197),('B',100,177),('C',0,241),('D',0,241)]:
   np.testing.assert_allclose(x[a:b,ix[k+'_3']],np.repeat(x[a:a+1,ix[k+'_3']],b-a,axis=0),atol=1e-10)
  np.testing.assert_allclose(x[108:133],np.repeat(x[120:121],25,axis=0),atol=1e-12)
if __name__=='__main__':unittest.main()
