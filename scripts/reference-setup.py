"""Install only pinned binary packages into project state; never modify Hermes's venv."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

os.umask(0o077)
runtime = Path('/opt/data/reference-runtime')
requirements = Path('/project/config/reference-requirements.lock')
digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
ledger = runtime / 'reference-install.json'
if not (runtime / 'bin/python').is_file():
    subprocess.run(['/usr/bin/python3', '-m', 'venv', str(runtime)], check=True)
python = str(runtime / 'bin/python')
if not ledger.exists() or json.loads(ledger.read_text()).get('lock_sha256') != digest:
    subprocess.run([python, '-m', 'pip', 'install', '--require-hashes', '--only-binary=:all:', '-r', str(requirements)], check=True)
    subprocess.run([python, '-m', 'pip', 'check'], check=True)
    ledger.write_text(json.dumps({'lock_sha256': digest, 'python': '/usr/bin/python3 (3.13)',
                                  'model_revision': 'd90ca5fe260221311c53c58e660288d3deb8d356'}, indent=2) + '\n')
model = Path('/opt/data/reference-model')
if not all((model / name).is_file() for name in ['model.bin', 'config.json', 'tokenizer.json', 'vocabulary.txt']):
    subprocess.run([python, '-c', "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-tiny', revision='d90ca5fe260221311c53c58e660288d3deb8d356', local_dir='/opt/data/reference-model', allow_patterns=['model.bin','config.json','tokenizer.json','vocabulary.txt'], token=False)"],
                   check=True, env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HF_HUB_DISABLE_XET': '1'})
print('Reference runtime ready; official Hermes image and its Python environment unchanged.')
