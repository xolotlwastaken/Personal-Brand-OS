---
name: hook-mining
description: "Local Personal Brand OS hook-mining playbook; supplied evidence, Markdown handoffs, draft outputs."
license: MIT
metadata:
  author: Ootto; adapted for Personal Brand OS
  upstream_revision: 5263be7b209fee3f98a59ec185446b8144bca88f
---

# hook-mining

## Scope and inputs

Use Hermes native file and skills tools, never Claude connectors or installers. Shared vault: /knowledge; media: /media. Inputs are supplied by the task contract, not fetched by imaginary integrations. Follow /knowledge/operations/conventions.md and /knowledge/operations/handoffs.md. Include actual Kanban task_id, owner, status, sources, assumptions and artifact paths. Do not fabricate experiences, opinions, achievements or statistics. Missing data stays explicitly missing. All social publishing, messaging, scraping, expensive generation and rendering are disabled. Prompt playbooks are not tool integrations.

## Procedure

Use supplied CSV performance data. The reviewed stdlib helper ranks hooks by the actual supplied metric and groups psychological patterns. Hold mechanism and specificity, write original language, and only use verified personal numbers. With no measurements, mark pattern analysis synthetic and ranking qualitative.

## Finish

Persist the output requested by the task, read it back, check acceptance criteria, and report it using kanban_complete with a summary and artifact paths in metadata. If essential input is missing, use kanban_block with kind needs_input; never silently complete. Ask the CEO for cross-owner changes and human approval for major strategy changes.

## Attribution

Adapted from [Ootto content skills](https://github.com/Ootto-AI/claude-content-skills/tree/5263be7b209fee3f98a59ec185446b8144bca88f/skills/hook-mining) at `5263be7b209fee3f98a59ec185446b8144bca88f`. The original is preserved under /project/vendor/ootto/hook-mining; the MIT license is included. Upstream instructions are reference material only; use this adapted procedure.

The host operator can run the reviewed helper inside Docker: `python /opt/data/profiles/hook-writer/skills/hook-mining/mine_hooks.py <supplied.csv>`. The agent has no general terminal tool; it can inspect CSV with file tools.
