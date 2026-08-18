"""Guarded local Blender inspection and format conversion."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .doctor import detect_tools
from .texture_validation import _classification


class BlenderWorkflowError(ValueError):
    """Raised when a Blender workflow is unsafe or unsupported."""


_SUPPORTED = {".blend", ".fbx", ".obj", ".gltf", ".glb"}
_EXPORTERS = {
    ".blend": "bpy.ops.wm.save_as_mainfile(filepath=output)",
    ".fbx": "bpy.ops.export_scene.fbx(filepath=output)",
    ".obj": "bpy.ops.wm.obj_export(filepath=output)",
    ".glb": "bpy.ops.export_scene.gltf(filepath=output, export_format='GLB')",
}


def batch_convert_3d(
    source_directory: Path,
    output_directory: Path,
    *,
    output_format: str,
    previews: bool = False,
    overwrite: bool = False,
    max_assets: int = 500,
) -> dict[str, Any]:
    """Convert a bounded local directory while preserving every source file."""
    source_directory = source_directory.resolve()
    output_directory = output_directory.resolve()
    if not source_directory.is_dir():
        raise FileNotFoundError(f"3D source directory does not exist: {source_directory}")
    output_suffix = f".{output_format.casefold().lstrip('.')}"
    if output_suffix not in _EXPORTERS:
        raise BlenderWorkflowError("Batch output format must be .blend, .fbx, .obj, or .glb")
    if output_directory == source_directory:
        raise BlenderWorkflowError("Batch output directory must differ from the source directory")
    if not 1 <= max_assets <= 5000:
        raise BlenderWorkflowError("max_assets must be between 1 and 5000")
    sources = [
        path for path in source_directory.rglob("*")
        if path.is_file() and path.suffix.casefold() in _SUPPORTED and output_directory not in path.parents
    ]
    if len(sources) > max_assets:
        raise BlenderWorkflowError(f"Found {len(sources)} assets; narrow the directory or raise --max-assets")
    destinations: set[Path] = set()
    for source in sources:
        destination = (output_directory / source.relative_to(source_directory)).with_suffix(output_suffix)
        if destination in destinations:
            raise BlenderWorkflowError(f"Multiple source assets would write '{destination.relative_to(output_directory)}'")
        destinations.add(destination)
    results: list[dict[str, Any]] = []
    for source in sorted(sources, key=lambda item: str(item).casefold()):
        destination = (output_directory / source.relative_to(source_directory)).with_suffix(output_suffix)
        try:
            result = convert_3d(source, destination, overwrite=overwrite)
            result["status"] = "CONVERTED"
            if previews and source.suffix.casefold() == ".blend":
                preview = destination.with_suffix(".preview.png")
                result["preview"] = render_preview(source, preview, overwrite=overwrite)
            elif previews:
                result["preview_status"] = "SKIPPED_SOURCE_NOT_BLEND"
        except (BlenderWorkflowError, FileExistsError) as error:
            result = {"source": str(source), "output": str(destination), "status": "FAILED", "error": str(error)}
        results.append(result)
    return {
        "format": "toolbox-blender-batch/v1",
        "source_directory": str(source_directory),
        "output_directory": str(output_directory),
        "output_format": output_suffix.lstrip("."),
        "requested_previews": previews,
        "results": results,
        "converted": sum(result["status"] == "CONVERTED" for result in results),
        "failed": sum(result["status"] == "FAILED" for result in results),
        "execution": "local_only",
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


def assign_material_maps(
    source: Path,
    textures_directory: Path,
    output: Path,
    *,
    material: str | None = None,
    texture_group: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create a `.blend` derivative with explicit local texture-node assignments."""
    source, _ = _validate(source)
    output = output.resolve()
    textures_directory = textures_directory.resolve()
    if source.suffix.casefold() != ".blend" or output.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Material assignment currently requires .blend source and output files")
    if not textures_directory.is_dir():
        raise FileNotFoundError(f"Texture directory does not exist: {textures_directory}")
    if output == source:
        raise BlenderWorkflowError("Output must differ from source; Toolbox never overwrites a 3D source")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    maps: dict[str, dict[str, str]] = {}
    for path in textures_directory.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tga"}:
            continue
        map_name, group = _classification(path.stem)
        if map_name:
            maps.setdefault(group, {})[map_name] = str(path.resolve())
    if not maps:
        raise BlenderWorkflowError("No conventionally named material maps were found in the texture directory")
    if texture_group:
        group_name = texture_group.casefold().replace(" ", "_")
        if group_name not in maps:
            raise BlenderWorkflowError(f"Texture group '{texture_group}' was not found")
        maps = {group_name: maps[group_name]}
    output.parent.mkdir(parents=True, exist_ok=True)
    marker = "TOOLBOX_MATERIAL_ASSIGN="
    assignments = json.dumps(maps)
    requested_material = json.dumps(material)
    body = (
        "import bpy,json,re\n"
        f"maps={assignments}\n"
        f"requested={requested_material}\n"
        "def norm(value): return re.sub(r'[^a-z0-9]+','_',value.casefold()).strip('_')\n"
        "applied=[]\n"
        "for mat in bpy.data.materials:\n"
        "    if requested and mat.name != requested: continue\n"
        "    group=norm(mat.name)\n"
        "    if group not in maps:\n"
        "        if requested and len(maps)==1: group=next(iter(maps))\n"
        "        else: continue\n"
        "    mat.use_nodes=True\n"
        "    nodes=mat.node_tree.nodes; links=mat.node_tree.links\n"
        "    principled=next((node for node in nodes if node.type=='BSDF_PRINCIPLED'),None)\n"
        "    if not principled: continue\n"
        "    for kind,path in maps[group].items():\n"
        "        tex=nodes.new('ShaderNodeTexImage'); tex.label='Toolbox '+kind; tex.image=bpy.data.images.load(path,check_existing=True)\n"
        "        if kind=='base_color': links.new(tex.outputs['Color'],principled.inputs['Base Color'])\n"
        "        elif kind=='roughness': links.new(tex.outputs['Color'],principled.inputs['Roughness'])\n"
        "        elif kind=='metallic': links.new(tex.outputs['Color'],principled.inputs['Metallic'])\n"
        "        elif kind=='emissive': links.new(tex.outputs['Color'],principled.inputs['Emission Color'])\n"
        "        elif kind=='normal':\n"
        "            normal=nodes.new('ShaderNodeNormalMap'); links.new(tex.outputs['Color'],normal.inputs['Color']); links.new(normal.outputs['Normal'],principled.inputs['Normal'])\n"
        "    applied.append({'material':mat.name,'texture_group':group,'maps':sorted(maps[group])})\n"
        f"bpy.ops.wm.save_as_mainfile(filepath={json.dumps(str(output))})\n"
        f"print('{marker}'+json.dumps({{'applied':applied}}))\n"
    )
    command = [blender_binary(), "--background", "--disable-autoexec", str(source), "--python-expr", "exec(" + json.dumps(body) + ")"]
    completed = subprocess.run(command, text=True, capture_output=True, check=False, timeout=300)
    if completed.returncode or not output.is_file() or output.stat().st_size == 0:
        detail = (completed.stderr or completed.stdout).strip()[-1200:]
        raise BlenderWorkflowError(f"Blender could not assign material maps for {source.name}: {detail}")
    applied: list[dict[str, Any]] = []
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(marker):
            applied = json.loads(line[len(marker):]).get("applied", [])
            break
    return {"source": str(source), "textures_directory": str(textures_directory), "output": str(output), "applied": applied, "status": "ASSIGNED" if applied else "NO_MATCHING_MATERIAL", "autoexec": "disabled", "execution": "local_only"}


