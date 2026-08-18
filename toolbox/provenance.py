"""Explicit sidecar creation for generated or transformed assets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def sidecar_path(asset: Path) -> Path:
    return asset.with_name(f"{asset.name}.provenance.json")


def create_sidecar(
    asset: Path,
    *,
    tools: list[str],
    source_assets: list[str],
    human_modifications: str,
    commercial_use: str,
    force: bool = False,
) -> Path:
    if not asset.is_file():
        raise FileNotFoundError(f"Asset does not exist: {asset}")
    sidecar = sidecar_path(asset)
    if sidecar.exists() and not force:
        raise FileExistsError(f"Sidecar already exists: {sidecar}; use --force to replace it")
    payload = {
        "format": "toolbox-provenance/v1",
        "artifact": asset.name,
        "created_at": datetime.now(UTC).isoformat(),
        "created_with": [{"tool": tool} for tool in tools],
        "commercial_use": commercial_use,
        "source_assets": source_assets,
        "human_modifications": human_modifications,
    }
    sidecar.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return sidecar
