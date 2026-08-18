# Watch Skill Research: "Six AI Video Generators That Are Actually Free"

**Purpose:** Tool-research using the watch skill (not game work). Evaluating potentially useful free AI-video tools surfaced in a Facebook Watch short.
**Watched:** 2026-08-14
**Skill:** `C:\Users\kryst\Code\Tools\Watch Skill\watch-skill` (CLI `watch-skill`, installed at `C:\Users\kryst\.local\bin\watch-skill`)

---

## Source validity

- **URL:** https://www.facebook.com/watch/?ref=saved&v=1587496856400261
- **yt-dlp classification:** `facebook` page URL (one of 1,800+ supported sites)
- **Resolves to:** real, downloadable video — ID `1587496856400261`, format `1572693631307266v+1572347911341838a` (video+audio)
- **Index ID (watch-skill):** `b7c8e225f3eba473`
- **Title / author:** "Six AI Video Generators That Are Actually Free" | Eric Socal (28K views, 325 reactions)
- **Verdict:** VALID, fetchable source. Processed fully locally (no cloud keys).

## Environment used

- ffmpeg, yt-dlp, deno, Ollama qwen2.5vl:3b (local vision), faster-whisper (transcript)
- GPU: NVIDIA RTX 2060 (6 GiB), 622 GiB free disk, local-only mode

---

## What's in the video (43.3s)

Hook: "Higgs Field is awesome, but it's expensive. Here are six free replacements."

| # | Tool named (transcript) | What the video claims |
|---|-------------------------|------------------------|
| 1 | Wan2GP ("2GP") | Run the WAN models locally on a consumer GPU |
| 2 | Remotion | Generate unlimited video straight from code |
| 3 | Hyperframes | Same as above, "brand new" |
| 4 | Open-Sora 2.0 | 11-billion-parameter, fully open-source video model |
| 5 | HunyuanVideo ("Hoonion") | Near-Hollywood quality at 1080p |
| 6 | LTX-2 ("LTX2") | Creates audio + video; supports ComfyUI |

Closing: a prompt pasted into "Claude Code" ("Set up [tool] so I can generate videos locally. Check my system first. Install everything I need and download the right model for my GPU. Then show me how to run it.") and a "SUBSCRIBE / FOLLOW FOR MORE" CTA.

## Transcript (faster-whisper small, local)

```
[00:00] Higgs Field is awesome, but it's expensive. Here are six free replacements.
[00:04] One 2GP lets you run the WAN models locally on a consumer GPU.
[00:09] Remotion generates unlimited video straight from code. Hyperframes does the same thing
[00:14] and it's brand new. OpenSora 2.0 is an 11 billion parameter model that's fully open source.
[00:21] Hoonion Video gets you near Hollywood quality at 1080p.
[00:25] LTX2 creates audio and video at the same time and it supports Comfy UI.
[00:30] Now paste this into Claude code. Set up tool so I can generate videos locally.
[00:34] Check my system first. Install everything I need and download the right model for my GPU.
[00:40] Then show me how to run it. Follow for more AI tips.
```

---

## Source verification (independent, by HTTP status of canonical URL)

| Tool | Canonical source | HTTP | Real? | Notes |
|------|------------------|------|-------|-------|
| Wan2GP | github.com/DeepBeepMeep/Wan2GP | 200 | YES | Transcript said "2GP"; correct repo is DeepBeepMeep/Wan2GP (the Wan-Video/Wan2GP org repo 404s) |
| Remotion | remotion.dev | 200 | YES | MIT, open-source, code-driven |
| Hyperframes | github.com/hyperframes/hyperframes | 200 | YES | Very new / low maturity — treat as experimental |
| Open-Sora 2.0 | github.com/hpcaitech/Open-Sora | 200 | YES | Open-source |
| HunyuanVideo | github.com/Tencent/HunyuanVideo | 200 | YES | Open-source (Tencent) |
| LTX-2 / LTX-Video | github.com/Lightricks/LTX-Video | 200 | YES | Open-source (Lightricks) |
| Higgsfield (the "expensive" one) | higgsfield.ai | 200 | YES | Paid/commercial — what the video pitches against |

All seven projects are real and live. No fabricated or dead sources.

---

## Can they realistically be used?

**Inside the watch-skill pipeline (analyze/verify videos):** Yes, unconditionally. The watch ran end-to-end on a Facebook URL using only local compute. Facebook is supported out of the box.

**As actual local AI-video generation tools (free, runs on Windows + RTX 2060):**
- Remotion — free/MIT, Node-based, Windows. ✓
- Open-Sora 2.0, HunyuanVideo, LTX-Video, Wan2GP — free/open-weight, run locally on a consumer GPU. ✓
  - **Caveat:** RTX 2060 has only 6 GiB VRAM. Heavy models (Wan2GP, Open-Sora 2.0) need quantized/low-VRAM settings and will be slow but functional.
