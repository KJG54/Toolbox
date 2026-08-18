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
toolbox catalog index assets --output outputs/assets-catalog.json
toolbox texture validate textures
toolbox blender batch assets --output-dir outputs/converted --format glb --preview
toolbox audio assemble intro.wav narration.wav --output outputs/track.wav
toolbox delivery package outputs/delivery --output outputs/delivery.zip --require asset.glb
toolbox atlas pack sprites --output outputs/sprites.png
toolbox video assemble intro.mp4 main.mp4 --output outputs/final.mp4
toolbox blender assign-material asset.blend --textures textures --output outputs/asset-textured.blend
toolbox research evaluate-generation image
toolbox catalog find-duplicates assets
toolbox texture export-profile texture.png --profile mobile --output outputs/texture.webp
toolbox review export-subtitles outputs/review.json --output outputs/review.vtt
toolbox audio mix --narration narration.wav --bed music.wav --output outputs/mix.wav
toolbox blender turntable asset.blend --output-dir outputs/turntable
toolbox game scaffold-kit --name "My Prototype" --output outputs/my-prototype
toolbox game naming-plan assets
toolbox game manifest assets --output outputs/assets-before.json
toolbox game compare-manifests outputs/assets-before.json outputs/assets-after.json
toolbox game plan-highlights outputs/review.json --output outputs/highlights.json
toolbox video contact-sheet playthrough.mp4 --output outputs/playthrough-sheet.png
toolbox blender handoff-report prop.blend
toolbox audio procedural --kind loop --duration 12 --output outputs/music-loop.wav
toolbox audio procedural --kind coin --output outputs/coin.wav
toolbox blender procedural-prop --kind crate --output outputs/crate.blend
toolbox game engine-readiness
toolbox game godot-scaffold --name "My Godot Prototype" --output outputs/my-godot-game
toolbox game godot-inspect outputs/my-godot-game
toolbox game godot-import-map outputs/my-godot-game
toolbox texture export-profile texture.png --profile godot-mobile --output outputs/texture.png
toolbox game sprite-animation-plan outputs/sprites.atlas.json --output outputs/animations.json
toolbox game compare-gameplay outputs/baseline-review.json outputs/candidate-review.json
toolbox game prototype-handoff outputs/my-godot-game --require-build
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

Use `toolbox catalog` to search your downloaded assets without contacting an asset provider.
`toolbox texture validate` gives naming and image-property evidence before a material handoff.
`toolbox blender batch` keeps source 3D files intact while making a bounded set of derivatives.
`toolbox audio assemble` joins local clips in order. `toolbox delivery audit` and `toolbox delivery
package` require the requested files and provenance records before they produce a ZIP handoff.

Use `toolbox atlas pack` for local sprite and texture sheets, `toolbox video assemble` for ordered
clips, and `toolbox blender assign-material` for a reviewable material-map derivative. Local image,
music, and SFX model research remains an explicit approval gate: `toolbox research evaluate-generation`
reports only the candidate, current hardware fit, and required changes—it never installs or routes to cloud compute.

Use `toolbox catalog find-duplicates` to reduce review clutter without deleting assets. Texture profiles,
Watch subtitle/chapter exports, local audio mixing, and Blender turntables all produce reviewable local derivatives.

For a mostly-free game prototype, start with `toolbox game scaffold-kit`, generate temporary original procedural
music/SFX and a simple Blender prop, then use the manifest and handoff-report commands as assets become real.
Procedural audio is deliberately a simple local synthesis tool—not a substitute for an AI music model or a final
license review of externally acquired assets. `toolbox game engine-readiness` only detects installed engine commands;
it never installs or selects an engine for you. Image-generation providers remain an explicit, external workflow.

`toolbox game godot-scaffold` creates a minimal project definition and scene only; it does not download or run Godot.
Godot assets are expected to live in the project folder and are mapped as reviewable `res://` paths. The installed editor,
not Toolbox, generates and validates import metadata. Godot texture profiles create local PNG derivatives; sprite animation
plans group Toolbox atlas entries by filename prefix. Use gameplay comparison to flag evidence events that were previously
observed but are no longer observed, and use prototype handoff audit for structural/provenance readiness before sharing.
