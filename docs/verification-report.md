# Verification report — 2026-10-09 (Asia/Singapore)

## Status

The foundation is complete: one healthy official Hermes container, seven persistent named profiles, native CEO-driven Kanban orchestration, a shared vault and tested backup/migration scripts. All required infrastructure checks passed. The live six-card workflow, measured revision/re-review and all 29 skill assignments ran successfully. Draft content still requires human factual/creative review; social actions remain disabled. Docker Desktop was restarted after a workstation reboot, and native dispatch reclaimed a stale worker lease and resumed unfinished checks.

Reference acquisition was subsequently authorized and added on the same date.
See [reference verification](references.md) for its separate evidence: 27
synthetic tests (88% coverage), native tool discovery/restrictions, actual public
Instagram downloads, local machine transcription, 12 timestamped frames, real
vision observations, cached repeats and dispatcher card `t_d1a9c972` with owner
correction `t_386c590b`. The prior synthetic E2E below remains a distinct test.

## Inspected environment and pins

- Ubuntu 26.04, amd64; Docker Desktop 4.94 / Engine 29.8.2, Compose 5.5.1. Approximately 14 GiB RAM and 854 GB free disk at initial inspection.
- Existing host Hermes gateway and databases were kept separate. SQLite-safe copies of its relevant databases were saved under ignored data/host-safety-backup. Only a static NVIDIA model key was reused; no host messaging tokens or OAuth grants were transferred.
- Official Hermes 0.21.6, source `818c13be1dc4fd28987e1e881a9408224afd4535`; published image index `sha256:9774f4f39a9bb8c2f68ce728ed5e99ddbad282163be56764afacf88ed952b784`. amd64 executed; the published arm64 variant is untested here.
- Ootto skills revision `5263be7b209fee3f98a59ec185446b8144bca88f`; 26 unique adapted playbooks, 29 assignments. Original selected material and MIT license preserved. Claude installer not executed.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Compose, health, entrypoint/s6, bind mounts, ports, UID/GID, caps and resource limits | PASS | data/hermes/verification/docker.json |
| Exactly seven named profiles, identities/configs, distinct memories | PASS | data/hermes/verification/deterministic.json |
| Hermes skills_list / skill_view for all 29 assignments | PASS | same report, profile-specific discovery records |
| Manual and worker tool definitions; specialist restrictions | PASS | same report, exact native tool names |
| Native file read/write and shared handoff access in all seven profiles | PASS | same report and vault verification artifacts |
| Native create/assign/show/complete/block/unblock and dependency eligibility | PASS | isolated native test boards; no model execution claimed |
| Local human-approval demonstration | PASS | isolated board: blocked, operator comment, unblock, complete; no external action |
| Reviewed hook-mining helper selftest and supplied synthetic CSV | PASS | data/verify-handover.log; media/incoming/synthetic-hooks.mined.json |
| Read-only validator word/timing checks and path/traversal/symlink/size rejection | PASS | data/hermes/verification/validator.json |
| Fresh provisioning and repeated provisioning from a clean Git checkout | PASS | data/git-fresh-provision.log |
| Runtime memory, credential sentinel, edited vault preservation and unknown config drift handling | PASS | same log: drift preserved/reported; explicit apply keeps prior copy |
| SQLite-safe backup/restore, including a committed row present only in WAL | PASS | data/hermes/verification/backup-restore.json; separate data/wal-restore-test |
| Initial live CEO-to-specialists workflow and measured revision/re-review | PASS | data/hermes/verification/live.json; four dependency timing gates |
| All 29 live procedural skill examples, including owner corrections | PASS | data/hermes/verification/live.json and per-skill manifest |
| Idle container removal/recreation: 324 file hashes and eight database histories | PASS | data/hermes/verification/persistence.json |
| Final secret-free archive: 746 files, 21 historical cards, seven session DBs, WAL-only fixture | PASS | data/hermes/verification/backup-restore-final.json |
| Restored-data reprovisioning and native board access without model credentials | PASS | data/hermes/verification/restored-bootstrap.json; data/restored-bootstrap.log |

