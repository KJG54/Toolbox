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
```

Read [TOOLBOX.md](TOOLBOX.md) before asking an agent to create an artifact. The preserved
Watch source lives in `components/watch-skill`; TTS material is deliberately retained as
examples rather than presented as a production engine.

`watch-review` is the local evidence workflow: it optionally creates a portable proxy,
runs the preserved Watch component, and saves timestamped frames and available transcript
segments as a versioned JSON timeline. Cloud STT and model downloads are blocked; `--ocr`
and `--local-whisper` are explicit local add-ons, with Whisper restricted to already-cached
models.
