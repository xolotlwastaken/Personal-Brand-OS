"""Verification-only: keep committed data in WAL until backup test finishes."""
import sqlite3,time,sys
from pathlib import Path
root=Path('/opt/data/verification');root.mkdir(exist_ok=True)
name=sys.argv[1] if len(sys.argv)>1 else 'wal-fixture.db'
assert Path(name).name==name and name.endswith('.db')
p=root/name;release=root/'wal-fixture-release';release.unlink(missing_ok=True)
c=sqlite3.connect(p);c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA wal_autocheckpoint=0')
c.execute('CREATE TABLE IF NOT EXISTS fixture (id INTEGER PRIMARY KEY, value TEXT)');c.execute('INSERT OR REPLACE INTO fixture VALUES (42, ?)',('committed-in-WAL',));c.commit()
assert Path(str(p)+'-wal').stat().st_size>0
print('WAL fixture ready: committed row 42, live connection held open.',flush=True)
for _ in range(120):
 if release.exists():break
 time.sleep(1)
c.close()
