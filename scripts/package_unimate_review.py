"""Offline raw-video gallery, prompt grids, pose/contact atlases and provenance."""
import hashlib,html,json,shutil,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');run=BASE/'pilgrim_harvest_001';out=run/'review';out.mkdir(exist_ok=True)
manifest=json.loads((run/'run.json').read_text());analysis=json.loads((run/'raw_comparison.json').read_text());rows=[r for r in analysis['records'] if r['model']=='UniMate'];cond=np.load(BASE/'pilgrim_canonical_v002/cond.npy',allow_pickle=True).item()['Pilgrim'];mapping=json.loads((BASE/'pilgrim_canonical_v002/asset_validation.json').read_text());parents=cond['parents'];names=cond['joint_names'];scale=mapping['scale'];ffmpeg=shutil.which('ffmpeg');assert ffmpeg
colors={'A':'#26b7cc','B':'#d95c33','C':'#61ad4f','D':'#9e59d9','core':'#99783d'}
edgecolors=[colors.get(mapping['canonical_to_original'][n].split('_')[0],colors['core']) for n in names]
page=['<!doctype html><html><head><meta charset="utf-8"><title>Pilgrim · UniMate raw review</title><style>body{background:#111820;color:#e6e9ee;font:16px system-ui;max-width:1400px;margin:auto;padding:32px}h1{font-size:40px}p{max-width:950px;line-height:1.6}a{color:#83d3df}section{margin:48px 0;border-top:1px solid #405060;padding-top:24px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.card{background:#202b36;padding:12px;border-radius:8px}video,img{width:100%}small{color:#bdc7d1}button,select{font:inherit;padding:8px;background:#304252;color:white;border:0;border-radius:5px}summary{cursor:pointer;padding:16px}</style></head><body><h1>Pilgrim · UniMate raw review</h1><p>80 untouched text-conditioned samples · 10 prompts × 8 seeds · 23 joints · 60 frames at 30 fps · CFG 3. Independent <code>tarn59/UniMate-Weights</code> checkpoint. No IK, guidance poses, smoothing, contact solve, or loop correction. These are motion-skeleton previews, not a finished creature mesh.</p><p>Stock videos may track the root; displacement below is measured in world coordinates. Pose sheets explicitly align root X/Z for shape inspection. Ground and height are never corrected. Contact intervals are geometric candidates, not evidence of balance. Playback repeats with a hard reset.</p><p><a href="../unimate_raw_master.blend">Blender master</a> · <a href="../raw_comparison.json">Raw comparison data</a> · <a href="../run.json">Generation provenance</a> · <a href="../analysis.json">Trajectories and metrics index</a></p><p><button onclick="document.querySelectorAll(\'video\').forEach(v=>v.pause())">Pause all</button> <select onchange="document.querySelectorAll(\'video\').forEach(v=>v.playbackRate=+this.value)"><option value="1">1× speed</option><option value="0.5">0.5× speed</option><option value="0.25">0.25× speed</option></select></p>']
page.append('<p>Current finding: walking and turning respond most clearly. Lowering/reaching is inconsistent; recovery often fails. The gait reads mainly as arms plus two legs, not four interchangeable supports.</p><p><a href="anytop_unimate_raw.mp4">Common-view raw AnyTop comparison</a> · <a href="../../pilgrim_expansion_001/expansion_comparison.mp4">Two expansion trials (including failure)</a></p>')
for label,prompt in manifest['prompts'].items():
    clips=sorted([r for r in rows if r['label']==label],key=lambda r:r['seed']);videos=[];traces=[]
    all_x=np.concatenate([np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale for r in clips]);proj_all=(all_x[:,:,0]-all_x[:,0:1,0])*.85+(all_x[:,:,2]-all_x[:,0:1,2])*.53
    xlim=(min(-1.8,float(proj_all.min())-.15),max(1.8,float(proj_all.max())+.15));ylim=(min(-.2,float(all_x[:,:,1].min())-.15),max(3.3,float(all_x[:,:,1].max())+.15))
    fig,axs=plt.subplots(8,4,figsize=(10,18));fig.suptitle(f'{label}: {prompt}\nRaw FK; root X/Z aligned for pose inspection. A cyan / B orange / C green / D purple',fontsize=12)
    for row,r in enumerate(clips):
        folder=Path(r['path']);video=next((folder/'samples/animations').glob('*_fk.mp4'));videos.append(video);x=np.load(folder/'raw_fk.xyz.npy')/scale;traces.append(x)
        for col,f in enumerate([0,19,39,59]):
            ax=axs[row,col];pts=x[f].copy();pts[:,[0,2]]-=pts[0,[0,2]];proj=pts[:,0]*.85+pts[:,2]*.53
            for j,p in enumerate(parents):
                if p>=0:ax.plot(proj[[p,j]],pts[[p,j],1],color=edgecolors[j],lw=2)
            ax.axhline(0,color='#bb4444',lw=.7);ax.set_xlim(*xlim);ax.set_ylim(*ylim);ax.set_aspect('equal');ax.set_title(f'{r["seed"]} · f{f+1}',fontsize=9);ax.set_xticks([]);ax.set_yticks([])
    fig.tight_layout(rect=(0,0,1,.96));fig.savefig(out/(label+'_poses.png'),dpi=130);plt.close(fig)
    fig,axs=plt.subplots(8,2,figsize=(12,14));fig.suptitle(f'{label} · raw trajectories / candidate contacts')
    for row,(r,x) in enumerate(zip(clips,traces)):
        ax=axs[row,0];t=np.arange(60)/30;ax.plot(t,x[:,0,1],label='root height');ax.plot(t,np.linalg.norm(x[:,0,[0,2]]-x[0,0,[0,2]],axis=-1),label='root travel');ax.set_ylabel(str(r['seed']));ax.grid(alpha=.2)
        if row==0:ax.legend(fontsize=8)
        ax=axs[row,1]
        for j,k in enumerate('ABCD'):
            for a,b in r['metrics']['contact_intervals'][k]:ax.broken_barh([(a/30,(b-a)/30)],(j-.3,.6),facecolors=colors[k])
        ax.set_xlim(0,2);ax.set_ylim(-.5,3.5);ax.set_yticks(range(4),list('ABCD'));ax.grid(alpha=.2)
    fig.tight_layout(rect=(0,0,1,.97));fig.savefig(out/(label+'_contacts.png'),dpi=110);plt.close(fig)
    cmd=[ffmpeg,'-y','-loglevel','error','-threads','2'];filters=[]
    for i,(v,r) in enumerate(zip(videos,clips)):
        cmd+=['-i',str(v)];filters.append(f'[{i}:v]scale=400:400:force_original_aspect_ratio=decrease,pad=400:424:(ow-iw)/2:24,drawtext=text=seed_{r["seed"]}:fontcolor=white:fontsize=18:x=10:y=2[v{i}]')
    layout='|'.join(f'{(i%4)*400}_{(i//4)*424}' for i in range(8));filters.append(''.join(f'[v{i}]' for i in range(8))+f'xstack=inputs=8:layout={layout}[grid]')
    cmd+=['-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[grid]','-an','-c:v','libx264','-crf','20','-threads','2','-pix_fmt','yuv420p',str(out/(label+'_grid.mp4'))];subprocess.run(cmd,check=True)
    page.append(f'<section id="{label}"><h2>{label} · {html.escape(prompt)}</h2><video controls loop muted preload="none" src="{label}_grid.mp4"></video><details><summary>Pose and contact atlases</summary><img loading="lazy" src="{label}_poses.png"><img loading="lazy" src="{label}_contacts.png"></details><div class="grid">')
    for r,v in zip(clips,videos):
        m=r['metrics'];rel='../'+str(v.relative_to(run));page.append(f'<div class="card"><b>Seed {r["seed"]}</b><video controls loop muted preload="none" src="{rel}"></video><small>Travel {m["root_displacement_m"]:.2f} m · Δheight {m["root_height_change_m"]:+.2f} m<br>Lowest joint {m["min_joint_height_m"]:+.3f} m · accel p95 {m["joint_acceleration_p95_m_s2"]:.1f} m/s²</small></div>')
    page.append('</div></section>');print('PACKAGED',label,flush=True)
page.append('</body></html>');(out/'index.html').write_text('\n'.join(page))
