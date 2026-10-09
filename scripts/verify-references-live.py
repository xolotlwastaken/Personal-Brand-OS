"""Explicit bounded live checks. Native handlers or one real dispatcher card.

Unlike verify-references.sh, --tools performs public network requests, CPU speech
inference and up to one vision request. --dispatcher asks the real profile worker
to exercise the same tools and write a task-specific handoff. No custom task queue.
"""
import argparse
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['tools', 'dispatcher'])
args = parser.parse_args()
profile = 'reference-builder' if args.mode == 'tools' else 'brand-ceo'
os.environ['HERMES_HOME'] = '/opt/data/profiles/' + profile
os.environ['HERMES_PROFILE'] = profile
from hermes_cli.env_loader import load_hermes_dotenv
load_hermes_dotenv()
from hermes_cli.plugins import discover_plugins
discover_plugins()
from tools.kanban_tools import registry

OUT = Path('/opt/data/verification')
OUT.mkdir(exist_ok=True)
SOURCE = 'https://www.instagram.com/reel/DdT9g1kKngq/'


def call(name, params):
    result = json.loads(registry.get_entry(name).handler(params))
    if result.get('error'):
        raise RuntimeError(result['error'])
    return result


if args.mode == 'tools':
    results = {}
    try:
        results['search'] = call('brand_reference_search', {'query': 'AI automation workflow', 'platform': 'instagram', 'limit': 3})
        assert results['search']['results'], 'No indexed public references returned'
        results['fetch'] = call('brand_reference_fetch', {'url': SOURCE})
        results['prepare'] = call('brand_reference_prepare', {'media_path': results['fetch']['media_path'], 'source_url': SOURCE})
        assert results['prepare']['transcript_status'] == 'machine-transcribed', results['prepare']['transcript_status']
        assert len(results['prepare']['frames']) <= 12
        results['visual'] = call('brand_reference_visual', {'evidence_path': results['prepare']['evidence_path']})
        assert results['visual'].get('completion_status') == 'complete', 'Visual observations were truncated'
        results['repeat_fetch'] = call('brand_reference_fetch', {'url': SOURCE})['cached']
        results['repeat_prepare'] = call('brand_reference_prepare', {'media_path': results['fetch']['media_path'], 'source_url': SOURCE})['cached']
        results['repeat_visual'] = call('brand_reference_visual', {'evidence_path': results['prepare']['evidence_path']})['cached']
        assert results['repeat_fetch'] and results['repeat_prepare'] and results['repeat_visual']
        results['status'] = 'passed-native-tools'
    except Exception as exc:
        results['status'] = 'failed-or-unavailable'
        results['error'] = str(exc)[:300]
    results['limits'] = 'Actual native tool calls, not an agent dispatcher run. Speech and sampled-frame observations require human review.'
    (OUT / 'reference-live.json').write_text(json.dumps(results, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': results['status'], 'error': results.get('error'),
                      'evidence': results.get('prepare', {}).get('evidence_path'),
                      'visual': results.get('visual', {}).get('artifact_path')}))
    if results['status'] != 'passed-native-tools':
        raise SystemExit(1)
else:
    body = f'''User-authorized bounded REAL reference acquisition acceptance test. Use only native tools; no terminal, login/cookies, comments collection, publishing or messages. At most one retrieval and one visual model call; no downstream cards. Read skill reel-analyzer and /knowledge/operations/reference-acquisition.md.
Run brand_reference_search for public topic "AI automation workflow", platform instagram, limit 3. Treat snippets as unverified leads. Then test the supplied accessible source {SOURCE} through brand_reference_fetch and brand_reference_prepare(source_url=that URL). If the transcript is unavailable from an old cached attempt, use prepare refresh=true once. Call brand_reference_visual on returned evidence_path. Read the source, transcript and visual artifact files. Never claim full-video viewing, exact motion/cuts, personal user history or virality. Transcript is Hindi/Urdu/English and may be inaccurate; explicitly flag uncertain wording.
Write /knowledge/research/references/<ACTUAL_TASK_ID>-live-reference-teardown.md with real task ID, owner, sources, retrieval date, approval=analysis-only, hook/observed beats supported by timestamps, original technique ideas and uncertainties. Include returned source/media/evidence/visual paths and actual metrics only when available; null view count remains unavailable. Read back; complete only if retrieval, machine transcript and visual observations exist. If access, quota or essential evidence prevents completion, block capability with the exact reason. Native Kanban is the only execution engine.
This test uses Reference Builder’s configured deployment model/provider; no per-card provider override is applied.'''
    result = call('kanban_create', {'title': 'Verify real public reference search, download and evidence analysis',
                                  'assignee': 'reference-builder', 'body': body, 'workspace_kind': 'dir',
                                  'workspace_path': '/knowledge', 'tenant': 'brand-os-references-e2e',
                                  'max_runtime_seconds': 300, 'priority': 40,
                                  'idempotency_key': 'brand-os-reference-acquisition-neuralwatt-v1', 'completion_contract': 'local-only'})
    (OUT / 'reference-dispatch-submission.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'task_id': result.get('task_id') or result.get('task', {}).get('id') or result.get('id'),
                      'native_submission': result}))
