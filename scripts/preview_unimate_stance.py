"""Paired stance videos and common-axis raw pose/contact sheets."""
import html,json,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=BASE/'pilgrim_stance_001';review=out/'review';review.mkdir(exist_ok=True);m=json.loads((out/'run.json').read_text());validation=json.loads((out/'asset_validation.json').read_text());scale=validation['scale'];c=np.load(out/'conditions/upright/cond.npy',allow_pickle=True).item()['Pilgrim'];parents=c['parents'];names=c['joint_names'];ends=[names.index(n) for n in ['LeftFingers','RightFingers','LeftToes','RightToes']];colors={'A':'#24b3c9','B':'#d95c33','C':'#61ad4f','D':'#9e59d9','core':'#aa8648'};edge=[colors.get(validation['canonical_to_original'][n].split('_')[0],colors['core']) for n in names];lookup={(r['variant'],r['prompt_id'],r['seed']):r for r in m['runs']}
page=['<!doctype html><html><head><meta charset="utf-8"><title>Pilgrim reference stance</title><style>body{font:17px system-ui;background:#121922;color:#eee;max-width:1400px;margin:auto;padding:35px;line-height:1.6}a{color:#7dd9e9}img,video{max-width:100%}section{border-top:1px solid #456;margin:30px 0}summary{cursor:pointer;padding:10px}</style></head><body><h1>Pilgrim · Reference stance comparison</h1><p>Identical joint names, lengths, topology, scale, prompts and initial noise. Only reference geometry and its required offset representation change. Nine upright controls reproduce prior samples bit for bit. No animation poses are pinned; no cleanup is applied.</p><p><a href="../stance_review.blend">Blender comparison</a> · <a href="../analysis.json">Measurements</a> · <a href="../stance_validation.json">Reference validation</a></p><h2>Authored input stances — not generated animation frames</h2><img src="../reference_stances.png">']
for pid,prompt in m['prompts'].items():
    page.append('<section><h2>'+html.escape(prompt)+'</h2>')
    for seed in m['seeds']:
        entries=[lookup[var,pid,seed] for var in ['upright','quadruped']];xs=[np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale for r in entries];proj=[(x[:,:,0]-x[:,0:1,0])*.85+(x[:,:,2]-x[:,0:1,2])*.53 for x in xs];ylim=(min(-.2,min(x[:,:,1].min() for x in xs)-.1),max(3.2,max(x[:,:,1].max() for x in xs)+.1));lim=max(1.8,max(abs(y).max() for y in proj)+.1)
        fig,axs=plt.subplots(3,6,figsize=(16,9),gridspec_kw={'height_ratios':[2,2,1]});fig.suptitle(f'{pid} · seed {seed} · {prompt}\nRAW generated poses: root X/Z aligned for inspection; original floor height retained',fontsize=13)
        for row,(x,pj,var) in enumerate(zip(xs,proj,['UPRIGHT REFERENCE','QUADRUPEDAL REFERENCE'])):
            for col,f in enumerate([0,11,23,35,47,59]):
                ax=axs[row,col]
                for j,pa in enumerate(parents):
                    if pa>=0:ax.plot(pj[f,[pa,j]],x[f,[pa,j],1],color=edge[j],lw=2)
                ax.axhline(0,color='red',lw=.7);ax.set_xlim(-lim,lim);ax.set_ylim(*ylim);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f'{var} · f{f+1}',fontsize=8)
        gs=axs[2,0].get_gridspec()
        for ax in axs[2]:ax.remove()
        for col,x in enumerate(xs):
            ax=fig.add_subplot(gs[2,col*3:(col+1)*3]);tip=x[:,ends]
            for j,l in enumerate('ABCD'):ax.plot(np.arange(60)/30,tip[:,j,1],color=colors[l],label=l)
            ax.axhline(0,color='black',lw=.5);ax.axhline(.12,color='gray',ls='--');ax.set_xlabel('Seconds');ax.set_ylabel('Tip height (m)');ax.set_title(['Upright reference','Quadrupedal reference'][col],fontsize=10);ax.legend(ncol=4,fontsize=8)
        fig.tight_layout(rect=(0,0,1,.90));sheet=f'{pid}_{seed}.png';fig.savefig(review/sheet,dpi=110);plt.close(fig)
        cmd=['ffmpeg','-y','-v','error'];filters=[]
        for i,r in enumerate(entries):
            video=next((Path(r['path'])/'samples/animations').glob('*_fk.mp4'));cmd+=['-i',str(video)];title=['UPRIGHT REFERENCE','QUADRUPED REFERENCE'][i];filters.append(f'[{i}:v]scale=600:600:force_original_aspect_ratio=decrease,pad=600:634:(ow-iw)/2:34,drawtext=text={title}:fontcolor=white:fontsize=23:x=12:y=5[v{i}]')
        filters.append('[v0][v1]hstack=inputs=2[v]');video=review/f'{pid}_{seed}.mp4';cmd+=['-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[v]','-an','-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p',str(video)];subprocess.run(cmd,check=True)
        page.append(f'<h3>Seed {seed}</h3><video controls loop muted preload="none" src="{video.name}"></video><details><summary>Common-axis poses and tip heights</summary><img src="{sheet}"></details>')
    page.append('</section>')
page.append('<p>Stock cameras may differ between video columns. Use common-axis pose sheets or Blender for spatial comparison. Playback wrapping hard-resets, not a generated return.</p></body></html>');(review/'index.html').write_text('\n'.join(page))
