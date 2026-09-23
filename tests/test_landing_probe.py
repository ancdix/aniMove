import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_rise_land_loop import raw_metrics

class LandingProbeTests(unittest.TestCase):
    def fixture(self):
        x=np.zeros((120,44,3));x[:,:,1]=1.;x[:,17,2]=1
        # Nondegenerate front chains and two feet that start on their rest plane.
        for foot,bend,upper in [(29,26,25),(23,20,19)]:
            x[:,foot]=[.3,0,1];x[:,bend]=[.3,.4,.6];x[:,upper]=[.3,.8,.7]
        feat=np.zeros((120,44,13));mask=np.zeros_like(feat,dtype=bool);mask[:10]=True;mask[48:59]=True;mask[110:]=True
        return x,feat,mask
    def test_forced_suffix_contact_is_not_counted_as_generated_landing(self):
        x,f,m=self.fixture();x[60:110,[29,23],1]=.5
        metrics=raw_metrics(x,f,m)
        self.assertIsNone(metrics['landing_probes']['front_left']['touchdown_frame'])
    def test_free_touchdown_is_identified_without_claiming_physics(self):
        x,f,m=self.fixture();x[60:90,[29,23],1]=np.linspace(.5,0,30)[:,None]
        metrics=raw_metrics(x,f,m);p=metrics['landing_probes']['front_left']
        self.assertTrue(85<=p['touchdown_frame']<=91);self.assertTrue(p['touchdown_in_generated_region'])
        self.assertTrue(p['all_post_touch_samples_generated'])

if __name__=='__main__':unittest.main()
