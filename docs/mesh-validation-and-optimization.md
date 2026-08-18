# Mesh Validation and glTF Optimization

Toolbox now recognizes two local-only 3D tools. Neither is installed or
downloaded by this repository. `toolbox doctor` reports their actual state.

## Trimesh: topology evidence

Trimesh provides the missing geometry gate before an asset is used for collision
or 3D printing.

```powershell
toolbox mesh validate .\asset.glb --output .\reports\asset-mesh.json
```

The report includes edge-manifold evidence (boundary and non-manifold edge
counts), watertightness, winding consistency, volume, Euler number, and mesh
counts. A non-watertight mesh can still be valid for a game; it is not
automatically suitable for 3D printing. It also does not replace Blender checks
for UVs, materials, scale, collision, or licensing.

Trimesh is an MIT-licensed Python dependency. If the owner approves its
installation later, install it through the configured project environment using
the `mesh-validation` optional dependency. Do not install it merely because a
recommendation lists it.

## gltfpack: shipping derivative

`gltfpack` is the meshoptimizer command-line companion for local glTF/GLB
optimization.

```powershell
toolbox gltfpack .\asset.glb --output .\outputs\asset-optimized.glb
```

The source is always preserved and the optimized artifact receives a provenance
sidecar by default. Add `--texture-compression` only after reviewing the target
engine, texture quality, and binary support. Reopen the derivative in the
target engine after optimization; this command does not certify gameplay
correctness or release rights.

gltfpack is MIT-licensed and must be installed as a local binary separately,
after explicit approval. Its official project distributes pre-built binaries
and documents source builds; Toolbox does neither automatically.
