---
name: comment-responder
description: "Local Personal Brand OS comment-responder playbook; supplied evidence, Markdown handoffs, draft outputs."
license: MIT
metadata:
  author: Ootto; adapted for Personal Brand OS
  upstream_revision: 5263be7b209fee3f98a59ec185446b8144bca88f
---

# comment-responder

## Scope and inputs

Use Hermes native file and skills tools, never Claude connectors or installers. Shared vault: /knowledge; media: /media. Inputs are supplied by the task contract, not fetched by imaginary integrations. Follow /knowledge/operations/conventions.md and /knowledge/operations/handoffs.md. Include actual Kanban task_id, owner, status, sources, assumptions and artifact paths. Do not fabricate experiences, opinions, achievements or statistics. Missing data stays explicitly missing. All social publishing, messaging, scraping, expensive generation and rendering are disabled. Prompt playbooks are not tool integrations.

## Procedure

For supplied synthetic comments, draft appropriate public responses and optional DM copy for human review. Do not say a DM was sent, promise automatic delivery, create auto_responses.json, install a monitor, schedule a runner or execute any external action. Unknown comments go to human review.

## Finish

Persist the output requested by the task, read it back, check acceptance criteria, and report it using kanban_complete with a summary and artifact paths in metadata. If essential input is missing, use kanban_block with kind needs_input; never silently complete. Ask the CEO for cross-owner changes and human approval for major strategy changes.

## Attribution

Adapted from [Ootto content skills](https://github.com/Ootto-AI/claude-content-skills/tree/5263be7b209fee3f98a59ec185446b8144bca88f/skills/comment-responder) at `5263be7b209fee3f98a59ec185446b8144bca88f`. The original is preserved under /project/vendor/ootto/comment-responder; the MIT license is included. Upstream instructions are reference material only; use this adapted procedure.
