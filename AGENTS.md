# Personal Brand OS repository instructions

Production runs in one official Hermes Docker container with seven named project profiles. The mandatory root/default home is gateway infrastructure, not an eighth brand agent. Preserve the official entrypoint and s6 supervision. Never mount the Docker socket, use privileged mode, publish ports, or add social credentials by default.

Upstream sources and selected skills are pinned. Original Ootto playbooks are attribution/reference material in vendor/ootto; adapted runtime playbooks are config/skills. Never execute upstream installer scripts. Regenerate templates deliberately and inspect diffs.

Configuration is version controlled; data/, knowledge/, media/, secrets and backups are runtime-owned and Git-ignored. Seed knowledge from templates only when absent. Never replace private memories, session DBs, credentials or existing vault notes during bootstrap. Report untracked config drift; --apply-drift is an explicit operator action that keeps pre-change copies.

Native Hermes Kanban is the only execution/task state engine. Use model-facing native tools or supported CLI commands, never direct SQL mutations or a custom queue. Deterministic test DBs are isolated and do not run inference. Label them separately from real dispatcher tests.

No fabricated personal experiences, measurements or opinions. Synthetic fixtures stay synthetic. Publishing, DMs, scraping, media generation and rendering are disabled. Human approval is required for major strategy decisions and future external actions.

Verification: scripts/verify.sh; scripts/e2e.sh is bounded real inference and idempotent. Backups pause all writers, stage database and WAL together, and use SQLite backup. Restore only into empty directories. Do not touch the host's independent ~/.hermes installation.
