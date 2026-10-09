"""Provision one static model API key via stdin; never echo or store it in Git."""
import json, os, sys
from pathlib import Path
from dotenv import set_key
allowed={'neuralwatt':'NEURALWATT_API_KEY','nvidia':'NVIDIA_API_KEY','openrouter':'OPENROUTER_API_KEY','openai':'OPENAI_API_KEY','custom':'CUSTOM_API_KEY'}
provider=sys.argv[1]; assert provider in allowed,'unsupported provider'
key=sys.stdin.read().strip();assert key and '\n' not in key,'empty/invalid key'
roles=json.loads(Path('/project/config/agents.json').read_text())
for name in roles:
    f=Path('/opt/data/profiles')/name/'.env';set_key(str(f),allowed[provider],key);os.chmod(f,0o600)
print('Static model key saved to seven profiles; restart the gateway to reload it.')
