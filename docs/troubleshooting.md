# Troubleshooting

| Failure | Check and recovery |
|---|---|
| Docker unavailable | `docker version`, `docker compose version`, `docker info`; install Engine/plugin or start Docker Desktop. Check deploying user's daemon access. |
| Container starts then exits | Inspect Compose logs. Keep official entrypoint, root init, UID/GID variables and required bootstrap/supervision capabilities. Do not set arbitrary Compose user or inject another PID-1 init. |
| Health starts slowly | Allow up to two minutes. Inspect gateway_state.json, actual gateway process, control socket and per-profile gateway logs. Full CLI startup can be slow; healthcheck deliberately uses stdlib only. |
| Supervisor claims running but process absent | s6 status alone can report a supervised slot without a healthy gateway. Use provided healthcheck plus actual PID/control socket; inspect data/hermes/logs/gateways/default/current. Restart through Compose after fixing cause. |
| Permission denied in vault/media | Check .env HERMES_UID/GID and host ownership of all bind roots. The official entrypoint remaps/chowns its data volume but does not fix an arbitrarily owned external vault/media mount. Correct ownership on the fresh target; do not chmod everything 777. |
| Write denied outside safe root | Keep `HERMES_WRITE_SAFE_ROOT=/opt/data:/knowledge:/media`. Do not unset the protection or expand it to the host filesystem. |
| No usable model credential | Provision the model key with credentials.sh. Native profile creation seeds a comment-only .env; a file existing does not mean it contains a key. Check key presence without printing values; match provider/model/base URL. Restart gateway to reload scope. |
| OAuth refresh conflicts | Stop copying refresh-token auth.json files. Use native root credential pooling or separately authorize a profile. This deployment initially uses static model keys only. |
| Skills missing | Check config/skills-manifest.yaml and runtime profile skills/<name>/SKILL.md. Run verify.sh. No-skills profiles omit unrelated bundled playbooks; native Kanban may expose its own lifecycle skill automatically. |
| Skill describes a nonexistent integration | Read adapted config/skills, not vendor reference instructions. Agent Reach, Ootto/Filesystem MCP, Instagram/Apify/Composio, media generation and rendering are disabled. Supply mock/transcript/CSV evidence instead. |
| Ready cards do not run | Check container health, native `kanban dispatch --dry-run --json`, exact assignee, dispatch_profiles and global cap. A running card occupies the single slot. Native cooldown, auth or circuit-breaker diagnostics explain guarded cards. |
| Dependency never becomes ready | Every parent must be done, not review/blocked. Ensure producing cards were linked to producing cards, not to an unfinished planning card. Inspect native context and graph IDs; fix through CLI link/unlink, not SQL. |
| Worker writes draft but card remains running | Final chat text does not complete a card. Worker must validate its artifact and call kanban_complete with artifact paths. Inspect log for lifecycle tool errors. |
| Initial triage stays idle | Intended: kanban.auto_decompose=false. CEO/operator creates a concrete graph or intentionally promotes a specification. Do not enable built-in auto decomposition to hide missing CEO instructions. |
| SQLite locked/corrupt | Keep project DBs off sync/NFS folders. Stop extra writers to this state. Back up safely, use native kanban repair for diagnosis; restore into a new empty folder if needed. Never delete WAL files from a live DB. |
| Backup fails opening WAL DB on read-only mount | Use provided pause+DB/WAL staging+SQLite backup flow. Read-only WAL source connections can need a writable shm file. Do not use immutable=1 on a live/WAL database; it can ignore committed WAL transactions. |
| Restore target rejected | Restore requires an empty separate directory and rejects archive traversal/links. Inspect existing target; choose a new directory instead of deleting original state. |
| Config drift | Inspect reported relative paths and compare template/runtime content without exposing credentials. Bring intentional changes into versioned templates or use explicit --apply-drift after review. Memories/credentials are never managed. |
| Python helper missing dependencies | Execute helpers using /opt/hermes/.venv/bin/python inside the pinned image. Hermes uses its bundled hermes_yaml module, not an assumed host PyYAML install. Do not install Python packages on the production host. |

If a test cannot run, retain its exit code and actual failure evidence in data/hermes/verification, report it as failed or unverified, and fix the underlying problem before declaring it passed. No claims of real scraping, publishing or rendering should be inferred from a prompt playbook passing discovery tests.

## Reconciliation and container restarts

Bootstrap reconciles templates while leaving an already running container intact. Apply Compose changes only after active workers finish, using `docker compose up -d --force-recreate`; wait with `scripts/wait-healthy.sh`. Health probes use `/command/s6-setuidgid` explicitly because Docker exec PATH differs from upstream supervision PATH. KILL is needed by the root s6 supervisor to terminate unprivileged services cleanly.

After an unexpected container replacement, an old claim can retain the previous container hostname until its lease expires. Confirm the previous container and worker are gone, inspect `kanban show/runs/log`, comment the recovery reason, then use native `kanban block --kind transient --reason ...` and `kanban unblock --reason ...`. Keep historical runs; do not edit SQL or signal a possibly reused PID. This recovery was exercised during setup.

A ready backlog with one active worker is expected under the configured concurrency limit. Upstream can emit a dispatcher-stuck warning during long tasks even though the active worker is progressing; inspect actual running-card logs before intervening. Auxiliary Nous-auth warnings do not supply credentials and are not evidence of a failed configured NVIDIA primary call. The tested primary provider works; optional Nous-specific auxiliary features remain unconfigured.

On Docker Desktop for Linux, the Desktop service must also be running after a workstation reboot. `docker desktop start` or the installed user service `systemctl --user start docker-desktop.service` starts it; wait for `docker info` before running project scripts. Use the existing desktop-linux context. The project does not install or enable a different Docker daemon, or enable Desktop at login without the operator choosing that host policy.
