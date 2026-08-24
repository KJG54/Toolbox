# Helpful Links: Toolbox

This is the short, practical map of Toolbox: what it can do, where to learn more, and the commands to start with.

## Start here

- [Toolbox overview and safety protocol](../TOOLBOX.md) — the overall workflow: discover a capability, inspect its local readiness, then run it with explicit opt-in where a public URL or external service is involved.
- [README](../README.md) — the project overview, installation, and examples.
- [Watch local installation and usage](watch-local-install.md) — detailed Watch setup, privacy model, troubleshooting, and supported input types.
- [Tool registry](../registry/tools.yaml) — the source of truth for each registered tool, its inputs, hardware needs, and external-service policy.
- [Workflow registry](../registry/workflows.yaml) — reusable multi-step workflows, including public-video review.

## What Toolbox can help with

### Watch a video and answer questions about it

Watch can inspect a local video or, with your explicit permission, download one public video from a URL and analyze it locally. It can produce a factual description, search the video evidence, and answer a question about what happens in it.

```powershell
# Local video: no network download.
.\toolbox.cmd watch "C:\Videos\clip.mp4" --question "What is being demonstrated?"

# Public video: this one URL download is explicitly authorized by the flag.
.\toolbox.cmd watch "https://example.com/public-video" --allow-download --question "Summarize the important steps."
```

The URL must be public and accessible to the downloader. Login-only, private, DRM-protected, deleted, or platform-blocked videos may not be available. The result is based on downloaded frames, OCR, and locally run transcription; it is not a claim that every social platform or every video can be retrieved.

For a strict evidence-only report instead of the full local analysis, use:

```powershell
.\toolbox.cmd run watch-review "C:\Videos\clip.mp4"
```

More detail: [Watch guide](watch-local-install.md), [Watch skill instructions](../skills/watch/SKILL.md), and [Watch-review instructions](../skills/watch-review/SKILL.md).

### Check whether a tool is ready on this computer

```powershell
.\toolbox.cmd status watch-skill
.\toolbox.cmd doctor
.\toolbox.cmd search "video analysis"
```

`status` reports one capability's readiness and limits. `doctor` checks dependencies and hardware signals without installing or changing anything. `search` helps find the registered tool or workflow that matches a job.

### Understand local hardware fit

Toolbox reports hardware requirements and uses clear outcomes such as `READY`, `MISSING`, and `LOCAL_SLOW`. It is designed to be candid about this computer's local limits rather than silently routing work to rented or cloud GPUs.

For Watch, the locally installed lightweight transcription model is the dependable baseline. Larger vision-language analysis can require more GPU memory and may be reported as slow or unavailable rather than being substituted with a cloud service.

### Work with local creative and 3D tools

The registry also describes local-first tools and workflows for creative assets, audio generation, and 3D optimization. Use the registry links above or ask Toolbox to search by the outcome you want; it will return the local option, prerequisite checks, and any hardware limitation.

## A useful prompt for an agent

When you have a public video link, give an agent this:

> In `C:\Users\kryst\Code\Tools`, use the Toolbox Watch capability on this public video: `<link>`. You have permission to download this one URL. Tell me what happens in the video, answer `<your question>`, and state whether my local hardware is sufficient or whether the result is `LOCAL_SLOW`.

For a local file, replace the link with the full file path and omit the permission sentence.

## Boundaries worth remembering

- A public URL download requires the explicit `--allow-download` flag each time.
- Toolbox does not bypass platform access controls, authentication, DRM, or private-video restrictions.
- Local files and local analysis stay on the computer unless a separately configured tool says otherwise.
- Read the tool's status before relying on it for an important task; `READY` means the checked local prerequisites are present, not that a third-party site will always permit access.
