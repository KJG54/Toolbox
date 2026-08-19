# Delivery package

Audit a handoff folder before creating a portable ZIP:

```powershell
toolbox delivery audit outputs/delivery --require asset.glb
toolbox delivery package outputs/delivery --output outputs/delivery.zip --require asset.glb
```

Provenance sidecars are required by default. The package command stops if required files or valid
provenance are missing; use `--allow-missing-provenance` only after an explicit human decision.
