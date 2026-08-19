# Watch delivery exports

Create subtitle and chapter files from an existing local Watch timeline:

```powershell
toolbox review export-subtitles review.json --output outputs/review.vtt
toolbox review export-chapters review.json --output outputs/review.ffmeta
```

The exports use only saved transcript and scene evidence; they do not reprocess the original video.
