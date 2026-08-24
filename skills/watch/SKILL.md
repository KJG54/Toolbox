# Watch

Use the Toolbox wrapper, not direct `watch-skill`, for media review. From the Toolbox root,
run `& ".\toolbox.cmd" doctor` and then use `& ".\toolbox.cmd" watch <source>` to acquire,
index, and answer from a video. For a public link, proceed only when the owner explicitly
authorizes retrieval of that exact URL and the command includes `--allow-download`. The local
yt-dlp extractor may self-update after a requested source has extractor breakage; no cloud AI,
credentials, cookies, Cobalt fallback service, or model downloads are allowed. Do not run `uv`,
`watch-skill setup`, or direct `watch-skill doctor`. See `docs/watch-local-install.md` for the
canonical flow.
