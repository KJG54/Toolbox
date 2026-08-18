# Agent Creator Toolbox

Toolbox is a local-first capability registry and selection layer for agents. It answers
what is available, whether it is installed, whether local hardware can run it, and what
must be reviewed before an agent uses an external service or new tool.

Start with:

```powershell
toolbox doctor
toolbox search watch
toolbox recommend watch_video --commercial --free
toolbox run normalize-media recording.mov --output outputs/recording-proxy.mp4
toolbox run watch-review recording.mov --output outputs/recording-review.json --normalize
toolbox review ask outputs/recording-review.json "When do the calibration bars appear?"
toolbox review assess outputs/asset-review.json --criteria criteria.json --output outputs/asset-assessment.json
toolbox review tutorial outputs/tutorial-review.json --steps tutorial-steps.json --output outputs/tutorial-verification.json
toolbox review gameplay outputs/playthrough-review.json --events gameplay-events.json --output outputs/gameplay-review.json
toolbox library search outputs "Where do we change the export setting?" --semantic
toolbox blender convert asset.blend --output outputs/asset.glb
toolbox blender preflight asset.blend
toolbox blender preview asset.blend --output outputs/asset-preview.png
toolbox visual compare reference.png candidate.png
toolbox tts speak "Local narration" --output outputs/narration.wav
toolbox research gap generate_image --commercial --free
toolbox research assets "stone wall texture" --kind texture --commercial
toolbox image prepare reference.png --output outputs/reference.webp --max-width 2048
toolbox audio clean narration.wav --output outputs/narration-clean.wav
toolbox blender game-asset prop.blend
toolbox blender create-lod prop.blend --output outputs/prop-lod.blend --ratio 0.5
toolbox vision describe reference.png --task detailed-caption
toolbox research generation music
```

Read [TOOLBOX.md](TOOLBOX.md) before asking an agent to create an artifact. The preserved
Watch source lives in `components/watch-skill`; TTS material is deliberately retained as
examples rather than presented as a production engine.

`watch-review` is the local evidence workflow: it optionally creates a portable proxy,
runs the preserved Watch component, and saves timestamped frames and available transcript
segments as a versioned JSON timeline. Cloud STT and model downloads are blocked; `--ocr`
and `--local-whisper` are explicit local add-ons, with Whisper restricted to already-cached
models.

Use `toolbox review ask` to query a saved review without reprocessing the original video.
It returns matching transcript or OCR evidence with timestamps and never invents content
that is not represented in the local timeline.

Use `toolbox review assess` for an explicit asset-review checklist. It can pass or fail
only from matching local transcript/OCR evidence; criteria without that support are marked
`NEEDS_HUMAN_REVIEW` instead of being guessed.

Use `toolbox review tutorial` to verify that a software walkthrough covered expected steps
in order. Missing or out-of-order evidence is reported honestly with the matching timestamps.

Use `toolbox review gameplay` for ordered gameplay events, and `toolbox library search` to
search local review timelines without reprocessing original media. The optional semantic
search uses the cached local embedding model. Add `--ocr --local-whisper --whisper-model tiny`
to `watch-review` when locally cached OCR and offline transcription are wanted.

Use `toolbox visual` for local pixel/perceptual comparison of still images and rendered previews.
It is not a semantic vision-language model. `toolbox blender preflight` detects missing linked
images and scene readiness without auto-running scripts embedded in the `.blend` file. `toolbox
research` produces either deterministic routing advice or a review-only gap brief; it never installs
software, downloads an asset, or contacts a service.

Use `toolbox image prepare` to make a derived texture or reference image without replacing the
original. Its `--allow-upscale` option uses high-quality interpolation, not generative detail. Use
`toolbox audio clean` for a local trim and loudness-normalization derivative. `toolbox blender
game-asset` reports, but does not create, UVs, LODs, or collision objects. Local music and SFX
generation are research-only until an exact runtime and model have been reviewed and approved.

Use `toolbox blender create-lod` to create a separate, decimated `.blend` derivative; inspect it
before importing it into a game. `toolbox vision describe` uses the approved, pinned Florence-2 Base
model from the local cache only. This environment currently runs it on CPU, which is suitable for
occasional still-image inspection but may be slow for detailed or large images.
