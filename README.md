# Agentic Personal Brand OS

A portable content team: one official Hermes container, seven named persistent profiles, native SQLite Kanban dispatch, private profile memory, and one shared Obsidian Markdown vault. The CEO coordinates six specialists. The initial workflow produces drafts and human-reviewable artifacts; social publishing, DMs, scraping, video generation and rendering are disabled.

## Start on Linux

Prerequisites: Docker Engine (or Desktop), Docker Compose v2+, Bash, Git, GNU coreutils, local disk. No host Hermes/Python installation is needed. Allow roughly 3 GB container RAM plus Docker overhead, two CPUs and several GB for the official image; media needs additional disk space. x86_64 is tested here; the pinned official index also publishes arm64, which has not been tested in this project.

```bash
git clone <your-repository-url-or-transferred-Git-bundle> personal-brand-os
cd personal-brand-os
./scripts/bootstrap.sh
./scripts/credentials.sh nvidia    # hidden prompt for your MODEL API key
# Or: ./scripts/credentials.sh openrouter (also change model/provider/base URL in .env)
docker compose restart hermes
./scripts/wait-healthy.sh
./scripts/verify.sh
```

Bootstrap creates `.env` from `.env.example` using your UID/GID. The current image is official Hermes **0.21.6**, index digest `sha256:9774f4f39a9bb8c2f68ce728ed5e99ddbad282163be56764afacf88ed952b784`, source revision `818c13be1dc4fd28987e1e881a9408224afd4535`. It preserves upstream entrypoint and s6 supervision. No ports are published and no Docker socket is mounted. Upstream starts an authenticated internal loopback API for its control plane; it is reachable only within this container. Dashboard and social adapters are unconfigured.

The repository is committed locally, and a portable Git bundle is available under backups/personal-brand-os.bundle. The verified state archive and transfer commands are recorded in docs/verification-report.md and docs/deployment.md.

This local installation has securely reused only an existing static NVIDIA model API key. A fresh server must provision its own model credential. Nothing connects to the separate host Hermes installation. Model calls use the configured provider's account; costs and quotas depend on that account. The initial choice follows the available provider, with one worker at a time and bounded turns; model pricing has not been verified.

## Use the team

```bash
./scripts/chat.sh                         # interactive CEO chat
./scripts/chat.sh brand-manager           # interview / refine brand strategy
./scripts/chat.sh script-writer           # specialist chat
./scripts/chat.sh brand-ceo -q 'Create a draft Reel from my supplied experiment notes.' --oneshot
./scripts/e2e.sh                          # bounded REAL Kanban workflow; idempotent
# Inspect native board, worker logs and attempts:
docker compose exec --user hermes hermes hermes -p brand-ceo kanban list --json
docker compose exec --user hermes hermes hermes -p brand-ceo kanban show <task-id>
docker compose exec --user hermes hermes hermes kanban runs <task-id> --json
docker compose exec --user hermes hermes hermes kanban log <task-id> --tail 5000
docker compose logs --tail 100 hermes
```

Ask the CEO for an outcome, supplied personal facts and useful source material. It creates named specialist cards with dependency IDs, persists handoffs, and reviews the script in a final CEO card. Kanban's built-in automatic triage decomposition is explicitly disabled. CLI conversations can end while queued cards continue through the gateway; inspect the board or ask the CEO for results.

The demo request is “Create a 45-second Instagram Reel about how I used AI to plan my personal brand.” It uses mock references. Since the user's actual planning steps/results were not supplied, the resulting script must stay a **hypothetical draft with missing personal details**, not a publishable autobiographical claim. Only Brand Manager, Reference Builder, Hook Writer, Script Writer and CEO participate in this demo.

## Profiles and files

| Profile | Owns | Adapted Ootto skills |
|---|---|---|
| brand-ceo | Coordination, reviews, analytics summaries | analytics-readout, content-audit, content-calendar |
| brand-manager | Canonical brand strategy | ai-brain, audience-personas, positioning-audit, content-pillar-builder, series-planner, content-calendar |
| reference-builder | Supplied-reference research | reel-analyzer, competitor-teardown, trend-spotter, comment-mining |
| hook-writer | Spoken/on-screen hooks | going-viral, hook-mining, viral-hook-writer, ab-hook-tester |
| script-writer | Reel scripts and shots | reel-scripter, b-roll-shot-list, cta-writer, on-screen-text-writer |
| video-editor | Editing plans, test media | reel-builder, b-roll-shot-list, on-screen-text-writer, cover-thumbnail-brief |
| publisher | Draft publication/engagement packages | caption-and-hashtags, best-time-scheduler, comment-responder, dm-script-writer |

Hermes always includes an infrastructure `default` slot. Exactly seven **named project profiles** are provisioned. It is not an eighth brand specialist.

```text
compose.yaml / Dockerfile / .env.example    exact official runtime pin
config/agents/<profile>/                  managed config, SOUL and routing description
config/skills/                            26 adapted native skills (29 assignments)
config/skills-manifest.yaml               source pin, dependencies and validation records
vendor/ootto/                            original reviewed playbooks + MIT license
templates/knowledge/                     versioned starting brief, conventions and fixture
scripts/                                 provisioning, verification, chat, backup/restore/update
knowledge/                               runtime Obsidian vault (Git-ignored)
media/{incoming,working,exports}/         runtime media (Git-ignored)
data/hermes/                             persistent profiles, SQLite, skills, memories, sessions
docs/                                    architecture, agents, deployment, operations, troubleshooting
```

The user's private initial brief lives in `knowledge/brand/starting-brief.md`, seeded from a versioned template. Templates deliberately contain the supplied project brief only; keep future private personal details in the ignored runtime vault. Skills are prompt playbooks, not installed platform integrations. See [skill review](docs/skills-review.md).

## Stop, back up and move

```bash
docker compose stop
# Resume:
docker compose up -d
./scripts/backup.sh
./scripts/restore.sh backups/<archive>.tar.gz data/recovery-test
# Inspect restored files before installing them on a fresh server.
./scripts/update.sh                       # show current pin and usage
```

Backups exclude credential stores and logs by default, preserve committed SQLite WAL transactions, and restore only into an empty location. They still contain private content/history: protect them. For a separate secret archive use `./scripts/backup.sh --secrets`, encrypt it immediately, and transfer it through a secure channel. Never commit or publicly upload backups.

Detailed instructions: [deployment](docs/deployment.md), [architecture](docs/architecture.md), [agents](docs/agents.md), [operations](docs/operations.md), [troubleshooting](docs/troubleshooting.md). Actual test evidence and limitations: [verification report](docs/verification-report.md).