The production service has no exposed ports/Docker socket, no host network or privileged mode. It retains the official entrypoint, uses one multiplexed gateway/embedded dispatcher and transient workers inside the same container. Root/default is mandatory infrastructure; it is not an eighth brand agent. Per-profile memory is logically separate; same OS UID means it is not a confidentiality boundary between compromised profiles.

## Actual live Kanban graph

Planning CEO `t_2baeb900` created the five-card graph and completed. The native gateway then ran the dependency chain:

`brand-manager t_fefaf823 → reference-builder t_0d11f6f9 → hook-writer t_5d1b32b8 → script-writer t_b81ce578 → CEO review t_42bf7e5e`

No Video Editor or Publisher was invoked in this initial workflow. Each worker wrote its own persistent Markdown and used native lifecycle tools. Sources were supplied mock references, never scraped social accounts. The initial script failed measured quality despite its first CEO review: actual 116 words versus declared 103, and an 18-word opening in 3 seconds (360 WPM). The first script/review are retained as superseded history.

CEO revision planning `t_0db0d2d3` created Script Writer revision `t_7a1483e8` and final CEO review `t_d6408bce`. Corrected script: 97 spoken words, 45 seconds, all shot rates ≤180 WPM; native validator valid=true. Final draft and review:

- [Revised script](../knowledge/content/scripts/t_7a1483e8-revised-reel-script.md)
- [CEO follow-up review](../knowledge/operations/reviews/t_d6408bce-revised-e2e-review.md)
- [Hooks](../knowledge/content/hooks/t_5d1b32b8-hooks.md)
- [Research](../knowledge/research/references/t_0d11f6f9-research.md)
- [Brand brief](../knowledge/content/ideas/t_fefaf823-brand-brief.md)

The script is a hypothetical how-to framework. Real planning steps, outputs, voice samples and human approval are still required before autobiographical content can be produced or published. A technical pass does not approve publication or establish factual/creative quality.

## Failures diagnosed and fixed

1. Official-image Python differs from system Python. Production scripts use the image venv and Hermes's bundled YAML parser; no host dependencies were added.
2. Early profile configs exposed unnecessary default tools. All manual/worker tool definitions were inspected and restricted; native worker lifecycle remains available.
3. A PID-only health probe failed when root lacked permission to signal unprivileged processes. The probe now verifies process fingerprint, command line and listening control socket; health drops to hermes using the absolute `/command/s6-setuidgid` path.
4. Upstream supervision needs KILL to terminate its unprivileged children; the narrowly documented capability was added and the official entrypoint retained.
5. Backup of read-only WAL files initially failed. Paused DB+WAL staging followed by SQLite online backup fixed it; a committed WAL-only row survived restore. Strict manifest validation then caught SQLite-generated temporary sidecars; archiving only indexed checkpointed files fixed that mismatch. The final restore was checked against the original historical task/session IDs and a fresh WAL-only fixture.
6. Re-running bootstrap could recreate an active deployment. It now reconciles a running deployment without restarting it. One stopped worker's old-container claim was recovered through native comment/block/unblock, retaining history.
7. The first CEO review missed script measurements. A read-only native validator was added to CEO/Script Writer/Video Editor and the owner revision/re-review completed.
8. Synthetic skill outputs inferred retention/format effects from save rates or included unsupported first-person hooks/resource promises. Native owner revision/patch tasks corrected the identified evidence attribution and the publisher resource claims. This illustrates why drafts still require review; textual playbooks are not guarantees of truth.
9. Git ignore patterns could hide the seed vault. Root-only ignores and a clean Git-checkout provisioning test verified that templates ship while runtime data/secrets do not.


## Live skill examples and recorded usage

All 29 assignments executed in seven native profile cards, separate from the initial E2E. Each loaded its assigned playbooks and produced a concrete persistent synthetic example. Additional owner revision/patch cards corrected identified draft defects. The combined live verifier checks completed cards, actual artifacts, exact skill section names, owners/task IDs and the measured final script. This is a procedural smoke-test pass, not factual/creative certification of every line or validation of an external integration.

