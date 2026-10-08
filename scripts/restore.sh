#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
[[ $# -eq 2 ]] || { echo 'Usage: scripts/restore.sh ARCHIVE EMPTY_TEST_DIRECTORY' >&2;exit 1; }
ARCHIVE="$(realpath "$1")"
mkdir -p "$2"
TARGET="$(realpath "$2")"
[[ -z "$(ls -A "$TARGET")" ]] || { echo 'Restore target must be empty.' >&2;exit 1; }
IMAGE="$(docker compose config --images)"
docker run --rm --network none --user "$(id -u):$(id -g)" --cap-drop ALL \
  --security-opt no-new-privileges:true --entrypoint /opt/hermes/.venv/bin/python \
  -v "$ARCHIVE:/archive.tar.gz:ro" -v "$TARGET:/restore" -v "$ROOT/scripts:/scripts:ro" \
  "$IMAGE" /scripts/archive.py restore --archive /archive.tar.gz
