#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
python3 -m unittest discover -s tests -p 'test_dashboard*.py' -v
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-dashboard-native.py
# Live read only. Native list may promote dependencies, exactly as the supported CLI does.
python3 - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('dashboard_server', 'dashboard/server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
snapshot = module.bridge({'op': 'snapshot'})
assert len(snapshot['agents']) == 7
assert all(a['id'] != 'default' and a['provisioned'] for a in snapshot['agents'])
assert snapshot['gateway'] == 'healthy'
tasks = snapshot['board']['tasks']
if tasks:
    result = module.bridge({'op': 'detail', 'task_id': tasks[0]['id']})
    assert result['task']['id'] == tasks[0]['id']
print('PASS LIVE dashboard reads: seven profiles, gateway, native board and task detail.')
PY
