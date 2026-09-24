"""Contact, trajectory, source-contribution and onion-skin studies from saved arrays."""
import argparse,json,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/pilgrim_studies_mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from motion_lab import to_blender

def main(p):
 d=json.loads((p/'skeleton.json').read_text());m=np.load(p/'motion.npz');ix={n:i for i,n in enumerate(d['names'])};parents=d['parents'];x=m['clean'];t=np.arange(241)/20
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'#f4f1e8','axes.facecolor':'#f4f1e8','axes.spines.top':False,'axes.spines.right':False})
 colors=['#9c4737','#2a798c','#a47a26','#547348'];fig,axs=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
 for k,col in zip('ABCD',colors):
  tip=x[:,ix[k+'_3']];axs[0,0].plot(tip[:,0],tip[:,2],c=col,label=k,lw=2);axs[0,1].plot(t,tip[:,1]-.06,c=col,label=k,lw=2);axs[1,0].plot(t,m['contacts'][:,'ABCD'.index(k)]*.7+'ABCD'.index(k),c=col,lw=3)
 axs[0,0].set(title='Palm/sole paths · plan view',xlabel='X · design meters',ylabel='Forward Z · design meters');axs[0,0].axis('equal');axs[0,0].legend(ncol=4)
 axs[0,1].set(title='Contact height',xlabel='Seconds',ylabel='Palm height above planted level');axs[0,1].axhline(0,color='#777777',lw=.5)
 axs[1,0].set(title='Authored support weights',xlabel='Seconds',yticks=np.arange(4)+.35,yticklabels=list('ABCD'))
 for key,label,col in [('raw','Raw guided AnyTop','#ad7967'),('fitted','Fixed-length fit','#60899a'),('clean','Final directed loop','#182e35'),('guide','Authored guide','#b69a39')]:
  v=m[key];axs[1,1].plot(np.arange(len(v))/20,v[:,0,1],label=label,c=col,lw=1.4)
 axs[1,1].set(title='Root height · source and corrections',xlabel='Seconds',ylabel='Design meters');axs[1,1].legend(fontsize=8)
 fig.suptitle('FIRST GENUFLECTION  /  contacts and trajectories',fontsize=18,fontweight='bold');fig.savefig(p/'trajectory_study.png',dpi=160);plt.close(fig)
 # Six simultaneous, consistently scaled skeleton poses, source Y-up converted to Blender axes.
 fig=plt.figure(figsize=(15,6),constrained_layout=True);fig.suptitle('FIRST GENUFLECTION  /  pose and support study',fontsize=18,fontweight='bold')
 for i,(name,f) in enumerate([('Upright',0),('Bow',56),('A planted',84),('Four contacts',120),('Reorient',160),('B released',196)]):
  ax=fig.add_subplot(1,6,i+1);pose=np.c_[x[f,:,0]+.45*x[f,:,2],x[f,:,1]];
  for j,pa in enumerate(parents):
   if pa<0:continue
   limb=d['names'][j][0];col=colors['ABCD'.index(limb)] if limb in 'ABCD' else '#293d43';ax.plot(*pose[[pa,j]].T,color=col,lw=2.4)
  for li,j in enumerate(d['contact_joints']):ax.scatter(*pose[j],s=30,c=colors[li],marker='s' if m['contacts'][f,li]>.99 else 'o')
  ax.set(xlim=(-1.2,1.5),ylim=(-.05,3.2),title=name+'\n'+str(f/20)+' s');ax.set_aspect('equal');ax.set_axis_off()
 fig.text(.5,.06,'Squares: planted contacts   ·   A then B plant   ·   B then A release   ·   Body path is not reversed',ha='center',fontsize=11);fig.savefig(p/'pose_study.png',dpi=180);plt.close(fig)
 # Overlay poses in side elevation; shows the distinct return arc directly.
 fig,ax=plt.subplots(figsize=(8,7),constrained_layout=True)
 for f in [24,56,78,100,132,160,176,196,220]:
  col='#a35f43' if f<=100 else '#296c81';alpha=.25 if f not in [78,196] else .9
  for j,pa in enumerate(parents):
   if pa>=0:ax.plot(x[f,[pa,j],2],x[f,[pa,j],1],color=col,alpha=alpha,lw=1.6)
 for n,col in [('ROOT','#182e35'),('HEAD','#a07a28')]:ax.plot(x[:,ix[n],2],x[:,ix[n],1],color=col,lw=2,label=n+' path')
 ax.axhline(0,color='#555555',lw=.7);ax.set_aspect('equal');ax.set(title='FIRST GENUFLECTION / onion skin\nRust: descent · Blue: turn and recovery',xlabel='Forward Z · design meters',ylabel='Height · design meters');ax.legend();fig.savefig(p/'onion_skin.png',dpi=160)
 print('STUDIES',p,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory',type=Path);main(a.parse_args().directory)
