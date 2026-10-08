#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/skill-examples.py
