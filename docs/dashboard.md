# Local agent dashboard

The default page is **Brand CEO**. Talk to the CEO about outcomes, strategy and
changes; it delegates to specialists and relays their questions and results.
The page uses a chat layout: conversation history on the left, chronological
messages in the center, and a composer at the bottom. **New chat** starts a separate
conversation. Linked discovery rounds stay together in the original chat.
The send arrow answers the current interview question or continues the latest
completed exchange automatically. Enter sends; Shift + Enter adds a new line.
Drafts are preserved when switching conversations or when the page refreshes.
A red dot beside **Brand CEO** and each conversation marks unread CEO replies,
including recovery updates. Replies are checked while you browse other dashboard
pages. Opening a conversation clears its dot when the latest replies are visible;
scrolling through older messages or opening a dialog keeps new replies unread.
Read state persists in this browser across reloads, storing message IDs only.
**Team activity** expands to show the underlying specialists and execution cards.
The strategy badge reads canonical `brand/strategy.md` metadata only, never test
artifacts. Existing starting notes are discovery context, not an approved strategy.

**Live chat** opens the CEO's conversation panel. Select **New direct chat**
for a conversation with streamed assistant text and visible tool calls/results.
The CEO remains the main contact and delegates work through native Kanban.
In **Your agents**, click an agent's name or **Chat & activity** to inspect its
recorded conversations. Select a task run to watch its saved transcript, including
tool arguments and results; the viewer refreshes every two seconds. Worker messages
appear when native Hermes persists them. Worker token streaming is not available
through this adapter; direct chat replies use a live SSE stream.

Direct chats are separate native sessions in the selected profile, sharing that
profile's memory and vault access. They do not inject messages into a running
worker. Choose **Resume direct chat** on a saved direct conversation to continue it.
CLI, Telegram and worker conversations can be inspected; this UI does not take
over those sessions. Viewing history runs no inference. New chat prepares a native
agent; inference starts when you send a message. The adapter uses the profile's
configured `api_server` tool allowlist without enabling an HTTP API listener.

The CEO desk's delegation thread is an asynchronous conversation backed entirely
by native Kanban cards and comments in project `brand-os-ceo`. Live chat is available
separately through **Live chat**.
The CEO creates Brand Manager discovery rounds and dependent CEO follow-ups.
Brand Manager saves up to three questions per round; the CEO presents them and
waits for your input. Sending a message saves your answer and resumes that CEO card.
Completed exchanges can be continued with a new dependent CEO card. Failed provider
attempts remain visible; answering does not resume capability or transient failures.
Draft strategy proposals require your explicit approval before canonical changes.

The main desk directs you to the CEO. Specialist chat and **Advanced task brief**
remain optional operator access. Messages and submitted answers are
persistent; an unsent composer draft stays in browser memory through page navigation
and Refresh, and is lost when the page is reloaded or closed.

Run from the repository root:

```bash
./scripts/dashboard.sh --background
# Open http://127.0.0.1:8765
./scripts/dashboard.sh --status
./scripts/dashboard.sh --stop
```

Background mode uses a transient Linux systemd user service. It survives a closed
terminal and restarts on failure, but does not install a boot-time service. Stop
and start it after dashboard server changes. Without systemd, run
`./scripts/dashboard.sh` in a terminal; Ctrl-C stops it. Pass `--port 8766`
after either launch command to change the port. Host Python 3.10+ and Docker
CLI/Compose are required; no Node packages or upstream installers are needed.

The overview covers seven named project profiles. Hermes's default home remains
gateway infrastructure. The board offers search, agent/project filters,
dependencies, handoffs, attempts and links to visible agent transcripts. The overview also
flags failed attempts, including provider quota limits, without changing task state. Agent pages show
roles, skills, recent sessions, transcripts, direct chats and usage. Incomplete actual provider cost is
unavailable. Vault and skill previews display escaped Markdown text and headings;
raw HTML never executes.

**Advanced task brief** submits real work to the CEO or a specialist. Supply personal facts
and references. The default project is `brand-os-dashboard`; you can choose a
different namespace and parent task IDs. Submission uses native `kanban_create`,
a fixed `/knowledge` workspace, a 300-second per-card runtime cap and a retry-safe
request key. Profile configuration controls worker turns, retries and downstream
tasks. The cap applies to this card, not the total CEO-created task graph. Model
usage applies when workers execute. Notes use `kanban_comment`. Blocked/scheduled
cards can be unblocked; review cards can be returned with a reason through
`kanban_request_changes`.

Completed cards are execution results, not publication or strategy approvals.
Publishing, DMs, bulk scraping, media generation and production rendering remain disabled.
Reference Builder can use the [authorized reference tools](references.md) when a brief requests research.
No dashboard button enables publishing or audience messaging. The interface offers
native agent chat and task coordination within the existing project safeguards.

The server binds exclusively to `127.0.0.1`, runs as the host user and invokes
fixed Docker Compose commands with container-side adapters running as `hermes`.
The read/task adapter keeps one warm pipe; direct chat uses one native Hermes
stdio backend shared by the seven profiles. These are transport processes, not
task dispatchers or an additional agent profile. One direct chat turn runs at a
time; native Hermes owns session persistence and leases.
Docker's socket is never mounted. Compose, the official entrypoint, s6 and
container port exposure remain unchanged. File previews cover adapted skills and
Markdown inside the project's vault. Credential stores are never served; native
Hermes resolves its own configured provider credentials. The independent host
`~/.hermes` is untouched. Usage queries are read-only SQLite; transcripts use
native read-only SessionDB APIs. All task operations use native tools or supported CLI.
The browser receives explicitly allowed chat actions, never arbitrary native RPC
or configuration slash commands. Hidden reasoning, system messages and hidden
carrier rows are omitted. Credentials are redacted before transcript/event delivery.
Transcripts show the latest 200 native messages, bounded to 64 KB per displayed content field.

