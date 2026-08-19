# Semantic image understanding

Describe one local image using the approved, pinned Florence-2 Base runtime:

```powershell
toolbox vision describe reference.png --task caption
toolbox vision describe reference.png --task detailed-caption
toolbox vision describe reference.png --task object-detection
```

The command uses only cached files and never uploads the image or downloads a model during a
request. Treat its result as model evidence for human review, not ground truth. Use pixel or
perceptual comparison for acceptance checks that require exact visual evidence.
