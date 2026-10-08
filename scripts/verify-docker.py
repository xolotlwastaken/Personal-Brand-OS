"""Inspect supplied Docker metadata and mounted filesystem; no daemon socket required."""
import json, os, sys
from pathlib import Path
metadata=json.load(sys.stdin)[0];host=metadata['HostConfig'];config=metadata['Config']
assert metadata['State']['Running'] and metadata['State']['Health']['Status']=='healthy'
assert not host['Privileged'] and host['NetworkMode']!='host'
assert not host['PortBindings'] and not metadata['NetworkSettings']['Ports']
assert host['RestartPolicy']['Name']=='unless-stopped'
assert 'ALL' in host['CapDrop'] and {c.removeprefix('CAP_') for c in host['CapAdd']}=={'CHOWN','SETUID','SETGID','DAC_OVERRIDE','FOWNER','KILL'}
assert 'no-new-privileges:true' in host['SecurityOpt']
assert host['Memory']==3*1024**3 and host['NanoCpus']==2_000_000_000 and host['PidsLimit']==256
assert config['Entrypoint']==['/opt/hermes/docker/entrypoint-dispatch.sh']
mounts={m['Destination']:m for m in metadata['Mounts']}
expected={'/opt/data':True,'/knowledge':True,'/media':True,'/project/scripts':False,'/project/config':False,'/project/vendor':False,'/project/templates':False}
assert set(mounts)==set(expected),set(mounts)
for destination,writable in expected.items():
    m=mounts[destination];assert m['Type']=='bind' and m['RW']==writable,(destination,m)
    assert 'docker.sock' not in m['Source']
assert len({mounts[p]['Source'] for p in ['/opt/data','/knowledge','/media']})==3
assert os.getuid()==int(os.environ['HERMES_UID']) and os.getgid()==int(os.environ['HERMES_GID'])
for p in ['/opt/data','/knowledge','/media']:
    assert Path(p).stat().st_uid==os.getuid() and os.access(p,os.R_OK|os.W_OK|os.X_OK),p
assert Path('/opt/data').stat().st_mode&0o077==0
report={'status':'passed','container_id':metadata['Id'],'image':config['Image'],'entrypoint':config['Entrypoint'],'mounts':expected,'ports':'none','resources':{'memory_bytes':host['Memory'],'cpus':2,'pids':256},'runtime_uid':os.getuid(),'runtime_gid':os.getgid()}
Path('/opt/data/verification/docker.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS Docker health, official entrypoint, mount separation, UID/GID, private ports, capabilities and resource limits.')
