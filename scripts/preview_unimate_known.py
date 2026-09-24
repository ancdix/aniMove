"""Build a raw-motion pose sheet and matched-seed stock-preview strips."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    a=argparse.ArgumentParser();a.add_argument('run',type=Path);a.add_argument('--cond',type=Path,default=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/known/features/cond.npy'));args=a.parse_args();p=args.run
    r=json.loads((p/'analysis.json').read_text())['records'];labels=list(dict.fromkeys(x['label'] for x in r));assert len(labels)==3;lookup={(x['seed'],x['label']):x for x in r};seeds=sorted(s for s in {x['seed'] for x in r} if all((s,label) in lookup for label in labels))
    cond=np.load(args.cond,allow_pickle=True).item();d=next(iter(cond.values()));parents=d['parents']
    aligned=[]
    for item in r:
        x=np.load(item['fk']);y=x.copy();y[:,:,0]-=x[:,0:1,0];y[:,:,2]-=x[:,0:1,2];aligned.append(y)
    all_points=np.concatenate(aligned).reshape(-1,3);low=all_points.min(0)-.1;high=all_points.max(0)+.1
    fig,axes=plt.subplots(len(seeds),3,figsize=(15,3.5*len(seeds)),squeeze=False)
    for row,seed in enumerate(seeds):
        videos=[]
        for col,label in enumerate(labels):
            item=lookup[(seed,label)];folder=Path(item['fk']).parent;x=np.load(item['fk']);ax=axes[row,col]
            for k,f in enumerate([0,19,39,59]):
                pose=x[f].copy();pose[:,0]-=pose[0,0];pose[:,2]-=pose[0,2]
                # Side view: forward Z horizontally, height Y vertically.
                for j,pa in enumerate(parents):
                    if pa>=0:ax.plot(pose[[pa,j],2],pose[[pa,j],1],color=plt.cm.viridis(k/3),alpha=.8,lw=1.2)
            ax.axhline(0,color='.6',lw=.6);ax.set_aspect('equal');ax.set_xlim(low[2],high[2]);ax.set_ylim(min(0,low[1]),high[1]);ax.set_title(f'{label} / seed {seed}');ax.set_xlabel('Forward Z (root XZ aligned for this sheet)');ax.set_ylabel('Y / canonical units')
            videos.append(next((folder/'samples/animations').glob('*_fk.mp4')))
        out=p/f'comparison_seed{seed}.mp4';cmd=['ffmpeg','-y','-v','error']
        for v in videos:cmd+=['-i',str(v)]
        cmd+=['-filter_complex','[0:v][1:v][2:v]hstack=inputs=3[v]','-map','[v]','-c:v','libx264','-crf','19','-pix_fmt','yuv420p',str(out)];subprocess.run(cmd,check=True)
    fig.suptitle('UniMate raw FK — four poses per clip; no correction',fontsize=18);fig.tight_layout(rect=[0,0,1,.97]);fig.savefig(p/'raw_pose_sheet.png',dpi=150);plt.close(fig)
    concat=p/'comparisons.txt';concat.write_text(''.join("file '%s'\n"%(p/f'comparison_seed{s}.mp4') for s in seeds))
    subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(p/'prompt_comparison.mp4')],check=True)

if __name__=='__main__':main()
