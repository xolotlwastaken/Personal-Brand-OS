#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == --stop ]]; then
  exec systemctl --user stop personal-brand-os-dashboard.service
fi
if [[ "${1:-}" == --status ]]; then
  exec systemctl --user status personal-brand-os-dashboard.service
fi
source "$(dirname "$0")/common.sh"
command -v python3 >/dev/null || { echo 'The local dashboard needs Python 3.10+.' >&2; exit 1; }
if [[ "${1:-}" == --background ]]; then
  shift
  command -v systemd-run >/dev/null || { echo 'Background mode needs a Linux systemd user session. Run without --background otherwise.' >&2; exit 1; }
  exec systemd-run --user --unit=personal-brand-os-dashboard --collect \
    --working-directory="$ROOT" --property=Restart=on-failure \
    -- "$(command -v python3)" "$ROOT/dashboard/server.py" "$@"
fi
exec python3 "$ROOT/dashboard/server.py" "$@"
