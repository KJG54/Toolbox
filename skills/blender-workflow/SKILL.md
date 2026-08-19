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

Preflight a `.blend` before delivery, then optionally render a bounded preview:

```powershell
toolbox blender preflight asset.blend
toolbox blender preview asset.blend --output outputs/asset-preview.png --max-resolution 1024
```

Preflight and preview run Blender in background mode with auto-executed scripts disabled. They do
not change the source file. A missing texture or camera is a handoff issue, not a reason to guess.
