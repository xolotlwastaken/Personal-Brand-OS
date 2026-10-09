'use strict';
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names = {'brand-ceo':'Brand CEO','brand-manager':'Brand Manager','reference-builder':'Reference Builder','hook-writer':'Hook Writer','script-writer':'Script Writer','video-editor':'Video Editor','publisher':'Publisher'};
const initials = {'brand-ceo':'BC','brand-manager':'BM','reference-builder':'RB','hook-writer':'HW','script-writer':'SW','video-editor':'VE','publisher':'PB'};
const views = {
  ceo:['Brand CEO','Your direction. Your CEO.','Talk to your CEO. Your CEO brings the team together.'],
  overview:['Overview','A little clarity. A lot of momentum.','Seven specialists, one shared direction. Here’s where your work stands.'],
  board:['Task board','From a spark to a finished draft.','Follow the handoffs, inspect the work, and keep your team moving.'],
  agents:['Your agents','Meet your content team.','Distinct expertise. Persistent context. A shared knowledge vault.'],
  vault:['Knowledge vault','Good work leaves a trail.','Browse the briefs, research, scripts, and reviews your team has saved.'],
  skills:['Skills library','The playbooks behind the work.','Your adapted, pinned skills — organized by the specialists who use them.']
};
let snapshot = null;
let token = '';
let currentView = 'ceo';
let ceoThread = null;
let ceoDraft = '';
let ceoReplyTo = '';
let ceoRequestKey = '';
let ceoSending = false;
let ceoRefreshing = false;
let ceoError = '';
let ceoConversationId = '';
let ceoDraftTarget = '';
let ceoCurrentTarget = '';
let ceoPending = null;
let ceoCanSend = false;
const ceoDrafts = new Map();
let ceoReadState=new CEOReadState();
try {ceoReadState=new CEOReadState(localStorage);} catch { /* Browser storage may be disabled. */ }
let refreshing = false;
let filters = {assignee:'', tenant:'', query:''};
let requestKey = '';
let activeTask = '';
let detailGeneration = 0;
let readerGeneration = 0;
const knownProjects = new Set();

