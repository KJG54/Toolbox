"""Local texture and material naming validation without changing images."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image


class TextureValidationError(ValueError):
    """Raised when no supported local texture can be inspected."""


_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tga"}
_MAPS = {
    "base_color": ("basecolor", "base_color", "albedo", "diffuse", "color"),
    "normal": ("normal", "nrm"),
    "roughness": ("roughness", "rough"),
    "metallic": ("metallic", "metalness", "metal"),
    "ambient_occlusion": ("ambientocclusion", "ambient_occlusion", "ao"),
    "emissive": ("emissive", "emission", "emit"),
    "opacity": ("opacity", "alpha", "transparency"),
}


def _files(source: Path) -> list[Path]:
    source = source.resolve()
    if source.is_file():
        files = [source]
    elif source.is_dir():
        files = [path for path in source.rglob("*") if path.is_file()]
    else:
        raise FileNotFoundError(f"Texture source does not exist: {source}")
    files = [path for path in files if path.suffix.casefold() in _FORMATS]
    if not files:
        raise TextureValidationError("No supported texture images were found")
    return sorted(files, key=lambda path: str(path).casefold())


def _power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def _classification(stem: str) -> tuple[str | None, str]:
    normalized = re.sub(r"[^a-z0-9]+", "_", stem.casefold()).strip("_")
    for map_name, aliases in _MAPS.items():
        for alias in aliases:
            if normalized == alias or normalized.endswith(f"_{alias}"):
                base = normalized[: -len(alias)].rstrip("_") or normalized
                return map_name, base
    return None, normalized


def validate_textures(source: Path) -> dict[str, Any]:
    """Report dimensions, alpha, and recognizable material-map groups locally."""
    source = source.resolve()
    textures = []
    groups: dict[str, list[str]] = defaultdict(list)
    for path in _files(source):
        with Image.open(path) as image:
            width, height = image.size
            has_alpha = "A" in image.getbands() or "transparency" in image.info
            map_name, group = _classification(path.stem)
            record = {
                "path": str(path if source.is_file() else path.relative_to(source)),
                "format": path.suffix.casefold().lstrip("."),
                "width": width,
                "height": height,
                "power_of_two": _power_of_two(width) and _power_of_two(height),
                "square": width == height,
                "has_alpha": has_alpha,
                "map_type": map_name,
                "material_group": group,
            }
            textures.append(record)
            if map_name:
                groups[group].append(map_name)
    material_groups = [
        {"name": name, "maps": sorted(set(maps)), "missing_common_maps": [map_name for map_name in ("base_color", "normal", "roughness") if map_name not in maps]}
        for name, maps in sorted(groups.items())
    ]
    issues = []
    if any(not texture["power_of_two"] for texture in textures):
        issues.append("non_power_of_two_dimensions")
    if any(texture["map_type"] is None for texture in textures):
        issues.append("unclassified_texture_names")
    if any(group["missing_common_maps"] for group in material_groups):
        issues.append("incomplete_material_map_sets")
    return {
        "format": "toolbox-texture-validation/v1",
        "source": str(source),
        "textures": textures,
        "material_groups": material_groups,
        "issues": issues,
        "status": "READY_FOR_HUMAN_REVIEW" if not issues else "NEEDS_TEXTURE_REVIEW",
        "execution": "local_only",
    }
