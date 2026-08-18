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
```

Read [TOOLBOX.md](TOOLBOX.md) before asking an agent to create an artifact. The preserved
Watch source lives in `components/watch-skill`; TTS material is deliberately retained as
examples rather than presented as a production engine.
