# Normalize Local Media

Use `toolbox run normalize-media` to create a portable derivative for Watch or another
local workflow. Require an explicit output path. The command refuses to overwrite the
source and creates a provenance sidecar unless `--no-provenance` is explicitly supplied.

Use `.mp4` outputs for video proxies and `--audio-only` with a `.wav` output for mono,
16 kHz audio suitable for local transcription.
