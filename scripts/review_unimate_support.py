"""Screen raw support behavior and build an uncorrected review gallery."""
import argparse,html,json,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from compare_unimate_anytop import ROOT,scale,measure,ends,parents,names,v
from analyze_unimate_raw import intervals
p=argparse.ArgumentParser();p.add_argument('--name',default='pilgrim_support_001');args=p.parse_args();out=ROOT/args.name;m=json.loads((out/'run.json').read_text());review=out/'review';review.mkdir(exist_ok=True);records=[]
colors={'A':'#24b3c9','B':'#d95c33','C':'#61ad4f','D':'#9e59d9','core':'#aa8648'};ec=[colors.get(v['canonical_to_original'][n].split('_')[0],colors['core']) for n in names]
page=['<!doctype html><html><head><meta charset="utf-8"><title>Pilgrim support feasibility</title><style>body{font:16px system-ui;background:#121922;color:#e5ebf0;max-width:1500px;margin:auto;padding:32px}p{line-height:1.6}section{margin-top:30px;border-top:1px solid #456}video,img{max-width:100%}a{color:#80d3e0}summary{padding:12px;cursor:pointer}</style></head><body><h1>Pilgrim · Four-limb walking feasibility</h1><p>Raw 60-frame / 30-fps samples. Existing upright rest skeleton; naming schemes, prompts and seeds recorded in run.json. No starting-pose clamp, IK, contact correction, smoothing or loop repair. Repeated playback hard-resets.</p><p>Candidate contacts are geometric estimates, not measured loads. A lowered body or swinging arms alone is not four-limb walking. Pose thumbnails align root X/Z only; heights retain the declared floor.</p>']
for r in m['runs']:
    x=np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale;tip=x[:,ends];vel=np.gradient(x,1/30,axis=0);speed=np.linalg.norm(vel[:,ends],axis=-1);metric=measure(x,30);checks={}
    for label,h,s in [('strict',.06,.30),('relaxed',.12,.60)]:
        mask=(np.abs(tip[:,:,1])<h)&(speed<s);durations={c:intervals(mask[:,j],minimum=3) for j,c in enumerate('ABCD')};frames=[sum(b-a for a,b in durations[c]) for c in 'ABCD'];lift=(tip[:,:,1]>h+.05).sum(0)
        checks[label]=dict(height_m=h,max_speed_m_s=s,intervals=durations,stance_frames=frames,lift_frames=lift.tolist(),at_least_two_candidates_fraction=float((mask.sum(1)>=2).mean()),all_four_candidates_fraction=float(mask.all(1).mean()))
    # Screening target, not a learned classifier or physical-balance certificate.
    z=checks['relaxed'];candidate=bool(metric['root_displacement_m']>.15 and min(z['stance_frames'])>=6 and min(z['lift_frames'])>=3 and z['at_least_two_candidates_fraction']>=.3)
    records.append(dict(**{k:r[k] for k in ['label','variant','prompt_id','prompt','seed','path','feature_sha256']},metrics=metric,support=checks,passes_permissive_walk_screen=candidate))
    key=r['label']+'_'+str(r['seed']);fig,axs=plt.subplots(2,6,figsize=(16,6),gridspec_kw={'height_ratios':[2,1]});fig.suptitle(f"{r['variant']} · {r['prompt_id']} · seed {r['seed']}\n{r['prompt']}\nRaw poses: root X/Z aligned for display only",fontsize=12)
    proj=(x[:,:,0]-x[:,0:1,0])*.85+(x[:,:,2]-x[:,0:1,2])*.53;lim=max(1.7,abs(proj).max()+.1);ylo=min(-.2,float(x[:,:,1].min())-.1);yhi=max(3.3,float(x[:,:,1].max())+.1)
    for col,f in enumerate([0,11,23,35,47,59]):
        ax=axs[0,col]
        for j,pa in enumerate(parents):
            if pa>=0:ax.plot(proj[f,[pa,j]],x[f,[pa,j],1],color=ec[j],lw=2)
        ax.axhline(0,color='red',lw=.7);ax.set_xlim(-lim,lim);ax.set_ylim(ylo,yhi);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([]);ax.set_title('Frame '+str(f+1),fontsize=10)
    gs=axs[1,0].get_gridspec()
    for ax in axs[1]:ax.remove()
    hax=fig.add_subplot(gs[1,:3]);sax=fig.add_subplot(gs[1,3:]);t=np.arange(60)/30
    for j,c in enumerate('ABCD'):hax.plot(t,tip[:,j,1],label=c,color=colors[c]);sax.plot(t,speed[:,j],label=c,color=colors[c])
    hax.axhline(0,color='black',lw=.6);hax.axhline(.12,color='gray',ls='--');hax.set_ylabel('Tip height (m)');hax.set_xlabel('Seconds');hax.legend(ncol=4,fontsize=8);sax.axhline(.6,color='gray',ls='--');sax.set_ylabel('Tip speed (m/s)');sax.set_xlabel('Seconds');fig.tight_layout(rect=(0,0,1,.86));fig.savefig(review/(key+'.png'),dpi=110);plt.close(fig)
    video=next((Path(r['path'])/'samples/animations').glob('*_fk.mp4'));relative='../'+str(video.relative_to(out));page.append(f'<section><h2>{html.escape(key)}</h2><p>{html.escape(r["prompt"])}</p><p>Travel {metric["root_displacement_m"]:.2f} m · permissive stance frames A/B/C/D: {z["stance_frames"]} · screen {"candidate" if candidate else "not passed"}</p><video controls loop muted preload="none" src="{relative}"></video><details><summary>Pose and contact diagnostics</summary><img loading="lazy" src="{key}.png"></details></section>')
page.append('</body></html>');(review/'index.html').write_text('\n'.join(page));result=dict(status='measured_requires_visual_review',screen='Travel >0.15m; each tip >=6 stance frames in runs >=3 frames, >=3 lift frames, and >=30% frames with >=2 candidates. Permissive candidates: abs height<0.12m and speed<0.60m/s. Lift: height>0.17m. Diagnostic only; not force, balance, or production validation.',passes=[r['label']+'_'+str(r['seed']) for r in records if r['passes_permissive_walk_screen']],records=records);(out/'support_analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passes=result['passes'],records=[dict(label=r['label'],seed=r['seed'],travel=round(r['metrics']['root_displacement_m'],3),stance=r['support']['relaxed']['stance_frames']) for r in records]),indent=2))
