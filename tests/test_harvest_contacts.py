"""Contact candidates must be both near the floor and nearly stationary."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_pilgrim_harvest import contacts
class HarvestContacts(unittest.TestCase):
 def test_stationary_floor_and_hovering_points_differ(self):
  x=np.zeros((60,4,3));x[:,:,1]=.06;x[:,1,1]=.4;x[:,2,1]=-.3
  c,v=contacts(x,[0,1,2,3]);self.assertTrue(c[:,0].all());self.assertFalse(c[:,1:3].any())
 def test_fast_floor_motion_is_not_a_planted_contact(self):
  x=np.zeros((60,4,3));x[:,:,1]=.06;x[:,:,0]=np.arange(60)[:,None]*.05
  c,v=contacts(x,[0,1,2,3]);self.assertFalse(c.any())
if __name__=='__main__':unittest.main()
