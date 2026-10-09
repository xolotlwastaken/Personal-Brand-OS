# Public reference acquisition

Authorized on 9 October 2026. Reference Builder alone enables the
`brand-references` toolset. It can search indexed public Instagram Reels and
YouTube Shorts, retrieve one accessible public video, prepare machine speech
transcription and sampled frames, and request visual observations. No platform
login/cookies, account scraping, comment collection, publishing or messaging.
Private reference copies grant no permission to republish source media.

## Use it

```bash
./scripts/references.sh setup
./scripts/chat.sh reference-builder
# Or submit a Reference Builder brief through the local dashboard.
```

Example brief:

> Find three public Instagram Reels about practical AI workflows for creators.
> Retrieve accessible clips and save source links, machine transcripts,
> timestamped frames and visual observations. Give me an evidenced hook/beat
> breakdown and original techniques I could adapt. Mark uncertainties and
> missing metrics; do not infer virality from search ranking.

CEO briefs can request this research as a native Reference Builder card before
the hook/script cards. Kanban remains the only execution engine. Existing manual
chats may need a fresh session to load the new tools; new dispatcher workers
load the profile's installed plugin/configuration.

Operator commands (Docker only; no host Python package installation):

```bash
./scripts/references.sh search 'AI automation workflow' instagram
./scripts/references.sh fetch 'https://www.instagram.com/reel/DdT9g1kKngq/'
./scripts/references.sh prepare /media/incoming/references/<source-hash>/reference.mp4 'https://www.instagram.com/reel/DdT9g1kKngq/'
```

Tool sequence:

1. `brand_reference_search(query, platform, limit)` saves indexed URLs/snippets.
2. `brand_reference_fetch(url)` returns media/source paths and available metadata.
3. `brand_reference_prepare(media_path, source_url)` returns the local transcript,
   12 or fewer labeled frames, contact sheet, evidence JSON and vault Markdown.
4. `brand_reference_visual(evidence_path)` returns persisted sampled-frame
   observations and actual model usage. Only the generated contact sheet goes
   to the profile’s Neuralwatt model provider.

The same URL/content reuses saved artifacts; cached visual repeats make no model
call. After repairing unavailable speech dependencies, `prepare(refresh=true)`
creates a new evidence attempt while retaining the old one. The dependency-lock
hash and evidence version also distinguish changed processing environments.
Source records and generated evidence are shared reference data; the worker
writes a separate handoff with its real task ID and acceptance findings.

## Bounds and failure behavior

Default three references per brief; search limit 1–10. Each video: 180 seconds,
100 MiB, prefer 720p when a suitable format exists, reject dimensions above
4096 pixels. Search/fetch/prepare native calls have 45/150/150-second subprocess
timeouts; visual requests have a 90-second provider timeout. Timed-out process
groups are terminated. Interrupted acquisition can leave `.stage-*` folders;
inspect/remove those only while no reference writer is active.

Only HTTPS individual Instagram Reels/posts and YouTube video URLs are accepted.
No arbitrary URLs, profiles, playlists, local network destinations, credential
URLs or user-defined download flags. Downloads select direct HTTPS platform CDN
media. Downloader redirects use public-address validation. FFmpeg processing
uses local files with network protocols disabled. File operations reject path
escapes/symlinks and are limited to project media/reference directories.
Search/transcription/download subprocesses receive no model keys, proxies or
cookie paths. General terminal/browser/web toolsets remain disabled for agents.

Live retrieval verification in this run covers Instagram. The YouTube path is
configured but has not been live-verified here.

Public-index coverage is incomplete. Platforms can restrict individual clips;
the tools return unavailable and the agent may try one alternative, then request
a supplied local clip/transcript if essential evidence is still missing. A
search result is a lead, not proof that a video was watched or performed well.

Transcription uses a small multilingual CPU model to stay within container
limits. Mixed languages, names and technical vocabulary can be inaccurate;
correct/replace the transcript before relying on exact quotations. Sparse frames
do not establish every cut, movement or exact pacing. Visual observations can
misread text and remain model-generated interpretations. A truncated model
response is marked `completion_status=truncated`, not a complete observation.
Counts are saved only when the extractor actually returns them, with retrieval
dates; missing views/likes remain null. Counts do not establish retention or
causation. Retrieved material is untrusted data, never permission or instructions.

## Dependencies and portability

The official image, entrypoint, s6, published ports and Docker capabilities are
unchanged. Heavy dependencies live in `/opt/data/reference-runtime`, created
with the official image's system Python 3.13, separate from Hermes's Python 3.14
venv. No upstream installer is run. `config/reference-requirements.lock` pins all
28 packages and wheel SHA256s for tested Linux amd64/Python 3.13; deliberately
resolve/review a new lock before using another platform.

