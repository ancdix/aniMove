"""Common-view raw comparison and uncorrected text-expansion diagnostics."""
import json,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from compare_unimate_anytop import ROOT,old,cond,parents,names,scale,v,measure
run=ROOT/'pilgrim_harvest_001';review=run/'review';manifest=json.loads((run/'run.json').read_text());oldrun=json.loads((old/'run.json').read_text());oldskel=json.loads((old/'skeleton.json').read_text());ix=[oldskel['names'].index(v['canonical_to_original'][n]) for n in names];source='Pilgrim_bipeds_seed7120';anyx=np.load(old/(source+'.xyz.npy'))[:40,ix]/oldrun['normalized_units_per_design_meter']
colors={'A':'#26b7cc','B':'#d95c33','C':'#61ad4f','D':'#9e59d9','core':'#aa8648'};ec=[colors.get(v['canonical_to_original'][n].split('_')[0],colors['core']) for n in names]
# No retiming or interpolation: 60fps holds each AnyTop frame3ticks, UniMate2ticks.
fig=plt.figure(figsize=(12,6));axs=[fig.add_subplot(1,2,i+1,projection='3d') for i in range(2)];writer=FFMpegWriter(fps=60,codec='libx264',extra_args=['-crf','20','-pix_fmt','yuv420p','-threads','2']);pairs=[]
with writer.saving(fig,str(review/'anytop_unimate_raw.mp4'),100):
    for label,seed in [('p01',9402),('p06',9400),('p07',9400)]:
        r=next(r for r in manifest['runs'] if r['label']==label and r['seed']==seed);ux=np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale;seq=[anyx,ux]
        low=np.concatenate(seq).min((0,1))-.2;high=np.concatenate(seq).max((0,1))+.2;low[1]=min(low[1],-.2);span=max(high-low);center=(low+high)/2;lines=[];trails=[]
        for k,ax in enumerate(axs):
            ax.clear();ax.set_xlim(center[0]-span/2,center[0]+span/2);ax.set_ylim(center[2]-span/2,center[2]+span/2);ax.set_zlim(center[1]-span/2,center[1]+span/2);ax.set_box_aspect((1,1,1));ax.view_init(20,-55);ax.set_xlabel('X / design m');ax.set_ylabel('Forward Z');ax.set_zlabel('Y up');ax.set_title(('AnyTop raw · Orient source\n'+source) if k==0 else f'UniMate raw · {label} / {seed}\n'+r['prompt'],fontsize=10)
            lines.append([ax.plot([],[],[],color=ec[j],lw=3)[0] for j in range(1,len(names))]);trails.append(ax.plot([],[],[],color='.4',lw=1)[0]);xx=np.linspace(center[0]-span/2,center[0]+span/2,2);zz=np.linspace(center[2]-span/2,center[2]+span/2,2);xx,zz=np.meshgrid(xx,zz);ax.plot_surface(xx,zz,np.zeros_like(xx),color='gray',alpha=.08)
        fig.suptitle('Raw examples, not paired prompts · same units, axes, floor, time and fixed camera\nNo fitting, contacts or cleanup. AnyTop20fps / UniMate30fps held at native sample times.',fontsize=12);fig.tight_layout(rect=(0,0,1,.9))
        for tick in range(120):
            for k,x in enumerate(seq):
                f=min(len(x)-1,tick//(3 if k==0 else 2));pose=x[f]
                for j,line in enumerate(lines[k],1):p=parents[j];line.set_data_3d(pose[[p,j],0],pose[[p,j],2],pose[[p,j],1])
                path=x[:f+1,0];trails[k].set_data_3d(path[:,0],path[:,2],path[:,1])
            writer.grab_frame()
        pairs.append(dict(anytop=source,unimate=label,seed=seed))
plt.close(fig);(review/'comparison_selection.json').write_text(json.dumps(dict(pairs=pairs,selection='Existing AnyTop Orient source versus illustrative UniMate weight-shift, twist and walk; not random selection or a paired semantic benchmark.'),indent=2)+'\n')
exp=ROOT/'pilgrim_expansion_001';rows=json.loads((exp/'run.json').read_text())['runs'];fig,axs=plt.subplots(2,8,figsize=(18,7));diagnostics=[]
for row,r in enumerate(rows):
    x=np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale
    for col,f in enumerate([0,59,60,109,110,159,160,209]):
        ax=axs[row,col];pose=x[f].copy();pose[:,[0,2]]-=pose[0,[0,2]];proj=pose[:,0]*.85+pose[:,2]*.53
        for j,p in enumerate(parents):
            if p>=0:ax.plot(proj[[p,j]],pose[[p,j],1],color=ec[j],lw=2)
        ax.axhline(0,color='red',lw=.6);ax.set_xlim(-2,2);ax.set_ylim(-1,11);ax.set_aspect('equal');ax.set_title(f'{r["seed"]} / f{f+1}',fontsize=9);ax.set_xticks([])
    steps=np.linalg.norm(np.diff(x,axis=0),axis=-1);seams=[60,110,160];diagnostics.append(dict(seed=r['seed'],metrics=measure(x,30),seam_max_joint_step_m={str(f):float(steps[f-1].max()) for f in seams},all_steps_p95_m=float(np.percentile(steps,95))))
fig.suptitle('Raw expansion · still → lower → four-limb forward → rise\nRoot X/Z aligned only; height/floor unchanged. Frames around each splice. No cleanup.',fontsize=14);fig.tight_layout(rect=(0,0,1,.87));fig.savefig(exp/'expansion_poses.png',dpi=140);plt.close(fig)
(exp/'expansion_diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
videos=[next((Path(r['path'])/'samples/animations').glob('*_fk.mp4')) for r in rows];subprocess.run(['ffmpeg','-y','-v','error','-i',str(videos[0]),'-i',str(videos[1]),'-filter_complex_threads','1','-filter_complex','[0:v][1:v]hstack=inputs=2[v]','-map','[v]','-c:v','libx264','-threads','2','-crf','20','-pix_fmt','yuv420p',str(exp/'expansion_comparison.mp4')],check=True)
