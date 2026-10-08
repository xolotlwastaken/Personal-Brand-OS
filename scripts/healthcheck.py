"""Lightweight readiness check; importing the full CLI is too costly for health probes."""
import json, os, socket
from pathlib import Path
try:
    state=json.loads(Path('/opt/data/gateway_state.json').read_text())
    assert state.get('gateway_state')=='running'
    pid=int(state['pid'])
    assert Path(f'/proc/{pid}').is_dir()
    if state.get('start_time') is not None:
        stat=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        assert int(stat[19])==int(state['start_time'])
    assert b'gateway' in Path(f'/proc/{pid}/cmdline').read_bytes()
    assert Path('/opt/data/gateway.sock').is_socket()
    # Native control socket is private. Connection verifies a listener exists.
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(3);s.connect('/opt/data/gateway.sock');s.close()
    assert Path('/opt/data/kanban.db').is_file()
except (OSError,ValueError,KeyError,AssertionError):
    raise SystemExit(1)
