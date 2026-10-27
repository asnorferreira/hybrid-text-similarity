#!/usr/bin/env bash
set -euo pipefail

root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
if [[ $(uname -s) != Linux ]]; then
  printf '%s\n' 'Este coletor exige Linux com Docker Engine.' >&2
  exit 2
fi
if [[ ${1:-} != --help && ${1:-} != -h ]]; then
  available=$(awk '/^MemAvailable:/ {printf "%.0f", $2 * 1024}' /proc/meminfo)
  if [[ -z $available || $available -lt 2000000000 ]]; then
    printf 'H2 bloqueada: %s bytes físicos disponíveis; são necessários 2000000000 antes de iniciar.\n' "${available:-0}" >&2
    exit 2
  fi
fi

exec docker run --rm --init --pull never --network none --cpus 2 \
  --memory 2000000000 --memory-swap 2000000000 \
  --user "$(id -u):$(id -g)" --workdir /workspace/core \
  -e PYTHONPATH=/workspace/core/src -e PYTHONHASHSEED=20261025 \
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  -e HTS_TORCH_THREADS=2 -e OMP_NUM_THREADS=2 -e MKL_NUM_THREADS=2 \
  -e HTS_MODEL_PATH=/workspace/core/models/e8f8c211226b894fcb81acc59f3b34ba3efd5f42 \
  -v "$root/core:/workspace/core" \
  "${HTS_S5B_IMAGE:-hts-ci-core:local}" python -m hts_core.cli.training \
  "$@" --task H2 --protocol configs/experiment_s5b.r4.json
