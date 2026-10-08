#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
umask 077
mkdir -p backups
NAME="brand-os-$(date -u +%Y%m%dT%H%M%SZ)-${RANDOM}.tar.gz"
MODE=backup
if [[ "${1:-}" == --secrets ]]; then
  MODE=secrets
  NAME="brand-os-secrets-$(date -u +%Y%m%dT%H%M%SZ)-${RANDOM}.tar.gz"
fi
IMAGE="$(docker compose config --images)"
RUNNING="$(docker compose ps --status running -q hermes)"
# Pause ALL writers before reading files and SQLite WAL. Never raw-copy a live DB.
if [[ -n "$RUNNING" ]]; then
  docker compose pause hermes >/dev/null
  trap 'docker compose unpause hermes >/dev/null' EXIT
fi
docker run --rm --network none --user "$(id -u):$(id -g)" --cap-drop ALL \
  --security-opt no-new-privileges:true --entrypoint /opt/hermes/.venv/bin/python \
  -v "$ROOT/data/hermes:/source/hermes:ro" -v "$ROOT/knowledge:/source/knowledge:ro" \
  -v "$ROOT/media:/source/media:ro" -v "$ROOT/scripts:/scripts:ro" -v "$ROOT/backups:/backups" \
  "$IMAGE" /scripts/archive.py "$MODE" --output "/backups/$NAME"
echo "$ROOT/backups/$NAME"
