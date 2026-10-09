# Prepare and push to GitHub

Only source, reviewed configuration, templates, tests, documentation and attributed
upstream reference material belong in Git. Private runtime state remains on this
machine: `data/`, `knowledge/`, `media/`, `backups/`, environment files and secret
directories are ignored. `.env.example`, dependency pins and
`templates/knowledge/` remain versioned. The knowledge templates include the
starting brand brief; review that content when choosing repository visibility.

Ignore rules do not remove files already committed. Before the first push, review
both the files being added and existing commits for credentials or private notes.
If a real credential has been committed, rotate it and remove it from history
before publishing. Do not add files using `git add -f` to bypass these rules.

## Local checks

```bash
git status --short
git ls-files --cached --ignored --exclude-standard  # should print nothing
git diff --check
./scripts/verify.sh
```

`verify.sh` requires the provisioned, running project container and reference
runtime. It runs deterministic checks and synthetic reference tests. The separate
`e2e.sh` runs bounded real model inference; use it deliberately when verifying
workflow changes. Never include its runtime output or backups in a commit.

Review new files as well as the existing diff, then stage and inspect the actual
commit contents:

```bash
git diff
git ls-files --others --exclude-standard
git add .
git diff --cached --stat
git diff --cached --check
git diff --cached
git ls-files --cached --ignored --exclude-standard  # should still print nothing
git commit -m "feat: add reference acquisition and local agent dashboard"
```

Choose a commit message that matches the changes you reviewed. Keep the upstream
MIT license and per-skill license files with the vendored/adapted playbooks. No
project-wide license has been chosen; select one deliberately if you intend to
grant reuse rights to your original code.

## First push

Create an empty GitHub repository with your chosen visibility. Leave GitHub's
README, license and `.gitignore` initialization options off, since this repository
already has local history. Replace `YOUR_ACCOUNT` and `YOUR_REPOSITORY` below with
the destination you created:

```bash
git remote add origin git@github.com:YOUR_ACCOUNT/YOUR_REPOSITORY.git
git remote -v
git push -u origin main
```

Use your normal SSH or HTTPS credential helper; never put a token in a remote URL.
If `origin` already exists, inspect it before deciding whether to change it. Push
the intended branch explicitly; avoid `--mirror`, `--all` and force pushes for
this first publication.
