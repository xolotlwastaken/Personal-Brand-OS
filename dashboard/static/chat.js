'use strict';
let agentChat = null;
let chatGeneration = 0;
let chatStream = null;
let chatTimer = null;
const directChats = new Map();

function stopChatView() {
  chatGeneration++;
  chatStream?.close(); chatStream = null;
  clearInterval(chatTimer); chatTimer = null;
}
$('#chat-dialog').addEventListener('close', stopChatView);

function chatError(message) {
  if ($('#chat-error')) $('#chat-error').textContent = message;
}
function chatStatus(message) {
  if ($('#chat-status')) $('#chat-status').textContent = message;
}
function isChatVisible(state) { return agentChat === state && $('#chat-dialog').open; }

function sessionButtons(state) {
  return state.sessions.map(s=>`<button type="button" class="chat-session ${state.storedId===s.id?'selected':''}" data-conversation="${esc(s.id)}"><strong>${esc(s.title || 'Untitled conversation')}</strong><small>${s.source==='kanban'?'Task run':s.source==='api_server'?'Direct chat':'Recorded chat'} · ${date(s.started_at)}</small></button>`).join('') || '<p class="muted">No recorded conversations yet.</p>';
}
function drawChatShell(state) {
  const agent = snapshot.agents.find(a=>a.id===state.profile);
  $('#chat-body').innerHTML = `<div class="chat-agent-summary">${avatar(state.profile)}<div><strong>${esc(agent.role)}</strong><p>${esc(agent.description)}</p></div><button class="secondary" data-ceo="${esc(state.profile)}">Ask CEO to coordinate ↗</button></div>
    <div class="chat-layout"><aside class="chat-sidebar"><button id="chat-new" class="primary" type="button">New direct chat ↗</button><p class="hint">Your CEO remains your main contact. Direct specialist chats are optional.</p><h3>Conversations</h3><div id="chat-sessions">${sessionButtons(state)}</div><details class="chat-profile"><summary>Skills & assigned tasks</summary><div class="skill-tags">${agent.skills.map(s=>`<button data-skill="${esc(s)}">${esc(s)}</button>`).join('')}</div>${snapshot.board.tasks.filter(t=>t.assignee===state.profile).slice(0,8).map(taskRow).join('') || '<p class="muted">No assigned tasks.</p>'}</details></aside>
    <div class="chat-main"><div class="chat-toolbar"><strong id="chat-conversation-title">Choose a conversation</strong><span id="chat-status" role="status">Loading…</span></div><div id="chat-transcript" class="chat-transcript" aria-label="Agent transcript" tabindex="0"></div><p id="chat-error" class="form-error" role="alert"></p><div id="chat-controls"></div></div></div>`;
  $('#chat-new').addEventListener('click',()=>startDirectChat(state));
  $('#chat-sessions').addEventListener('click',event=>{
    const button=event.target.closest('[data-conversation]');
    if (button) viewConversation(state,button.dataset.conversation);
  });
  drawTranscript(state, true); drawChatControls(state);
}

function drawTranscript(state, forceBottom=false) {
  if (!isChatVisible(state)) return;
  const el=$('#chat-transcript');
  const atBottom=forceBottom || el.scrollHeight-el.scrollTop-el.clientHeight<90;
  const opened=new Set([...el.querySelectorAll('details[open]')].map(d=>d.dataset.message));
  el.innerHTML = state.messages.map((m,i)=>{
    if (m.role==='tool') return `<details class="chat-tool" data-message="${i}" ${opened.has(String(i))?'open':''}><summary><span>${m.live?'◌':'✓'}</span> ${esc(m.tool_name || m.name || 'Tool')} ${m.live?'· running':''}</summary>${m.args?`<h4>Arguments</h4><pre>${esc(typeof m.args==='string'?m.args:JSON.stringify(m.args,null,2))}</pre>`:''}<h4>Result</h4><pre>${esc(m.content || 'Waiting for result…')}</pre></details>`;
    const label=m.role==='user'?(state.selectedSource==='kanban'?'Input / worker brief':'You'):names[state.profile];
    return `<article class="chat-bubble ${m.role}"><div class="chat-bubble-meta"><strong>${esc(label)}</strong>${m.timestamp?`<small>${date(m.timestamp)}</small>`:''}${m.live?'<span class="chat-live">Streaming</span>':''}</div><div class="chat-text">${esc(m.content || (m.live?'Waiting for response…':''))}</div>${m.tool_calls?`<details><summary>Tool calls</summary><pre>${esc(m.tool_calls)}</pre></details>`:''}</article>`;
  }).join('') || '<div class="empty">Open a recorded conversation to inspect it, or start a direct chat with this agent.</div>';
  if (atBottom) el.scrollTop=el.scrollHeight;
}

