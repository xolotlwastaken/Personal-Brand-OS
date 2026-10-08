---
name: reel-builder
description: "Local Personal Brand OS reel-builder playbook; supplied evidence, Markdown handoffs, draft outputs."
license: MIT
metadata:
  author: Ootto; adapted for Personal Brand OS
  upstream_revision: 5263be7b209fee3f98a59ec185446b8144bca88f
---

# reel-builder

## Scope and inputs

Use Hermes native file and skills tools, never Claude connectors or installers. Shared vault: /knowledge; media: /media. Inputs are supplied by the task contract, not fetched by imaginary integrations. Follow /knowledge/operations/conventions.md and /knowledge/operations/handoffs.md. Include actual Kanban task_id, owner, status, sources, assumptions and artifact paths. Do not fabricate experiences, opinions, achievements or statistics. Missing data stays explicitly missing. All social publishing, messaging, scraping, expensive generation and rendering are disabled. Prompt playbooks are not tool integrations.

## Procedure

Translate an approved script into a beat-by-beat editing plan: spoken line reference, overlay, visual, cut, duration, caption style and missing footage. Verify timing and source links. Do not rewrite the specialist's script or render/generate video. Future FFmpeg/Remotion/Seedance integrations require separate review.

## Finish

Persist the output requested by the task, read it back, check acceptance criteria, and report it using kanban_complete with a summary and artifact paths in metadata. If essential input is missing, use kanban_block with kind needs_input; never silently complete. Ask the CEO for cross-owner changes and human approval for major strategy changes.

## Attribution

Adapted from [Ootto content skills](https://github.com/Ootto-AI/claude-content-skills/tree/5263be7b209fee3f98a59ec185446b8144bca88f/skills/reel-builder) at `5263be7b209fee3f98a59ec185446b8144bca88f`. The original is preserved under /project/vendor/ootto/reel-builder; the MIT license is included. Upstream instructions are reference material only; use this adapted procedure.
