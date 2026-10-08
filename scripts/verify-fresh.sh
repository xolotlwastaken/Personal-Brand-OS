#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
TESTROOT="$ROOT/data/fresh-provision-$(date -u +%Y%m%dT%H%M%SZ)-${RANDOM}"
mkdir -p "$TESTROOT"/{hermes,knowledge,media}
IMAGE="$(docker compose config --images)"
RUN=(docker run --rm --cpus 2 --memory 3g --cap-drop ALL --cap-add CHOWN --cap-add SETUID --cap-add SETGID --cap-add DAC_OVERRIDE --cap-add FOWNER --cap-add KILL --security-opt no-new-privileges:true
  -e "HERMES_UID=$(id -u)" -e "HERMES_GID=$(id -g)" -e HERMES_HOME=/opt/data -e HERMES_DASHBOARD=0
  -e HERMES_WRITE_SAFE_ROOT=/opt/data:/knowledge:/media
  -v "$TESTROOT/hermes:/opt/data" -v "$TESTROOT/knowledge:/knowledge" -v "$TESTROOT/media:/media"
  -v "$ROOT/scripts:/project/scripts:ro" -v "$ROOT/config:/project/config:ro"
  -v "$ROOT/vendor:/project/vendor:ro" -v "$ROOT/templates:/project/templates:ro")
"${RUN[@]}" "$IMAGE" /opt/hermes/.venv/bin/python /project/scripts/provision.py
# Sentinel setup and second provision inside official runtime: no host Python needed.
"${RUN[@]}" "$IMAGE" /opt/hermes/.venv/bin/python /project/scripts/verify-idempotence.py
printf 'PASS fresh provisioning and idempotence: %s\n' "$TESTROOT"
