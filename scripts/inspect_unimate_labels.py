"""Audit naming acceptance, rule normalization, published vocabulary and embeddings."""
import collections,csv,hashlib,json,os,sys
from pathlib import Path
import numpy as np,torch
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');sys.path.insert(0,str(BASE/'UniMate'))
os.environ.update(HF_HOME=str(BASE/'cache/huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1');torch.set_num_threads(4)
from unimate.dataset.mixture.dataset import model_joint_names
from data_process.joint_annotation.names_clean_rule import clean_joint_name,post_process
from unimate.models.text_encoder.factory import create_text_encoder
out=BASE/'pilgrim_labels_001';file=BASE/'known/export/clean_joint_names.json';data=json.loads(file.read_text());occ=collections.Counter(n for rig in data.values() for n in rig);rigs=collections.Counter(n for rig in data.values() for n in set(rig));vocab=[dict(label=n,joint_occurrences=occ[n],annotated_rigs=rigs[n]) for n in sorted(occ)]
(out/'published_objaverse_vocabulary.json').write_text(json.dumps(dict(annotation_file=str(file),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),dataset_revision='c2b7ad6926b03dd72fae7934656dd4d4b9056029',rigs=len(data),unique_labels=len(occ),caveat='Unfiltered published Objaverse annotations, not this independent checkpoint exact training subset or per-label performance.',labels=vocab),indent=2)+'\n')
examples=['LeftUpperArm','mixamorig:LeftArm','Bip01_L_Thigh','L_Foreleg','LeftFrontPaw','LeftHindFoot','Tail03','LeftWing','Tentacle02','Wheel_FL','joint_014','Bone.003','Left Load Bearing Paw','SacredHydraulicActuator']
cleaned=[dict(raw=s,cleaned=post_process(clean_joint_name(s,'Pilgrim'))) for s in examples]
acceptance=[]
for supplied in [['Left Front Leg','Sacred Hydraulic Actuator'],['Bone','Bone'],['Bone',''],['Bone'],None]:
    d={'joint_names':['OriginalA','OriginalB']}
    if supplied is not None:d['clean_joint_names']=supplied
    accepted=model_joint_names(d,'probe');acceptance.append(dict(supplied=supplied,used=accepted))
probe=['Left Upper Arm','Left Front Leg','Left Hind Leg','Left Front Paw','Left Wing','Tail','Tentacle','Wheel','Bone','Sacred Hydraulic Actuator','xyzzy'];encoder=create_text_encoder('t5','google/flan-t5-base',device='cpu',pool=True);tokens=encoder.tokenize(probe);embedding=encoder(tokens).cpu().numpy();assert embedding.shape==(len(probe),768) and np.isfinite(embedding).all();np.save(out/'label_probe_embeddings.npy',embedding)
checks=[dict(label=n,token_count=int(tokens['attention_mask'][i].sum()),embedding_norm=float(np.linalg.norm(embedding[i])),published_occurrences=occ[n],published_rigs=rigs[n]) for i,n in enumerate(probe)]
result=dict(status='passed',runtime_rule='clean_joint_names must have one nonblank string per joint. Repeats accepted; no anatomical whitelist. Invalid field falls back to raw joint_names for the whole rig.',cleaner_note='Applied during preprocessing, not rerun over supplied clean_joint_names by inference. Drops rig indices/noise and maps synonyms. Does not define an exhaustive runtime enum.',normalization_examples=cleaned,acceptance=acceptance,encoder_probe=checks,embedding_source='Pinned Flan-T5-base, CPU; shape11x768; no generation claims for arbitrary labels.');(out/'label_acceptance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
