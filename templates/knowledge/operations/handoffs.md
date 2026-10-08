# Artifact handoff formats

Common frontmatter:
```yaml
id: <task-id>-<artifact-slug>
task_id: <real-kanban-id>
owner: <profile-name>
created: <actual-current-YYYY-MM-DD; or verified ISO8601-with-+08:00>
status: draft # draft / review / approved / blocked
sources: [<paths-or-URLs>]
assumptions: []
approval: pending # pending / not-required-for-draft / human-approved
```
Common end: **Acceptance checks**, **Uncertainties / missing inputs**, **Completion summary**, **Persistent artifact paths**. Native kanban_complete.metadata.artifact_paths must match actual files.

Brand brief: topic, objective, audience, evidence-led angle, voice rules, supplied personal details, missing facts, source notes.

Research: topic/objective, audience, sources/URLs, observed formats, hook patterns, beat structure, measured evidence (or unavailable), recommendations, uncertainty.

Hooks: topic, research reference, five spoken candidates and on-screen variants, ranking criteria, top three, selected recommendation and explanation.

Script: title/objective/audience, selected hook/source, complete spoken script, timed shot table with on-screen text, B-roll, transitions, CTA, spoken word count/duration estimate and missing personal facts.

Editing plan: script reference, footage requirements, shot sequence, estimated timings, graphics/caption styling, future rendering requirements, missing footage and timing validation.

Publication package: asset/script reference, caption, hashtags/keywords, proposed local date/time and timezone, approval status, platform constraints to verify, readiness checklist. Always draft; no live publishing.

CEO review: request, task graph IDs and owners, validated linked deliverables, quality findings, revisions if needed, blockers, approval needs and final outcome.

Task contracts must include title, assignee, objective, context, input artifacts, output requirements, acceptance criteria and dependencies. Create tasks with workspace dir:/knowledge. Parent result summaries convey paths; they do not replace reading artifacts.