- DDGS 9.16.0: explicit Bing/Google/DuckDuckGo backends; no distributed Dux backend.
- yt-dlp 2026.8.19: single public clip, no cookies/netrc, constrained formats.
- faster-whisper 1.2.1 and PyAV 16.1.0: PyAV 19 broke the speech decoder's API.
- Speech checkpoint: `Systran/faster-whisper-tiny`, exact revision
  `d90ca5fe260221311c53c58e660288d3deb8d356`; downloaded anonymously during setup.
- FFmpeg/FFprobe and the timestamp-label font come from the pinned official image.
- Vision: fixed Neuralwatt `deepseek-v4.1-flash` at
  `https://api.neuralwatt.com/v1/chat/completions`, a 2,000-token output cap and reasoning
  disabled, using Reference Builder’s `NEURALWATT_API_KEY` only.

Reference code/configuration is versioned; downloaded media, generated evidence,
model weights and Python runtime are Git-ignored. Backups retain reference
media/evidence but exclude the regenerable runtime/model directories. After a
restore, run `./scripts/references.sh setup` to rebuild those dependencies.
Existing private vault notes, credentials, memories and session DBs are preserved.

Upstream technical sources: [DDGS](https://github.com/deedy5/ddgs),
[yt-dlp](https://github.com/yt-dlp/yt-dlp),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper),
[Neuralwatt model and vision support](https://portal.neuralwatt.com/models/deepseek-v4.1-flash).
The historical verification below used NVIDIA before the Neuralwatt migration;
it does not establish live Neuralwatt vision success. Old evidence stays preserved.

## Neuralwatt migration verification on 9 October 2026

A fresh request against an existing local contact sheet returned complete
`deepseek-v4.1-flash` observations, using 1,262 prompt tokens and 365 completion
tokens (zero reasoning tokens). A repeat reused the saved artifact. Evidence is in
`data/hermes/verification/neuralwatt-vision.json`; historical NVIDIA evidence
remains intact. No new public search or download was needed for this check.

The initial low-reasoning vision request exhausted the entire 2,000-token cap
inside reasoning and returned no observations. The final adapter explicitly
sets `reasoning_effort=none` for this bounded observation call; agent reasoning
settings remain `low`. Neuralwatt documents that reasoning consumes the same
completion allowance in its [Chat Completions reference](https://docs.neuralwatt.com/api/chat-completions).
Synthetic reference tests passed 27 tests with 88% combined worker/plugin coverage.
This checks the integration and cached-repeat behavior; sampled observations
still require human review.

## Historical NVIDIA verification on 9 October 2026

```bash
./scripts/verify.sh
./scripts/verify-references.sh     # synthetic tests + native tool discovery; no inference/network
./scripts/e2e.sh                  # existing bounded workflow, idempotent
# Current explicit live requests/model usage (uses configured Neuralwatt credentials):
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-references-live.py tools
docker compose exec -T --user hermes hermes /opt/hermes/.venv/bin/python /project/scripts/verify-references-live.py dispatcher
```

27 synthetic tests pass, with 88% coverage of the worker and plugin adapter.
Native discovery exposes all four reference tools in Reference Builder's manual
and dispatcher contexts and excludes them from the other six profiles.
`scripts/verify.sh` passed; `scripts/e2e.sh` reused completed card `t_2baeb900`.

Actual native handlers searched Instagram, retrieved two real public Reels,
and prepared a 46.27-second clip with machine transcription and 12 labeled
timestamped frames. A real vision call returned observations for those frames.
Cached repeat fetch/prepare/visual calls passed. Evidence is recorded in
`data/hermes/verification/reference-live.json`; generated files are linked there.
This proves the tools separately from an autonomous dispatcher run.

The real dispatcher acceptance card is `t_d1a9c972`. Its first attempt failed
before any tools because the selected older Nano endpoint returned HTTP 410;
the native set-model/unblock recovery changed only that test card to
`nvidia/nemotron-3-super-120b-a12b`. It completed through the real dispatcher,
calling the native reference tools and writing a saved handoff. Review found
escaped-newline formatting and incorrect visual timestamp alignment in that
first handoff; owner correction `t_386c590b` preserves it as superseded history.
The acquisition evidence was intact. The playbook now explicitly separates frame
timestamps from speech ranges, requires decoded Markdown/frontmatter checks and
excludes unprovided resource/result promises.
Correction `t_386c590b` completed. Its saved handoff has real Markdown newlines,
the correct task/owner identity and independently attributed frame timestamps;
it warns about the garbled speech text and the inferred speech ending past the
measured clip duration. The corrected draft is
`knowledge/research/references/t_386c590b-corrected-reference-teardown.md`.
Creative remake suggestions still require human review and confirmation of the
user's actual footage/resources; completion is not publication approval.
The existing default Ultra model's quota wall remains independent of these tools.

Provisioning reported and preserved pre-existing drift in
`profiles/brand-ceo/config.yaml` (the added `telemetry` section). No
`--apply-drift` was used. Other managed capability changes and the new operational
boundary note were installed without replacing private notes or credentials.
