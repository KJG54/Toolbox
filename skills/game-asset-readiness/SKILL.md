# Game asset readiness

Inspect a local `.blend` file before game-engine handoff:

```powershell
toolbox blender game-asset prop.blend
toolbox blender create-lod prop.blend --output outputs/prop-lod.blend --ratio 0.5
```

The report identifies missing UV layers and conventional collision/LOD object names. It is evidence
for a human or later finishing workflow; it does not fabricate collision geometry or UVs. The
explicit `create-lod` command creates a separate `.blend` derivative by applying Blender's Decimate
modifier to mesh objects. Review the derivative before game-engine use.
