"""Durable, sequential full-survey runner; each clip is independently resumable."""
import argparse,fcntl,hashlib,json,os,shutil,signal,statistics,subprocess,sys,time,traceback
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
LAB=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')

def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def make_entries(config):
    entries=[]
    for seed in config['seeds']:
        for prompt in config['prompts']:
            for target in config['targets']:
                entries.append(dict(id=f"{prompt['id']}_{target}_s{seed}",target=target,prompt_id=prompt['id'],seed=seed,
                    request=dict(target=target,prompt=prompt['text'],seconds=config['seconds'],seed=seed),
                    experimental=target not in prompt['intended_targets'],status='pending',attempts=[]))
    assert len({e['id'] for e in entries})==len(entries)
    return entries

def initialize(root,config_file):
    root.mkdir(parents=True,exist_ok=True)
    config=read(config_file)
    if (root/'manifest.json').exists():
        assert read(root/'manifest.json')['config']==config,'Survey configuration already exists and differs'
        return
    targets=read(LAB/'targets.json');selected=[t for t in targets if t['id'] in config['targets']]
    assert len(selected)==len(config['targets'])
    for folder in ['web/clips','web/models','web/vendor','runtime/motion_lab','runtime/configs']:(root/folder).mkdir(parents=True,exist_ok=True)
    for name in ['worker.py','survey.py']:shutil.copy2(REPO/'motion_lab'/name,root/'runtime/motion_lab'/name)
    shutil.copy2(REPO/'configs/motion_lab_model.json',root/'runtime/configs/motion_lab_model.json')
    for name in ['index.html','app.js']:shutil.copy2(REPO/'motion_lab/survey_web'/name,root/'web'/name)
    for path in (REPO/'motion_lab/survey_web/vendor').iterdir():shutil.copy2(path,root/'web/vendor'/path.name)
    manifest=dict(config=config,targets=selected,created=time.time(),model=read(REPO/'configs/motion_lab_model.json'),
        targets_sha256=sha(LAB/'targets.json'),condition_sha256={t['id']:sha(t['condition']) for t in selected},
        worker_sha256=sha(root/'runtime/motion_lab/worker.py'),runtime='Sequential independent official-v2 GPU calls; fixed seed per clip; no motion cleanup')
    write(root/'manifest.json',manifest);write(root/'state.json',dict(status='prepared',entries=make_entries(config),created=time.time()))
    write(root/'ratings.json',{})
    publish(root,manifest,read(root/'state.json'))

def publish(root,manifest,state):
    entries=state['entries'];done=[e for e in entries if e['status']=='complete'];durations=[e['elapsed_seconds'] for e in done if 'elapsed_seconds' in e]
    state['updated']=time.time();state['completed']=len(done);state['failed']=sum(e['status']=='failed' for e in entries);state['total']=len(entries)
    state['eta_seconds']=(len(entries)-len(done)-state['failed'])*statistics.median(durations[-36:]) if durations else None
    write(root/'state.json',state)
    write(root/'web/index.json',dict(title=manifest['config']['title'],status=state['status'],started=state.get('started'),updated=state['updated'],
        completed=len(done),failed=state['failed'],total=len(entries),current=state.get('current'),eta_seconds=state['eta_seconds'],error=state.get('error'),
        prompts=manifest['config']['prompts'],targets=[dict(id=t['id'],title=t['title']) for t in manifest['targets']],seeds=manifest['config']['seeds'],entries=entries))

def export_clip(root,entry,job,manifest):
    import numpy as np
    result=read(job/'result.json')
    assert result['request']==entry['request']
    assert result['checkpoint_sha256']==manifest['model']['checkpoint_sha256']
    assert result['condition_sha256']==manifest['condition_sha256'][entry['target']]
    assert result['device']=='cuda' and result['frames']==60
    assert sha(job/'motion.npy')==result['feature_sha256']
    with np.load(job/'kinematics.npz') as d:
        positions=d['positions'];quats=d['global_quaternions_wxyz'];assert np.isfinite(positions).all() and np.isfinite(quats).all()
        clip=dict(id=entry['id'],target=entry['target'],job=job.name,seed=entry['seed'],fps=30,
            positions=np.round(positions,6).tolist(),quaternions=np.round(quats,7).tolist(),
            root_displacement_m=float(np.linalg.norm(positions[-1,0,[0,2]]-positions[0,0,[0,2]])),
            root_height_range_m=[float(positions[:,0,1].min()),float(positions[:,0,1].max())])
    write(root/'web/clips'/(entry['id']+'.json'),clip)
    entry.update(status='complete',job=job.name,elapsed_seconds=result['elapsed_seconds'],clip='clips/'+entry['id']+'.json')
    entry.pop('error',None)

