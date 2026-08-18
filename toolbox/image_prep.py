"""Non-destructive local image preparation for textures and reference assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image


class ImagePrepError(ValueError):
    """Raised when an image derivative would be unsafe or unsupported."""


_SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def _source(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Image source does not exist: {path}")
    if path.suffix.casefold() not in _SUPPORTED:
        raise ImagePrepError(f"Unsupported image format: {path.suffix}")
    return path


def inspect_image_asset(source: Path) -> dict[str, Any]:
    source = _source(source)
    with Image.open(source) as image:
        width, height = image.size
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        return {
            "format": "toolbox-image-prep/v1",
            "source": str(source),
            "width": width,
            "height": height,
            "mode": image.mode,
            "has_alpha": has_alpha,
            "format_detected": image.format,
            "execution": "local_only",
        }


def prepare_image(
    source: Path,
    output: Path,
    *,
    max_width: int | None = None,
    max_height: int | None = None,
    allow_upscale: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    source = _source(source)
    output = output.resolve()
    if source == output:
        raise ImagePrepError("Output must differ from source; Toolbox never overwrites image sources")
    if output.suffix.casefold() not in _SUPPORTED:
        raise ImagePrepError("Image output must be PNG, JPEG, WebP, BMP, or TIFF")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if max_width is not None and max_width < 1 or max_height is not None and max_height < 1:
        raise ImagePrepError("Maximum image dimensions must be positive")
    with Image.open(source) as image:
        original_size = image.size
        bounds = (max_width or image.width, max_height or image.height)
        scale = min(bounds[0] / image.width, bounds[1] / image.height)
        if not allow_upscale:
            scale = min(scale, 1.0)
        destination_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        derivative = image.copy()
        if destination_size != image.size:
            derivative = derivative.resize(destination_size, Image.Resampling.LANCZOS)
        if output.suffix.casefold() in {".jpg", ".jpeg"} and "A" in derivative.getbands():
            derivative = derivative.convert("RGB")
        output.parent.mkdir(parents=True, exist_ok=True)
        derivative.save(output)
    return {
        "source": str(source),
        "output": str(output),
        "original_size": original_size,
        "output_size": destination_size,
        "resampled": destination_size != original_size,
        "upscale_allowed": allow_upscale,
        "execution": "local_only",
    }