def render_turntable(source: Path, output_directory: Path, *, frames: int = 12, resolution: int = 512, overwrite: bool = False) -> dict[str, Any]:
    """Render a local image sequence around the scene without saving source changes."""
    source, _ = _validate(source)
    output_directory = output_directory.resolve()
    if source.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Turntable rendering currently supports .blend files")
    if output_directory == source.parent:
        raise BlenderWorkflowError("Turntable output directory must differ from the source directory")
    if output_directory.exists() and any(output_directory.iterdir()) and not overwrite:
        raise FileExistsError(f"Output directory is not empty: {output_directory}; use --force to replace files")
    if not 3 <= frames <= 120 or not 64 <= resolution <= 2048:
        raise BlenderWorkflowError("frames must be 3-120 and resolution must be 64-2048")
    output_directory.mkdir(parents=True, exist_ok=True)
    marker = "TOOLBOX_TURNTABLE="
    body = (
        "import bpy,math,json\n"
        "from mathutils import Vector\n"
        f"out={json.dumps(str(output_directory))}\n"
        f"frames={frames}; resolution={resolution}\n"
        "scene=bpy.context.scene; meshes=[obj for obj in scene.objects if obj.type=='MESH']\n"
        "if not meshes: raise RuntimeError('Scene has no mesh objects')\n"
        "center=sum((obj.matrix_world.translation for obj in meshes),Vector((0,0,0)))/len(meshes)\n"
        "radius=max(max(obj.dimensions) for obj in meshes)*2.5 or 5\n"
        "camera=scene.camera\n"
        "if camera is None:\n"
        "    data=bpy.data.cameras.new('ToolboxTurntableCamera'); camera=bpy.data.objects.new('ToolboxTurntableCamera',data); scene.collection.objects.link(camera); scene.camera=camera\n"
        "scene.render.resolution_x=resolution; scene.render.resolution_y=resolution; scene.render.resolution_percentage=100\n"
        "scene.render.image_settings.file_format='PNG'\n"
        "rendered=[]\n"
        "for index in range(frames):\n"
        "    angle=2*math.pi*index/frames; camera.location=center+Vector((math.cos(angle)*radius,math.sin(angle)*radius,radius*0.35)); camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()\n"
        "    scene.render.filepath=f'{out}/frame_{index:03d}.png'; bpy.ops.render.render(write_still=True); rendered.append(scene.render.filepath)\n"
        f"print('{marker}'+json.dumps({{'frames':rendered}}))\n"
    )
    completed = subprocess.run([blender_binary(), "--background", "--disable-autoexec", str(source), "--python-expr", "exec(" + json.dumps(body) + ")"], text=True, capture_output=True, check=False, timeout=300)
    files = sorted(output_directory.glob("frame_*.png"))
    if completed.returncode or len(files) != frames:
        raise BlenderWorkflowError(f"Blender could not render turntable for {source.name}: {(completed.stderr or completed.stdout).strip()[-1200:]}")
    return {"format":"toolbox-turntable/v1","source":str(source),"output_directory":str(output_directory),"frames":[str(path) for path in files],"resolution":resolution,"autoexec":"disabled","execution":"local_only"}