def reconcile(root,manifest,state):
    for entry in state['entries']:
        # Recover a completed child even if the supervisor was interrupted before publishing it.
        found=False
        for attempt in reversed(entry['attempts']):
            job=LAB/'jobs'/attempt['job']
            if (job/'result.json').exists():
                try:export_clip(root,entry,job,manifest);found=True;break
                except Exception as exc:entry['error']='Saved result rejected: '+str(exc)
        if not found:entry['status']='pending' if len(entry['attempts'])<manifest['config']['max_attempts'] else 'failed'

def run(root):
    with (root/'runner.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=read(root/'manifest.json');state=read(root/'state.json');config=manifest['config']
        assert sha(LAB/'targets.json')==manifest['targets_sha256'],'Target definitions changed during survey'
        for t in manifest['targets']:assert sha(t['condition'])==manifest['condition_sha256'][t['id']]
        assert sha(root/'runtime/motion_lab/worker.py')==manifest['worker_sha256']
        reconcile(root,manifest,state);state.update(status='running',started=state.get('started',time.time()),pid=os.getpid());state.pop('error',None);publish(root,manifest,state)
        try:
            for round_number in range(1,config['max_attempts']+1):
                for entry in state['entries']:
                    if entry['status']=='complete' or len(entry['attempts'])>=round_number:continue
                    job_id=f"ems001_20260930_{entry['id']}_a{round_number}";job=LAB/'jobs'/job_id
                    if job.exists():
                        # An interrupted mkdir before state publication is retained, never overwritten.
                        job_id+='_'+str(int(time.time()));job=LAB/'jobs'/job_id
                    job.mkdir();write(job/'request.json',entry['request']);write(job/'survey.json',dict(survey=config['id'],entry=entry['id'],attempt=round_number))
                    entry['attempts'].append(dict(job=job_id,started=time.time()));entry['status']='running';state['current']=entry['id'];publish(root,manifest,state)
                    print('START',entry['id'],'attempt',round_number,flush=True)
                    try:
                        with (job/'worker.log').open('w') as log:
                            process=subprocess.Popen([sys.executable,str(root/'runtime/motion_lab/worker.py'),str(job/'request.json')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                            try:code=process.wait(timeout=720)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid,signal.SIGKILL);process.wait();raise RuntimeError('Generation timed out after 12 minutes')
                        if code!=0:
                            detail=read(job/'status.json').get('error','Worker failed') if (job/'status.json').exists() else 'Worker exited '+str(code)
                            raise RuntimeError(detail)
                        export_clip(root,entry,job,manifest)
                        print('COMPLETE',entry['id'],round(entry['elapsed_seconds'],2),flush=True)
                    except Exception as exc:
                        entry.update(status='retry_pending' if round_number<config['max_attempts'] else 'failed',error=str(exc))
                        entry['attempts'][-1]['error']=str(exc);print('FAILED',entry['id'],str(exc),flush=True)
                    entry['attempts'][-1]['finished']=time.time();publish(root,manifest,state)
            state.update(status='complete' if all(e['status']=='complete' for e in state['entries']) else 'complete_with_failures',current=None,finished=time.time())
            publish(root,manifest,state);print('SURVEY_FINISHED',state['completed'],state['failed'],flush=True)
        except BaseException as exc:
            state.update(status='interrupted',error=str(exc));publish(root,manifest,state);raise

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['init','run']);p.add_argument('--root',type=Path,required=True);p.add_argument('--config',type=Path,default=REPO/'configs/essential_motion_survey_001.json');a=p.parse_args()
    if a.command=='init':initialize(a.root,a.config)
    else:run(a.root)
if __name__=='__main__':main()
