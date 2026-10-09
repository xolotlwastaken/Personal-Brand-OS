"""Artifact checks and CEO handoff guard; all execution state stays in native Kanban."""
import datetime, json, os, re
from pathlib import Path
from zoneinfo import ZoneInfo

WORD=re.compile(r"\b[\w]+(?:['’-][\w]+)*\b")
def words(text):return len(WORD.findall(text))
def check(path, target_seconds=45, min_words=95, max_words=115):
    p=Path(path)
    if not p.is_absolute():raise ValueError('Use an absolute /knowledge Markdown path')
    p=p.resolve();root=Path('/knowledge').resolve()
    if not p.is_relative_to(root) or p.suffix.lower()!='.md':raise ValueError('Only Markdown inside /knowledge is allowed')
    if not p.is_file() or p.stat().st_size>262144:raise ValueError('Missing or oversized Markdown artifact')
    text=p.read_text();errors=[];warnings=[]
    # Standard handoff: ## Spoken Script, blockquote or plain lines, then next heading/rule.
    heading=re.search(r'^##\s+(?:Complete\s+)?Spoken Script[^\n]*\n',text,re.I|re.M)
    speech=''
    if heading:
        segment=text[heading.end():]
        segment=re.split(r'^---\s*$|^##\s+',segment,maxsplit=1,flags=re.M)[0]
        speech=' '.join(line.lstrip('> ').strip(' "“”') for line in segment.splitlines() if line.strip() and not line.startswith('```'))
    count=words(speech)
    if not heading:errors.append('No ## Spoken Script section found; use the documented handoff format')
    elif not min_words<=count<=max_words:errors.append(f'Actual spoken words {count}, outside task bounds {min_words}–{max_words}')
    stated=re.search(r'\((\d+)\s+words',heading.group() if heading else '',re.I)
    if stated and int(stated.group(1))!=count:errors.append(f'Declared {stated.group(1)} words differs from measured {count}')
    durations=[];header=None;shot_rates=[]
    for line in text.splitlines():
        if not line.strip().startswith('|'):header=None;continue
        cells=[c.strip().strip('*') for c in line.strip().strip('|').split('|')]
        lower=[c.lower() for c in cells]
        if 'duration' in lower and any('spoken' in c for c in lower):header=lower;continue
        if not header or len(cells)!=len(header) or all(re.fullmatch(r'[-: ]+',c) for c in cells):continue
        duration=cells[header.index('duration')];match=re.fullmatch(r'(\d+(?:\.\d+)?)\s*s',duration)
        if not match:continue
        seconds=float(match.group(1));durations.append(seconds)
        index=next(i for i,c in enumerate(header) if 'spoken' in c)
        n=words(cells[index]);rate=round(n/seconds*60,1) if seconds else 999
        shot_rates.append({'beat':cells[0],'seconds':seconds,'words':n,'wpm':rate})
        if rate>180:errors.append(f'{cells[0]} needs {rate} words/minute; shorten speech or reallocate time')
    total=round(sum(durations),2)
    if not durations:errors.append('No timed shot table with Duration and Spoken Line columns found')
    elif abs(total-target_seconds)>.1:errors.append(f'Shot durations total {total}s; expected {target_seconds}s')
    created=re.search(r'^created:\s*(.+)$',text,re.M)
    if created:
        try:
            raw=created.group(1).strip(' "\'');stamp=datetime.datetime.fromisoformat(raw)
            if 'T' in raw and stamp.tzinfo and stamp>datetime.datetime.now(ZoneInfo('Asia/Singapore'))+datetime.timedelta(minutes=1):errors.append('Creation timestamp is in the future; use actual current date/time')
        except ValueError:warnings.append('Creation date format could not be parsed')
    if 'everyone' in speech.lower():warnings.append('Universal "everyone" claim needs evidence or more precise wording')
    if 'caption' in speech.lower():warnings.append('Verify promised caption resource actually exists before publication')
    return {'path':str(p),'valid':not errors,'spoken_words':count,'estimated_wpm':round(count/target_seconds*60,1),'shot_total_seconds':total,'shot_rates':shot_rates,'errors':errors,'warnings':warnings,'limits':'Deterministic text/timing checks only; human approves factual claims, actual footage and final pacing.'}

def handle(params,**kwargs):
    try:
        if set(params)-{'path','target_seconds','min_words','max_words'}:raise ValueError('Unknown parameter')
        target=params.get('target_seconds',45);minimum=params.get('min_words',95);maximum=params.get('max_words',115)
        if not 1<=target<=600 or not 0<=minimum<=maximum<=2000:raise ValueError('Invalid bounds')
        return json.dumps(check(params['path'],target,minimum,maximum))
    except (ValueError,OSError,KeyError,TypeError) as e:return json.dumps({'error':str(e),'valid':False})

CEO_TENANT = 'brand-os-ceo'
RELAY_BODY = '''You are the user's primary contact. Read the producing Brand Manager
card with kanban_show, its completion handoff and saved discovery/proposal artifact.
Relay its unanswered questions or specific strategy proposal to the user in a
kanban_comment prefixed "CEO to you:". Then kanban_block this card with kind
needs_input and a concise description of the answer or approval needed. Do not
complete merely because the specialist finished; questions require a human answer.
Do not repeat answered questions or invent personal evidence or measurements.
On resume, read the actual operator answers in this card's comments and prior cards.
Commission the next Brand Manager round through kanban_create in tenant brand-os-ceo,
workspace dir:/knowledge, max_runtime_seconds=300. The native handoff guard returns
ceo_followup_task_id: reuse it rather than creating another relay. Complete this card
once that next graph exists, including both returned task IDs in created_cards.
An interview answer is not approval of strategy decisions. Present the exact proposal
and collect explicit human approval before delegating canonical strategy changes.
If no further questions or decisions remain, report the evidenced outcome in a
"CEO to you:" comment before completing. Publishing, DMs, media generation and
production rendering remain disabled. Use native Kanban only; no polling loops.
'''


