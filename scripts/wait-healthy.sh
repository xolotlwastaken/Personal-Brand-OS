#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
for ((attempt=0; attempt<90; attempt++)); do
  CONTAINER_ID="$(docker compose ps -q hermes)"
  if [[ -n "$CONTAINER_ID" ]]; then
    STATUS="$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER_ID")"
    [[ "$STATUS" == healthy ]] && { echo 'Hermes container is healthy.'; exit 0; }
    [[ "$(docker inspect --format '{{.State.Running}}' "$CONTAINER_ID")" == true ]] || break
  fi
  sleep 2
done
echo 'Hermes did not become healthy within 180 seconds; inspect docker compose logs.' >&2
exit 1
