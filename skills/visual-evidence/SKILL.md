# Visual evidence

Inspect or compare images locally; neither command uploads source images:

```powershell
toolbox visual inspect render.png
toolbox visual compare reference.png candidate.png
```

The current implementation reports pixel and perceptual-feature evidence. For separately reviewed
local semantic analysis, use `toolbox vision describe image.png`; it uses the pinned cached model
only and does not upload the image.
