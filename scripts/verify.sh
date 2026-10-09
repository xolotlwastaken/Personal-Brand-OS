#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
docker compose config --quiet
for path in data/hermes knowledge media/incoming media/working media/exports; do [[ -d "$path" ]] || { echo "Missing $path" >&2;exit 1; }; done
[[ -n "$(docker compose ps --status running -q hermes)" ]] || { echo 'Hermes container is not running' >&2;exit 1; }
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/healthcheck.py
docker inspect "$(docker compose ps -q hermes)" | docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-docker.py
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-runtime.py

docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-helper.py
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-validator.py
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-ceo-relay.py
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-ceo-recovery.py
./scripts/verify-references.sh
