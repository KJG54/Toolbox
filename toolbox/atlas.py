"""Source-preserving local sprite-sheet and texture-atlas packing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image


class AtlasError(ValueError):
    """Raised when local images cannot fit a requested atlas."""


_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def pack_atlas(source_directory: Path, output: Path, *, padding: int = 2, max_width: int = 2048, overwrite: bool = False) -> dict[str, Any]:
    """Pack local images in deterministic filename order; never alter inputs."""
    source_directory = source_directory.resolve()
    output = output.resolve()
    if not source_directory.is_dir():
        raise FileNotFoundError(f"Atlas source directory does not exist: {source_directory}")
    if output.suffix.casefold() != ".png":
        raise AtlasError("Atlas output must use .png to preserve alpha")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    metadata = output.with_name(f"{output.stem}.atlas.json")
    if metadata.exists() and not overwrite:
        raise FileExistsError(f"Atlas metadata already exists: {metadata}; use --force to replace it")
    if not 0 <= padding <= 128 or not 16 <= max_width <= 16384:
        raise AtlasError("padding must be 0-128 and max_width must be 16-16384")
    sources = sorted([path for path in source_directory.iterdir() if path.is_file() and path.suffix.casefold() in _FORMATS and path.resolve() != output], key=lambda path: path.name.casefold())
    if not sources:
        raise AtlasError("No supported images were found directly in the atlas source directory")
    sprites: list[tuple[Path, Image.Image]] = []
    for source in sources:
        with Image.open(source) as opened:
            image = opened.convert("RGBA")
            if image.width + 2 * padding > max_width:
                image.close()
                raise AtlasError(f"{source.name} exceeds the maximum atlas width")
            sprites.append((source, image))
    positions: list[dict[str, Any]] = []
    x = y = row_height = 0
    for source, image in sprites:
        if x and x + image.width + padding > max_width:
            x, y, row_height = 0, y + row_height + padding, 0
        positions.append({"name": source.name, "x": x, "y": y, "width": image.width, "height": image.height})
        x += image.width + padding
        row_height = max(row_height, image.height)
    atlas_width = min(max_width, max(item["x"] + item["width"] for item in positions) + padding)
    atlas_height = y + row_height + padding
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    try:
        for (_, image), position in zip(sprites, positions, strict=True):
            atlas.alpha_composite(image, (position["x"], position["y"]))
        output.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(output)
    finally:
        atlas.close()
        for _, image in sprites:
            image.close()
    metadata.write_text(json.dumps({"format": "toolbox-atlas-layout/v1", "atlas": output.name, "padding": padding, "sprites": positions}, indent=2) + "\n", encoding="utf-8")
    return {"format": "toolbox-atlas/v1", "source_directory": str(source_directory), "output": str(output), "metadata": str(metadata), "size": [atlas_width, atlas_height], "sprites": positions, "execution": "local_only"}
