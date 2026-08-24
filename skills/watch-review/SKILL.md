# Watch review

Use this workflow when a person needs inspectable evidence from a local recording: tutorials,
software walkthroughs, gameplay, renders, or asset-review videos. It leaves the source file
unchanged and emits a timestamped JSON timeline plus a provenance sidecar.

Run:

```powershell
$toolbox = ".\toolbox.cmd"
& $toolbox run watch-review recording.mov --output outputs/recording-review.json --normalize
```

`--normalize` is optional and creates a 1280px local proxy first. `--ocr` and
`--local-whisper` are opt-in local enhancements. Whisper model downloads remain blocked;
if the requested model is not already cached, report the missing local requirement.

For a public URL, require explicit owner permission for that exact URL and add
`--allow-download`. Do not use the preserved component's direct setup or self-healing paths.
