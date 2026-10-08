#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
if [[ $# -eq 0 ]]; then
  echo 'Current pinned deployment:'
  docker compose config --images
  echo 'Usage: scripts/update.sh nousresearch/hermes-agent@sha256:<verified-64-hex-digest>'
  exit 0
fi
NEW_IMAGE="$1"
[[ "$NEW_IMAGE" =~ ^nousresearch/hermes-agent@sha256:[0-9a-f]{64}$ ]] || { echo 'Require an exact official image digest.' >&2;exit 1; }
# Pull before changing running state. No moving tags and no in-container updater.
docker pull "$NEW_IMAGE"
./scripts/backup.sh
cp .env data/pre-update-compose.env
chmod 600 data/pre-update-compose.env
sed -i "s|^HERMES_IMAGE=.*|HERMES_IMAGE=$NEW_IMAGE|" .env
docker compose up -d
# Report drift rather than blindly overwriting runtime configuration.
./scripts/bootstrap.sh
./scripts/verify.sh
