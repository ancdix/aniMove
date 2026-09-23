#!/usr/bin/env python3
"""Run pinned AnyTop inference offline, preserving assets and outputs on ShareDrive."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
ASSETS = Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove')
SOURCE = PROJECT / 'external' / 'AnyTop'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', default='quadropeds', choices=['quadropeds', 'bipeds', 'all', 'flying', 'millipeds_snakes'])
    parser.add_argument('--object', default='Hound')
    parser.add_argument('--seed', type=int, default=100)
    parser.add_argument('--repetitions', type=int, default=1)
    parser.add_argument('--name', required=True, help='New output folder name; existing runs are never overwritten.')
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in ('.', '..'):
        parser.error('--name must be a single folder name')
    if args.repetitions < 1:
        parser.error('--repetitions must be positive')
    checkpoints = sorted((ASSETS / 'AnyTop' / 'checkpoints').glob(args.family + '_model_*/model*.pt'))
    if len(checkpoints) != 1:
        raise RuntimeError('Expected one pinned checkpoint: ' + repr(checkpoints))
    # These links live on Linux, while their large targets live on exFAT.
    for name, target in [('save', ASSETS / 'AnyTop' / 'checkpoints'),
                         ('dataset', ASSETS / 'AnyTop' / 'dataset'),
                         ('t5-base', ASSETS / 't5-base')]:
        link = SOURCE / name
        if not link.is_symlink() and not link.exists():
            link.symlink_to(target, target_is_directory=True)
        if link.resolve() != target.resolve():
            raise RuntimeError('Unexpected existing asset path: ' + str(link))
    out = ASSETS / 'generated' / args.name
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, HF_HOME=str(ASSETS / 'cache' / 'huggingface'),
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', MPLBACKEND='Agg',
               MPLCONFIGDIR=str(ASSETS / 'cache' / 'matplotlib'),
               TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
               IMAGEIO_FFMPEG_EXE='/usr/bin/ffmpeg', PYTHONUNBUFFERED='1')
    cmd = [sys.executable, '-m', 'sample.generate', '--model_path', str(checkpoints[0]),
           '--object_type', args.object, '--seed', str(args.seed),
           '--num_repetitions', str(args.repetitions), '--motion_length', '6',
           '--output_dir', str(out)]
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable in the AnyTop environment')
    run = dict(vars(args), schema_version=1, command=cmd, cwd=str(SOURCE),
               checkpoint_sha256=sha256(checkpoints[0]),
               asset_manifest_sha256=sha256(ASSETS / 'asset_manifest.json'),
               source_revision=subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip(),
               source_diff=subprocess.check_output(['git', '-C', str(SOURCE), 'diff'], text=True),
               motion_revision=subprocess.check_output(['git', '-C', str(PROJECT / 'external' / 'Motion'), 'rev-parse', 'HEAD'], text=True).strip(),
               motion_diff=subprocess.check_output(['git', '-C', str(PROJECT / 'external' / 'Motion'), 'diff'], text=True),
               python=sys.version, torch=torch.__version__, cuda=torch.version.cuda,
               gpu=torch.cuda.get_device_name(), status='running')
    run['packages'] = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True).splitlines()
    manifest = out / 'run.json'
    manifest.write_text(json.dumps(run, indent=2) + '\n')
    print('OUTPUT', out, flush=True)
    start = time.monotonic()
    with (out / 'generation.log').open('w') as log:
        process = subprocess.Popen(cmd, cwd=SOURCE, env=env, stdout=log, stderr=subprocess.STDOUT)
        print('INFERENCE_PID', process.pid, flush=True)
        returncode = process.wait()
    run.update(status='generated' if returncode == 0 else 'failed',
               returncode=returncode, elapsed_seconds=time.monotonic() - start)
    manifest.write_text(json.dumps(run, indent=2) + '\n')
    print('RESULT', run['status'], run['elapsed_seconds'], flush=True)
    if returncode:
        print((out / 'generation.log').read_text()[-6000:])
        raise SystemExit(returncode)
    subprocess.run([sys.executable, str(PROJECT / 'scripts' / 'validate_outputs.py'), str(out)], check=True, env=env)


if __name__ == '__main__':
    main()
