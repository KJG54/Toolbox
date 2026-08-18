# Evidence library

Use this to search multiple saved Watch review JSON files in a local folder.

```powershell
toolbox library search outputs "Where do we change the export setting?"
toolbox library search outputs "Where do we change the export setting?" --semantic
```

The search is local and read-only. It returns timestamped transcript/OCR evidence and does
not scan original media again. `--semantic` uses the approved cached local embedding model.
