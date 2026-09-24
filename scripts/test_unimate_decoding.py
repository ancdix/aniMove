"""Representation checks for the independent UniMate environment."""
import numpy as np
from analyze_unimate_raw import decode, measure, ROOT
from Quaternions import Quaternions

# Non-collinear reference bones catch the bone-local vs T-pose-offset error.
rest=np.array([[0,.6,0],[0,.8,.2],[.3,.4,.1],[.3,0,.2]],dtype=float)
cond={'parents':[-1,0,0,2],'tpos_first_frame':rest,'offsets':np.array([[0,.6,0],[.28,0,0],[.37,0,0],[.41,0,0]])}
features=np.zeros((60,4,12));features[:,:,3:9]=Quaternions.id(1).rotation_matrix(cont6d=True)[0];features[:,0,1]=.6
x=decode(features,cond);assert np.max(abs(x-rest[None]))<1e-12
# A translated root must move every descendant equally, not deform the rig.
features[:,0,9]=.01
x=decode(features,cond);relative=x-x[:,:1];assert np.max(abs(relative-(rest-rest[:1])[None]))<1e-12
assert np.linalg.norm(x[-1,0]-x[0,0])>.5
print('PASS: identity rest roundtrip and rigid root-translation propagation')

# Semantic-name experiments must not change which anatomical tips we measure.
original = np.load(ROOT/'pilgrim_canonical_v002/cond.npy', allow_pickle=True).item()['Pilgrim']
renamed = np.load(ROOT/'pilgrim_labels_001/conditions/front_hind/cond.npy', allow_pickle=True).item()['Pilgrim']
positions = np.repeat(np.asarray(original['tpos_first_frame'])[None], 60, axis=0)
a = measure(positions, original)['effectors']
b = measure(positions, renamed)['effectors']
assert set(a) == set('ABCD') and a == b
print('PASS: A/B/C/D measurement invariant under semantic joint renaming')
