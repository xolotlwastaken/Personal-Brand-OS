"""Synthetic CEO chat journeys. No production writes or model calls."""
import subprocess
import unittest


class CEOPageTests(unittest.TestCase):
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
