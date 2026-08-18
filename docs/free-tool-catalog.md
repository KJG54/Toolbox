# Free Tool and Website Catalog

> Research snapshot: 2026-08-18. This is a curated starting point, not an
> exhaustive directory or legal advice. “Free” can mean free/open-source
> software, a no-cost hosted tier, or an asset with a free-content license.
> Before a production use, recheck the linked official license/terms and record
> the exact version and asset/model license in provenance.

## How humans and agents should use this catalog

1. Start with an installed local tool in the Toolbox registry.
2. If none is suitable, prefer a **local-first** item below. Check disk, RAM,
   GPU, formats, and the current license before proposing an install.
3. Use an **external opt-in** website only after the owner approves the exact
   service and the media/data that may leave the machine. A free tier is not a
   promise of free commercial use, privacy, unlimited credits, or permanence.
4. For downloadable assets, save the asset URL, creator, license, and required
   attribution in the asset provenance sidecar. Do not infer a whole site's
   license from one asset.
5. Never silently add a registry record, install software, download a model,
   create an account, upload media, or use a paid/credit-based feature.

### Fast agent recommendation template

```text
Need: <capability + inputs/outputs>
Best current option: <installed local tool, or local-first candidate>
Why: <fit, format, license, privacy>
Hardware/runtime: <LOCAL_OK | LOCAL_SLOW | HARDWARE_UPGRADE_REQUIRED>
License/asset check: <exact linked record to verify>
External boundary: <none | approval required before upload/account/API>
Alternative: <one viable fallback>
Output status: <LOCAL_OK | DRAFT_ONLY | PERSONAL_ONLY | ATTRIBUTION_REQUIRED | RECHECK_TERMS>
```

For generative websites, an agent must state the **output status**. A free
credit allotment alone never makes an asset safe to publish, sell, use in a
client project, or train another model on.

`DRAFT_ONLY` means no release use until exact rights are checked;
`PERSONAL_ONLY` means it cannot ship in a commercial/public project;
`ATTRIBUTION_REQUIRED` means the attribution belongs in the release credits and
provenance; and `RECHECK_TERMS` means the site has a potentially usable free
tier but current terms must be confirmed for that exact output.

## Local-first creation, editing, and development tools

These entries are websites for obtaining and learning about software that runs
on the local machine. They are the preferred first choices for Toolbox.

