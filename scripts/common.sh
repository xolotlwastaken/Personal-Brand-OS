#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v docker >/dev/null || { echo 'Install Docker Engine and the Compose plugin first.' >&2; exit 1; }
docker compose version >/dev/null
docker info >/dev/null
