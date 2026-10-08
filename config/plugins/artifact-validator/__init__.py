"""Read-only deterministic checks; native Hermes plugin, not an execution engine."""
import datetime, json, re
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

def register(ctx):
    schema={'name':'brand_artifact_check','description':'Read-only: measure actual spoken words, declared count, per-shot speaking rates, summed timings and future timestamps in a local /knowledge Markdown Reel script. Call before script completion and CEO approval. Does not verify personal facts or publish anything.','parameters':{'type':'object','properties':{'path':{'type':'string','description':'Absolute /knowledge/...md script path. Must use ## Spoken Script and timed table with Duration / Spoken Line columns.'},'target_seconds':{'type':'number','default':45},'min_words':{'type':'integer','default':95},'max_words':{'type':'integer','default':115}},'required':['path'],'additionalProperties':False}}
    ctx.register_tool(name='brand_artifact_check',toolset='brand-validation',schema=schema,handler=handle)