def create_procedural_prop(output: Path, *, kind: str, overwrite: bool = False) -> dict[str, Any]:
    """Create a simple original Blender prop derivative without opening a source file."""
    output = output.resolve()
    if output.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Procedural prop output must use .blend")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if kind not in {"crate", "barrel", "ramp", "platform"}:
        raise BlenderWorkflowError("kind must be crate, barrel, ramp, or platform")
    output.parent.mkdir(parents=True, exist_ok=True)
    marker = "TOOLBOX_PROP="
    body = (
        "import bpy,json\n"
        f"kind={json.dumps(kind)}; out={json.dumps(str(output))}\n"
        "bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)\n"
        "if kind=='crate':\n"
        " bpy.ops.mesh.primitive_cube_add(size=2); obj=bpy.context.object; obj.name='SM_Crate'; bpy.ops.object.modifier_add(type='BEVEL'); obj.modifiers[-1].width=.06; obj.modifiers[-1].segments=2\n"
        "elif kind=='barrel':\n"
        " bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=.8, depth=1.8); obj=bpy.context.object; obj.name='SM_Barrel'; bpy.ops.object.modifier_add(type='BEVEL'); obj.modifiers[-1].width=.08; obj.modifiers[-1].segments=2\n"
        "elif kind=='ramp':\n"
        " verts=[(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0),(-1,-1,0),(1,-1,0),(1,1,1),(-1,1,1)]; faces=[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,7,6,5)]; mesh=bpy.data.meshes.new('SM_RampMesh'); mesh.from_pydata(verts,[],faces); obj=bpy.data.objects.new('SM_Ramp',mesh); bpy.context.collection.objects.link(obj)\n"
        "else:\n"
        " bpy.ops.mesh.primitive_cube_add(size=2); obj=bpy.context.object; obj.name='SM_Platform'; obj.scale=(2,2,.25); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)\n"
        "obj['toolbox_generated']=True; obj['collision_hint']='UCX_'+obj.name\n"
        "bpy.ops.wm.save_as_mainfile(filepath=out); print('" + marker + "'+json.dumps({'object':obj.name}))\n"
    )
    completed = subprocess.run([blender_binary(), "--background", "--factory-startup", "--disable-autoexec", "--python-expr", "exec(" + json.dumps(body) + ")"], text=True, capture_output=True, check=False, timeout=120)
    if completed.returncode or not output.is_file():
        raise BlenderWorkflowError(f"Blender could not create procedural {kind}: {(completed.stderr or completed.stdout).strip()[-1200:]}")
    return {"format": "toolbox-procedural-blender-prop/v1", "kind": kind, "output": str(output), "autoexec": "disabled", "generation": "simple_original_procedural_geometry", "execution": "local_only"}


def handoff_report(source: Path) -> dict[str, Any]:
    """Combine non-mutating Blender inspection evidence into a game handoff report."""
    source, _ = _validate(source)
    if source.suffix.casefold() != ".blend":
        raise BlenderWorkflowError("Blender handoff reports currently support .blend files")
    return {
        "format": "toolbox-blender-handoff-report/v1",
        "source": str(source),
        "scene": inspect_blend(source),
        "preflight": preflight_blend(source),
        "game_asset": inspect_game_asset(source),
        "mutation": "none",
        "execution": "local_only",
    }
