"""Guarded local Blender inspection and format conversion."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .doctor import detect_tools


class BlenderWorkflowError(ValueError):
    """Raised when a Blender workflow is unsafe or unsupported."""


_SUPPORTED = {".blend", ".fbx", ".obj", ".gltf", ".glb"}
_EXPORTERS = {
    ".blend": "bpy.ops.wm.save_as_mainfile(filepath=output)",
    ".fbx": "bpy.ops.export_scene.fbx(filepath=output)",
    ".obj": "bpy.ops.wm.obj_export(filepath=output)",
    ".glb": "bpy.ops.export_scene.gltf(filepath=output, export_format='GLB')",
}


def blender_binary() -> str:
    path = detect_tools().get("blender", {}).get("path")
    if not path:
        raise BlenderWorkflowError("Blender is not installed; run toolbox doctor for the detected state")
    return path


def _validate(source: Path, output: Path | None = None, *, overwrite: bool = False) -> tuple[Path, Path | None]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"3D source does not exist: {source}")
    if source.suffix.casefold() not in _SUPPORTED:
        raise BlenderWorkflowError(f"Unsupported 3D source format: {source.suffix}")
    if output is None:
        return source, None
    output = output.resolve()
    if output == source:
        raise BlenderWorkflowError("Output must differ from source; Toolbox never overwrites a 3D source")
    if output.suffix.casefold() not in _EXPORTERS:
        raise BlenderWorkflowError("Output must be .blend, .fbx, .obj, or .glb")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    return source, output


def _import_script(source: Path) -> str:
    source_json = json.dumps(str(source))
    suffix = source.suffix.casefold()
    if suffix == ".fbx":
        return f"bpy.ops.import_scene.fbx(filepath={source_json})"
    if suffix == ".obj":
        return f"bpy.ops.wm.obj_import(filepath={source_json})"
    if suffix in {".gltf", ".glb"}:
        return f"bpy.ops.import_scene.gltf(filepath={source_json})"
    return ""


def conversion_command(source: Path, output: Path, *, overwrite: bool = False) -> list[str]:
    """Build a background Blender conversion command without invoking it."""
    source, output = _validate(source, output, overwrite=overwrite)
    assert output is not None
    output.parent.mkdir(parents=True, exist_ok=True)
    export = _EXPORTERS[output.suffix.casefold()].replace("output", json.dumps(str(output)))
    if source.suffix.casefold() == ".blend":
        script = f"import bpy; {export}"
        return [blender_binary(), "--background", str(source), "--python-expr", script]
    script = f"import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); {_import_script(source)}; {export}"
    return [blender_binary(), "--background", "--python-expr", script]


def convert_3d(source: Path, output: Path, *, overwrite: bool = False) -> dict[str, Any]:
    command = conversion_command(source, output, overwrite=overwrite)
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    destination = output.resolve()
    if completed.returncode or not destination.is_file() or destination.stat().st_size == 0:
        detail = (completed.stderr or completed.stdout).strip()[-1200:]
        raise BlenderWorkflowError(f"Blender could not convert {source.name}: {detail}")
    return {"source": str(source.resolve()), "output": str(destination), "tool": "blender", "mode": "local_conversion"}


def inspect_blend(source: Path) -> dict[str, Any]:
    source, _ = _validate(source)
    if source.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Inspection currently supports .blend files; convert another format into .blend first")
    marker = "TOOLBOX_BLENDER_INSPECT="
    script = (
        "import bpy,json; print('TOOLBOX_BLENDER_INSPECT=' + json.dumps({"
        "'objects': len(bpy.data.objects), 'meshes': len(bpy.data.meshes), "
        "'materials': len(bpy.data.materials), 'images': len(bpy.data.images)}))"
    )
    completed = subprocess.run([blender_binary(), "--background", str(source), "--python-expr", script], text=True, capture_output=True, check=False)
    if completed.returncode:
        raise BlenderWorkflowError(f"Blender could not inspect {source.name}: {(completed.stderr or completed.stdout).strip()[-1200:]}")
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(marker):
            return {"source": str(source), "tool": "blender", "mode": "local_inspection", **json.loads(line[len(marker):])}
    raise BlenderWorkflowError("Blender inspection returned no structured result")
