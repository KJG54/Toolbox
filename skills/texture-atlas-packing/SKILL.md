# Texture atlas packing

Pack a folder of local sprites or textures into a PNG atlas and layout manifest:

```powershell
toolbox atlas pack sprites --output outputs/sprites.png --padding 2
```

Inputs are not resized or changed. The result uses deterministic filename order and is a derivative
that should be visually reviewed before use in a game or UI.