const number = (n) => n == null ? '—' : new Intl.NumberFormat('en', {notation: n >= 10000 ? 'compact' : 'standard'}).format(n);
const date = (seconds) => seconds ? new Intl.DateTimeFormat('en-SG', {day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Singapore'}).format(seconds * 1000) : '—';
function age(seconds) {
  if (!seconds) return 'No timestamp';
  const mins = Math.max(0, Math.floor((Date.now() / 1000 - seconds) / 60));
  return mins < 1 ? 'Just now' : mins < 60 ? `${mins}m ago` : mins < 1440 ? `${Math.floor(mins / 60)}h ago` : `${Math.floor(mins / 1440)}d ago`;
}
function avatar(id) { return `<span class="avatar ${esc(id)}">${esc(initials[id] || '?')}</span>`; }
function badge(status) { return `<span class="badge ${esc(status)}"><i></i>${esc(status.replaceAll('_',' '))}</span>`; }
function tasks() {
  return (snapshot?.board.tasks || []).filter(t => (!filters.assignee || t.assignee === filters.assignee) &&
    (!filters.tenant || t.tenant === filters.tenant) && (!filters.query || `${t.title} ${t.id} ${t.assignee}`.toLowerCase().includes(filters.query.toLowerCase())));
}
function taskState(t) {
  // Native "running" without a run ID is dispatchable, not proof of a live worker.
  return t.status === 'running' && !t.current_run_id ? 'ready' : t.status;
}
function agentState(id) {
  const all = snapshot.board.tasks.filter(t => t.assignee === id);
  if (all.some(t => t.status === 'running' && t.current_run_id)) return 'working';
  if (all.some(needsAttention)) return 'attention';
  if (all.some(t => ['ready','running','todo'].includes(t.status))) return 'queued';
  return 'idle';
}
function needsAttention(t) {
  return ['blocked','review'].includes(t.status) ||
    (!t.current_run_id && !['done','archived'].includes(t.status) && Boolean(t.last_error));
}
async function api(path, payload) {
  const response = await fetch(path, payload ? {method:'POST', headers:{'Content-Type':'application/json','X-Dashboard-Token':token}, body:JSON.stringify(payload)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The request failed. Please refresh.');
  return data;
}
function toast(message) {
  $('#toast').textContent = message; $('#toast').hidden = false;
  setTimeout(() => { $('#toast').hidden = true; }, 5500);
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  $('#refresh').disabled = true;
  $('#sync-state').textContent = 'Syncing…';
  try {
    token = (await api('/api/bootstrap')).token;
    const params = new URLSearchParams();
    if (filters.assignee) params.set('assignee', filters.assignee);
    if (filters.tenant) params.set('tenant', filters.tenant);
    snapshot = await api(`/api/snapshot?${params}`);
    snapshot.board.tasks.forEach(t => { if (t.tenant) knownProjects.add(t.tenant); });
    $('#connection-error').hidden = true;
    $('#gateway-dot').classList.toggle('healthy', snapshot.gateway === 'healthy');
    $('#gateway-label').textContent = snapshot.gateway === 'healthy' ? 'Connected · 1 container' : 'Needs attention';
    $('#sync-state').textContent = `Updated ${date(snapshot.updated_at)} SGT`;
    $('#nav-count').textContent = snapshot.board.tasks.filter(t => !['done','archived'].includes(t.status)).length;
    render();
    await refreshCEO();
  } catch (error) {
    $('#connection-error').textContent = error.message;
    $('#connection-error').hidden = false;
    $('#gateway-dot').classList.remove('healthy');
    $('#gateway-label').textContent = 'Connection unavailable';
    $('#sync-state').textContent = snapshot ? 'Showing last successful snapshot' : 'Offline';
    if (!snapshot) $('#view').innerHTML = '<div class="empty">Your workspace is unavailable. Start the Hermes container, then select Refresh.</div>';
  } finally { refreshing = false; $('#refresh').disabled = false; }
}
function agentCard(agent, expanded=false) {
  const state = agentState(agent.id);
  const all = snapshot.board.tasks.filter(t => t.assignee === agent.id);
  const working = all.find(t => t.status === 'running' && t.current_run_id);
  const failure = all.find(t=>needsAttention(t) && t.last_error);
  const count = all.filter(t => t.status === 'done').length;
  return `<article class="agent-card ${state}"><div class="agent-top">${avatar(agent.id)}<span class="agent-state ${state}"><i></i>${agent.provisioned ? ({working:'Working',attention:'Needs attention',queued:'Work queued',idle:'Available'}[state]) : 'Needs setup'}</span></div>
    <button class="agent-name" data-agent="${esc(agent.id)}">${esc(names[agent.id])} <span>↗</span></button><p class="agent-role">${esc(agent.role)}</p>
    ${expanded ? `<p class="agent-description">${esc(agent.description)}</p><div class="skill-tags">${agent.skills.map(s=>`<button data-skill="${esc(s)}">${esc(s)}</button>`).join('')}</div>` : ''}
    <div class="agent-current">${working ? `<span class="pulse"></span><button data-task="${esc(working.id)}">${esc(working.title)}</button>` : failure ? `<button data-task="${esc(failure.id)}">${failure.last_outcome === 'rate_limited' ? 'Provider quota reached · View attempt ↗' : 'Last attempt needs attention ↗'}</button>` : `<span>${state === 'queued' ? 'Waiting for the dispatcher' : state === 'attention' ? 'Open the board to review' : 'Ready for the next good idea'}</span>`}</div>
    <div class="agent-bottom"><span>${agent.skills.length} skills <i>·</i> ${count} done</span><button class="text-button" data-agent="${esc(agent.id)}">Chat & activity ↗</button></div></article>`;
}
function taskRow(t) {
  return `<button class="task-row" data-task="${esc(t.id)}">${avatar(t.assignee)}<span class="task-row-title">${esc(t.title)}<small>${esc(names[t.assignee] || t.assignee)} <i>·</i> ${esc(t.tenant || 'No project')}</small></span>${badge(taskState(t))}<span class="row-age">${age(t.completed_at || t.started_at || t.created_at)}</span><span class="row-arrow">↗</span></button>`;
}
function artifactRow(f) {
  return `<button class="artifact-row" data-artifact="${esc(f.path)}"><span class="file-icon">▤</span><span>${esc(f.title || f.name.replaceAll('-',' '))}<small>${f.synthetic?'SYNTHETIC FIXTURE · ':''}${esc(f.path)}</small></span><span class="row-arrow">↗</span></button>`;
}
function overview() {
  const all = snapshot.board.tasks;
  const working = all.filter(t => t.status === 'running' && t.current_run_id).length;
  const queued = all.filter(t => ['todo','ready'].includes(t.status) || (t.status === 'running' && !t.current_run_id)).length;
  const attention = all.filter(needsAttention).length;
  const done = all.filter(t => t.status === 'done').length;
  const metrics = [['01','Agents at work',working,'One worker at a time','active'],['02','In the pipeline',queued,'Ideas taking shape',''],['03','Needs your eye',attention,'Reviews, blockers & failed attempts','amber'],['04','Completed cards',done,'Finished execution, drafts remain','']];
  return `<div class="metrics">${metrics.map(([idx,label,val,sub,cls])=>`<div class="metric ${cls}"><div><span>${label}</span><small>${idx}</small></div><strong>${val}</strong><p>${sub}</p></div>`).join('')}</div>
    <div class="section-heading"><div><h2>Your team <span>07</span></h2><p>A specialist for every step of the story.</p></div><a href="#agents">Meet the team ↗</a></div>
    <div class="agent-grid">${snapshot.agents.map(a=>agentCard(a)).join('')}</div>
    <div class="lower-grid"><section class="panel"><div class="panel-heading"><h2>On the desk <span>${all.length}</span></h2><a href="#board">View board ↗</a></div>${[...all].sort((a,b)=>((['blocked','review'].includes(b.status)?3:taskState(b)==='running'?2:!['done','archived'].includes(b.status)?1:0)-(['blocked','review'].includes(a.status)?3:taskState(a)==='running'?2:!['done','archived'].includes(a.status)?1:0)) || (b.completed_at || b.created_at)-(a.completed_at || a.created_at)).slice(0,5).map(taskRow).join('') || '<div class="empty">A clean slate. Send your first brief to the CEO.</div>'}</section>
    <section class="panel"><div class="panel-heading"><h2>Fresh from the vault</h2><a href="#vault">Browse ↗</a></div>${snapshot.artifacts.filter(f=>!f.synthetic).slice(0,4).map(artifactRow).join('') || '<div class="empty">Saved draft artifacts will appear here.</div>'}<div class="vault-note"><span>◈</span> Shared knowledge. Lasting context.</div></section></div>
    <div class="review-strip"><span>✳</span><div><strong>Your judgment is part of the workflow.</strong><p>Completed cards are execution results. Strategy and publication still need your review.</p></div><button class="secondary" data-ceo="brand-ceo">Talk to CEO ↗</button></div>`;
}
function filterBar() {
  const tenants = [...knownProjects].sort();
  if (filters.tenant && !tenants.includes(filters.tenant)) tenants.push(filters.tenant);
  return `<div class="filters"><label class="search"><span>⌕</span><input id="task-search" value="${esc(filters.query)}" placeholder="Search tasks, IDs, or agents" aria-label="Search tasks"></label><select id="agent-filter" aria-label="Filter by agent"><option value="">All agents</option>${snapshot.agents.map(a=>`<option value="${esc(a.id)}" ${filters.assignee===a.id?'selected':''}>${esc(names[a.id])}</option>`).join('')}</select><select id="tenant-filter" aria-label="Filter by project"><option value="">All projects</option>${tenants.map(t=>`<option ${filters.tenant===t?'selected':''}>${esc(t)}</option>`).join('')}</select>${filters.assignee || filters.tenant || filters.query ? '<button class="secondary" id="clear-filters">Clear</button>':''}</div>`;
}
function board() {
  const lanes = [['todo','Waiting'],['ready','Ready'],['running','In progress'],['review','Review'],['blocked','Blocked'],['done','Done']];
  const all = tasks();
  return `${filterBar()}<div class="kanban">${lanes.map(([status,label])=>{const cards=all.filter(t=>taskState(t)===status);return `<section class="lane ${status}"><div class="lane-heading"><i></i><h2>${label}</h2><span>${cards.length}</span></div><div class="lane-cards">${cards.map(t=>`<button class="kanban-card" data-task="${esc(t.id)}"><div class="card-project">${esc(t.tenant || 'No project')} <span>↗</span></div><h3>${esc(t.title)}</h3><div class="card-owner">${avatar(t.assignee)}<span>${esc(names[t.assignee] || t.assignee)}</span></div><div class="card-meta"><span>${esc(t.id)}</span><span>${t.parents.length ? `${t.parents.length} dependencies` : age(t.created_at)}</span></div></button>`).join('') || '<div class="lane-empty">Nothing here yet</div>'}</div></section>`;}).join('')}</div><p class="hint">Waiting cards have unmet dependencies. Ready cards await native dispatch. Task states and handoffs come from Hermes.</p>`;
}
function agentsView() {
  return `<div class="agent-grid expanded">${snapshot.agents.map(a=>agentCard(a,true)).join('')}</div><div class="panel usage-panel"><div class="panel-heading"><h2>Workspace usage</h2><span class="muted">Recorded session totals · All local runs</span></div><div class="table-scroll"><table><thead><tr><th>Agent</th><th>Sessions</th><th>API calls</th><th>Input tokens</th><th>Output tokens</th><th>Recorded cost</th></tr></thead><tbody>${snapshot.agents.map(a=>`<tr><td>${esc(names[a.id])}</td><td>${number(a.usage.sessions)}</td><td>${number(a.usage.api_calls)}</td><td>${number(a.usage.input_tokens)}</td><td>${number(a.usage.output_tokens)}</td><td>${a.usage.actual_cost_usd == null ? 'Unavailable' : '$'+Number(a.usage.actual_cost_usd).toFixed(4)}</td></tr>`).join('')}</tbody></table></div><p class="hint">Unavailable cost means the provider has not recorded a complete actual cost total.</p></div>`;
}
function vaultView(query='') {
  const files = snapshot.artifacts.filter(f=>f.path.toLowerCase().includes(query.toLowerCase()));
  return `<div class="filters"><label class="search"><span>⌕</span><input id="vault-search" value="${esc(query)}" placeholder="Search saved knowledge" aria-label="Search knowledge vault"></label><span class="muted">${files.length} Markdown documents</span></div><div class="panel vault-list">${files.map(f=>`<div class="vault-file">${artifactRow(f)}<span>${date(f.modified_at)}</span><span>${number(Math.ceil(f.bytes/1024))} KB</span></div>`).join('') || '<div class="empty">No matching documents.</div>'}</div><p class="hint">Previews are read-only. Existing vault notes and private agent state are preserved.</p>`;
}
function skillsView() {
  const skills = [...new Set(snapshot.agents.flatMap(a=>a.skills))].sort();
  return `<div class="skills-summary"><strong>${skills.length}</strong><span>adapted playbooks</span><span class="muted">Pinned source · Local runtime skills</span></div><div class="skills-grid">${skills.map(s=>{const owners=snapshot.agents.filter(a=>a.skills.includes(s));return `<button class="skill-card" data-skill="${esc(s)}"><span class="skill-symbol">✳</span><h3>${esc(s.replaceAll('-',' '))}</h3><p>${esc(owners.map(a=>names[a.id]).join(' · '))}</p><span class="text-button">Read playbook ↗</span></button>`;}).join('')}</div>`;
}
function ceoView() {
  if (!ceoThread) return ceoError ? `<div class="notice error" role="alert">${esc(ceoError)}</div>` : '<div class="loading">Reading your CEO conversation…</div>';
  const chats = ceoConversations(ceoThread.tasks, snapshot.board.tasks);
  if (!ceoConversationId) ceoConversationId = chats[0]?.id || 'new';
  const chat = chats.find(c=>c.id===ceoConversationId);
  const selected = chat?.reply;
  ceoReplyTo = selected?.task.id || '';
  ceoCurrentTarget = chat ? selected ? `${selected.task.id}:${selected.question_key || ''}` : 'busy' : 'new';
  const stale = ceoDraft && ceoDraftTarget && ceoDraftTarget!==ceoCurrentTarget;
  const pendingHere = ceoPending?.conversation===ceoConversationId;
  ceoCanSend = !ceoSending && !(pendingHere && ceoPending.task_id) && (!chat || Boolean(selected));
  const disabled = !ceoCanSend || stale || !ceoDraft.trim();
  const messages = [...(chat?.messages || [])];
  if (ceoPending && ceoPending.conversation===ceoConversationId && !messages.some(m=>m.role==='user' && m.body===ceoPending.body && m.task_id===ceoPending.task_id)) {
    messages.push({role:'user',body:ceoPending.body,time:ceoPending.time,pending:true});
  }
  const state = ceoThread.brand_state;
  const status = ceoSending ? 'Sending your message…' : pendingHere ? 'Your CEO will respond here' : chat?.status || 'Start a conversation';
  return `<div class="ceo-chat-page"><aside class="ceo-history"><details id="ceo-history" ${matchMedia('(min-width:701px)').matches?'open':''}><summary>Conversations <span>⌄</span></summary><button class="ceo-new" data-ceo-new="true" ${ceoSending?'disabled':''}><span>＋</span> New chat</button><h2>Conversations</h2><div class="ceo-history-list">${chats.map(c=>`<button class="ceo-history-item ${c.id===ceoConversationId?'selected':''}" data-ceo-conversation="${esc(c.id)}" title="${esc(c.title)}" ${ceoSending?'disabled':''}><span>${esc(c.title)}<i class="ceo-unread-dot" aria-hidden="true" hidden></i></span><small>${c.status==='Waiting for your answer'?'● Waiting for you':date(c.updated_at)}</small></button>`).join('') || '<p class="hint">Your conversations will appear here.</p>'}</div>${ceoThread.truncated?'<p class="hint">Recent history is shown. Older work is on the task board.</p>':''}</details><div class="ceo-history-foot"><span>YOUR BRAND</span><p>${esc(state.label)}</p>${state.path?`<button class="text-button" data-artifact="${esc(state.path)}">View strategy ↗</button>`:''}</div></aside>
    <section class="ceo-chat-main" aria-label="CEO chat"><header class="ceo-chat-header"><div>${avatar('brand-ceo')}<div><h1>Brand CEO</h1><p>Your personal brand partner</p></div></div><div class="ceo-chat-tools"><button class="text-button" data-agent="brand-ceo">Live chat ↗</button><button class="icon-button" id="ceo-refresh" aria-label="Refresh conversation">↻</button></div></header>
    <details class="ceo-activity" id="ceo-activity"><summary><span class="ceo-status ${chat?.busy?'working':''}"></span><span id="ceo-chat-status" role="status">${esc(status)}</span><span>Team activity ⌄</span></summary><div>${chat?.cards.map(t=>`<button data-task="${esc(t.id)}"><span>${esc(names[t.assignee] || t.assignee)}</span><span>${esc(t.title)}</span>${badge(taskState(t))}</button>`).join('') || '<p>Your CEO coordinates the team and brings their questions and results here.</p>'}</div><button class="text-button" data-advanced-brief="true">Advanced task brief ↗</button></details>
    <div id="ceo-messages" class="ceo-messages" data-conversation="${esc(ceoConversationId)}" aria-label="Conversation messages" tabindex="0">${messages.map(m=>`<article class="ceo-chat-message ${m.role}" ${m.pending?'data-pending="true"':''}><div class="ceo-message-label">${m.role==='user'?'You':avatar('brand-ceo')+'Brand CEO'}<time>${date(m.time)}</time>${m.pending?'<span>Sending…</span>':''}</div><div class="ceo-message-content">${m.role==='user'?`<p>${esc(m.body)}</p>`:ceoMarkdown(m.body)}</div></article>`).join('') || '<div class="ceo-chat-welcome"><span>✦</span><h2>What would you like to work on?</h2><p>Build your brand, shape an idea, or plan your next piece of content.</p><button class="secondary" data-ceo-start="discover">Develop my personal brand</button></div>'}</div>
    <div class="ceo-compose-area"><form id="ceo-form"><label class="sr-only" for="ceo-message">Message Brand CEO</label><textarea id="ceo-message" name="body" required maxlength="12000" rows="2" placeholder="${selected?.task.status==='blocked'?'Answer your CEO’s questions…':'Message Brand CEO…'}">${esc(ceoDraft)}</textarea><button class="ceo-send" type="submit" aria-label="Send message" ${disabled?'disabled':''}>↑</button></form><p id="ceo-error" class="form-error" role="alert">${esc(ceoError)}</p>${stale?'<p class="ceo-compose-note">The conversation has moved on. Your draft is preserved. <button class="text-button" data-ceo-latest="true">Reply to the latest message</button></p>':`<p class="ceo-compose-note">${chat && !selected?'Your CEO’s next question or result will appear here.':'Enter to send · Shift + Enter for a new line'} <span>Strategy decisions need your approval.</span></p>`}</div></section></div>`;
}
async function refreshCEO() {
  if (ceoRefreshing) return;
  ceoRefreshing = true;
  try {
    ceoThread = await api('/api/ceo'); ceoError='';
    if (ceoPending?.task_id && ceoThread.tasks.some(d=>d.task.id===ceoPending.task_id && (
        (d.task.body || '').split('\n\nCEO desk operator request.')[0]===ceoPending.body ||
        d.comments.some(c=>c.body.startsWith('Operator answer via CEO desk') && c.body.includes(ceoPending.key))))) ceoPending=null;
  }
  catch(error) { ceoError = error.message; }
  finally { ceoRefreshing=false; if(currentView==='ceo') render(); else updateCEOUnread(); }
}
function updateCEOUnread() {
  if (!ceoThread || !snapshot) return;
  const chats=ceoConversations(ceoThread.tasks,snapshot.board.tasks);
  const counts=new Map(chats.map(chat=>[chat.id,ceoReadState.unreadCount(chat)]));
  const total=[...counts.values()].reduce((sum,count)=>sum+count,0);
  $('#ceo-unread').hidden=!total;
  const label=total?`Brand CEO, ${total} unread ${total===1?'reply':'replies'}`:'Brand CEO';
  $('[data-view="ceo"]').setAttribute('aria-label',label);
  $('[data-view="ceo"]').title=label;
  const status=$('#ceo-unread-status');
  const announcement=total?`${total} unread ${total===1?'reply':'replies'} from Brand CEO`:'';
  if (status.textContent!==announcement) status.textContent=announcement;
  document.querySelectorAll('[data-ceo-conversation]').forEach(button=>{
    const count=counts.get(button.dataset.ceoConversation) || 0;
    button.classList.toggle('unread',Boolean(count));
    button.querySelector('.ceo-unread-dot').hidden=!count;
    button.setAttribute('aria-label',`${button.title}${count?`, ${count} unread ${count===1?'reply':'replies'}`:''}`);
  });
}
function readVisibleCEO() {
  if (currentView!=='ceo' || document.hidden || !document.hasFocus() || document.querySelector('dialog[open]') || !ceoThread || !snapshot) return;
  const messages=$('#ceo-messages');
  if (!messages || messages.scrollHeight-messages.scrollTop-messages.clientHeight>=90) return;
  const chat=ceoConversations(ceoThread.tasks,snapshot.board.tasks).find(c=>c.id===messages.dataset.conversation);
  if (chat) ceoReadState.markRead(chat);
  updateCEOUnread();
}
function goCEO(message='') {
  if (ceoSending) return;
  if (message) {selectCEOConversation('new'); ceoDraft=message; ceoDraftTarget='new'; ceoRequestKey='';}
  location.hash='ceo';
  if(currentView==='ceo') {render(); $('#ceo-message')?.focus();}
}
function selectCEOConversation(id) {
  if (ceoSending) return;
  ceoDrafts.set(ceoConversationId,{body:ceoDraft,key:ceoRequestKey,target:ceoDraftTarget});
  ceoConversationId=id;
  const saved=ceoDrafts.get(id);
  ceoDraft=saved?.body || ''; ceoRequestKey=saved?.key || ''; ceoDraftTarget=saved?.target || '';
  ceoReplyTo=''; ceoError='';
  render();
}
async function sendCEO(form) {
  if (ceoSending) return;
  ceoDraft = new FormData(form).get('body').trim();
  if (!ceoDraft) return;
  const chat=ceoConversations(ceoThread.tasks,snapshot.board.tasks).find(c=>c.id===ceoConversationId);
  if ((chat && !chat.reply) || (ceoDraftTarget && ceoDraftTarget!==ceoCurrentTarget)) return;
  const selected = ceoThread.tasks.find(d=>d.task.id === ceoReplyTo);
  if (!ceoRequestKey) ceoRequestKey=`dashboard-${crypto.randomUUID()}`;
  const payload = {op:selected?.task.status==='blocked'?'ceo_reply':'ceo_message',body:ceoDraft,idempotency_key:ceoRequestKey};
  if(selected) {
    if(payload.op==='ceo_reply') {payload.task_id=selected.task.id; payload.question_key=selected.question_key;}
    else payload.reply_to=selected.task.id;
  }
  ceoPending={conversation:ceoConversationId,body:ceoDraft,time:Date.now()/1000,key:ceoRequestKey};
  ceoSending=true; ceoError=''; render();
  try {
    const result=await api('/api/action',payload);
    ceoPending.task_id=result.task_id || selected?.task.id;
    if (!chat) {ceoConversationId=ceoPending.task_id; ceoPending.conversation=ceoConversationId;}
    ceoDrafts.delete(chat?.id || 'new');
    ceoDraft=''; ceoDraftTarget=''; ceoReplyTo=''; ceoRequestKey='';
    await refresh();
  } catch(error) {ceoError=error.message; ceoPending=null;}
  finally {ceoSending=false; if(currentView==='ceo') render();}
}
function render() {
  if (!snapshot) return;
  const renderers = {ceo:ceoView,overview,board,agents:agentsView,vault:vaultView,skills:skillsView};
  const messages=$('#ceo-messages');
  const textarea=$('#ceo-message');
  const old = messages ? {id:messages.dataset.conversation,top:messages.scrollTop,
    bottom:messages.scrollHeight-messages.scrollTop-messages.clientHeight<90,
    focused:document.activeElement===textarea,start:textarea?.selectionStart,end:textarea?.selectionEnd,
    textareaScroll:textarea?.scrollTop,activity:$('#ceo-activity')?.open,history:$('#ceo-history')?.open} : null;
  $('#view').innerHTML = (snapshot.board.truncated && currentView!=='ceo' ? '<div class="notice">Showing the native tool’s latest 200 cards. Filter by agent or project to inspect older work. Counts reflect this selection.</div>' : '') + renderers[currentView]();
  if (currentView==='ceo' && $('#ceo-messages')) {
    const next=$('#ceo-messages');
    if (old?.id===next.dataset.conversation) {
      $('#ceo-activity').open=old.activity;
      $('#ceo-history').open=old.history;
    }
    resizeCEOInput();
    next.scrollTop=old?.id===next.dataset.conversation && !old.bottom?old.top:next.scrollHeight;
    if (old?.focused) {const input=$('#ceo-message'); input.focus({preventScroll:true}); input.setSelectionRange(old.start,old.end); input.scrollTop=old.textareaScroll;}
  }
  if(ceoSending) document.querySelectorAll('#ceo-form input, #ceo-form textarea, #ceo-form select, #ceo-form button').forEach(input=>input.disabled=true);
  $('#view-description').textContent = currentView==='ceo'?'Your CEO conversation · Persistent native task threads':filters.assignee || filters.tenant ? `Native board selection: ${names[filters.assignee] || 'all agents'} / ${filters.tenant || 'all projects'}` : 'Live from your native Hermes workspace';
  readVisibleCEO();
  updateCEOUnread();
}
function navigate() {
  currentView = Object.hasOwn(views,location.hash.slice(1)) ? location.hash.slice(1) : 'ceo';
  document.body.classList.toggle('view-ceo',currentView==='ceo');
  const [label,title,subtitle] = views[currentView];
  $('#breadcrumb').textContent = label; $('#page-title').textContent = title; $('#page-subtitle').textContent = subtitle;
  document.querySelectorAll('[data-view]').forEach(a=>{a.classList.toggle('selected',a.dataset.view===currentView); if (a.dataset.view===currentView) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current');});
  render();
  if(currentView==='ceo' && snapshot) refreshCEO();
}
function openBrief(id='brand-ceo') {
  if (!snapshot) return toast('Connect to Hermes before submitting work.');
  $('#brief-assignee').innerHTML = snapshot.agents.map(a=>`<option value="${esc(a.id)}">${esc(names[a.id])} · ${esc(a.role)}</option>`).join('');
  $('#brief-assignee').value = id;
  if (!requestKey) requestKey = `dashboard-${crypto.randomUUID()}`;
  $('#brief-error').textContent = '';
  $('#brief-dialog').showModal();
}
function markdown(content) {
  // Untrusted Markdown is displayed with escaped text only; raw HTML never executes.
  return `<div class="markdown">${String(content).split('\n').map(line=>{
    const header = line.match(/^(#{1,4}) (.+)/);
    return header ? `<h${header[1].length}>${esc(header[2])}</h${header[1].length}>` : `<div class="markdown-line">${esc(line) || '&nbsp;'}</div>`;
  }).join('')}</div>`;
}
async function reader(kind, name) {
  const generation = ++readerGeneration;
  const dialog = $('#reader-dialog');
  $('#reader-title').textContent = kind === 'artifact' ? name.split('/').at(-1) : name;
  $('#reader-body').innerHTML = '<div class="loading">Reading document…</div>';
  if (!dialog.open) dialog.showModal();
  try {
    const data = await api(`/api/${kind}?${new URLSearchParams({[kind==='artifact'?'path':'name']:name})}`);
    if (generation !== readerGeneration || !dialog.open) return;
    $('#reader-body').innerHTML = markdown(data.content);
  } catch(error) { if (generation === readerGeneration && dialog.open) $('#reader-body').innerHTML = `<div class="notice error">${esc(error.message)}</div>`; }
}
async function showTask(id) {
  activeTask = id;
  const generation = ++detailGeneration;
  const dialog = $('#detail-dialog');
  $('#detail-title').textContent = 'Task details';
  $('#detail-body').innerHTML = '<div class="loading">Reading the native task and handoff…</div>';
  if (!dialog.open) dialog.showModal();
  try {
    const d = await api(`/api/task?${new URLSearchParams({id})}`);
    if (generation !== detailGeneration || !dialog.open) return;
    const t = d.task;
    $('#detail-title').textContent = t.title;
    const linked = snapshot.artifacts.filter(f=>f.name.startsWith(t.id+'-'));
    const handoffs = (d.runs || []).filter(r=>r.summary || r.error);
    $('#detail-body').innerHTML = `<div class="detail-meta">${badge(taskState(t))}<span>${esc(names[t.assignee] || t.assignee)}</span><code>${esc(t.id)}</code><span>${esc(t.tenant || '')}</span><button class="text-button" id="refresh-task">Refresh ↻</button></div><div class="detail-grid"><div><h3>Brief</h3><div class="brief-text">${esc(t.body || 'No brief recorded.')}</div></div><div class="task-facts"><h3>Task context</h3><dl><dt>Created</dt><dd>${date(t.created_at)}</dd><dt>Started</dt><dd>${date(t.started_at)}</dd><dt>Completed</dt><dd>${date(t.completed_at)}</dd><dt>Workspace</dt><dd>${esc(t.workspace_path || '—')}</dd></dl><h3>Dependencies</h3>${d.parents.length ? d.parents.map(p=>`<button class="dependency" data-task="${esc(p)}">${esc(p)} ↗</button>`).join('') : '<p class="muted">No parent dependencies.</p>'}${d.children.length ? `<h3>Follow-up cards</h3>${d.children.map(p=>`<button class="dependency" data-task="${esc(p)}">${esc(p)} ↗</button>`).join('')}`:''}</div></div>
      <h3>Saved artifacts</h3>${linked.map(artifactRow).join('') || '<p class="muted">No task-ID artifacts saved yet.</p>'}
      <h3>Handoffs & attempts <span class="muted">${(d.runs || []).length}</span></h3>${handoffs.map(r=>`<div class="handoff"><div>${badge(r.status || 'unknown')}<span>${esc(r.profile)} · ${date(r.started_at)}</span></div><p>${esc(r.summary || '')}</p>${r.error?`<p class="form-error">${esc(r.error)}</p>`:''}</div>`).join('') || '<p class="muted">No recorded handoff yet.</p>'}
      <p><button class="secondary" data-agent="${esc(t.assignee)}">Open agent chat & activity ↗</button></p>
      <details><summary>Native events</summary>${(d.events || []).map(e=>`<div class="event"><strong>${esc(e.kind)}</strong><span>${date(e.created_at)}</span><pre>${esc(JSON.stringify(e.payload,null,2))}</pre></div>`).join('')}</details>
      <h3>Operator notes</h3>${(d.comments || []).map(c=>`<div class="comment"><small>${esc(c.author)} · ${date(c.created_at)}</small><p>${esc(c.body)}</p></div>`).join('') || '<p class="muted">Add context or feedback for this task.</p>'}
      <form id="note-form"><label>Note<textarea name="body" required maxlength="4000" rows="3" placeholder="Add supplied facts, clarify the brief, or give feedback."></textarea></label><p class="form-error" id="note-error" role="alert"></p><div class="note-actions"><button class="secondary" type="submit">Add operator note</button>${['blocked','scheduled'].includes(t.status)?'<button class="primary" type="button" id="unblock-task">Unblock for dispatch ↗</button>':''}${t.status==='review'?'<button class="secondary" type="button" id="request-changes">Request changes ↗</button>':''}</div></form>`;
  } catch (error) { if (generation === detailGeneration) $('#detail-body').innerHTML = `<div class="notice error">${esc(error.message)}</div>`; }
}
async function taskAction(op, body) {
  const id = activeTask;
  const buttons = document.querySelectorAll('#note-form button');
  buttons.forEach(b=>b.disabled=true);
  try {
    await api('/api/action',{op,task_id:id,body});
    toast(op==='comment'?'Operator note saved.':op==='unblock'?'Task returned to native dispatch.':'Changes requested.');
    await refresh();
    if (activeTask === id && $('#detail-dialog').open) await showTask(id);
  } catch(error) { const notice=$('#note-error'); if(notice) notice.textContent=error.message; else toast(error.message); }
  finally { buttons.forEach(b=>b.disabled=false); }
}
document.addEventListener('click', (event)=>{
  const target = event.target.closest('button');
  if (!target) return;
  if (target.classList.contains('close-dialog')) target.closest('dialog').close();
  if (target.dataset.task) showTask(target.dataset.task);
  if (target.dataset.artifact) reader('artifact',target.dataset.artifact);
  if (target.dataset.skill) reader('skill',target.dataset.skill);
  if (target.dataset.ceo) {target.closest('dialog')?.close(); goCEO(target.dataset.ceo==='brand-ceo'?'':`Please coordinate ${names[target.dataset.ceo]} to help me with `);}
  if (target.dataset.advancedBrief) openBrief();
  if (target.dataset.ceoStart) goCEO(target.dataset.ceoStart==='discover'?'Help me develop my personal brand strategy. Review what you already know, delegate discovery to Brand Manager, and interview me through this CEO conversation about what is missing.':'I want to refine my personal brand. Review my current strategy and ask me what I want to change or add.');
  if (target.dataset.ceoConversation) selectCEOConversation(target.dataset.ceoConversation);
  if (target.dataset.ceoNew) {selectCEOConversation('new'); $('#ceo-message').focus();}
  if (target.dataset.ceoLatest) {ceoDraftTarget=ceoCurrentTarget; ceoRequestKey=''; render(); $('#ceo-message').focus();}
  if (target.id==='ceo-refresh') refresh();
  if (target.dataset.agent) {target.closest('dialog')?.close(); showAgent(target.dataset.agent);}
  if (target.id==='refresh-task') showTask(activeTask);
  if (target.id==='clear-filters') {filters={assignee:'',tenant:'',query:''}; refresh();}
  if (target.id==='unblock-task') taskAction('unblock');
  if (target.id==='request-changes') {
    const body = $('#note-form textarea').value.trim();
    if (body) taskAction('request_changes',body); else $('#note-error').textContent = 'Describe the changes needed in the note first.';
  }
});
async function showAgent(id) {
  openAgentChat(id);
}
document.addEventListener('input',(event)=>{
  if(event.target.id==='task-search') {filters.query=event.target.value; const start=event.target.selectionStart; render(); $('#task-search').focus(); $('#task-search').setSelectionRange(start,start);}
  if(event.target.id==='vault-search') {const query=event.target.value; const start=event.target.selectionStart; $('#view').innerHTML=vaultView(query); $('#vault-search').focus(); $('#vault-search').setSelectionRange(start,start);}
});
document.addEventListener('change',(event)=>{
  if(event.target.id==='agent-filter') {filters.assignee=event.target.value; refresh();}
  if(event.target.id==='tenant-filter') {filters.tenant=event.target.value; refresh();}
});
document.addEventListener('submit',(event)=>{
  if(event.target.id==='ceo-form') {event.preventDefault(); sendCEO(event.target);}
  if(event.target.id==='note-form') {event.preventDefault(); taskAction('comment',new FormData(event.target).get('body'));}
});
$('#brief-form').addEventListener('submit',async (event)=>{
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));
  data.parents = data.parents.split(/[\s,]+/).filter(Boolean);
  data.op='create'; data.idempotency_key=requestKey;
  $('#submit-brief').disabled=true; $('#submit-brief').textContent='Submitting…';
  try {
    const result=await api('/api/action',data);
    $('#brief-dialog').close(); form.reset(); requestKey='';
    filters={assignee:'',tenant:'',query:''};
    toast(`Brief saved as ${result.task_id}. Hermes will dispatch it.`);
    location.hash='board'; await refresh(); await showTask(result.task_id);
  } catch(error) {$('#brief-error').textContent=error.message;}
  finally {$('#submit-brief').disabled=false; $('#submit-brief').textContent='Send brief ↗';}
});
$('#brief-form').addEventListener('input',()=> { requestKey=`dashboard-${crypto.randomUUID()}`; });
$('#brief-form').addEventListener('change',()=> { requestKey=`dashboard-${crypto.randomUUID()}`; });
$('#refresh').addEventListener('click',refresh);
function resizeCEOInput() {
  const input=$('#ceo-message');
  if(input) {input.style.height='auto'; input.style.height=`${Math.min(160,input.scrollHeight)}px`;}
  const send=$('#ceo-form button[type=submit]');
  if(send) send.disabled=!ceoCanSend || !ceoDraft.trim() || Boolean(ceoDraftTarget && ceoDraftTarget!==ceoCurrentTarget);
}
document.addEventListener('input',(event)=>{if(event.target.id==='ceo-message') {
  ceoDraft=event.target.value; ceoRequestKey='';
  if(!ceoDraft) ceoDraftTarget='';
  else if(!ceoDraftTarget) ceoDraftTarget=ceoCurrentTarget;
  resizeCEOInput();
}});
document.addEventListener('keydown',(event)=>{
  if(event.target.id==='ceo-message' && event.key==='Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if(!$('#ceo-form button[type=submit]').disabled) $('#ceo-form').requestSubmit();
  }
});
$('#new-task').addEventListener('click',()=>goCEO());
window.addEventListener('hashchange',navigate);
$('#detail-dialog').addEventListener('close',()=>{detailGeneration++; readVisibleCEO();});
$('#reader-dialog').addEventListener('close',()=>{readerGeneration++; readVisibleCEO();});
$('#chat-dialog').addEventListener('close',readVisibleCEO);
document.addEventListener('scroll',event=>{if(event.target.id==='ceo-messages') readVisibleCEO();},true);
window.addEventListener('focus',readVisibleCEO);
document.addEventListener('visibilitychange',()=>{if(!document.hidden && snapshot) refreshCEO();});
window.addEventListener('storage',event=>{
  if(event.key===ceoReadState.key || event.key===null) {
    try {ceoReadState=new CEOReadState(localStorage);} catch {return;}
    readVisibleCEO(); updateCEOUnread();
  }
});
$('#clock').textContent=new Intl.DateTimeFormat('en-SG',{weekday:'short',day:'numeric',month:'short',timeZone:'Asia/Singapore'}).format(new Date());
navigate();
(async ()=>{
  try {token=(await api('/api/bootstrap')).token; await refresh();}
  catch(error) {$('#connection-error').textContent=error.message; $('#connection-error').hidden=false;}
})();
setInterval(()=>{if(!document.hidden && !document.querySelector('dialog[open]') && !document.activeElement?.matches('input,textarea,select')) refresh();},15000);
setInterval(()=>{if(currentView==='ceo' && !document.hidden && snapshot && !ceoSending && !document.querySelector('dialog[open]')) refreshCEO();},3000);
setInterval(()=>{if((currentView!=='ceo' || document.querySelector('dialog[open]')) && !document.hidden && snapshot && !ceoSending) refreshCEO();},15000);