def relay_scope():
    # Native multiprofile TUI uses a ContextVar home; process env alone is unsafe.
    from hermes_constants import get_hermes_home
    return get_hermes_home() == Path('/opt/data/profiles/brand-ceo')


def relay_native(name, args):
    from tools.kanban_tools import registry
    result = json.loads(registry.get_entry(name).handler(args))
    if result.get('error'):
        raise ValueError(result['error'])
    return result


def ensure_ceo_relay(manager_id):
    if not relay_scope():
        raise ValueError('CEO handoff guard is restricted to the project CEO profile')
    detail = relay_native('kanban_show', {'task_id': manager_id})
    task = detail['task']
    if task['assignee'] != 'brand-manager' or task['tenant'] != CEO_TENANT:
        raise ValueError('Only Brand Manager cards in the CEO conversation can be paired')
    for child in detail['children']:
        row = relay_native('kanban_show', {'task_id': child})['task']
        if row['assignee'] == 'brand-ceo' and row['tenant'] == CEO_TENANT:
            return child
    result = relay_native('kanban_create', {
        'title': f'CEO follow-up: Brand Manager {manager_id}',
        'body': f'Producing Brand Manager card: {manager_id}.\n\n' + RELAY_BODY,
        'assignee': 'brand-ceo', 'tenant': CEO_TENANT, 'parents': [manager_id],
        'workspace_kind': 'dir', 'workspace_path': '/knowledge',
        'max_runtime_seconds': 300, 'triage': False,
        'idempotency_key': f'ceo-relay:{manager_id}'})
    return result['task_id']


def relay_after_create(tool_name='', args=None, result=None, **kwargs):
    args = args or {}
    if (tool_name != 'kanban_create' or args.get('assignee') != 'brand-manager'
            or args.get('tenant', os.environ.get('HERMES_TENANT')) != CEO_TENANT
            or not relay_scope()):
        return None
    row = json.loads(result) if isinstance(result, str) else dict(result or {})
    if row.get('error') or not row.get('task_id'):
        return None
    try:
        row['ceo_followup_task_id'] = ensure_ceo_relay(row['task_id'])
        row['ceo_followup_note'] = 'Native dependent CEO relay exists. Reuse this ID; do not create a duplicate.'
    except (ValueError, KeyError, TypeError) as exc:
        row['ceo_followup_error'] = str(exc)
        row['ceo_followup_note'] = 'Do not complete orchestration until the native CEO relay is repaired.'
    return json.dumps(row)


def relay_before_tool(tool_name='', args=None, **kwargs):
    if tool_name not in {'kanban_complete', 'kanban_create'} or not relay_scope():
        return None
    args = args or {}
    try:
        if tool_name == 'kanban_create':
            if args.get('assignee') == 'brand-manager' and not (
                    args.get('tenant') or os.environ.get('HERMES_TENANT')):
                current = os.environ.get('HERMES_KANBAN_TASK')
                tenant = (relay_native('kanban_show', {'task_id': current})['task']['tenant']
                          if current else None)
                return {'action': 'modify', 'args': {'tenant': tenant or CEO_TENANT}}
            if (args.get('assignee') != 'brand-ceo'
                    or args.get('tenant', os.environ.get('HERMES_TENANT')) != CEO_TENANT):
                return None
            for parent in args.get('parents') or []:
                task = relay_native('kanban_show', {'task_id': parent})['task']
                if task['assignee'] == 'brand-manager' and task['tenant'] == CEO_TENANT:
                    relay = ensure_ceo_relay(parent)
                    return {'action': 'block', 'message': f'CEO follow-up already exists: {relay}. Reuse that native card ID in your handoff; no duplicate is needed.'}
        else:
            tid = args.get('task_id') or os.environ.get('HERMES_KANBAN_TASK')
            if not tid:
                return None
            detail = relay_native('kanban_show', {'task_id': tid})
            if detail['task']['assignee'] != 'brand-ceo' or detail['task']['tenant'] != CEO_TENANT:
                return None
            for child in set(detail['children']) | set(args.get('created_cards') or []):
                task = relay_native('kanban_show', {'task_id': child})['task']
                if task['assignee'] == 'brand-manager' and task['tenant'] == CEO_TENANT:
                    ensure_ceo_relay(child)
    except (ValueError, KeyError, TypeError) as exc:
        return {'action': 'block', 'message': f'CEO handoff guard could not verify the native follow-up: {exc}. Repair the Brand Manager/CEO dependency before completing.'}
    return None


def register(ctx):
    schema={'name':'brand_artifact_check','description':'Read-only: measure actual spoken words, declared count, per-shot speaking rates, summed timings and future timestamps in a local /knowledge Markdown Reel script. Call before script completion and CEO approval. Does not verify personal facts or publish anything.','parameters':{'type':'object','properties':{'path':{'type':'string','description':'Absolute /knowledge/...md script path. Must use ## Spoken Script and timed table with Duration / Spoken Line columns.'},'target_seconds':{'type':'number','default':45},'min_words':{'type':'integer','default':95},'max_words':{'type':'integer','default':115}},'required':['path'],'additionalProperties':False}}
    ctx.register_tool(name='brand_artifact_check',toolset='brand-validation',schema=schema,handler=handle)
    ctx.register_hook('transform_tool_result', relay_after_create)
    ctx.register_hook('pre_tool_call', relay_before_tool)
