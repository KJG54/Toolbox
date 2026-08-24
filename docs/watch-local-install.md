# Watch Skill — canonical Toolbox quick start

Use this page, not the preserved upstream guides, when an agent needs to inspect a video.
The Toolbox wrapper is the supported front door because it preserves the original media,
creates timestamped evidence, disables cloud STT/model downloads, and reports honest local
readiness.

## Start from the Toolbox folder

```powershell
$toolbox = ".\toolbox.cmd"
& $toolbox doctor
& $toolbox status watch-skill
```

`toolbox.cmd` is local to this repository; do not assume a `toolbox` command exists on PATH.
`doctor` is read-only. It reports both local analysis readiness and whether public URL retrieval
has an installed downloader. `READY` means the current machine can run the local Watch workflow;
`LOCAL_SLOW` means it can run but needs patience; `INSTALLATION_REQUIRED` means stop and ask the
owner before installing anything.

## Review a local file

```powershell
& $toolbox run watch-review "C:\videos\demo.mp4" `
  --output "C:\videos\outputs\demo-review.json" `
  --normalize --ocr --local-whisper --whisper-model tiny
```

This creates a JSON evidence timeline, a sibling `demo-review.watch-work` directory for frames
and derivatives, and a provenance sidecar. It leaves the original file unchanged and refuses to
overwrite prior artifacts unless `--force` is supplied.

## Review one owner-approved public link

Use this only when the owner gave both the URL and explicit permission to retrieve it:

```powershell
& $toolbox run watch-review "https://example.com/public-video" `
  --allow-download `
  --output "outputs\public-video-review.json" `
  --normalize --ocr --local-whisper --whisper-model tiny
```

`--allow-download` authorizes retrieval of that single public source. The wrapper does not use
cookies or credentials; does not invoke Watch's self-update, Cobalt, or fallback service paths;
does not install software; and does not send audio or frames to cloud AI. It stops if the URL
requires login, DRM, or an unavailable downloader.

## Watch and answer from one public link

Use this for the experience where an agent receives a public social-media or video link and tells
you what is in it:

```powershell
& $toolbox watch "https://example.com/public-video" `
  --allow-download `
  --question "What happens in this video, and what software or hardware does it use?"
```

This is the full Watch route: it acquires the owner-approved public source, indexes frames, OCR,
and transcript evidence, then returns an answer with timestamps. It uses local Tiny Whisper when
captions are unavailable and keeps cloud STT and cloud vision disabled. The local `yt-dlp`
extractor can self-update after extractor breakage, which is necessary to keep public social-media
sources working as their sites change. It never sends cookies, credentials, frames, or audio to a
remote service; it never uses the Cobalt fallback service.

## Ask from saved evidence

```powershell
& $toolbox review ask "outputs\public-video-review.json" "What does this video demonstrate?"
```

Answers cite timestamps from locally saved OCR/transcript/frame evidence. If the evidence does
not support an answer, the result says so rather than guessing.

## Agent instruction to copy

```text
Use the Toolbox at C:\Users\kryst\Code\Tools. First run its repository-local toolbox.cmd
doctor and status for watch-skill. I authorize retrieval of this one public URL: <URL>.
Use only `.\toolbox.cmd watch <URL> --allow-download --question "What happens in this video?"`;
do not use uv, direct watch-skill, watch-skill doctor/setup, model downloads, cloud AI,
credentials, or MCP setup. A local yt-dlp extractor update is permitted only when the requested
source has extractor breakage. Report a timestamp-supported summary, the Watch runtime status,
and whether this machine can run the workflow. Stop if the source needs login/DRM.
```

The original Watch source remains at `components/watch-skill`, and its original repository
history remains in `archives/watch-skill-pre-toolbox.bundle`. Its `docs/` directory is preserved
reference material, not current Toolbox instructions.
