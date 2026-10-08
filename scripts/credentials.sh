#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
PROVIDER="${1:-nvidia}"
case "$PROVIDER" in nvidia|openrouter|openai|custom) ;; *) echo 'Supported: nvidia openrouter openai custom' >&2;exit 1;; esac
IFS= read -rsp 'Model API key (hidden): ' BRAND_MODEL_KEY
echo
printf '%s' "$BRAND_MODEL_KEY" | docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/credentials.py "$PROVIDER"
unset BRAND_MODEL_KEY
