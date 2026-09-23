#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
asset_root="/media/ipsedesktop/ShareDrive1/ModelData/aniMove"
conda_bin="${CONDA_EXE:-/home/ipsedesktop/miniconda3/bin/conda}"
cd "$project_root"
mkdir -p external
if [[ ! -d external/AnyTop ]]; then
  git clone https://github.com/Anytop2025/Anytop.git external/AnyTop
  git -C external/AnyTop checkout --detach e780d1575ca0121f29bb53821b309cf564156a95
fi
if [[ ! -d external/Motion ]]; then
  git clone https://github.com/inbar-2344/Motion.git external/Motion
  git -C external/Motion checkout --detach ac236251f90e5ca37c444c53ad383fc85de6d833
fi
[[ "$(git -C external/AnyTop rev-parse HEAD)" == e780d1575ca0121f29bb53821b309cf564156a95 ]] || {
  echo 'AnyTop revision differs. Check out e780d1575ca0121f29bb53821b309cf564156a95 before continuing.' >&2; exit 1;
}
[[ "$(git -C external/Motion rev-parse HEAD)" == ac236251f90e5ca37c444c53ad383fc85de6d833 ]] || {
  echo 'Motion revision differs. Check out ac236251f90e5ca37c444c53ad383fc85de6d833 before continuing.' >&2; exit 1;
}
for pair in 'AnyTop:anytop-generation.patch' 'AnyTop:anytop-editing.patch' 'Motion:motion-named-leaf-joints.patch'; do
  checkout="${pair%%:*}"
  patch_file="$project_root/patches/${pair#*:}"
  if git -C "external/$checkout" apply --reverse --check "$patch_file" 2>/dev/null; then
    echo "$checkout patch is already applied"
  else
    git -C "external/$checkout" apply --check "$patch_file"
    git -C "external/$checkout" apply "$patch_file"
  fi
done
export PIP_CACHE_DIR="$asset_root/cache/pip"
if [[ ! -x .venv-anytop/bin/python ]]; then
  "$conda_bin" env create --prefix "$project_root/.venv-anytop" --file configs/anytop-conda.yaml --solver libmamba --yes
fi
export UV_CACHE_DIR="$project_root/.cache/uv"
/home/ipsedesktop/.local/bin/uv pip install --python .venv-anytop/bin/python --link-mode copy \
  --find-links "$asset_root/cache/wheels" -r configs/anytop-requirements.txt
.venv-anytop/bin/python -m pip install --no-deps --no-build-isolation -e external/Motion
.venv-anytop/bin/python -m pip check
.venv-anytop/bin/python -c 'import torch; assert torch.cuda.is_available(); print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name())'
touch .venv-anytop/.animove-ready
