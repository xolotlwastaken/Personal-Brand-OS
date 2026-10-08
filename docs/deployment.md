# Deployment and migration

## Fresh Linux server

Install Docker Engine and Compose plugin from Docker's official installation instructions for your distribution. Give the deploying user Docker access (membership in the Docker group is effectively host administration). Use a local ext4/xfs filesystem, not cloud-sync/NFS/SMB, for data/hermes. No Python/Hermes packages on the host are required.

Clone this repository, run `./scripts/bootstrap.sh`, provision a static model key through `./scripts/credentials.sh nvidia`, then `docker compose restart hermes`, `./scripts/wait-healthy.sh` and `./scripts/verify.sh`. Bootstrap uses the invoking user's IDs in .env. If deploying for another owner, configure HERMES_UID/HERMES_GID and ensure knowledge/media are writable by that owner. Do not use Compose `user:` with the official image: init must run as root before dropping to hermes.

The published official index pin is in compose.yaml, Dockerfile and .env.example. Tested runtime: Hermes 0.21.6, source 818c13be1dc4fd28987e1e881a9408224afd4535, amd64. arm64 is published in that index but untested locally. Record a replacement index digest before upgrading; never silently use latest.

## Model settings and credentials

`.env` contains deployment IDs, image pin and BRAND_MODEL/BRAND_PROVIDER/BRAND_BASE_URL, not keys. The available local provider is NVIDIA and the starting model is nvidia/nemotron-3-ultra-550b-a55b. This preserves a provider already verified on this machine; pricing is account-dependent and not verified. One worker, 24 tool turns and task runtime caps limit initial usage. Change the three model variables to your tested provider/model, then bootstrap to reconcile owned config fields.

Static keys live at data/hermes/profiles/<name>/.env (0600). `credentials.sh` prompts without echo and writes through stdin. Never type keys into prompts or CLI arguments, commit them, or render a full `docker compose config` into logs. To give one profile its own model, edit that profile's versioned config.yaml model block, replacing variable placeholders with the intended non-secret provider/model, then run bootstrap. Runtime edits outside templates are reported as drift.

For future OAuth use `docker compose exec --user hermes hermes hermes -p <name> auth add <provider>` or the official setup wizard. Do not copy single-use refresh grants into sibling profiles. Use Hermes's native root credential-pool fallback where appropriate. When moving servers, reauthorize OAuth providers and external services rather than relying on copied refresh grants. None of those integrations is active here. API keys may be securely reprovisioned or transferred in a separately encrypted secret archive. The internal control-plane API key is regenerated if absent.

## Lifecycle

```bash
docker compose up -d
./scripts/chat.sh
./scripts/verify.sh
docker compose stop
docker compose down             # removes container/network, bind-mounted state survives
./scripts/bootstrap.sh          # recreates runtime and preserves existing data
```

Allow up to two minutes for cold startup. Healthcheck verifies real gateway PID/control socket and the persisted board without importing the expensive full CLI. Logs: Compose boot logs plus data/hermes/logs/gateways/default/current; worker logs in data/hermes/kanban/logs.

Bootstrap checks prerequisites, Compose syntax, creates folders, creates missing profiles through Hermes's own profile API with empty skills, configures routing/identity, installs adapted skills, initializes native Kanban and seeds missing vault notes. A hash ledger tracks managed files. It never overwrites memories, credentials, session databases or existing vault content. Unrecognized edits cause a DRIFT report and nonzero exit. Review before explicitly running `./scripts/bootstrap.sh --apply-drift`; changed config copies are retained in data/hermes/config-backups. For an already running deployment bootstrap reconciles files without recreating its container. Restart the gateway after active tasks finish so cached settings are reloaded; apply Compose changes with a deliberate idle `docker compose up -d --force-recreate`.

## Backups

`./scripts/backup.sh` pauses the whole deployment, including dispatcher and worker writers. A separate short-lived maintenance container, without network/capabilities, reads the mounted state. For every SQLite file it stages the database AND WAL while writers are paused, then uses sqlite3.Connection.backup to produce a consistent checkpointed destination; integrity checks must pass. It archives profiles, memories, skills, session data, native board/history, knowledge and media with checksums. Runtime files, logs/caches, local managed dependency stores and credentials are excluded. It unpauses even on failure.

Do not run a concurrent host process against the same project state while backing up. If a container is already paused, do not start this script; unpause first. A backup pauses content work briefly and may need extra disk roughly equal to the persistent data size. API/server health warnings during the pause are expected.

Backups remain private: transcripts and vault notes can contain private information, and filename-based credential exclusion is not arbitrary-content secret scrubbing. Protect archives with permissions and encryption. Use `./scripts/backup.sh --secrets` to create a separate 0600 credential archive. Encrypt it with your existing trusted tool, for example `gpg --symmetric --cipher-algo AES256 backups/<secret-archive>.tar.gz`, and keep the encrypted file separate. Do not store secrets in unrecognized filenames or embedded in config YAML.

## Restore test and transfer

```bash
./scripts/restore.sh backups/<archive>.tar.gz data/recovery-test
```

Restore rejects a nonempty target, unsafe paths/links, checksum mismatches and corrupt SQLite. It leaves the original installation untouched. Restored folders are recovery-test/hermes, recovery-test/knowledge and recovery-test/media. No credentials are in the normal backup.

On another server:

1. Install Docker/Compose, clone repository (or transferred Git bundle) and run `docker compose pull` (this does not start writers).
2. Run restore into an empty directory, e.g. `./scripts/restore.sh /secure-transfer/brand-os.tar.gz data/import`.
3. Before bootstrap, install restored trees into their canonical destinations. Confirm data/hermes does not already exist with content; do not overwrite a live install. Example for a fresh checkout:
   ```bash
   mkdir -p data
   mv data/import/hermes data/hermes
   mv data/import/knowledge knowledge
   mv data/import/media media
   ```
   If media was empty and omitted from the archive, create its incoming/working/exports directories; bootstrap also does so. Remove only the empty import folder after reviewing MANIFEST.json.
4. Run bootstrap (new UID/GID aligns the Hermes volume; ensure vault/media ownership matches the new user). Managed files are already present; drift is reported for intentional review. Restore did not include the machine-specific provision ledger, so identical files are accepted and recorded again.
5. Reprovision model credentials with credentials.sh. Reauthorize any future OAuth integrations; do not copy refresh tokens. Restart gateway; run verify.sh; inspect historical native Kanban cards and output artifacts.

Worker PIDs/leases from the old machine are not portable active processes. The native dispatcher reclaims stale/orphaned runs after restore; review any incomplete cards before unblocking. Never delete task history to solve a migration. Completed historical tasks and artifact paths remain intact because container paths stay identical.

## Updates

`./scripts/update.sh` with no argument shows the current pin. To apply a separately reviewed official release use `./scripts/update.sh nousresearch/hermes-agent@sha256:<digest>`. It validates/pulls the digest before changing state, makes a safe backup, saves the old deployment .env under data/, then replaces the image, reconciles config and verifies. Bootstrap waits up to 180 seconds for healthy startup before verification. Do not run hermes update inside a running container. A newly changed config schema may need explicit migration review. If an upgrade fails, retain its logs, restore the previous pin and recover the pre-update backup into an empty location before replacing state; do not overwrite SQLite blindly.
