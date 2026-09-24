"""Download a pinned third-party checkpoint and one public UniML3D rig subset."""
import concurrent.futures, hashlib, json, subprocess, urllib.request, time
from pathlib import Path

ROOT=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
UID='4798d8c87a0e4ad8835217fe93ddf67b'

def get_json(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url,timeout=60) as r:return json.load(r)
        except Exception:
            if attempt==4:raise
            time.sleep(1+attempt)

def download(repo,revision,path,target,dataset=False):
    url='https://huggingface.co/'+('datasets/' if dataset else '')+repo+'/resolve/'+revision+'/'+path
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        temp=target.with_name(target.name+'.partial')
        subprocess.run(['curl','-L','--fail','--retry','5','--retry-delay','2','--connect-timeout','20','--max-time','1800','-C','-','-o',str(temp),url],check=True)
        temp.rename(target)
    h=hashlib.sha256()
    with target.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    expected={'checkpoints/checkpoint_step_120000.pt':'116fbc42f2436fbd115e6558dcfa17adc3a614bf937e17bb743a6a31aadf09c7','model.safetensors':'1dfb70afdcedceb9f9fae2f9b68e004ad934361fb35b9b2bd50b45ea90790fc8'}
    if path in expected:assert h.hexdigest()==expected[path],('Checksum mismatch',target)
    print('STAGED',str(target),target.stat().st_size,flush=True)
    return dict(repo=repo,revision=revision,remote_path=path,path=str(target),sha256=h.hexdigest(),bytes=target.stat().st_size)

def main():
    ROOT.mkdir(exist_ok=True,parents=True)
    model='tarn59/UniMate-Weights';dataset='Linzhan/UniML3D'
    revisions=ROOT/'source_revisions.json'
    if revisions.exists():
        pinned=json.loads(revisions.read_text());mr=pinned['checkpoint'];dr=pinned['dataset']
    else:
        mr='31df0920ee13dad80440821b93baf223e43d4c65';dr='c2b7ad6926b03dd72fae7934656dd4d4b9056029'
        revisions.write_text(json.dumps(dict(checkpoint=mr,dataset=dr),indent=2)+'\n')
    tasks=[]
    for name in ['config.json','dataset_stats.npy','checkpoints/checkpoint_step_120000.pt','README.md','LICENSE']:
        tasks.append((model,mr,name,ROOT/'weights'/name,False))
    er='7bcac572ce56db69c1ea7c8af255c5d7c9672fc2'
    cache=ROOT/'cache/huggingface/hub/models--google--flan-t5-base'
    for name in ['config.json','model.safetensors','spiece.model','tokenizer_config.json','tokenizer.json','special_tokens_map.json','README.md']:
        tasks.append(('google/flan-t5-base',er,name,cache/'snapshots'/er/name,False))
    export=ROOT/'known/export'
    for name in ['clean_joint_names.json','face_joint_names.json','joint_names.json','motion_captions.json','category_groups.json','filtered_objects.txt','filtered_clips.txt']:
        tasks.append((dataset,dr,'export/objaverse/'+name,export/name,True))
    tree='https://huggingface.co/api/datasets/'+dataset+'/tree/'+dr+'/export/objaverse/motions/'
    def shard(i):return get_json(tree+format(i,'02x'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        paths=[x['path'] for entries in pool.map(shard,range(64)) for x in entries if UID in x['path']]
    assert paths,'Known skeleton motion files missing'
    for path in paths:tasks.append((dataset,dr,path,export/'motions'/Path(path).name,True))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(lambda args:download(*args),tasks))
    (cache/'refs').mkdir(exist_ok=True,parents=True);(cache/'refs/main').write_text(er)
    manifest=dict(status='staged',known_object=UID,files=records)
    (ROOT/'asset_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('COMPLETE',len(records),flush=True)

if __name__=='__main__':main()
