#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
[[ $# -eq 1 ]] || { echo 'Usage: scripts/verify-restored.sh DISPOSABLE_RESTORE_DIRECTORY' >&2; exit 1; }
TESTROOT="$(realpath "$1")"
[[ -f "$TESTROOT/MANIFEST.json" && -d "$TESTROOT/hermes" && -d "$TESTROOT/knowledge" ]] || { echo 'Use a separate restored test directory, never the live deployment.' >&2; exit 1; }
mkdir -p "$TESTROOT/media"
IMAGE="$(docker compose config --images)"
docker run --rm --network none --cpus 2 --memory 3g --cap-drop ALL \
  --cap-add CHOWN --cap-add SETUID --cap-add SETGID --cap-add DAC_OVERRIDE --cap-add FOWNER --cap-add KILL \
  --security-opt no-new-privileges:true \
  -e "HERMES_UID=$(id -u)" -e "HERMES_GID=$(id -g)" -e HERMES_HOME=/opt/data -e HERMES_DASHBOARD=0 \
  -e HERMES_WRITE_SAFE_ROOT=/opt/data:/knowledge:/media \
  -v "$TESTROOT/hermes:/opt/data" -v "$TESTROOT/knowledge:/knowledge" -v "$TESTROOT/media:/media" \
  -v "$ROOT/scripts:/project/scripts:ro" -v "$ROOT/config:/project/config:ro" \
  -v "$ROOT/vendor:/project/vendor:ro" -v "$ROOT/templates:/project/templates:ro" \
  "$IMAGE" /opt/hermes/.venv/bin/python /project/scripts/verify-restored.py
