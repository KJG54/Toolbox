# ACE-Step local music generation

ACE-Step is installed as a separate local component with the 6 GB-safe Turbo profile. Check readiness first:

```powershell
toolbox status ace-step-local
toolbox research evaluate-generation music
```

Use the component's isolated Python 3.12 environment. Keep the language model disabled, retain INT8
quantization and CPU offload, and create provenance for each exported track. Do not enable XL models,
download additional weights, or use any external inference service without explicit approval.
