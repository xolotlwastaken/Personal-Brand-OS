"""Maintenance container: paused-source SQLite backups and safe empty-target restore."""
import argparse, hashlib, json, os, shutil, sqlite3, tarfile, tempfile, time
from pathlib import Path, PurePosixPath
parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
b=sub.add_parser('backup');b.add_argument('--output',required=True)
r=sub.add_parser('restore');r.add_argument('--archive',required=True)
s=sub.add_parser('secrets');s.add_argument('--output',required=True)
a=parser.parse_args();os.umask(0o077)
SECRET_NAMES={'.env','auth.json','.anthropic_oauth.json','provider-import.env','install_id','spawn-ledger.json'}
SKIP_PARTS={'logs','cache','audio_cache','image_cache','node','runtimes','models','sandboxes','terminal-sessions','pending_messages','pairing','platforms','config-backups','backups','.pm','.deps','installs','home'}
SKIP_SUFFIX=('.db-wal','.db-shm','.sock','.pid','.lock','.provision.tmp')
def is_secret(p):
    return p.name in SECRET_NAMES or p.name.startswith('.env.') or any(x in {'credentials','tokens','auth','secrets','secret-sources'} for x in p.parts) or p.suffix in {'.pem','.key'}
def skipped(p):
    return any(x in SKIP_PARTS for x in p.parts) or p.name.startswith('gateway_state') or p.name in {'gateway_state.json','gateway-starts.log','active_profile','brand-os-provision.json'} or p.name.endswith(SKIP_SUFFIX)

def validate_db(p):
    c=sqlite3.connect(f'file:{p}?mode=ro',uri=True);ok=c.execute('PRAGMA integrity_check').fetchone()[0];c.close()
    if ok!='ok':raise RuntimeError(f'Database integrity failed: {p.name}')

if a.mode in {'backup','secrets'}:
    with tempfile.TemporaryDirectory() as temp:
        stage=Path(temp); index=[]
        for tree in ['hermes','knowledge','media']:
            src=Path('/source')/tree
            if not src.exists():continue
            for f in src.rglob('*'):
                if not f.is_file() or f.is_symlink():continue
                rel=f.relative_to(src)
                if a.mode=='secrets':
                    if tree!='hermes' or not is_secret(rel):continue
                elif skipped(rel) or is_secret(rel):continue
                target=stage/tree/rel;target.parent.mkdir(parents=True,exist_ok=True)
                if a.mode=='backup' and f.suffix=='.db':
                    # Source is paused by backup.sh. Stage DB + WAL together, then use SQLite
                    # online backup on a writable staging directory (read-only WAL mounts
                    # can lack a reusable shm file). Never omit committed WAL frames.
                    db_input=stage/'.sqlite-input'/tree/rel
                    db_input.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,db_input)
                    wal=Path(str(f)+'-wal')
                    if wal.exists():shutil.copy2(wal,Path(str(db_input)+'-wal'))
                    source=sqlite3.connect(db_input)
                    dest=sqlite3.connect(target);source.backup(dest);dest.close();source.close();validate_db(target)
                else:shutil.copy2(f,target)
                os.chmod(target,0o600);index.append({'path':str(target.relative_to(stage)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
        manifest={'version':1,'created_unix':time.time(),'secrets_included':a.mode=='secrets','sqlite':'paused DB+WAL staging then sqlite3.Connection.backup','files':index}
        (stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
        out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists():raise RuntimeError('Output exists; refusing overwrite')
        with tarfile.open(out,'w:gz') as archive:
            for f in stage.rglob('*'):
                if f.is_file() and '.sqlite-input' not in f.parts:archive.add(f,arcname=str(f.relative_to(stage)),recursive=False)
        os.chmod(out,0o600); print(json.dumps({'archive':str(out),'files':len(index),'secrets':a.mode=='secrets'}))
else:
    dest=Path('/restore')
    if any(dest.iterdir()):raise RuntimeError('Restore target must be EMPTY; original state is never overwritten')
    with tarfile.open(a.archive,'r:gz') as archive:
        members=set()
        for member in archive.getmembers():
            p=PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or member.issym() or member.islnk() or not member.isfile():raise RuntimeError('Unsafe archive member')
            if p.parts[0] not in {'hermes','knowledge','media','MANIFEST.json'}:raise RuntimeError('Unexpected archive root')
            if str(p) in members:raise RuntimeError('Duplicate archive member')
            members.add(str(p))
        archive.extractall(dest,filter='data')
    manifest=json.loads((dest/'MANIFEST.json').read_text())
    expected={f['path']:f['sha256'] for f in manifest['files']}
    if len(expected)!=len(manifest['files']) or set(expected)!=members-{'MANIFEST.json'}:raise RuntimeError('Manifest/archive contents differ')
    for name,digest in expected.items():
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or p.parts[0] not in {'hermes','knowledge','media'}:raise RuntimeError('Unsafe manifest path')
        f=dest/name
        if hashlib.sha256(f.read_bytes()).hexdigest()!=digest:raise RuntimeError('Archive checksum mismatch')
        os.chmod(f,0o600)
        if f.suffix=='.db':validate_db(f)
    # Remove host-specific gateway flags/sockets/pids; dispatcher will reclaim old worker claims.
    print(json.dumps({'restored_files':len(expected),'sqlite_integrity':'passed','secrets_included':manifest['secrets_included']}))
