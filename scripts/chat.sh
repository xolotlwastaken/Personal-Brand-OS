#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
PROFILE="${1:-brand-ceo}"
if (($#)); then shift; fi
case "$PROFILE" in brand-ceo|brand-manager|reference-builder|hook-writer|script-writer|video-editor|publisher) ;; *) echo 'Unknown project profile' >&2;exit 1;; esac
docker compose exec --user hermes hermes hermes -p "$PROFILE" chat "$@"
