# Agent Operating Protocol

## Canonical command and public-video boundary

From the Toolbox root, invoke the repository-local CLI as:

```powershell
$toolbox = ".\toolbox.cmd"
& $toolbox doctor
```

Do not assume `toolbox` is on PATH. For a local media file, use `& $toolbox run
watch-review <path> --output <review.json>`. For a public HTTP(S) video URL, use the same
workflow only when the owner explicitly authorizes retrieving that exact URL, and pass
`--allow-download`. The workflow uses the installed downloader once, without cookies,
credentials, self-installation, self-update, cloud STT, or cloud models. If `doctor` reports
`public_url_download: INSTALLATION_REQUIRED`, stop and ask the owner whether to install the
missing downloader; never call direct `watch-skill doctor`, `watch-skill setup`, or `uv sync`.

The preserved material under `components/watch-skill/docs/` is upstream reference material,
not Toolbox operating instructions. It may describe direct setup, self-healing, MCP setup,
or cloud-capable paths that are outside this Toolbox workflow.

For the complete public-video experience, use `& $toolbox watch <source>`. A public URL still
requires `--allow-download`, which authorizes retrieval of that owner-supplied source. This full
workflow indexes the video and answers a question from timestamped evidence. Its local `yt-dlp`
extractor may self-update only when a requested source has extractor breakage; the alternative
remote Cobalt fallback, cloud STT, cloud vision, credentials, cookies, and model downloads remain
disabled.

When a user asks whether a tool exists, first run `toolbox search` or `toolbox recommend`
with the requested capability and constraints. Treat the registry as the source of truth
for what is known and the doctor report as the source of truth for this machine's runtime
state.

If a suitable local tool is returned, explain the recommendation, hardware result, license
status, and input/output assumptions before executing it. Use `toolbox status <id>` when
availability is unclear.

If no suitable tool is returned, report a capability gap. Research candidates only from
official product, project, and license sources; compare local hardware requirements,
commercial-use terms, interfaces, and file formats. Present a proposed registry record for
review. Do not install software, download models, add registry records, spend money, or
upload user content as part of research.

When recommending a next capability, state the concrete use cases, why it helps this
workflow over time, its local hardware and installation prerequisites, and what it does
not do. Make the recommendation actionable without implying approval to install or invoke
anything external.

External APIs are `external_opt_in`: do not invoke them or send media outside the machine
without explicit approval. Cloud GPU, rented GPU, remote jobs, and billable compute are out
of scope. If the machine is insufficient, report `HARDWARE_UPGRADE_REQUIRED`.

For generated or transformed assets, create an explicit provenance sidecar with
`toolbox provenance create`; never overwrite an existing sidecar unless the user asks.
