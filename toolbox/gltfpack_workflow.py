"""Guarded local GLB optimization using an explicitly installed gltfpack binary."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .paths import ROOT

class GltfpackError(ValueError):
    """Raised when local glTF optimization cannot safely run."""


def gltfpack_binary() -> str | None:
    installed = shutil.which("gltfpack")
    if installed:
        return installed

    component_root = ROOT / "components" / "gltfpack"
    if not component_root.is_dir():
        return None
    bundled = next(component_root.rglob("gltfpack.exe"), None)
    return str(bundled) if bundled else None


def optimization_command(source: Path, output: Path, *, texture_compression: bool = False, overwrite: bool = False) -> list[str]:
    source, output = source.resolve(), output.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"glTF source does not exist: {source}")
    if source.suffix.casefold() not in {".gltf", ".glb"}:
        raise GltfpackError("gltfpack optimization requires .gltf or .glb input")
    if output.suffix.casefold() != ".glb":
        raise GltfpackError("gltfpack output must use .glb")
    if output == source:
        raise GltfpackError("Output must differ from source; Toolbox never overwrites a glTF source")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    binary = gltfpack_binary()
    if not binary:
        raise GltfpackError("gltfpack is not installed; request approval before adding the local optimizer binary")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [binary, "-i", str(source), "-o", str(output)]
    if texture_compression:
        command.append("-tc")
    return command


def optimize_gltf(source: Path, output: Path, *, texture_compression: bool = False, overwrite: bool = False) -> dict[str, Any]:
    """Create a separate optimized GLB derivative and preserve the source file."""
    command = optimization_command(source, output, texture_compression=texture_compression, overwrite=overwrite)
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    output = output.resolve()
    if completed.returncode or not output.is_file() or output.stat().st_size == 0:
        detail = (completed.stderr or completed.stdout).strip()[-1200:]
        raise GltfpackError(f"gltfpack could not optimize {source.name}: {detail}")
    source_size, output_size = source.resolve().stat().st_size, output.stat().st_size
    return {
        "format": "toolbox-gltfpack-optimization/v1",
        "source": str(source.resolve()),
        "output": str(output),
        "source_bytes": source_size,
        "output_bytes": output_size,
        "bytes_saved": source_size - output_size,
        "texture_compression": texture_compression,
        "execution": "local_only",
        "note": "Review the optimized asset in its target engine; optimization can change binary representation and does not validate licensing or gameplay correctness.",
    }