| Profile | Final example task | Skills exercised |
|---|---|---|
| brand-ceo | t_d12003ad | analytics-readout, content-audit, content-calendar |
| brand-manager | t_3b163d2d | ai-brain, audience-personas, positioning-audit, content-pillar-builder, series-planner, content-calendar |
| reference-builder | t_f31cd66d | reel-analyzer, competitor-teardown, trend-spotter, comment-mining |
| hook-writer | t_2b7a98ab | going-viral, hook-mining, viral-hook-writer, ab-hook-tester |
| script-writer | t_e698a2d5 | reel-scripter, b-roll-shot-list, cta-writer, on-screen-text-writer |
| video-editor | t_763f6864 | reel-builder, b-roll-shot-list, on-screen-text-writer, cover-thumbnail-brief |
| publisher | t_1248f904 | caption-and-hashtags, best-time-scheduler, comment-responder, dm-script-writer |

Recorded Hermes telemetry across 25 profile sessions: 174 API calls, 3,128,861 input tokens and 78,118 output tokens. This includes tests, revisions and recovery attempts. Actual USD cost is null and cost_status is unknown for all seven profiles; no account bill or affordable-price guarantee is inferred. Interrupted/unreported requests can differ from these recorded totals. No paid media jobs were launched.

## Scope and limitations

Social credentials, publishing, messaging, Instagram scraping, paid generation, full rendering and a custom dashboard were not configured. The Video Editor produces plans and the Publisher produces draft packages only. Agent Reach/Content Factory were studied as reference material; no integrations installed. Optional Nous auxiliary credentials remain unconfigured; the tested primary provider is NVIDIA. Pricing/actual account bill is unavailable unless the provider reports it; do not interpret missing cost as zero.

Native model reviews can miss counts, source attribution and creative issues. The validator checks declared words and timing, not real footage, vocal delivery, personal truth, originality or engagement outcomes. Proposed calendars/personas/diagnoses remain hypotheses. Final skill examples are synthetic procedural smoke tests, not proof of real platform integrations or performance.

## Operate and migrate

See [README](../README.md) for the seven profiles and skill assignments, directory map and exact commands. [Deployment](deployment.md) covers an empty-target restore and credential reauthorization. [Operations](operations.md) covers CEO chat, native cards, revisions and human gates.

Next milestone: a Brand Manager interview with the user's real experience and voice samples, then one human-reviewed Reel based on an actual documented experiment and supplied footage. Rendering/platform integrations should follow that evidence and approval workflow.

## Final portable artifacts

- Repository bundle: `backups/personal-brand-os.bundle` (source/config/templates/docs; no runtime credentials).
- Verified state archive: `backups/brand-os-20261009T011245Z-19807.tar.gz` (746 indexed files; credentials excluded).
- Recovery copy: `data/recovery-final-wal-20261009`; never substitute it for the live state without an intentional migration.

For another Linux server, install Docker/Compose, transfer those two files securely, clone the bundle, pull the pinned image, restore into `data/import`, move its three trees to `data/hermes`, `knowledge` and `media` before bootstrap, then reprovision the static model key. The exact commands are in [deployment](deployment.md). The default source model works with this local NVIDIA credential, but its pricing has not been verified; configure another tested provider if needed. OAuth integrations were not migrated and must be reauthorized if added later.

All 14 definition-of-done infrastructure criteria are met by the executed tests above. No infrastructure blocker remains. arm64 execution, real brand discovery, actual footage, external platform integrations and a verified provider bill remain outside the tested foundation.

## Primary references

- [Official Hermes documentation](https://hermes-agent.nousresearch.com/docs/)
- [Pinned official Docker entrypoint](https://github.com/NousResearch/hermes-agent/blob/818c13be1dc4fd28987e1e881a9408224afd4535/docker/entrypoint-dispatch.sh)
- [Pinned profile implementation](https://github.com/NousResearch/hermes-agent/blob/818c13be1dc4fd28987e1e881a9408224afd4535/hermes_cli/profiles.py)
- [Pinned native dispatcher](https://github.com/NousResearch/hermes-agent/blob/818c13be1dc4fd28987e1e881a9408224afd4535/hermes_cli/kanban_db_dispatch.py)
- [Pinned native Kanban tools](https://github.com/NousResearch/hermes-agent/blob/818c13be1dc4fd28987e1e881a9408224afd4535/tools/kanban_tools.py)
- [Pinned Ootto playbooks](https://github.com/Ootto-AI/claude-content-skills/tree/5263be7b209fee3f98a59ec185446b8144bca88f)
