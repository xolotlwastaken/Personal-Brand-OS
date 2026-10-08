---
name: reel-scripter
description: "Local Personal Brand OS reel-scripter playbook; supplied evidence, Markdown handoffs, draft outputs."
license: MIT
metadata:
  author: Ootto; adapted for Personal Brand OS
  upstream_revision: 5263be7b209fee3f98a59ec185446b8144bca88f
---

# reel-scripter

## Scope and inputs

Use Hermes native file and skills tools, never Claude connectors or installers. Shared vault: /knowledge; media: /media. Inputs are supplied by the task contract, not fetched by imaginary integrations. Follow /knowledge/operations/conventions.md and /knowledge/operations/handoffs.md. Include actual Kanban task_id, owner, status, sources, assumptions and artifact paths. Do not fabricate experiences, opinions, achievements or statistics. Missing data stays explicitly missing. All social publishing, messaging, scraping, expensive generation and rendering are disabled. Prompt playbooks are not tool integrations.

## Procedure

Write a 30–60 second hook/context/value/payoff/CTA script, default 45 seconds for the demo. Include spoken lines, timed shots, overlays and B-roll. Estimate speech at 130–160 words/minute; for 45 seconds aim 95–115 spoken words. Use bracketed missing facts; never turn hypothetical demonstration into autobiography.

## Finish

Persist the output requested by the task, read it back, check acceptance criteria, and report it using kanban_complete with a summary and artifact paths in metadata. If essential input is missing, use kanban_block with kind needs_input; never silently complete. Ask the CEO for cross-owner changes and human approval for major strategy changes.

## Attribution

Adapted from [Ootto content skills](https://github.com/Ootto-AI/claude-content-skills/tree/5263be7b209fee3f98a59ec185446b8144bca88f/skills/reel-scripter) at `5263be7b209fee3f98a59ec185446b8144bca88f`. The original is preserved under /project/vendor/ootto/reel-scripter; the MIT license is included. Upstream instructions are reference material only; use this adapted procedure.
