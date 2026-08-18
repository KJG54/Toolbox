"""Read-only mesh validation through an explicitly installed local Trimesh runtime."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


class MeshValidationError(ValueError):
    """Raised when local mesh validation cannot safely run."""


_SUPPORTED = {".stl", ".obj", ".ply", ".off", ".glb", ".gltf"}


def trimesh_available() -> bool:
    return importlib.util.find_spec("trimesh") is not None


def validate_mesh(source: Path) -> dict[str, Any]:
    """Report mesh topology evidence without modifying the source asset."""
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Mesh source does not exist: {source}")
    if source.suffix.casefold() not in _SUPPORTED:
        raise MeshValidationError("Mesh validation supports .stl, .obj, .ply, .off, .glb, and .gltf")
    if not trimesh_available():
        raise MeshValidationError("Trimesh is not installed; request approval before adding the local mesh-validation dependency")
    import trimesh

    # Process only the in-memory copy so formats such as STL, which commonly
    # repeat vertices per face, get correct topology rather than false holes.
    loaded = trimesh.load(source, force="mesh", process=True)
    if isinstance(loaded, trimesh.Scene):
        geometries = list(loaded.geometry.values())
        if not geometries:
            raise MeshValidationError("Mesh scene contains no geometry")
        mesh = trimesh.util.concatenate(geometries)
        geometry_count = len(geometries)
    else:
        mesh = loaded
        geometry_count = 1
    if not isinstance(mesh, trimesh.Trimesh) or mesh.faces is None or len(mesh.faces) == 0:
        raise MeshValidationError("Input does not contain a triangle mesh")
    import numpy as np

    edge_counts = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    boundary_edges = int(np.count_nonzero(edge_counts == 1))
    non_manifold_edges = int(np.count_nonzero(edge_counts > 2))
    edge_manifold = non_manifold_edges == 0
    watertight = bool(mesh.is_watertight)
    winding_consistent = bool(mesh.is_winding_consistent)
    is_volume = bool(mesh.is_volume)
    print_status = "READY_FOR_PRINT_REVIEW" if watertight and winding_consistent and is_volume else "NOT_PRINT_READY"
    game_status = "READY_FOR_GAME_REVIEW" if len(mesh.vertices) and len(mesh.faces) else "INVALID"
    return {
        "format": "toolbox-trimesh-validation/v1",
        "source": str(source),
        "geometry_count": geometry_count,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "edge_manifold": edge_manifold,
        "boundary_edges": boundary_edges,
        "non_manifold_edges": non_manifold_edges,
        "watertight": watertight,
        "winding_consistent": winding_consistent,
        "is_volume": is_volume,
        "euler_number": int(mesh.euler_number),
        "bounds": [[float(value) for value in row] for row in mesh.bounds.tolist()],
        "print_status": print_status,
        "game_status": game_status,
        "execution": "local_only",
        "mutation": "none",
        "limitations": "Open surfaces can be valid for games but are not automatically valid for 3D printing. Collision, UVs, materials, scale, and licenses require separate review.",
    }