Loopback is the trust boundary: other local programs can access the dashboard.
It is not a remote multi-user authenticated service. Host/Origin validation, a
per-process action token, CSP, no-store responses, action rate limits and bounded
Docker operations guard browser access. Do not expose it through a public proxy.
Task content is not written to access logs or browser local storage. Backups
pause the container and therefore also pause dashboard task writes inside it.

Pages refresh every 15 seconds while visible and no dialog is open, with an
8-second snapshot cache. Task details have a Refresh button. Failures retain
the last snapshot and mark it stale. Native list is limited to 200 cards;
truncation prompts you to filter by agent/project. Counts reflect the fetched
selection. Listing may promote dependency-ready cards, as the native CLI does.

Live chat events reconnect with a cursor and bounded replay. Closing a dialog
detaches its stream and preserves a running turn. Reopening the agent within the
same page preserves its draft and catches up on events. Reloading loses unsent
drafts; saved direct conversations can be resumed from history. If delivery times
out, the server does not automatically repeat the message: reopen the saved
conversation before retrying. Restarting the host dashboard closes its native
chat transport; recover persisted messages through history. Stream overflow
prompts recovery from the saved transcript. Expandable tool output uses escaped
text, so content cannot execute HTML or JavaScript.

Warm measurements on 9 October: CEO reads took 0.05–0.07 seconds versus about
2.4 seconds with a fresh process, and transcript reads took about 0.01 seconds.
The first native chat backend startup took about 4.8 seconds. A bounded real
Hook Writer chat delivered its first token in about 7.4 seconds. These are
observations, not guarantees: provider response time, prompt size, tool work,
the 15-second native dispatch interval and sequential delegated cards still
affect completion time. Model and dispatcher concurrency are unchanged.

## Verification and upstream reference

```bash
./scripts/verify-dashboard.sh
./scripts/verify.sh
./scripts/e2e.sh
```

Dashboard verification separates deterministic HTTP/security tests, native
Kanban integration in a temporary isolated container database, and live reads.
Isolated create/comment/unblock tests never run inference or add production
cards. The existing E2E command uses the idempotent real dispatcher workflow,
separate from these deterministic tests.

[Hermes Workspace](https://github.com/outsourc-e/hermes-workspace) informed the
workspace/agent/board arrangement. Its Swarm control plane was not adopted:
this project preserves the seven profiles and native execution engine. No
upstream source was copied or installed, so no new runtime pin, upstream
dependency or installer was introduced.

## Verified on 9 October 2026

- Twenty-seven deterministic host HTTP/security, CEO conversation, streaming and transport tests passed.
- Isolated native Kanban create, idempotent retry, dependencies, notes, unblock
  and invalid-input checks passed without inference or production cards.
- Live gateway, seven provisioned profiles, task detail and visible transcript
  reads passed.
- `scripts/verify.sh` passed; `scripts/e2e.sh` reused completed card `t_2baeb900`.
- Browser checks covered desktop/mobile layout, board agent filtering and ID
  search, task dependencies/attempts, vault search/preview, skill preview and
  invalid-parent submission rejection before card creation.
- The CEO chat page joins native creation provenance and dependencies into
  conversation histories. Synthetic browser tests covered answering an interview,
  ordinary continuation, separate New chat requests, escaped HTML and no duplicated
  optimistic messages. Live read-only checks verified the existing discovery chat,
  per-conversation drafts and multiline composition. Mobile checks at 390 × 844
  verified that the send button stays visible and the page has no horizontal overflow.
- A transient user service runs the dashboard on host loopback port 8765.
- CEO desk checks cover forced CEO assignment, preserved interview answers,
  idempotent retries, stale-question rejection, linked continuation cards and
  native repeated-block triage preservation in an isolated database.
- A scoped native plugin automatically pairs Brand Manager cards in the CEO
  conversation with dependent CEO relays. The completion guard repairs missing
  pairs, and native idempotency prevents repeat relays. Isolated tests cover retries,
  completed relays, profile isolation and failure blocking without inference.
  Direct CEO chat defaults unscoped Brand Manager discovery cards to the same
  CEO conversation tenant. Explicit project tenants remain unchanged.
  Artifact validator and relay guard statement coverage is 95% in the isolated
  regression run; installed lifecycle hooks are exercised separately in that run.
- Live recovery of discovery card `t_057ed3c0` created relay `t_26977302`.
  The CEO posted the two unanswered questions and blocked with `needs_input`.
- An isolated synthetic browser fixture verified request submission, answering,
  escaped untrusted question text and composer preservation through Refresh.
  The live page shows the existing starting strategy and a prepared discovery message.
- Host coverage is 90% overall (HTTP server 86%, live transport 95%); adapter
  coverage is 90% across isolated native tests and separate live reads.
  No new real inference interview was run.
- Provisioning installed the CEO/Brand Manager policies and preserved existing
  CEO `config.yaml` telemetry drift. No `--apply-drift` action was taken.
- Isolated native session API fixtures verify profile scope, tool results,
  omission of hidden reasoning/system/carrier rows and transcript limits.
- Two bounded real Hook Writer connection tests verified native token events,
  saved history/resume and browser submission/SSE display. The smoke-test
  messages are connection checks, not personal brand evidence.
- Synthetic browser streaming checks verify interim messages, tool arguments/results,
  escaped HTML, hidden-reasoning exclusion and draft/replay preservation.
