"""Export raw-model diagnostics; no corrected trajectories enter these plots."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);base=p.parent/'rise_land_loop_v2';unified=p.parent/'rise_land_unified_v1'
reports=[json.loads((d/'raw_analysis.json').read_text()) for d in [base,unified,p]]
fig,axes=plt.subplots(2,2,figsize=(13,8.2));fig.patch.set_facecolor('#f5f7fa')
colors=['#596a7c','#d99030','#2d8ab4','#9a74b4']
series=[('Quad: endpoints',reports[0],'endpoints'),('Quad: waypoints',reports[0],'waypoints'),('Quad: torso guided',reports[2],'body_guided'),('Unified: waypoints',reports[1],'waypoints')]
ax=axes[0,0]
for i,(label,report,kind) in enumerate(series):
 values=[c['metrics']['max_step_body_lengths'] for c in report['clips'] if c['kind']==kind]
 ax.bar(np.arange(4)+(i-1.5)*.19,values,width=.18,label=label,color=colors[i])
ax.axhline(.5,color='#bd3434',linestyle='--',linewidth=1,label='Prototype rejection threshold')
ax.set_xticks(range(4));ax.set_xticklabels(['4200','4201','4202','4203']);ax.set_xlabel('Matched random seed');ax.set_ylabel('Largest one-frame step / body length');ax.set_title('Extra guidance did not remove raw discontinuities',loc='left',fontsize=11);ax.legend(fontsize=7.5,ncol=2)
t=np.arange(120)/20
for column,joint in enumerate([29,23]):
 ax=axes[1,column]
 for i,seed in enumerate(range(4200,4204)):
  x=np.load(p/('body_guided_seed'+str(seed)+'.xyz.npy'));body=np.linalg.norm(x[:10,17]-x[:10,0],axis=-1).mean();h=(x[:,joint,1]-x[:10,joint,1].mean())/body
  ax.plot(t,h,color=colors[i],label=str(seed),linewidth=1.6)
 ax.axvspan(4.15,5.5,color='#f0cd82',alpha=.35,label='Free landing probe');ax.axvspan(5.5,6,color='#9fc6ce',alpha=.35,label='Authored rest')
 ax.axhline(0,color='#444444',linewidth=.8);ax.axhline(.035,color='#777777',linewidth=.8,linestyle=':')
 ax.set_xlim(3.85,5.95);ax.set_ylim(-.32,.75);ax.set_xlabel('Time (s)');ax.set_ylabel('Foot height above its initial rest / body length');ax.set_title(['Left front foot: inconsistent landing','Right front foot: some samples remain raised'][column],loc='left',fontsize=11)
 ax.legend(fontsize=7.5,ncol=3)
ax=axes[0,1]
for i,seed in enumerate(range(4200,4204)):
 x=np.load(p/('body_guided_seed'+str(seed)+'.xyz.npy'));body=np.linalg.norm(x[:10,17]-x[:10,0],axis=-1).mean();h=(x[:,0,1]+x[:,17,1])/2/body
 ax.plot(t,h,color=colors[i],label=str(seed),linewidth=1.6)
ax.axvspan(4.15,5.5,color='#f0cd82',alpha=.35);ax.axvspan(5.5,6,color='#9fc6ce',alpha=.35);ax.set_xlim(3.85,5.95);ax.set_xlabel('Time (s)');ax.set_ylabel('Torso midpoint height / body length');ax.set_title('Some settling-like motion; no robust impact response',loc='left',fontsize=11)
for ax in axes.flat:
 ax.grid(axis='y',alpha=.15);ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
fig.suptitle('RISE–RETURN LOOP: RAW ANYTOP LANDING PROBE',x=.055,y=.985,ha='left',fontsize=16,fontweight='bold')
fig.text(.055,.938,'20 raw samples tested. Plots precede smoothing, foot pinning, reach correction and robot IK.',fontsize=10)
fig.text(.055,.025,'Kinematic cues only. Heights reference each foot’s initial rest pose; these are not force, dynamics or physical-balance measurements.',fontsize=9)
fig.tight_layout(rect=[.025,.055,.985,.92]);fig.savefig(p/'landing_probe.png',dpi=160);fig.savefig(p/'landing_probe.pdf')
print('PLOT_SAVED',p/'landing_probe.png')
