"""Common-camera three-way previews with original ground heights and raw motion."""
import json,html
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=BASE/'pilgrim_guided_001';m=json.loads((out/'review_run.json').read_text());v=json.loads((out/'asset_validation.json').read_text());scale=v['scale'];c=np.load(out/'condition/cond.npy',allow_pickle=True).item()['Pilgrim'];parents=c['parents'];names=c['joint_names'];ends=[names.index(n) for n in ['LeftFingers','RightFingers','LeftToes','RightToes']];colors={'A':'#24b3c9','B':'#d95c33','C':'#61ad4f','D':'#9e59d9','core':'#aa8648'};edge=[colors.get(v['canonical_to_original'][n].split('_')[0],colors['core']) for n in names];lookup={'UNI_'+r['label']+'_s'+str(r['seed']):r for r in m['runs']};review=out/'review';review.mkdir(exist_ok=True)
page=['<!doctype html><meta charset="utf-8"><title>Pilgrim wording and guidance</title><style>body{font:17px system-ui;background:#121922;color:#eee;max-width:1400px;margin:auto;padding:30px}a{color:#8cd}img,video{max-width:100%}section{border-top:1px solid #789;margin-top:25px}p{line-height:1.6}</style><h1>Pilgrim: animal wording and sparse support guidance</h1><p>Same quadrupedal reference, 23 joints and checkpoint. Wording compares adaptive stock sampling with identical initial noise. Guidance compares the stock 50-step Euler sampler with identical noise: no constraints; three support poses; those poses plus an authored root path. No post-generation cleanup. Video root X/Z tracking is display-only; heights retain the original floor. Playback hard-resets.</p><p><a href="../guided_review.blend">Blender master</a> · <a href="../analysis.json">Measurements</a> · <a href="../guide_validation.json">Authored constraints</a></p>']
for key,case in m['cases'].items():
    xs=[np.load(Path(lookup[a]['path'])/'raw_fk.xyz.npy')/scale for a in case['actions']];projs=[(x[:,:,0]-x[:,0:1,0])*.85+(x[:,:,2]-x[:,0:1,2])*.53 for x in xs];lim=max(1.6,max(abs(p).max() for p in projs)+.1);lo=min(-.2,min(x[:,:,1].min() for x in xs)-.1);hi=max(2.3,max(x[:,:,1].max() for x in xs)+.1)
    fig,axs=plt.subplots(4,6,figsize=(16,11),gridspec_kw={'height_ratios':[2,2,2,1]});fig.suptitle(key+' | '+case['prompt']+'\nRoot X/Z aligned for display; unchanged heights. Cyan A, orange B, green C, purple D.\n'+('Guidance poses are constrained at frames 1,30,60 only.' if key.startswith('guidance') else 'No pose or root constraints.'),fontsize=11)
    for row,(x,proj,title) in enumerate(zip(xs,projs,case['titles'])):
        for col,f in enumerate([0,11,23,29,47,59]):
            ax=axs[row,col]
            for j,p in enumerate(parents):
                if p>=0:ax.plot(proj[f,[p,j]],x[f,[p,j],1],color=edge[j],lw=2)
            ax.axhline(0,color='red',lw=.7);ax.set(xlim=(-lim,lim),ylim=(lo,hi),xticks=[],yticks=[]);ax.set_aspect('equal');ax.set_title(title+' f'+str(f+1),fontsize=8)
    gs=axs[-1,0].get_gridspec()
    for ax in axs[-1]:ax.remove()
    for col,x in enumerate(xs):
        ax=fig.add_subplot(gs[-1,col*2:(col+1)*2])
        for j,l in enumerate('ABCD'):ax.plot(np.arange(60)/30,x[:,ends[j],1],color=colors[l],label=l)
        ax.axhline(0,color='black',lw=.5);ax.axhline(.12,color='gray',ls='--');ax.set_ylabel('Tip height m');ax.set_xlabel('Seconds');ax.legend(ncol=4,fontsize=7)
    fig.tight_layout(rect=(0,0,1,.91));fig.savefig(review/(key+'.png'),dpi=110);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(12,4.5));lines=[]
    for ax,title in zip(axs,case['titles']):
        ax.set(xlim=(-lim,lim),ylim=(lo,hi),xticks=[],yticks=[]);ax.set_aspect('equal');ax.axhline(0,color='red',lw=.7);ax.set_title(title,fontsize=11);lines.append([ax.plot([],[],color=edge[j],lw=2.5)[0] for j in range(1,len(names))])
    fig.suptitle(key+' | raw motion, root X/Z tracked for display',fontsize=12);fig.tight_layout();writer=FFMpegWriter(fps=30,codec='libx264',extra_args=['-pix_fmt','yuv420p','-crf','19','-threads','2'])
    with writer.saving(fig,str(review/(key+'.mp4')),dpi=100):
        for f in range(60):
            for x,proj,line in zip(xs,projs,lines):
                for j in range(1,len(names)):line[j-1].set_data(proj[f,[parents[j],j]],x[f,[parents[j],j],1])
            writer.grab_frame()
    plt.close(fig);page.append(f'<section><h2>{html.escape(key)}</h2><p>{html.escape(case["prompt"])}</p><video controls loop muted src="{key}.mp4"></video><details><summary>Poses and contact heights</summary><img src="{key}.png"></details></section>');print('PREVIEW',key,flush=True)
poses=np.load(out/'authored_poses.npz')['poses'];fig,axs=plt.subplots(1,3,figsize=(12,4))
for ax,x,f in zip(axs,poses,[1,30,60]):
    pj=(x[:,0]-x[0,0])*.85+(x[:,2]-x[0,2])*.53
    for j,p in enumerate(parents):
        if p>=0:ax.plot(pj[[p,j]],x[[p,j],1],color=edge[j],lw=3)
    ax.axhline(0,color='red',lw=.7);ax.set(xlim=(-1.5,1.5),ylim=(-.1,2),xticks=[],yticks=[]);ax.set_aspect('equal');ax.set_title('AUTHORED pose · frame '+str(f))
fig.tight_layout();fig.savefig(review/'authored_poses.png',dpi=120);plt.close(fig);page.append('<h2>Authored constraints</h2><img src="authored_poses.png"><p>Only these three poses are supplied. Root-path mode additionally specifies 0.60 m forward travel. No intermediate limb motion is supplied.</p>');(review/'index.html').write_text('\n'.join(page))
