'use strict';

// Browser presentation state only; no task state or message text is stored here.
class CEOReadState {
  constructor(storage) {
    this.storage=storage;
    this.key='brand-os-ceo-read-v1';
    this.seen=new Map();
    try {
      const saved=JSON.parse(storage?.getItem(this.key) || '{}');
      if (saved && typeof saved==='object' && !Array.isArray(saved)) {
        for (const [id,messages] of Object.entries(saved)) {
          if (Array.isArray(messages)) this.seen.set(id,new Set(messages.filter(m=>typeof m==='string')));
        }
      }
    } catch { /* Read tracking still works when browser storage is unavailable. */ }
  }
  replyIds(chat) {
    return new Set(chat.messages.filter(m=>m.role==='assistant').map(m=>m.id));
  }
  unreadCount(chat) {
    const seen=this.seen.get(chat.id);
    return [...this.replyIds(chat)].filter(id=>!seen?.has(id)).length;
  }
  markRead(chat) {
    const seen=this.seen.get(chat.id) || new Set();
    const replies=this.replyIds(chat);
    if (![...replies].some(id=>!seen.has(id))) return false;
    this.seen.set(chat.id,new Set([...seen,...replies]));
    try {this.storage?.setItem(this.key,JSON.stringify(Object.fromEntries([...this.seen].map(([id,messages])=>[id,[...messages]]))));}
    catch { /* A full or disabled store must not stop the conversation. */ }
    return true;
  }
}

// Presentation only: native cards, creation provenance and dependencies remain
// the authoritative conversation history and execution state.
function ceoConversations(entries, board) {
  // Warm dashboard adapters may predate recovery metadata. Native card bodies
  // carry the same observation provenance, so open dashboards need no restart.
  entries = entries.map(d=>{
    const first=(d.task.body || '').split('\n')[0];
    if (!first.startsWith('Brand OS recovery: ')) return d;
    try {
      const context=JSON.parse(first.slice('Brand OS recovery: '.length));
      const valid=id=>typeof id==='string' && /^t_[a-zA-Z0-9]+$/.test(id);
      return {...d,recovery_origin_task_id:d.recovery_origin_task_id || (valid(context?.origin_task_id)?context.origin_task_id:null),
        recovery_source_task_id:d.recovery_source_task_id || (valid(context?.source_task_id)?context.source_task_id:null)};
    } catch {return d;}
  });
  const compare = (a,b)=>(a.created_at || 0)-(b.created_at || 0) || a.id.localeCompare(b.id);
  const nodes = new Map((board || []).map(t=>[t.id,{...t,parents:[...(t.parents || [])]}]));
  for (const d of entries) nodes.set(d.task.id,{...d.task,parents:[...(d.parents || []),...(d.creator_task_id?[d.creator_task_id]:[]),...(d.recovery_origin_task_id?[d.recovery_origin_task_id]:[])]});
  for (const d of entries) for (const id of d.children || []) {
    if (!nodes.has(id)) nodes.set(id,{id,parents:[]});
    nodes.get(id).parents.push(d.task.id);
  }
  const ceos = new Map(entries.map(d=>[d.task.id,d]));
  function root(id) {
    const visited = new Set();
    const pending = [id];
    while (pending.length && visited.size < 500) {
      const next = pending.pop();
      if (visited.has(next)) continue;
      visited.add(next);
      pending.push(...(nodes.get(next)?.parents || []));
    }
    const ancestors = [...visited].filter(t=>ceos.has(t)).map(t=>ceos.get(t).task).sort(compare);
    return ancestors[0]?.id;
  }
  const groups = new Map();
  for (const d of entries) {
    const id = root(d.task.id);
    if (!groups.has(id)) groups.set(id,{id,entries:[],cards:[],messages:[]});
    groups.get(id).entries.push(d);
  }
  for (const t of nodes.values()) {
    const id = root(t.id);
    if (groups.has(id) && t.assignee) groups.get(id).cards.push(t);
  }
  for (const chat of groups.values()) {
    // A specialist may be commissioned without depending on the planning CEO
    // card. Include producers of this chat's relays in its activity display.
    const producers=chat.entries.flatMap(d=>[...(d.parents || []),...(d.recovery_source_task_id?[d.recovery_source_task_id]:[])]);
    const seen=new Set(chat.cards.map(t=>t.id));
    while (producers.length && seen.size<500) {
      const id=producers.pop();
      if (seen.has(id) || ceos.has(id)) continue;
      seen.add(id);
      const task=nodes.get(id);
      if (task?.assignee) {chat.cards.push(task); producers.push(...(task.parents || []));}
    }
    chat.entries.sort((a,b)=>compare(a.task,b.task));
    const first = ceos.get(chat.id).task;
    chat.title = (first.title || 'Conversation').replace(/^(?:CEO request:|Continue CEO conversation:)\s*/,'');
    chat.updated_at = Math.max(...chat.entries.map(d=>d.task.completed_at || d.task.started_at || d.task.created_at || 0));
    for (const d of chat.entries) {
      const t = d.task;
      if ((t.body || '').includes('\n\nCEO desk operator request.')) {
        chat.messages.push({id:t.id,task_id:t.id,role:'user',body:t.body.split('\n\nCEO desk operator request.')[0],time:t.created_at});
      }
      const comments = (d.comments || []).filter(c=>c.body.startsWith('CEO to you:') || c.body.startsWith('Operator answer via CEO desk'));
      comments.forEach((c,i)=>{
        const assistant = c.body.startsWith('CEO to you:');
        chat.messages.push({id:`${t.id}-${i}`,task_id:t.id,role:assistant?'assistant':'user',
          body:assistant?c.body.slice('CEO to you:'.length).trim():c.body.split('\n\n').slice(1).join('\n\n'),
          time:c.created_at});
      });
      if (d===chat.entries.at(-1) && t.status==='done' && !(d.children || []).length && !comments.some(c=>c.body.startsWith('CEO to you:'))) {
        const handoff = [...(d.runs || [])].reverse().find(r=>r.summary);
        if (handoff) chat.messages.push({id:`${t.id}-result`,task_id:t.id,role:'assistant',body:handoff.summary,time:t.completed_at || t.created_at});
      }
    }
    chat.messages.sort((a,b)=>(a.time || 0)-(b.time || 0));
    const latest = chat.entries.at(-1);
    const outstanding = chat.cards.filter(t=>!['done','archived'].includes(t.status));
    const waiting = [...chat.entries].reverse().find(d=>d.task.status==='blocked' && d.question_kind==='needs_input' && !d.task.current_run_id);
    const working = outstanding.find(t=>t.current_run_id);
    chat.reply = waiting || (!outstanding.length && latest.task.status==='done' ? latest : null);
    const labels = {'brand-ceo':'Brand CEO','brand-manager':'Brand Manager','reference-builder':'Reference Builder','hook-writer':'Hook Writer','script-writer':'Script Writer','video-editor':'Video Editor','publisher':'Publisher'};
    chat.status = waiting ? 'Waiting for your answer' : working ? `${labels[working.assignee] || 'Your team'} is working` : outstanding.some(t=>['blocked','triage','review'].includes(t.status)) ? 'Needs your attention' : outstanding.length ? 'Your team is working on this' : 'Ready to continue';
    chat.busy = !chat.reply && outstanding.some(t=>!['blocked','triage','review'].includes(t.status) || t.current_run_id);
  }
  return [...groups.values()].sort((a,b)=>b.updated_at-a.updated_at || a.id.localeCompare(b.id));
}

