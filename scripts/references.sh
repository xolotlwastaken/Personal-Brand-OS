#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
case "${1:-}" in
  setup)
    docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/reference-setup.py
    ;;
  search)
    [[ $# -ge 2 && $# -le 3 ]] || { echo 'Usage: references.sh search "public topic" [instagram|youtube]' >&2; exit 2; }
    docker compose exec -T --user hermes hermes /opt/data/reference-runtime/bin/python /project/scripts/reference-worker.py search "$2" "${3:-instagram}"
    ;;
  fetch)
    [[ $# -eq 2 ]] || { echo 'Usage: references.sh fetch https://www.instagram.com/reel/...' >&2; exit 2; }
    docker compose exec -T --user hermes hermes /opt/data/reference-runtime/bin/python /project/scripts/reference-worker.py fetch "$2"
    ;;
  prepare)
    [[ $# -ge 2 && $# -le 3 ]] || { echo 'Usage: references.sh prepare /media/path.mp4 [source-url]' >&2; exit 2; }
    docker compose exec -T --user hermes hermes /opt/data/reference-runtime/bin/python /project/scripts/reference-worker.py prepare "$2" "${@:3}"
    ;;
  *) echo 'Usage: references.sh setup | search "public topic" [instagram|youtube] | fetch URL | prepare /media/file.mp4 [source-url]' >&2; exit 2 ;;
esac
