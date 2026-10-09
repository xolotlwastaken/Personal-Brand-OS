"""Synthetic CEO chat journeys. No production writes or model calls."""
import subprocess
import unittest


class CEOPageTests(unittest.TestCase):
    def test_unread_indicator_visibility_and_read_gates(self):
        subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {CEOReadState,ceoConversations}=require('./dashboard/static/ceo-page.js');
const element=()=>({hidden:true,textContent:'',title:'',setAttribute(key,value){this[key]=value;}});
const nav=element(),dot=element(),status=element();
const history=['t_synthetic1','t_synthetic2'].map(id=>({...element(),title:id,dataset:{ceoConversation:id},
  classList:{toggle(){}},dot:element(),querySelector(){return this.dot;}}));
const messages={dataset:{conversation:'t_synthetic1'},scrollHeight:1000,scrollTop:800,clientHeight:200};
const elements={'#ceo-unread':dot,'[data-view="ceo"]':nav,'#ceo-unread-status':status,'#ceo-messages':messages};
let focused=true,dialog=false;
const document={hidden:false,hasFocus:()=>focused,
  querySelector:selector=>selector==='dialog[open]'?dialog:elements[selector],
  querySelectorAll:()=>history};
const entries=[1,2].map(i=>({task:{id:`t_synthetic${i}`,title:'Synthetic conversation',assignee:'brand-ceo',status:'done',created_at:i},
  parents:[],children:[],comments:[{body:'CEO to you: Synthetic reply',created_at:i}],runs:[]}));
const context=vm.createContext({CEOReadState,ceoConversations,document,localStorage:{getItem:()=>null,setItem(){}},console});
const app=fs.readFileSync('dashboard/static/app.js','utf8');
vm.runInContext(app.slice(0,app.indexOf('function goCEO(')),context);
vm.runInContext(`snapshot={board:{tasks:[]}};ceoThread={tasks:${JSON.stringify(entries)}};currentView='overview';updateCEOUnread();`,context);
assert.equal(dot.hidden,false,'Replies show a dot while browsing other pages');
assert.equal(nav['aria-label'],'Brand CEO, 2 unread replies');
assert(history.every(button=>!button.dot.hidden));
vm.runInContext("readVisibleCEO()",context);
assert.equal(dot.hidden,false,'Another page cannot mark replies read');
vm.runInContext("currentView='ceo'",context);
focused=false; vm.runInContext('readVisibleCEO()',context);
assert.equal(history[0].dot.hidden,false,'An unfocused window cannot mark replies read');
focused=true; document.hidden=true; vm.runInContext('readVisibleCEO()',context);
assert.equal(history[0].dot.hidden,false,'A background tab cannot mark replies read');
document.hidden=false; dialog=true; vm.runInContext('readVisibleCEO()',context);
assert.equal(history[0].dot.hidden,false,'An open dialog keeps replies unread');
dialog=false; messages.scrollTop=0; vm.runInContext('readVisibleCEO()',context);
assert.equal(history[0].dot.hidden,false,'Reading older messages keeps new replies unread');
messages.scrollTop=800; vm.runInContext('readVisibleCEO()',context);
assert.equal(history[0].dot.hidden,true);
assert.equal(history[1].dot.hidden,false,'Only the visible conversation is cleared');
assert.equal(nav['aria-label'],'Brand CEO, 1 unread reply');
messages.dataset.conversation='t_synthetic2'; vm.runInContext('readVisibleCEO()',context);
assert.equal(dot.hidden,true,'Navigation dot clears after all replies are read');
assert.equal(status.textContent,'');
assert.equal(nav['aria-label'],'Brand CEO');
'''], check=True)

    def test_unread_replies_clear_per_conversation_and_survive_reload(self):
        subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const {CEOReadState} = require('./dashboard/static/ceo-page.js');
const saved=new Map();
const storage={getItem:key=>saved.get(key) || null,setItem:(key,value)=>saved.set(key,value)};
const replies=new CEOReadState(storage);
const a={id:'t_chatA',messages:[{id:'user1',role:'user',body:'Synthetic request'},{id:'reply1',role:'assistant',body:'Synthetic reply',time:1}]};
const b={id:'t_chatB',messages:[{id:'replyB',role:'assistant',body:'Synthetic question',time:1}]};
assert.equal(replies.unreadCount(a),1,'Only CEO replies are unread');
assert.equal(replies.unreadCount(b),1);
assert(replies.markRead(a));
assert.equal(replies.unreadCount(a),0);
assert.equal(replies.unreadCount(b),1,'Opening one conversation does not clear another');
assert.equal(replies.markRead(a),false,'Polling unchanged replies must not rewrite read state');
let restored=new CEOReadState(storage);
assert.equal(restored.unreadCount(a),0,'Read state survives reload');
a.messages.push({id:'user2',role:'user',body:'Synthetic answer',time:2});
assert.equal(restored.unreadCount(a),0,'User messages never notify');
a.messages.push({id:'reply2',role:'assistant',body:'Synthetic recovery update',time:1});
assert.equal(restored.unreadCount(a),1,'Same-second replies must still notify');
restored.markRead(a);
assert.equal(restored.unreadCount(a),0);
assert(![...saved.values()].some(value=>value.includes('Synthetic')),'Store message IDs, not private message text');
const broken={getItem:()=>{throw Error('disabled')},setItem:()=>{throw Error('full')}};
restored=new CEOReadState(broken);
assert.equal(restored.unreadCount(b),1);
restored.markRead(b);
assert.equal(restored.unreadCount(b),0,'Unavailable storage still supports in-memory notifications');
const corrupt=new CEOReadState({getItem:()=>'{bad json',setItem:()=>{}});
assert.equal(corrupt.unreadCount(b),1,'Invalid saved state cannot break the dashboard');
assert.equal(replies.unreadCount({id:'empty',messages:[]}),0);
'''], check=True)

    def test_failed_specialist_recovery_stays_in_its_conversation(self):
        subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const {ceoConversations} = require('./dashboard/static/ceo-page.js');