function drawChatControls(state) {
  if (!isChatVisible(state)) return;
  const el=$('#chat-controls');
  if(state.mode==='direct') {
    el.innerHTML=`<form id="chat-form"><label for="chat-message">Message ${esc(names[state.profile])}</label><div class="chat-compose"><textarea id="chat-message" required maxlength="12000" rows="3" placeholder="${state.profile==='brand-ceo'?'Help me develop my brand strategy. Review my notes and interview me about what is missing.':'Ask this specialist a question…'}">${esc(state.draft || '')}</textarea><button id="chat-send" class="primary" type="submit" ${state.running?'disabled':''}>${state.running?'Responding…':'Send ↗'}</button></div><p class="hint">Native persistent chat · Replies stream as they arrive. Work delegation stays on the task board.</p></form>`;
    $('#chat-message').addEventListener('input',event=>state.draft=event.target.value);
    $('#chat-form').addEventListener('submit',event=>{event.preventDefault();sendChatMessage(state);});
  } else {
    el.innerHTML=`<div class="chat-watch-note"><p>Recorded messages and tool calls update every 2 seconds. Worker transcripts appear when Hermes saves them.</p>${state.selectedSource==='api_server'?'<button id="chat-resume" class="primary">Resume direct chat ↗</button>':'<button id="chat-separate" class="secondary">Chat with this agent ↗</button>'}<p class="hint">A direct chat is a separate conversation from an assigned task.</p></div>`;
    $('#chat-resume')?.addEventListener('click',()=>startDirectChat(state,state.storedId));
    $('#chat-separate')?.addEventListener('click',()=>startDirectChat(state));
  }
}

async function openAgentChat(profile) {
  if (!names[profile]) return;
  stopChatView();
  const generation=chatGeneration;
  const state={profile,sessions:[],messages:[],mode:'watch',storedId:'',running:false};
  agentChat=state;
  $('#chat-title').textContent=names[profile];
  if(!$('#chat-dialog').open) $('#chat-dialog').showModal();
  drawChatShell(state);
  try {
    state.sessions=(await api(`/api/conversations?${new URLSearchParams({profile})}`)).sessions;
    if (generation!==chatGeneration) return;
    $('#chat-sessions').innerHTML=sessionButtons(state);
    const cached=directChats.get(profile);
    if(cached) {
      cached.sessions=state.sessions; agentChat=cached;
      drawChatShell(cached); connectChatStream(cached);
      const status=await api(`/api/chat/state?${new URLSearchParams({profile,session:cached.runtimeId})}`);
      if(isChatVisible(cached)) {cached.running=status.running;drawChatControls(cached);}
    } else if(state.sessions.length) await viewConversation(state,state.sessions[0].id);
    else chatStatus('Ready for a direct chat');
  } catch(error) {if(generation===chatGeneration) chatError(error.message);}
}

async function viewConversation(state,storedId) {
  stopChatView(); const generation=chatGeneration;
  state={profile:state.profile,sessions:state.sessions,messages:[],mode:'watch',storedId,running:false};
  agentChat=state;
  state.selectedSource=state.sessions.find(s=>s.id===storedId)?.source;
  drawChatShell(state); chatStatus('Loading transcript…');
  let polling=false;
  async function load() {
    if(polling || generation!==chatGeneration || document.hidden) return;
    polling=true;
    try {
      const data=await api(`/api/conversation?${new URLSearchParams({profile:state.profile,id:storedId})}`);
      if(generation!==chatGeneration) return;
      state.messages=data.messages;
      state.selectedSource=data.session.source;
      $('#chat-conversation-title').textContent=data.session.title || 'Recorded conversation';
      drawTranscript(state); chatError('');
      chatStatus(data.truncated?'Latest 200 saved messages':'Saved transcript · updated '+new Date().toLocaleTimeString());
    } catch(error) {if(generation===chatGeneration) chatError(error.message);}
    finally {polling=false;}
  }
  await load();
  if(generation!==chatGeneration) return;
  drawChatControls(state);
  chatTimer=setInterval(load,2000);
}

