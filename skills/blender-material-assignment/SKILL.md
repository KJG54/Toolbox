# Blender material assignment

Create a separate `.blend` file with conventionally named local maps assigned to matching materials:

```powershell
toolbox blender assign-material asset.blend --textures textures --output outputs/asset-textured.blend
```

Use `--material` and `--texture-group` to make the match explicit. The command links external local
texture files in a derivative; inspect the result before engine import.
