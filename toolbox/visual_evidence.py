"""Local pixel-level image inspection and comparison through Watch's environment."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .paths import ROOT


class VisualEvidenceError(ValueError):
    """Raised when a local visual-evidence operation cannot run."""


_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def _validate_image(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Image source does not exist: {path}")
    if path.suffix.casefold() not in _IMAGE_SUFFIXES:
        raise VisualEvidenceError(f"Unsupported image format: {path.suffix}")
    return path


def _run(*arguments: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "toolbox" / "visual_runner.py"), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()[-1200:]
        raise VisualEvidenceError(f"Local visual analysis failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise VisualEvidenceError("Local visual analysis returned malformed structured output") from error


def inspect_image(source: Path) -> dict[str, Any]:
    return _run("inspect", str(_validate_image(source)))


def compare_images(reference: Path, candidate: Path) -> dict[str, Any]:
    return _run("compare", str(_validate_image(reference)), str(_validate_image(candidate)))
