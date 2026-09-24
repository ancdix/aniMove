"""Matched three-way video strips and pose sheets for every seed and prompt."""
import html,json,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');run=BASE/'pilgrim_labels_001';out=run/'review';out.mkdir(exist_ok=True);m=json.loads((run/'run.json').read_text());analysis=json.loads((run/'paired_analysis.json').read_text());lookup={(r['variant'],r['prompt_id'],r['seed']):r for r in m['runs']};cond=np.load(BASE/'pilgrim_canonical_v002/cond.npy',allow_pickle=True).item()['Pilgrim'];v=json.loads((BASE/'pilgrim_canonical_v002/asset_validation.json').read_text());scale=v['scale'];names=list(cond['joint_names']);parents=cond['parents'];variants=['arms_legs','front_hind','neutral_limbs'];titles=['ARMS + LEGS','FRONT + HIND LEGS','GENERIC BONE LABELS'];colors={'A':'#26b7cc','B':'#d95c33','C':'#61ad4f','D':'#9e59d9','core':'#aa8648'};ec=[colors.get(v['canonical_to_original'][n].split('_')[0],colors['core']) for n in names];videos=[]
page=['<!doctype html><html><head><meta charset="utf-8"><title>Pilgrim joint-label experiment</title><style>body{font:16px system-ui;background:#121922;color:#e5ebf0;max-width:1500px;margin:auto;padding:32px}p{line-height:1.6;max-width:1100px}section{margin-top:40px;border-top:1px solid #456;padding-top:20px}video,img{width:100%}a{color:#80d3e0}summary{padding:12px;cursor:pointer}table{border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #456}</style></head><body><h1>Pilgrim · Do joint labels change motion?</h1><p>Only the sixteen limb names changed. All geometry, core labels, prompts, checkpoint, random noise and other model inputs match exactly. Three prompts × three seeds × three naming schemes = 27 raw clips, plus three identical baseline replays. No IK, guides, smoothing or grounding correction.</p><p>Columns: <b>arms + legs</b> → <b>front + hind legs</b> → <b>generic Bone labels</b>. The last condition removes side/segment naming too; it does not disable name embeddings. Stock preview cameras can differ; world/root-relative motion differences are measured separately.</p><p><a href="../labels_comparison.blend">Blender comparison</a> · <a href="../paired_analysis.json">Paired measurements</a> · <a href="../variant_labels.json">Exact name mappings</a> · <a href="../label_acceptance.json">Accepted strings and cleaner examples</a> · <a href="../published_objaverse_vocabulary.json">844 published labels and counts</a></p>']
for prompt,prompt_text in m['prompts'].items():
    page.append(f'<section><h2>{prompt} · {html.escape(prompt_text)}</h2>')
    for seed in m['seeds']:
        entries=[lookup[var,prompt,seed] for var in variants];xs=[np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale for r in entries];allpts=np.concatenate(xs);ymin=min(-.2,float(allpts[:,:,1].min())-.12);ymax=max(3.3,float(allpts[:,:,1].max())+.12);proj=[(x[:,:,0]-x[:,0:1,0])*.85+(x[:,:,2]-x[:,0:1,2])*.53 for x in xs];xmin=min(-1.7,min(p.min() for p in proj)-.1);xmax=max(1.7,max(p.max() for p in proj)+.1)
        fig,axs=plt.subplots(3,4,figsize=(11,9));fig.suptitle(f'{prompt} · seed {seed} · {prompt_text}\nRaw FK; root X/Z aligned for pose inspection; floor/height unchanged',fontsize=12)
        for row,(x,pr,title) in enumerate(zip(xs,proj,titles)):
            for col,f in enumerate([0,19,39,59]):
                ax=axs[row,col]
                for j,p in enumerate(parents):
                    if p>=0:ax.plot(pr[f,[p,j]],x[f,[p,j],1],color=ec[j],lw=2)
                ax.axhline(0,color='red',lw=.6);ax.set_xlim(xmin,xmax);ax.set_ylim(ymin,ymax);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f'{title} · f{f+1}',fontsize=8)
        fig.tight_layout(rect=(0,0,1,.92));sheet=f'{prompt}_{seed}.png';fig.savefig(out/sheet,dpi=135);plt.close(fig)
        files=[next((Path(r['path'])/'samples/animations').glob('*_fk.mp4')) for r in entries];cmd=['ffmpeg','-y','-v','error'];filters=[]
        for i,(f,title) in enumerate(zip(files,titles)):
            cmd+=['-i',str(f)];filters.append(f'[{i}:v]scale=480:480:force_original_aspect_ratio=decrease,pad=480:514:(ow-iw)/2:34,drawtext=text={title}:fontcolor=white:fontsize=21:x=10:y=5[v{i}]')
        filters.append('[v0][v1][v2]hstack=inputs=3[v]');video=out/f'{prompt}_{seed}.mp4';cmd+=['-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[v]','-an','-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p',str(video)];subprocess.run(cmd,check=True);videos.append(video)
        page.append(f'<h3>Seed {seed}</h3><video controls loop muted preload="none" src="{video.name}"></video><details><summary>Pose comparison</summary><img loading="lazy" src="{sheet}"></details>')
    page.append('</section>')
page.append('</body></html>');(out/'index.html').write_text('\n'.join(page));concat=out/'videos.txt';concat.write_text(''.join(f"file '{p}'\n" for p in videos));subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(out/'all_pairs.mp4')],check=True)
