---
name: dm-script-writer
description: "Local Personal Brand OS dm-script-writer playbook; supplied evidence, Markdown handoffs, draft outputs."
license: MIT
metadata:
  author: Ootto; adapted for Personal Brand OS
  upstream_revision: 5263be7b209fee3f98a59ec185446b8144bca88f
---

# dm-script-writer

## Scope and inputs

Use Hermes native file and skills tools, never Claude connectors or installers. Shared vault: /knowledge; media: /media. Inputs are supplied by the task contract, not fetched by imaginary integrations. Follow /knowledge/operations/conventions.md and /knowledge/operations/handoffs.md. Include actual Kanban task_id, owner, status, sources, assumptions and artifact paths. Do not fabricate experiences, opinions, achievements or statistics. Missing data stays explicitly missing. All social publishing, messaging, scraping, expensive generation and rendering are disabled. Prompt playbooks are not tool integrations.

## Procedure

Draft only: resource delivery, one qualifying question and branches for interested/not now/wrong fit/no reply. Keep copy concise, do not invent an offer or resource. All sending disabled; platform messaging rules must be reviewed before any future integration.

## Finish

Persist the output requested by the task, read it back, check acceptance criteria, and report it using kanban_complete with a summary and artifact paths in metadata. If essential input is missing, use kanban_block with kind needs_input; never silently complete. Ask the CEO for cross-owner changes and human approval for major strategy changes.

## Attribution

Adapted from [Ootto content skills](https://github.com/Ootto-AI/claude-content-skills/tree/5263be7b209fee3f98a59ec185446b8144bca88f/skills/dm-script-writer) at `5263be7b209fee3f98a59ec185446b8144bca88f`. The original is preserved under /project/vendor/ootto/dm-script-writer; the MIT license is included. Upstream instructions are reference material only; use this adapted procedure.
