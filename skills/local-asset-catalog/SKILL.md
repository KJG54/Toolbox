# Local asset catalog

Inventory downloaded assets without uploading or changing them:

```powershell
toolbox catalog index assets --output outputs/assets-catalog.json
toolbox catalog search assets "stone wall" --format png --commercial
```

Tags are derived from local filenames. Commercial filtering uses recorded provenance only; missing
or `requires_review` license state is never treated as commercially cleared.