const root={task:{id:'t_plan',assignee:'brand-ceo',status:'done',created_at:1},parents:[],children:[],comments:[]};
const followup={task:{id:'t_follow',assignee:'brand-ceo',status:'todo',created_at:3},creator_task_id:'t_plan',parents:['t_worker'],children:[],comments:[]};
const recovery={task:{id:'t_recovery',assignee:'brand-ceo',status:'blocked',created_at:5},parents:[],children:[],comments:[{body:'CEO to you: Synthetic failure; provide the missing evidence.',created_at:6}],recovery_origin_task_id:'t_plan',recovery_source_task_id:'t_worker',question_kind:'needs_input'};
const worker={id:'t_worker',assignee:'brand-manager',status:'blocked',created_at:2,parents:[]};
const chats=ceoConversations([root,followup,recovery],[worker]);
assert.equal(chats.length,1,'Independent recovery must stay in the original conversation');
assert.equal(chats[0].reply.task.id,'t_recovery');
assert.equal(chats[0].status,'Waiting for your answer');
assert.equal(chats[0].busy,false,'An unresolved producing dependency cannot hide the human reply');
assert(chats[0].messages.some(m=>m.body.includes('Synthetic failure')));
assert(chats[0].cards.some(t=>t.id==='t_worker'));
const oldAdapter={...recovery,task:{...recovery.task,body:'Brand OS recovery: '+JSON.stringify({origin_task_id:'t_plan',source_task_id:'t_worker'})}};
delete oldAdapter.recovery_origin_task_id; delete oldAdapter.recovery_source_task_id;
assert.equal(ceoConversations([root,followup,oldAdapter],[worker]).length,1,'Open dashboards tolerate warm adapters');
oldAdapter.task.body='Brand OS recovery: invalid json';
assert.equal(ceoConversations([oldAdapter],[]).length,1,'Malformed provenance cannot break the page');
'''], check=True)

    def test_linked_discovery_history_answer_routing_and_untrusted_markdown(self):
        subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const {ceoConversations, ceoMarkdown} = require('./dashboard/static/ceo-page.js');
const marker='\n\nCEO desk operator request.';
const card=(id, time, status='done', extra={})=>({task:{id,created_at:time,status,assignee:'brand-ceo',title:'CEO request: Synthetic discovery',body:'Synthetic request'+marker,...extra},parents:[],children:[],comments:[],runs:[]});
const root=card('t_root',1);
const first=card('t_first',3,'done',{body:'Internal specialist relay'});
first.creator_task_id='t_root'; first.parents=['t_manager'];
first.comments=[{body:'CEO to you:\n**First question**',created_at:4},{body:'Operator answer via CEO desk [synthetic-key]\n\nSynthetic answer',created_at:5}];
const next=card('t_next',7,'blocked',{body:'Internal specialist relay'});
next.creator_task_id='t_first'; next.parents=['t_manager2']; next.question_kind='needs_input'; next.question_key='q2';
next.comments=[{body:'CEO to you:\nSecond question',created_at:8}];
const separate=card('t_other',6);
const chats=ceoConversations([next,root,separate,first],[]);
assert.equal(chats.length,2,'Separate requests must stay separate');
const chat=chats.find(c=>c.id==='t_root');
assert.deepEqual(chat.messages.map(m=>m.body),['Synthetic request','**First question**','Synthetic answer','Second question']);
assert.deepEqual(chat.messages.map(m=>m.role),['user','assistant','user','assistant']);
assert.equal(chat.reply.task.id,'t_next','Send answers latest pending interview question');
assert.equal(chat.status,'Waiting for your answer');
next.task.current_run_id=99;
assert.equal(ceoConversations([root,first,next],[])[0].reply,null,'Do not send until blocked worker has released ownership');
next.task.current_run_id=null; next.task.status='done';
assert.equal(ceoConversations([root,first,next],[])[0].reply.task.id,'t_next','Continue latest completed CEO card');
const worker={id:'t_manager3',assignee:'brand-manager',status:'running',current_run_id:12,parents:['t_next'],created_at:9};
assert.equal(ceoConversations([root,first,next],[worker])[0].reply,null,'Do not continue past an unfinished specialist handoff');
assert.equal(ceoConversations([root,first,next],[worker])[0].status,'Brand Manager is working');
next.task.status='blocked'; next.question_kind='dependency';
assert.equal(ceoConversations([root,first,next],[])[0].reply,null,'Non-interview blockers require activity review');
assert.equal(ceoConversations([],[]).length,0);
const orphan=card('t_orphan',10); orphan.parents=['t_missing'];
assert.equal(ceoConversations([orphan],[])[0].id,'t_orphan');
const cycle=card('t_cycle',11); cycle.creator_task_id='t_orphan'; orphan.creator_task_id='t_cycle';
assert.equal(ceoConversations([cycle,orphan],[]).length,1,'Cycles are bounded and deterministic');
const html=ceoMarkdown('## Synthetic heading\n\n**Bold** <script>alert(1)</script>\n\n- One\n- Two\n\n> Quote\n\n```\n<img onerror=alert(1)>\n```\n\n1. First\n2. Second');
assert(html.includes('<strong>Bold</strong>'));
assert(html.includes('<ul>') && html.includes('<ol>') && html.includes('<blockquote>'));
assert(!html.includes('<script>') && !html.includes('<img '),'Raw HTML cannot execute');
assert(html.includes('&lt;script&gt;') && html.includes('&lt;img'));
assert(ceoMarkdown('`**literal**`').includes('<code>**literal**</code>'));
assert(ceoMarkdown('**Bold *nested* bold**').includes('<em>nested</em>'));
console.log('PASS synthetic CEO chat: discovery continuity, chronological messages, reply gates, independent histories, safe Markdown');
'''], check=True)


if __name__ == '__main__':
    unittest.main()
