"""Idempotent configuration reconciliation, executed inside official Hermes Docker."""
import argparse, hashlib, json, os, shutil, subprocess
from dotenv import dotenv_values, set_key
from pathlib import Path
from hermes_cli.profiles import create_profile, get_profile_dir, list_profile_names

P=Path('/project'); H=Path('/opt/data')
parser=argparse.ArgumentParser();parser.add_argument('--apply-drift',action='store_true');args=parser.parse_args()
os.umask(0o077)
roles=json.loads((P/'config/agents.json').read_text()); ledger=H/'brand-os-provision.json'
previous=json.loads(ledger.read_text()) if ledger.exists() else {}; current=dict(previous); conflicts=[]

def managed(dst, content):
    dst=Path(dst); key=str(dst.relative_to(H)); wanted=hashlib.sha256(content).hexdigest()
    if dst.exists():
        actual=hashlib.sha256(dst.read_bytes()).hexdigest()
        if actual==wanted: current[key]=wanted; return
        if actual!=previous.get(key) and not args.apply_drift:
            conflicts.append(key); print('DRIFT preserved:',key); return
        backup=H/'config-backups'/key
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists(): shutil.copy2(dst,backup)
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+'.provision.tmp');tmp.write_bytes(content);os.chmod(tmp,0o600);tmp.replace(dst);current[key]=wanted

# Root is Hermes's mandatory infrastructure slot, not an eighth project agent.
base=json.loads((P/'config/agents/brand-ceo/config.yaml').read_text())
def expand(cfg):
    s=json.dumps(cfg)
    for k,default in [('BRAND_MODEL','nvidia/nemotron-3-ultra-550b-a55b'),('BRAND_PROVIDER','nvidia'),('BRAND_BASE_URL','https://integrate.api.nvidia.com/v1')]:
        s=s.replace('${'+k+'}',os.environ.get(k,default))
    return json.loads(s)
base=expand(base);base['gateway']={'multiplex_profiles':True};base.pop('plugins',None);base['platform_toolsets']={'cli':['kanban'],'api_server':['kanban']}
# Discard upstream first-boot defaults only in this new project state.
root_config=H/'config.yaml'
if root_config.exists() and 'config.yaml' not in previous and not (H/'profiles').exists():
    managed_backup=H/'config-backups/upstream-first-boot.yaml';managed_backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root_config,managed_backup);root_config.unlink()
managed(root_config,json.dumps(base,indent=2).encode()+b'\n')
# Keep root offline for messaging; its gateway owns dispatcher/cron infrastructure only.
for profile,role in roles.items():
    if profile not in list_profile_names():
        create_profile(profile,no_alias=True,no_skills=True,description=role['description'])
        # create_profile seeds a model block; ours is authoritative on first creation.
        for starter in ['config.yaml', 'SOUL.md', 'profile.yaml']:
            (get_profile_dir(profile)/starter).unlink(missing_ok=True)
        print('CREATED:',profile)
    dest=get_profile_dir(profile)
    for name in ['SOUL.md','profile.yaml','config.yaml']:
        source=P/'config/agents'/profile/name
        content=source.read_bytes() if name!='config.yaml' else (json.dumps(expand(json.loads(source.read_text())),indent=2)+'\n').encode()
        managed(dest/name,content)
    for memory in ['MEMORY.md','USER.md']:
        f=dest/'memories'/memory
        if not f.exists(): f.parent.mkdir(parents=True,exist_ok=True);f.write_text(f'# {profile} private {memory}\n');os.chmod(f,0o600)
    if 'brand-validation' in role['tools']:
        for f in (P/'config/plugins/artifact-validator').rglob('*'):
            if f.is_file():managed(dest/'plugins/artifact-validator'/f.relative_to(P/'config/plugins/artifact-validator'),f.read_bytes())
    if 'brand-references' in role['tools']:
        for f in (P/'config/plugins/reference-acquisition').rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc':
                managed(dest/'plugins/reference-acquisition'/f.relative_to(P/'config/plugins/reference-acquisition'),f.read_bytes())
    for skill in role['skills']:
        source=P/'config/skills'/skill
        for f in source.rglob('*'):
            if f.is_file():managed(dest/'skills'/skill/f.relative_to(source),f.read_bytes())
    # Static model credentials only; preserve any existing per-profile credentials.
    imported=H/'provider-import.env'
    if imported.exists():
        existing=dotenv_values(dest/'.env')
        for key,value in dotenv_values(imported).items():
            if key in {'NVIDIA_API_KEY','OPENROUTER_API_KEY','OPENAI_API_KEY','CUSTOM_API_KEY'} and value and not existing.get(key):
                set_key(str(dest/'.env'),key,value)
        os.chmod(dest/'.env',0o600)
# Seed vault from templates only if absent; never reconcile or overwrite runtime knowledge.
for folder in ['brand/sessions','research/creators','research/references','research/formats','research/trends','content/ideas','content/hooks','content/scripts','content/production-plans','content/publication-packages','analytics/weekly-reports','analytics/experiments','operations/reviews']:
    (Path('/knowledge')/folder).mkdir(parents=True,exist_ok=True)
for f in (P/'templates/knowledge').rglob('*'):
    target=Path('/knowledge')/f.relative_to(P/'templates/knowledge')
    if f.is_dir(): target.mkdir(parents=True,exist_ok=True)
    elif not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
ledger.write_text(json.dumps(current,indent=2)+'\n');os.chmod(ledger,0o600)
subprocess.run(['hermes','kanban','init'],check=True)
print('Named project profiles:',', '.join(n for n in list_profile_names() if n != 'default'))
print('Drift conflicts:',len(conflicts),'(use --apply-drift after reviewing config-backups)')
if conflicts: raise SystemExit(2)
