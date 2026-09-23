"""Exercise the actual upstream input function without loading T5 or a GPU."""
import ast, unittest
from pathlib import Path
import numpy as np
import torch

class EditInputTest(unittest.TestCase):
    def prepare(self):
        p=Path(__file__).resolve().parents[1]/'external/AnyTop/sample/edit.py'
        tree=ast.parse(p.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_inpainting_inputs')
        env=dict(np=np,encode_joints_names=lambda names,t5:torch.ones((len(names),4)),create_temporal_mask_for_window=lambda w,n:None,truebones_batch_collate=lambda b:b)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),env)
        return env['prepare_inpainting_inputs']
    def cond(self):
        return dict(parents=np.array([-1,0]),mean=np.ones((2,13))*3,std=np.ones((2,13))*2,tpos_first_frame=np.zeros((2,13)),joint_relations=None,joints_graph_dist=None,offsets=None,joints_names=['root','tip'])
    def test_preserves_nonzero_motion_and_roundtrips(self):
        c=self.cond();x=np.arange(5*2*13).reshape(5,2,13)/10
        batch=self.prepare()([x],'test',c,30,None,2,13)
        restored=batch[0][0]*(c['std']+1e-6)+c['mean'];np.testing.assert_allclose(restored,x,atol=1e-12)
        self.assertGreater(abs(batch[0][0]).sum(),0)
    def test_rejects_xyz_in_place_of_features(self):
        with self.assertRaises(ValueError):self.prepare()([np.zeros((5,2,3))],'test',self.cond(),30,None,2,13)
    def test_rejects_nonfinite(self):
        with self.assertRaises(ValueError):self.prepare()([np.full((5,2,13),np.nan)],'test',self.cond(),30,None,2,13)

if __name__=='__main__':unittest.main()