| Tool / official site | Best for | Typical game/app use | License / boundary |
| --- | --- | --- | --- |
| [Godot](https://godotengine.org/) | 2D/3D game engine, UI, scripting, exports | Build a game prototype, menus, gameplay, and desktop/mobile/web builds | MIT; use local projects and retain third-party asset notices. |
| [Blender](https://www.blender.org/) | 3D modeling, sculpting, rigging, animation, rendering | Characters, props, environments, turntables, renders, and export to Godot | GPL software; output ownership is separate from input asset rights. |
| [Blockbench](https://www.blockbench.net/) | Low-poly/voxel models, UVs, pixel textures, animation | Fast stylized props and game-ready low-poly characters | GPL; especially good when Blender is more than a task needs. |
| [Krita](https://krita.org/) | Raster painting, concept art, texture and sprite creation | UI art, painted textures, concepts, sprite sheets | GPL; project output can be used independently of Krita's code license. |
| [Inkscape](https://inkscape.org/) | SVG/vector art and diagrams | Icons, UI vectors, logos, laser/CNC-ready vectors | GPL; verify fonts and imported artwork separately. |
| [GIMP](https://www.gimp.org/) | Image retouching, compositing, batch image edits | Marketing images, texture cleanup, mockups, format conversion | GPL; local, offline-capable image editing. |
| [Aseprite alternative: LibreSprite](https://libresprite.github.io/) | Pixel art and frame animation | Tile sets, pixel characters, animation frames | Free/open-source fork; check the current project license before distribution. |
| [FFmpeg](https://ffmpeg.org/) | Scriptable audio/video/image conversion and filters | Game trailer assembly, capture conversion, build-pipeline media jobs | License depends on the distributed build/configuration; Toolbox already tracks its local installation. |
| [Kdenlive](https://kdenlive.org/) | Full non-linear video editing, titles, subtitles, effects | Game trailers, tutorials, devlogs, cutscenes | GPL free software; local editor. |
| [Shotcut](https://www.shotcut.org/) | Lightweight cross-platform video editing | Quick cuts, captions, social clips, simple trailers | GPLv3; local editor. |
| [HandBrake](https://handbrake.fr/) | Video transcoding and compression | Deliverable encodes for uploads and store pages | GPLv2; local transcoder. |
| [OBS Studio](https://obsproject.com/) | Screen/game capture and streaming | Gameplay capture, tutorials, visual bug evidence | GPLv2; local capture and recording. |
| [Audacity](https://www.audacityteam.org/) | Waveform editing, cleanup, recording, batch processing | Voice cleanup, SFX editing, dialogue preparation | GPLv3; local audio editor. |
| [LMMS](https://lmms.io/) | MIDI composition and music sequencing | Sketch loops, themes, and simple game music | GPL; samples/plugins have their own terms. |
| [ACE-Step](https://github.com/ACE-Step/ACE-Step-1.5) | Local AI music generation | Draft non-licensed music ideas and iteration material | Already installed in Toolbox; current RTX 2060 profile is `LOCAL_SLOW`. Verify model and output terms before release. |

## 3D, CAD, fabrication, and physical prototyping

| Tool / official site | Best for | Practical use | License / boundary |
| --- | --- | --- | --- |
| [FreeCAD](https://www.freecad.org/) | Parametric mechanical CAD | Enclosures, fixtures, measured parts, assemblies, STEP export | LGPL 2+; local CAD. |
| [OpenSCAD](https://openscad.org/) | Scripted/parametric solid modeling | Repeatable 3D-print parts, game-controller mounts, custom brackets | GPLv2; excellent when dimensions should live in version control. |
| [PrusaSlicer](https://www.prusa3d.com/page/prusaslicer_424/) | 3D-print slicing and print preparation | Convert validated models into printer-specific G-code | Free/open source; local; a slicer does not guarantee a model is printable. |
| [KiCad](https://www.kicad.org/) | Electronics schematics and PCB design | Controller boards, LED props, small physical game peripherals | GPLv3+ software; symbol/footprint/library licenses can differ. |
| [MeshLab](https://www.meshlab.net/) | Mesh inspection, repair, simplification, conversion | Clean scans, reduce triangle counts, inspect geometry before print/export | GPL; validate manifoldness and scale separately. |
| [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) | Advanced 3D-print slicing | Alternative printer profiles and calibration workflow | Open-source project; verify the current release license and printer profile source. |

## Game, app, and software-engineering foundations

| Tool / official site | Best for | Practical use | License / boundary |
| --- | --- | --- | --- |
| [Git](https://git-scm.com/) | Version control | Source history, reproducible changes, collaboration | GPLv2; local repository operations. |
| [VSCodium](https://vscodium.com/) | Code editor built from VS Code sources | General programming, game scripts, configuration | MIT-licensed build artifacts/source where stated; extensions each have their own terms. |
| [Tauri](https://tauri.app/) | Small desktop apps using web UI + Rust | Package a local Toolbox or game companion desktop app | MIT or Apache-2.0; app dependencies still require review. |
| [Flutter](https://flutter.dev/) | Cross-platform app UI | Mobile/desktop companion apps and tools | BSD-style project license; third-party packages vary. |
| [Phaser](https://phaser.io/) | JavaScript/TypeScript 2D web games | Browser prototypes, minigames, playable landing pages | MIT; suitable with a normal web build chain. |
| [SQLite](https://sqlite.org/) | Embedded local database | Save games, local app state, asset catalogs | Public domain; local file database. |
| [Playwright](https://playwright.dev/) | Browser automation and testing | Test web builds, capture regression evidence, automate repetitive browser checks | Apache-2.0; target-site terms still apply. |
| [Godot Asset Library](https://godotengine.org/asset-library/asset) | Godot plugins and templates | Accelerate a prototype with reviewed community add-ons | Each asset has its own license; treat as third-party code. |

## Local AI and automation candidates

These are candidates, not authorized installs. Local model weights are always a
separate download with a separate license and hardware gate.

| Tool / official site | Best for | Practical use | Boundary |
| --- | --- | --- | --- |
| [Ollama](https://ollama.com/) | Running selected LLMs on a local machine | Private draft assistance, local chat, embeddings, scripted experiments | MIT runtime; select models individually and record their model licenses. Smaller models may be usable locally; `toolbox doctor` should decide. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Low-level local LLM inference | More controlled CPU/GPU quantized-model experiments | MIT; model license and hardware are separate. |
| [Node-RED](https://nodered.org/) | Visual local automation | Connect local files, webhooks, devices, and repeatable workflows | Apache-2.0; review nodes, credentials, and external endpoints. |
| [n8n](https://n8n.io/) | Workflow automation | Self-hosted internal automations with approvals | Source-available/fair-code terms, not a blanket open-source/commercial-use claim; review its current license before deployment. |
| [Activepieces](https://www.activepieces.com/) | Workflow automation | Simpler self-hosted automations and integrations | Review edition and current license before using commercially. |
| [ComfyUI](https://www.comfy.org/) | Node-based image-generation workflow host | Reproducible local image pipelines when suitable hardware and approved models exist | Interface/code and every model/node have separate terms. Flux remains owner-deferred; do not install it from this catalog. |

## Generative websites and AI editors — external opt-in

This is the deliberately external part of the catalog: services that generate
or substantially edit media on their servers. They are useful for fast
concepting and for working around local hardware limits, but every one requires
approval before an agent sends a prompt, reference, image, audio, video, code,
or model to it.

| Website | What it generates or edits | Current no-cost access | Output status and practical use |
| --- | --- | --- | --- |
| [Ideogram](https://ideogram.ai/) | Text-to-image, design images, image concepts with readable text | Free plan with slow credits (currently 10/week, up to 40 images/week) | `RECHECK_TERMS`. Its plan page says it does not restrict output rights, but free generations are not private; use for posters, UI concepts, and image references—not confidential inputs. |
| [Adobe Express / Firefly](https://www.adobe.com/express/pricing) | Image generation, insert/remove objects, editable templates, basic photo/video/document editing | Free plan offers limited daily generative actions and two lifetime five-second video trials | `RECHECK_TERMS`. Strong all-in-one option for social/video/game-marketing edits; keep its current asset and Firefly terms with the provenance record. |
| [Runway](https://runway.com/pricing) | Text/image-to-video, image generation, video transforms, upscaling, audio tools | 125 one-time free credits and 5 GB storage | `DRAFT_ONLY` until current output rights are verified for the exact account/model. Best for testing cinematic clips, trailer shots, and AI-assisted video fixes. |
| [Pika](https://pika.art/pricing) | Text/image-to-video plus additions, swaps, scenes, effects, and frames | Free tier currently lists 80 monthly video credits and 480p access | `RECHECK_TERMS`. Its pricing page lists commercial use on the free tier, but preserve the plan snapshot and terms before a game/trailer release. Useful for short VFX and animated marketing shots. |
| [Luma](https://lumalabs.ai/) | Text/image-to-video, video modification, image generation | Web free plan with limited monthly credits and draft resolution | `PERSONAL_ONLY`. Free output is watermarked/non-commercial and Luma's terms grant broad rights to free-use output; use only for disposable visual experiments. |
| [Meshy](https://www.meshy.ai/pricing) | Text/image-to-3D mesh, texture generation, remesh/refine | Free plan: 100 monthly credits, no credit card | `ATTRIBUTION_REQUIRED`. Free-plan outputs are CC BY 4.0; retain attribution. Useful for fast prop/blockout ideas, then clean topology/UVs in Blender before game or printing use. |
| [Tripo](https://www.tripo3d.ai/pricing) | Text/image-to-3D and model editing | Free plan currently lists 200 credits/month (up to eight models), public CC BY 4.0 models, and limited downloads | `ATTRIBUTION_REQUIRED` and `NONCOMMERCIAL_UNLESS_REVERIFIED`. Tripo's game-development guidance says free-plan models do not support commercial use. Use as reference/blockout, not a released paid-game asset. |
| [Suno](https://suno.com/pricing) | Text-to-music, song extension, basic audio uploads/edits | Free plan: 50 daily credits | `PERSONAL_ONLY`. Free-plan songs are non-commercial and Suno says it retains ownership; do not put them in a commercial game, monetized video, or client work. Use to explore music direction, then recreate locally or acquire rights. |
| [ElevenLabs Sound Effects](https://join.elevenlabs.io/sound-effects) | Text-to-SFX, looping ambience, foley, UI/game effects | Free plan currently advertises 50 SFX generations/month | `PERSONAL_ONLY` by the pricing page; its public free-sounds page has different attribution language. Treat the free tier as non-release material unless the current account terms specifically authorize the intended use. |
| [ElevenLabs](https://elevenlabs.io/pricing) | Text-to-speech, speech-to-text, voice design, music, dubbing, SFX | Free plan currently includes 10,000 credits/month across supported tools | `RECHECK_TERMS`. Useful for prototype narration, placeholder dialogue, and accessibility experiments; never clone a voice without rights/consent. |
| [Bolt.new](https://bolt.new/pricing) | Prompt-to-web app/site, code edits, browser preview, hosting | Free plan currently lists 300K tokens/day and 1M/month | `RECHECK_TERMS`. Great for disposable app/game-web prototypes; export code and review security, licenses, dependencies, and hosting before relying on it. |
| [Replit](https://replit.com/pricing) | Prompt-to-app, web development, database, deployment, media/slide creation | Free Starter tier with daily Agent credits and one published app | `RECHECK_TERMS`. Use for a quick working prototype, never as a substitute for local review, secret handling, or production testing. |
| [Lovable](https://lovable.dev/) | Prompt-to-web app and UI, hosted backend/AI options | Free daily build credits; limited monthly Cloud/AI usage | `RECHECK_TERMS`. Good for UI/product exploration, but hosted data, AI, and deployment consumption are external and quota-driven. |

### Generation-site selection rules

- **A commercial release needs a release-safe output status.** `PERSONAL_ONLY`
  and `DRAFT_ONLY` outputs may inspire a replacement, but they never ship.
- **3D generation makes a starting mesh, not a print-ready or game-ready asset.**
  Inspect non-manifold geometry, scale, UVs, texture license, topology,
  rigging, and polygon budget in Blender/FreeCAD/PrusaSlicer as appropriate.
- **Use an approved reference only.** An external service is not allowed to
  receive another creator's protected work, private gameplay footage, client
  files, unreleased code, personal voice, or credentials without explicit
  approval and rights.
- **Store a provenance sidecar** with provider, plan/tier, generation time,
  prompt/reference identifiers, output URL or hash, terms URL, and all later
  human edits. Do not store secrets or sensitive prompts in public metadata.
- **Paid conversion is a new approval.** An agent may point out that a paid
  tier changes rights or removes a watermark; it may not subscribe, buy credits,
  enable auto-reload, or send an API request.

## Free websites and hosted services — external opt-in

These are useful, but they are not local tools. Using them may require an
account and sends data to a third party. Never upload a private project, media,
source code, credentials, or client material without specific approval.

| Website | Useful for | Free-status note | Required guardrail |
| --- | --- | --- | --- |
| [Hugging Face](https://huggingface.co/) | Find model cards, datasets, Spaces demos, and official model files | Access varies by model/Space; models may be gated | Verify the exact model license, terms, files, and hardware before download or use. |
| [GitHub](https://github.com/) | Public source, issues, release provenance, collaboration | Free plans exist; hosted features and limits change | Never publish a repo, issue, secret, or private code without approval. |
| [itch.io](https://itch.io/) | Publish/host games and find game assets | Free publishing/listing is available; individual assets and payments differ | Check each asset/game license and revenue/processing terms. |
| [Photopea](https://www.photopea.com/) | Browser image editing and PSD-compatible quick edits | Free browser use is available | External service: confirm privacy and do not upload protected material without approval. |
| [Excalidraw](https://excalidraw.com/) | Diagrams, whiteboards, architecture sketches | Free web editor and open-source project | Use local/offline export when material is sensitive; shared rooms are external. |
| [Penpot](https://penpot.app/) | UI/UX mockups and collaborative design | Free/self-hosted options are offered | Hosted collaboration is external; review hosting/account plan terms. |
| [Figma](https://www.figma.com/pricing/) | UI design, prototypes, component libraries | A Starter tier is offered; limits change | External account and collaboration; do not assume a paid feature is free. |
| [Supabase](https://supabase.com/pricing) | Hosted Postgres, authentication, storage, server functions | Free plan exists but quotas and policy change | External database and credentials; require approval before project data leaves local storage. |
| [Cloudflare Pages](https://pages.cloudflare.com/) | Static app/game hosting and deployment previews | Free offering exists; limits/terms change | External deployment; require approval before publishing artifacts. |

## Freely licensed asset sources

Downloadable assets are inputs to a release, so their license belongs in each
asset's provenance. CC0 sources are the lowest-friction starting point; mixed
license libraries require per-asset review.

| Website | Strong use cases | License handling |
| --- | --- | --- |
| [Kenney](https://kenney.nl/assets) | Game UI, 2D/3D starter kits, prototype packs | Asset pages are generally CC0; keep the asset page/license record even when attribution is not required. |
| [Poly Haven](https://polyhaven.com/) | PBR materials, HDRIs, 3D environment assets | Site assets are CC0; useful for Blender scenes and game environment prototyping. |
| [OpenGameArt](https://opengameart.org/) | Sprites, tiles, music, SFX, models | Mixed licenses. Filter and record each asset's exact license; do not assume commercial compatibility. |
| [Freesound](https://freesound.org/) | Field recordings, SFX, ambience | Sound licenses vary (including non-commercial variants); filter for the needed rights and preserve attribution. |
| [Game-icons.net](https://game-icons.net/) | SVG icons for prototypes and UI | CC BY 3.0 by default; attribution requirements apply unless a stated exception applies. |
| [Openclipart](https://openclipart.org/) | Simple public-domain-style vector art | Confirm the individual asset status and download source before commercial use. |

## Capability-to-tool shortlist

| Need | Start here | Good fallback / next step |
| --- | --- | --- |
| Build a 2D/3D game | Godot + Git + Krita/Blender | Phaser for web-first 2D; Blockbench for quick low-poly assets |
| Make a game trailer/tutorial | OBS + Kdenlive + FFmpeg | Shotcut for a lighter editor; HandBrake for final encodes |
| Create/edit images and textures | Krita + GIMP + Inkscape | Photopea only after upload approval |
| Make 3D props/environment | Blender + Blockbench + Poly Haven | MeshLab for cleanup; FreeCAD for measured parts |
| Design something for 3D printing | FreeCAD or OpenSCAD + PrusaSlicer | MeshLab to inspect/repair imported meshes |
| Compose or edit audio | LMMS + Audacity + ACE-Step drafts | Freesound only with per-sound license review |
| Build a local desktop utility | Tauri + SQLite + Git | Flutter when mobile is also important |
| Automate repeated local work | Node-RED or scripts + Playwright | n8n/Activepieces only after their edition/license and endpoints are reviewed |
| Explore local AI | ACE-Step for music; Ollama/llama.cpp for text | `toolbox doctor` hardware gate and a model-specific approval first |
| Find production-ready starter assets | Kenney or Poly Haven | OpenGameArt/Freesound with per-asset license and attribution review |

## Deliberate exclusions and future review queue

- **Cloud GPUs, rented compute, remote rendering, and remote job packaging are
  excluded.** If a local task exceeds the machine, return
  `HARDWARE_UPGRADE_REQUIRED`.
- **Flux image generation** and **AI SFX generation** are intentionally
  deferred by owner decision. Do not suggest installing or downloading them
  until that decision changes.
- Credit-based AI generation websites are curated in the external-generation
  section as **opt-in candidates**, not dependable foundations. Their free
  credits, output rights, privacy, and availability change often; check the
  linked live plan before each approved use.
- Future useful categories to add when needed: localization, accessibility
  testing, game telemetry, level design, narrative tooling, 3D scanning,
  photogrammetry, QA/device testing, documentation, and release-store tooling.

## Primary-source verification notes

- Godot publishes its engine under MIT; Blender, Krita, Audacity, Inkscape,
  Kdenlive, and the other projects above link their current terms from their
  official sites. Always prefer those pages over third-party download sites.
- PrusaSlicer describes itself as free/open-source; its help documentation
  identifies its AGPL licensing. FreeCAD is LGPL 2+; KiCad is GPLv3+.
- Shotcut states GPLv3 and commercial use; HandBrake states GPLv2; OBS states
  GPLv2 with free commercial use.
- Kenney and Poly Haven describe their listed asset libraries as CC0. Open
  Game Art and Freesound deliberately have mixed licensing, so their entries
  require asset-level checks.
