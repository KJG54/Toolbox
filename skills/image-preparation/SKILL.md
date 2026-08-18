# Image preparation

Create a non-destructive local derivative for a texture, UI asset, or reference image:

```powershell
toolbox image inspect source.png
toolbox image prepare source.png --output outputs/source.webp --max-width 2048
```

Use `--allow-upscale` only when an enlarged derivative is useful. This workflow uses interpolation;
it does not claim to reconstruct or generate missing visual detail.
