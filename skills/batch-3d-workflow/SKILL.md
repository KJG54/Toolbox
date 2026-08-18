# Batch 3D workflow

Create local 3D derivatives for a bounded folder:

```powershell
toolbox blender batch assets --output-dir outputs/converted --format glb --preview
```

Sources remain untouched. Previewing is available for `.blend` inputs; other formats are converted
but their previews are explicitly reported as skipped.
