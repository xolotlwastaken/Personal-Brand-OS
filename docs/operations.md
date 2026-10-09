# Operations

## Chat and task graphs

Normally talk to brand-ceo through the dashboard's **Brand CEO** desk or `./scripts/chat.sh`.
The CEO delegates discovery and strategy revisions to Brand Manager and relays the
interview questions to you. Brand Manager prepares short question rounds as artifacts;
dependent CEO follow-ups present them and wait for human answers. Answers resume the
CEO, which commissions the next specialist round. A strategy proposal needs explicit
human approval before canonical changes. Existing starting drafts are incomplete discovery.

`./scripts/chat.sh <profile>` remains an optional specialist/operator interface. Supply
actual experiment notes, goal, sources and missing constraints; do not ask a script
generator to invent personality or past results.

CEO should use kanban_create to make specialist contracts and real returned task IDs as parent links. Producing cards depend on producing cards, not an unfinished planning card. Complete planning once the graph exists; schedule a separate CEO review card downstream of the script. A CLI chat need not stay open: gateway native dispatcher continues ready cards. Automatic built-in triage decomposition is off; triage cards await deliberate CEO/operator action.

Example human-operated native CLI contract:

```bash
docker compose exec --user hermes hermes hermes -p brand-ceo kanban create \
  'Draft a brand brief from supplied notes' --assignee brand-manager \
  --workspace dir:/knowledge --max-runtime 300 --max-retries 1 \
  --body-file /knowledge/operations/my-task-contract.md --json
# Create a downstream task with --parent <actual-first-task-id>.
docker compose exec --user hermes hermes hermes -p brand-ceo kanban list --json
docker compose exec --user hermes hermes hermes -p brand-ceo kanban show <task-id>
docker compose exec --user hermes hermes hermes kanban context <task-id>
docker compose exec --user hermes hermes hermes kanban dispatch --dry-run --json
```

Do not run `hermes kanban daemon` as another execution service. Gateway owns dispatch. Do not modify SQL tables. Native workers retrieve their own task using kanban_show, persist/read back artifacts and call kanban_complete or kanban_block. Handoff paths go in completion metadata. No temporary subagent conversations are required.

## Review and human approval

The normal initial output is a draft. For a local human gate, create a blocked card (`kanban_create.initial_status=blocked`) documenting the exact proposal and requested approval. It stays non-dispatchable; review_dispatch is false. Only a human operator records approval via a comment and unblocks/marks the local demonstration complete. The deterministic verifier simulates that operator response on an isolated test board and says so explicitly. This grants no publishing/DM permission, and no such tools are configured.

```bash
docker compose exec --user hermes hermes hermes kanban comment <task-id> \
  'Human decision: approve this local draft only; no external action authorized.'
docker compose exec --user hermes hermes hermes kanban unblock <task-id> \
  --reason 'Human reviewed the stated draft.'
```

Human approval is also required before major canonical brand decisions and future paid media generation beyond agreed limits. CEO cannot self-approve human gates.

## Blocked cards and attempts

Inspect `kanban show`, `kanban runs <id> --json` and `kanban log <id> --tail 5000`. needs_input means a human/CEO must supply missing information; capability means a required integration/footage is unavailable; dependency waits for a parent; transient failures require diagnosis. Correct the input/config/permission issue first, comment the resolution, then unblock through supported CLI. Avoid repeated unblocks without new information. Concurrency is one and failure_limit is one, so broken unattended cards do not churn through API calls.

If a result needs a revision, create a new specialist card referring to the artifact and concrete changes, or use native review/request-changes tooling where appropriate. Never let the CEO rewrite specialists' canonical outputs to hide a failure.

## Logs, skills and identity

`docker compose logs --tail 100` shows init/supervision. Gateway output is primarily in data/hermes/logs/gateways/default/current; specialist execution is data/hermes/kanban/logs/<id>.log. These can contain private conversation material; do not publish them. The CLI itself has substantial cold-start import cost, so use the lightweight container healthcheck for regular liveness rather than frequent full CLI polling.

Edit `config/agents/<profile>/SOUL.md` or the profile routing description in profile.yaml, then bootstrap. Runtime-owned changes are preserved/reported until explicitly applying drift. Use `--apply-drift` only after inspecting conflicts and the retained backup. Restart gateway after changes; existing workers retain the configuration they started with.

Skills: adapt config/skills/<name>/SKILL.md, preserve attribution/license, update adapted checksum in manifest and record the intended-use test. Bootstrap installs profile-local copies. Do not run Ootto's Claude installer. Runtime skill mutation is drift; it should be brought back to versioned config through a reviewed edit. Updating Ootto requires fetching/reviewing an exact revision, rerunning the development adapter deliberately and checking the resulting procedure differences. Agent Reach and Content Factory are reference-only.

## Models, scheduling and future agents

Edit global non-secret model settings in .env, or one profile's versioned model block for an override. Use credentials.sh for a static key; use the native auth CLI for provider-specific OAuth. Never copy refresh-token stores among profiles. Run bootstrap and restart gateway; verify a tiny reply before restarting larger workflows.

Hermes cron state is persistent under each profile. No content scheduling/cronjob tools are enabled initially. Publisher produces schedule proposals, not running cron or a publishing scheduler. An operator can later configure native cron only after the desired routine is reviewed; inspect official pinned-version cron docs rather than guessing schema.

The required deployment has exactly seven named project profiles. Adding another is a future architecture change: add templates/manifest contracts and permissions, update the role allowlist and verification expectation, provision through native profile APIs and test handoffs. Do not casually create an eighth profile in this deployment and then claim exact-seven validation.

## Media and persistence

Put supplied test footage in media/incoming; editing plans reference paths under /media. Working and export directories are prepared for later tools. No rendering integration is installed by this project. Synthetic file fixtures are not actual production footage.

For container recreation testing, wait until active cards finish, run `docker compose up -d --force-recreate`, wait for healthy status, then verify existing artifacts and histories. Never remove data/hermes to force bootstrap success. Back up before updates or migration. Restore always goes into an empty directory; see deployment.md.

## Bounded verification

Run `scripts/verify.sh` for deterministic Docker/profile/skill/helper/validator checks. `scripts/verify-fresh.sh` tests provisioning twice in an isolated ignored data directory without credentials. `scripts/skill-examples.sh` queues seven bounded native worker cards for synthetic intended-use examples of all 29 skill assignments; it is separate from the initial Reel workflow. After all live cards finish, run `docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-live.py` to verify the actual task graph, dependency timings, artifacts, examples and usage records.

Scripts and CEO reviews must call brand_artifact_check and fix measured errors before completion. If the first demo draft fails, the operator can run `docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/request-revision.py`; it asks the CEO to create a native Script Writer revision and a follow-up CEO review. It does not rewrite specialist outputs.
