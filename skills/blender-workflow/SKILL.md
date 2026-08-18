# Blender workflow

Inspect a local Blender file without changing it:

```powershell
toolbox blender inspect asset.blend
```

Create a derivative, preserving the source and attaching provenance:

```powershell
toolbox blender convert asset.blend --output outputs/asset.glb
```

Supported output formats are `.blend`, `.fbx`, `.obj`, and `.glb`. Complex renders may be
slow on the local RTX 2060; this workflow does not route rendering to cloud hardware.
