#!/usr/bin/env bash
# Invoke from the restored snapshot root. Host operations only prepare logs and
# invoke Docker; all builds, resource preparation and tests run in containers.
set -euo pipefail
resultdir=core/artifacts/ci/results/s5d
if [ -e "$resultdir" ]; then
  printf 'Preserve the previous attempt; use a new restored snapshot.\n' >&2
  exit 1
fi
mkdir -p "$resultdir"
dc=(docker compose -p "${HTS_REPRODUCTION_PROJECT:-hts_s5d}" -f docker-compose.ci.yml -f docker-compose.reproduction.yml)
dca=("${dc[@]}" -f docker-compose.models.yml)
run() {
  local name=$1
  shift
  printf '%q ' "$@" >> "$resultdir/commands.txt"
  printf '\n' >> "$resultdir/commands.txt"
  set +e
  "$@" > "$resultdir/$name.log" 2>&1
  local status=$?
  set -e
  printf '%s\n' "$status" > "$resultdir/$name.exit"
  printf '%s: exit %s\n' "$name" "$status"
  return "$status"
}
run compose "${dc[@]}" config --quiet
run build-core "${dc[@]}" build core
run build-web "${dc[@]}" build web
run build-browser "${dc[@]}" build browser
run core "${dc[@]}" run --rm --no-deps -e HTS_RG01_OBSERVED=/results/s5d/rg01-observado.json core python -m pytest -q -o cache_dir=/tmp/pytest-cache --junitxml=/results/s5d/core.xml
run web "${dc[@]}" run --rm --no-deps web sh -c 'npm test && npm run typecheck'
run prepare-config "${dc[@]}" run --rm --no-deps --user "$(id -u):$(id -g)" -v "$PWD/core/artifacts:/target" core python -c '
import json,pathlib
root=pathlib.Path("/target")
value=json.loads(pathlib.Path("/app/configs/trained_models.json").read_text())
value["enabled"]=True
(root/"trained_models.active.json").open("x").write(json.dumps(value,indent=2))
value["h1"]="artifacts/missing-development-control.json"
(root/"trained_models.missing.json").open("x").write(json.dumps(value,indent=2))'
run reload-models "${dc[@]}" run --rm --no-deps -v "$PWD:/snapshot:ro" core python /snapshot/scripts/check_saved_reproduction.py --root /snapshot --out /results/s5d/reload-models.json
run stack "${dca[@]}" up -d --wait --wait-timeout 180 mongo core web
run integration "${dca[@]}" exec -T web sh -c 'npm run integration && npx tsx scripts/integration-trained.ts && npm run test:security && npx tsx scripts/integration-failure.ts'
run e2e-active "${dca[@]}" run --rm --no-deps -e HTS_E2E_OUTPUT=/results/s5d/e2e-active browser npx playwright test e2e/system.spec.ts e2e/equivalence.spec.ts e2e/plan16.spec.ts
cat > "$resultdir/optional-missing.yml" <<'YAML'
services:
  core:
    environment:
      HTS_TRAINED_MODELS_CONFIG: /app/artifacts/trained_models.missing.json
YAML
cat > "$resultdir/base-missing.yml" <<'YAML'
services:
  core:
    environment:
      HTS_MODEL_PATH: /missing-base-control
YAML
run optional-stack "${dca[@]}" -f "$resultdir/optional-missing.yml" up -d --force-recreate --wait --wait-timeout 180 core
run e2e-optional-missing "${dca[@]}" run --rm --no-deps -e HTS_E2E_OUTPUT=/results/s5d/e2e-optional-missing browser npx playwright test e2e/trained-unavailable.spec.ts
run base-stack "${dca[@]}" -f "$resultdir/base-missing.yml" up -d --force-recreate --wait --wait-timeout 180 core
run e2e-base-missing "${dca[@]}" run --rm --no-deps -e HTS_FAILURE_KIND=model -e HTS_E2E_OUTPUT=/results/s5d/e2e-base-missing browser npx playwright test e2e/unavailable.spec.ts
run core-stop "${dca[@]}" stop core
run e2e-core-stopped "${dca[@]}" run --rm --no-deps -e HTS_FAILURE_KIND=core -e HTS_E2E_OUTPUT=/results/s5d/e2e-core-stopped browser npx playwright test e2e/unavailable.spec.ts
run stop "${dca[@]}" stop
