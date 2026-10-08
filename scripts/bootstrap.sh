#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
umask 077
if [[ ! -f .env ]]; then
  cp .env.example .env
  sed -i "s/^HERMES_UID=.*/HERMES_UID=$(id -u)/;s/^HERMES_GID=.*/HERMES_GID=$(id -g)/" .env
fi
mkdir -p data/hermes knowledge media/{incoming,working,exports}
chmod 700 data/hermes
# Never print rendered Compose environment values: it may contain overrides.
docker compose config --quiet
# Provision through the official entrypoint; no Python installation on the host.
if [[ -n "$(docker compose ps --status running -q hermes)" ]]; then
  docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/provision.py "$@"
else
  docker compose run --rm --no-deps hermes /opt/hermes/.venv/bin/python /project/scripts/provision.py "$@"
  docker compose up -d
fi
# Reconciliation of a running deployment must not interrupt its active workers.
# Apply Compose/image changes deliberately with update.sh or an idle recreation.
./scripts/wait-healthy.sh
