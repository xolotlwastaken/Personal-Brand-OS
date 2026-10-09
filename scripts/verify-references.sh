#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
# Copy only synthetic tests to ignored project state, without changing container mounts.
tar -c tests/test_references.py tests/test_reference_plugin.py |
  docker compose exec -T --user hermes hermes /opt/data/reference-runtime/bin/python -c '
import sys,tarfile
from pathlib import Path
root=Path("/opt/data/verification/reference-tests");root.mkdir(parents=True,exist_ok=True)
allowed={"tests/test_references.py","tests/test_reference_plugin.py"}
with tarfile.open(fileobj=sys.stdin.buffer,mode="r|") as archive:
 for member in archive:
  if member.name not in allowed or not member.isfile() or member.size>65536:raise ValueError("Unexpected test archive member")
  (root/Path(member.name).name).write_bytes(archive.extractfile(member).read())
'
docker compose exec -T --user hermes -e BRAND_REFERENCE_TEST_ROOT=/project hermes \
  /opt/data/reference-runtime/bin/python -m coverage run \
  --data-file=/opt/data/verification/reference.coverage \
  --include='/project/scripts/reference-worker.py,/project/config/plugins/reference-acquisition/__init__.py' \
  -m unittest discover -s /opt/data/verification/reference-tests -p 'test_reference*.py'
docker compose exec -T --user hermes hermes /opt/data/reference-runtime/bin/python -m coverage report \
  --data-file=/opt/data/verification/reference.coverage --show-missing --fail-under=80
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-profile.py reference-builder