function ceoMarkdown(text) {
  const escape = value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const inline = value=>value.split(/(`[^`\n]+`)/g).map(part=>part.startsWith('`') && part.endsWith('`')?
    `<code>${escape(part.slice(1,-1))}</code>`:escape(part)
      .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*]+)\*(?!\*)/g,'$1<em>$2</em>')).join('');
  const lines = String(text || '').split('\n');
  const blocks = []; let paragraph=[]; let list=[]; let listType=''; let code=null;
  function flush() {
    if (paragraph.length) blocks.push(`<p>${paragraph.map(inline).join('<br>')}</p>`);
    if (list.length) blocks.push(`<${listType}>${list.map(line=>`<li>${inline(line)}</li>`).join('')}</${listType}>`);
    paragraph=[]; list=[]; listType='';
  }
  for (const line of lines) {
    if (line.trim().startsWith('```')) {
      flush();
      if (code!==null) {blocks.push(`<pre><code>${escape(code.join('\n'))}</code></pre>`); code=null;}
      else code=[];
      continue;
    }
    if (code!==null) {code.push(line); continue;}
    const heading=line.match(/^#{1,6}\s+(.+)/);
    const bullet=line.match(/^\s*([-*]|\d+[.)])\s+(.+)/);
    if (!line.trim()) {flush(); continue;}
    if (heading) {flush(); blocks.push(`<h3>${inline(heading[1])}</h3>`); continue;}
    if (/^---+$/.test(line.trim())) {flush(); blocks.push('<hr>'); continue;}
    if (line.startsWith('>')) {flush(); blocks.push(`<blockquote>${inline(line.replace(/^>\s?/,''))}</blockquote>`); continue;}
    if (bullet) {
      const type=/\d/.test(bullet[1])?'ol':'ul';
      if (paragraph.length || (listType && listType!==type)) flush();
      listType=type; list.push(bullet[2]); continue;
    }
    if (list.length) flush();
    paragraph.push(line);
  }
  flush();
  if (code!==null) blocks.push(`<pre><code>${escape(code.join('\n'))}</code></pre>`);
  return blocks.join('');
}

if (typeof module !== 'undefined') module.exports={ceoConversations,ceoMarkdown,CEOReadState};