async function startDirectChat(state,storedId='') {
  if (!isChatVisible(state)) return;
  const generation=chatGeneration;
  $('#chat-new').disabled=true;
  $('#chat-resume')?.setAttribute('disabled','');
  $('#chat-separate')?.setAttribute('disabled','');
  chatStatus('Opening native conversation…');chatError('');
  try {
    const opened=await api('/api/action',{op:'chat_open',profile:state.profile,session_id:storedId});
    const direct={profile:state.profile,sessions:state.sessions,messages:opened.messages,
      mode:'direct',storedId:opened.stored_session_id,runtimeId:opened.session_id,
      lastId:opened.sequence,running:opened.running,draft:'',active:null};
    if(storedId) direct.messages=(await api(`/api/conversation?${new URLSearchParams({profile:state.profile,id:storedId})}`)).messages;
    if(opened.inflight?.assistant && opened.running) {
      direct.active={role:'assistant',content:opened.inflight.assistant,live:true};
      direct.messages.push(direct.active);
    }
    directChats.set(state.profile,direct);
    if(generation!==chatGeneration) return;
    stopChatView(); agentChat=direct;
    drawChatShell(direct); connectChatStream(direct);
    $('#chat-conversation-title').textContent='Direct chat · '+names[direct.profile];
    $('#chat-message').focus();
  } catch(error) {if(generation===chatGeneration) {chatError(error.message);chatStatus('Could not open chat');}}
  finally {if(isChatVisible(state)) {$('#chat-new').disabled=false;drawChatControls(state);}}
}

function connectChatStream(state) {
  chatStream?.close();
  const stream=new EventSource(`/api/chat/events?${new URLSearchParams({profile:state.profile,session:state.runtimeId,after:state.lastId})}`);
  chatStream=stream;
  $('#chat-conversation-title').textContent='Direct chat · '+names[state.profile];
  stream.onopen=()=>{if(isChatVisible(state)) {chatStatus(state.running?'Responding · live token stream':'Connected · live token stream');chatError('');}};
  stream.onerror=()=>{if(isChatVisible(state)) chatStatus('Stream reconnecting…');};
  stream.onmessage=event=>{
    if(!isChatVisible(state)) return;
    const frame=JSON.parse(event.data);
    if(frame.id<=state.lastId) return;
    state.lastId=frame.id;
    const p=frame.payload || {};
    if(frame.type==='stream.reset') {stream.close();chatError('Stream history expired. Reopen this saved chat to recover its transcript.');return;}
    if(frame.type==='message.start') {state.running=true;chatStatus('Responding · live token stream');}
    if(frame.type==='message.delta') {
      if(!state.active) {state.active={role:'assistant',content:'',live:true};state.messages.push(state.active);}
      state.active.content+=p.text || '';
    }
    if(frame.type==='message.interim') {
      if(!p.already_streamed && p.text) state.messages.push({role:'assistant',content:p.text});
      if(state.active) state.active.live=false;
      state.active=null;
    }
    if(frame.type==='tool.start') {
      if(state.active) state.active.live=false;state.active=null;
      state.messages.push({role:'tool',tool_name:p.name,tool_call_id:p.tool_id,args:p.args,content:'',live:true});
      chatStatus('Using '+p.name+'…');
    }
    if(frame.type==='tool.complete') {
      const tool=[...state.messages].reverse().find(m=>m.role==='tool' && m.tool_call_id===p.tool_id);
      const result=typeof p.result==='string'?p.result:JSON.stringify(p.result,null,2);
      if(tool) {tool.content=result;tool.live=false;} else state.messages.push({role:'tool',tool_name:p.name,args:p.args,content:result});
    }
    if(frame.type==='message.complete') {
      if(state.active) {if(p.text) state.active.content=p.text;state.active.live=false;}
      else if(p.text && !p.response_previewed) state.messages.push({role:'assistant',content:p.text});
      state.active=null;state.running=false;
      chatStatus(p.status==='error'?'Response failed · see transcript':'Connected · response complete');
      if(p.warning) chatError(p.warning);
      drawChatControls(state);
    }
    if(frame.type==='error') {state.running=false;stream.close();chatError(p.message || p.text || 'Native chat failed');drawChatControls(state);}
    drawTranscript(state);
  };
}

async function sendChatMessage(state) {
  if(state.running || !isChatVisible(state)) return;
  const body=state.draft.trim(); if(!body) return;
  const input={role:'user',content:body,timestamp:Date.now()/1000};
  state.messages.push(input);state.running=true;
  $('#chat-send').disabled=true;$('#chat-send').textContent='Sending…';
  chatError('');chatStatus('Sending to '+names[state.profile]+'…');drawTranscript(state,true);
  try {
    await api('/api/action',{op:'chat_send',profile:state.profile,session_id:state.runtimeId,body});
    state.draft='';
    if(isChatVisible(state)) {$('#chat-message').value='';$('#chat-send').textContent=state.running?'Responding…':'Send ↗';chatStatus(state.running?'Responding · waiting for first token':'Response complete');}
  } catch(error) {
    state.running=false;state.messages=state.messages.filter(m=>m!==input);
    if(isChatVisible(state)) {chatError(error.message);drawTranscript(state);drawChatControls(state);}
  }
}
