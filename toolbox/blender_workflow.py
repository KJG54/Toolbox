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


def preflight_blend(source: Path) -> dict[str, Any]:
    """Report common scene and external-image issues without enabling file auto-execution."""
    source, _ = _validate(source)
    if source.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Preflight currently supports .blend files; convert another format into .blend first")
    marker = "TOOLBOX_BLENDER_PREFLIGHT="
    script = (
        "import bpy,json,os; "
        "missing=[image.filepath for image in bpy.data.images if image.source=='FILE' and not image.packed_file and image.filepath and not os.path.isfile(bpy.path.abspath(image.filepath, library=image.library))]; "
        "packed=sum(1 for image in bpy.data.images if image.packed_file); "
        "print('TOOLBOX_BLENDER_PREFLIGHT=' + json.dumps({'objects':len(bpy.data.objects),'meshes':len(bpy.data.meshes),'materials':len(bpy.data.materials),'images':len(bpy.data.images),'missing_external_images':missing,'packed_images':packed,'active_camera':bpy.context.scene.camera.name if bpy.context.scene.camera else None,'render_engine':bpy.context.scene.render.engine}))"
    )
    completed = subprocess.run(
        [blender_binary(), "--background", "--disable-autoexec", str(source), "--python-expr", script],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise BlenderWorkflowError(f"Blender could not preflight {source.name}: {(completed.stderr or completed.stdout).strip()[-1200:]}")
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(marker):
            result = json.loads(line[len(marker):])
            result.update({
                "source": str(source),
                "tool": "blender",
                "mode": "local_preflight",
                "autoexec": "disabled",
                "status": "NEEDS_ATTENTION" if result["missing_external_images"] or not result["active_camera"] else "READY_FOR_PREVIEW",
            })
            return result
    raise BlenderWorkflowError("Blender preflight returned no structured result")


def preview_command(source: Path, output: Path, *, max_resolution: int = 1024, overwrite: bool = False) -> list[str]:
    """Build a bounded background preview-render command; source settings stay untouched."""
    source, _ = _validate(source)
    output = output.resolve()
    if source.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Preview rendering currently supports .blend files")
    if output.suffix.casefold() not in {".png", ".jpg", ".jpeg"}:
        raise BlenderWorkflowError("Preview output must use .png, .jpg, or .jpeg")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if output == source:
        raise BlenderWorkflowError("Output must differ from source; Toolbox never overwrites a 3D source")
    if not 64 <= max_resolution <= 4096:
        raise BlenderWorkflowError("max_resolution must be between 64 and 4096 pixels")
    output.parent.mkdir(parents=True, exist_ok=True)
    image_format = "JPEG" if output.suffix.casefold() in {".jpg", ".jpeg"} else "PNG"
    expression = (
        "import bpy; scene=bpy.context.scene; "
        f"scene.render.resolution_percentage=min(100, max(1, int({max_resolution} * 100 / max(scene.render.resolution_x, scene.render.resolution_y, 1)))); "
        f"scene.render.image_settings.file_format='{image_format}'; scene.render.filepath={json.dumps(str(output))}; "
        "bpy.ops.render.render(write_still=True)"
    )
    return [
        blender_binary(), "--background", "--disable-autoexec", str(source), "--python-expr", expression,
    ]


def render_preview(source: Path, output: Path, *, max_resolution: int = 1024, overwrite: bool = False) -> dict[str, Any]:
    command = preview_command(source, output, max_resolution=max_resolution, overwrite=overwrite)
    completed = subprocess.run(command, text=True, capture_output=True, check=False, timeout=300)
    destination = output.resolve()
    if completed.returncode or not destination.is_file() or destination.stat().st_size == 0:
        detail = (completed.stderr or completed.stdout).strip()[-1200:]
        raise BlenderWorkflowError(f"Blender could not render {source.name}: {detail}")
    return {"source": str(source.resolve()), "output": str(destination), "tool": "blender", "mode": "local_preview_render", "autoexec": "disabled"}


def inspect_game_asset(source: Path) -> dict[str, Any]:
    """Report local game-readiness evidence without altering the Blender source."""
    source, _ = _validate(source)
    if source.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Game-asset inspection currently supports .blend files")
    marker = "TOOLBOX_GAME_ASSET_INSPECT="
    script = (
        "import bpy,json; "
        "meshes=[{'name':obj.name,'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),'triangles':sum(max(0,len(poly.vertices)-2) for poly in obj.data.polygons),'uv_layers':len(obj.data.uv_layers),'materials':len(obj.data.materials)} for obj in bpy.data.objects if obj.type=='MESH']; "
        "colliders=[obj.name for obj in bpy.data.objects if obj.name.casefold().startswith(('ucx_','collision_','col_'))]; "
        "lods=[obj.name for obj in bpy.data.objects if 'lod' in obj.name.casefold()]; "
        "missing_uv=[mesh['name'] for mesh in meshes if mesh['uv_layers']==0]; "
        "print('TOOLBOX_GAME_ASSET_INSPECT=' + json.dumps({'meshes':meshes,'collider_objects':colliders,'lod_objects':lods,'missing_uv_meshes':missing_uv}))"
    )
    completed = subprocess.run(
        [blender_binary(), "--background", "--disable-autoexec", str(source), "--python-expr", script],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise BlenderWorkflowError(f"Blender could not inspect game asset {source.name}: {(completed.stderr or completed.stdout).strip()[-1200:]}")
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(marker):
            result = json.loads(line[len(marker):])
            issues = []
            if result["missing_uv_meshes"]:
                issues.append("mesh_without_uvs")
            if not result["collider_objects"]:
                issues.append("no_named_collision_objects")
            if not result["lod_objects"]:
                issues.append("no_named_lod_objects")
            return {
                "source": str(source),
                "tool": "blender",
                "mode": "local_game_asset_inspection",
                "autoexec": "disabled",
                **result,
                "issues": issues,
                "status": "READY_FOR_HUMAN_REVIEW" if not issues else "NEEDS_GAME_ASSET_FINISHING",
            }
    raise BlenderWorkflowError("Game-asset inspection returned no structured result")


def lod_command(source: Path, output: Path, *, ratio: float, overwrite: bool = False) -> list[str]:
    """Build a non-destructive Blender LOD derivative command with auto-execution disabled."""
    source, _ = _validate(source)
    output = output.resolve()
    if source.suffix.casefold() != ".blend" or output.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("LOD generation currently requires .blend source and output files")
    if output == source:
        raise BlenderWorkflowError("Output must differ from source; Toolbox never overwrites a 3D source")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if not 0.01 <= ratio < 1.0:
        raise BlenderWorkflowError("LOD ratio must be at least 0.01 and less than 1.0")
    output.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "import bpy\n"
        "for obj in [item for item in bpy.context.scene.objects if item.type == 'MESH']:\n"
        "    bpy.ops.object.select_all(action='DESELECT')\n"
        "    bpy.context.view_layer.objects.active = obj\n"
        "    obj.select_set(True)\n"
        "    modifier = obj.modifiers.new('Toolbox_LOD_Decimate', 'DECIMATE')\n"
        f"    modifier.ratio = {ratio}\n"
        "    bpy.ops.object.modifier_apply(modifier=modifier.name)\n"
        "    obj.select_set(False)\n"
        f"bpy.ops.wm.save_as_mainfile(filepath={json.dumps(str(output))})\n"
    )
    script = "exec(" + json.dumps(body) + ")"
    return [blender_binary(), "--background", "--disable-autoexec", str(source), "--python-expr", script]


def create_lod(source: Path, output: Path, *, ratio: float, overwrite: bool = False) -> dict[str, Any]:
    command = lod_command(source, output, ratio=ratio, overwrite=overwrite)
    completed = subprocess.run(command, text=True, capture_output=True, check=False, timeout=300)
    destination = output.resolve()
    if completed.returncode or not destination.is_file() or destination.stat().st_size == 0:
        detail = (completed.stderr or completed.stdout).strip()[-1200:]
        raise BlenderWorkflowError(f"Blender could not create an LOD derivative for {source.name}: {detail}")
    return {
        "source": str(source.resolve()),
        "output": str(destination),
        "tool": "blender",
        "mode": "local_lod_derivative",
        "ratio": ratio,
        "autoexec": "disabled",
    }
