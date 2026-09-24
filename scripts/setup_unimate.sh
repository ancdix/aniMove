#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
asset_root="/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate"
revision="9f3076e1db482883edb6f6a37a67f521c3853278"
cd "$project_root"
mkdir -p "$asset_root"
if [[ ! -d "$asset_root/UniMate/.git" ]]; then
  git clone https://github.com/Friedrich-M/UniMate.git "$asset_root/UniMate"
  git -C "$asset_root/UniMate" checkout --detach "$revision"
fi
[[ "$(git -C "$asset_root/UniMate" rev-parse HEAD)" == "$revision" ]]
export UV_CACHE_DIR="$project_root/.cache/uv"
export UV_HTTP_TIMEOUT=600
export UV_CONCURRENT_DOWNLOADS=4
uv_bin=/home/ipsedesktop/.local/bin/uv
if [[ ! -x .venv-unimate/bin/python ]]; then "$uv_bin" venv --python 3.10 .venv-unimate; fi
"$uv_bin" pip install --python .venv-unimate/bin/python 'setuptools<81' wheel pip
"$uv_bin" pip install --python .venv-unimate/bin/python --index-strategy unsafe-best-match --no-build-isolation -r configs/unimate_requirements.txt
.venv-unimate/bin/python -m pip check
.venv-unimate/bin/python -c 'import torch; assert torch.cuda.is_available(); print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name())'
.venv-unimate/bin/python -m pip freeze > "$asset_root/environment.lock.txt"
touch .venv-unimate/.animove-ready