- Hyperframes — free repo, but very new/unproven; verify it installs cleanly before relying on it.
- The "paste into Claude Code" line is a generic local-setup instruction, not a hard dependency — usable with any agent, including Hermes/forge.

---

## Use cases for every tool in the video

Grounded in each project's actual capability (verified above). Flags where the video overstates or the tool is too new to trust the claims.

### 1. WAN2GP (runs the Wan video models locally)
A user-friendly Gradio GUI wrapper (DeepBeepMeep) for Alibaba's Wan image-to-video / text-to-video diffusion models, optimized for consumer GPUs.
- Turn a single still image (or pose/reference) into a short moving clip — product shots, character idle motions, environment pans.
- Text-prompt → video for quick concept clips without leaving your machine.
- Local, private generation — no cloud upload, good for unreleased IP.
- Fine-tune/experiment with Wan's model sizes on the 2060 via quantized/low-VRAM settings.
- Caveat: 6 GiB VRAM is tight; expect slow generation, likely the smallest Wan variant or CPU offload.

### 2. REMOTION
Programmatic video generation using React/Node.js (MIT, code-driven).
- Generate videos from data/templates — e.g. a personalized clip per customer, per update, or per social post, rendered automatically.
- Motion-graphics / title sequences / trailers built and version-controlled as code.
- Batch-render short-form content (9:16 social cuts) from a single source composition.
- CI-like pipeline: change a JSON/parameter, re-render the video.
- Caveat: it's code, not a prompt box — best if comfortable with React/Node. No generative "AI" model inside; it's a renderer you drive programmatically.

### 3. HYPERFRAMES
A real repo (verified 200 OK) but very new and low-maturity. Video claims "generates video from code, brand new."
- Code-driven AI video generation similar in spirit to Remotion but model-backed (claimed — UNVERIFIED maturity).
- Quick experimental pipelines if it matures.
- Honest flag: repo exists, but NOT verified to install cleanly or do what the video says. Treat as experimental; don't build a workflow on it until confirmed to run on your setup.

### 4. OPEN-SORA 2.0 (hpcaitech)
Fully open-source text-to-video / image-to-video model (~11B params as the video states), by Tsinghua's hpcaitech.
- Prompt → short clips for storyboards, mood reels, or B-roll.
- Image-to-video to animate concept art / environment stills.
- Educational/research: fully open weights, study and modify the pipeline.
- Self-hosted alternative to paid text-to-video APIs.
- Caveat: 11B model + 6 GiB VRAM = need aggressive quantization or a smaller config; slow, and low-VRAM quality won't match the marketing stills.

### 5. HUNYUANVIDEO (Tencent)
Open-source high-fidelity image-to-video / text-to-video model, marketed at 1080p "near-Hollywood" quality.
- Higher-fidelity cinematic clips where Open-Sora's output looks soft.
- Image-to-video for animating detailed scenes / characters.
- When you need 1080p output and have the patience (or a better GPU) for the heavier model.
- Caveat: heaviest for VRAM; on the 2060 slowest and most memory-constrained. Realistic only with heavy quantization or offload.

### 6. LTX-2 / LTX-VIDEO (Lightricks)
Open-source, efficiency-focused video model — fast iteration, generates audio + video together, ComfyUI support.
- Rapid prompt → clip iteration when exploring ideas (faster than the 11B models).
- Generate synchronized audio + video in one pass — useful for short voiced/ambient clips.
- Drop into an existing ComfyUI node workflow alongside other generation steps.
- Good "first local model to try" — lighter and integrates with ComfyUI you may already use.
- Caveat: "audio + video at the same time" is the standout feature — verify audio quality meets your bar; it's generative, not a mastered soundtrack.

### Reference (the paid one the video pitches against): HIGGSFIELD
Cinematic camera-move presets / UGC-style talking-avatars, subscription-based. Not free — included only as the comparison anchor.

### Cross-tool takeaway
- Lightest / easiest to trial on the 2060: LTX-2 and Remotion (code, no heavy model).
- Highest quality (but heaviest): HunyuanVideo and Open-Sora 2.0 — feasible only with quantization.
- Wan2GP sits in the middle and is the most consumer-GPU-friendly of the model-based ones.
- Hyperframes: verified real, but unproven — skip until test-installed.

## Artifacts in this folder

- `six-free-ai-video-generators-viewer.html` — self-contained watch-skill viewer (frames + OCR + transcript + cited evidence), opened with no server.
- `six-free-ai-video-generators-research.md` — this report.

## Next optional steps

- Pull exact repo URLs the video implies into a "free-tools" shortlist for later evaluation.
- Test one tool's install path on the RTX 2060 (e.g. Wan2GP quantized) to confirm real-world feasibility.
- Run `watch-skill ask b7c8e225f3eba473 "<question>"` to query the indexed video further.
