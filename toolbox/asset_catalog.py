"""Read-only local asset cataloging and deterministic filtering."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .provenance import sidecar_path


class AssetCatalogError(ValueError):
    """Raised when a local catalog request is malformed or too broad."""


_IGNORED_DIRECTORIES = {".git", ".venv", "cache", "runtime", "__pycache__"}
_TOKEN = re.compile(r"[a-z0-9]+")


def _root(directory: Path) -> Path:
    directory = directory.resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"Asset directory does not exist: {directory}")
    return directory


def _tokens(value: str) -> list[str]:
    return _TOKEN.findall(value.casefold())


def _provenance(asset: Path) -> dict[str, Any] | None:
    path = sidecar_path(asset)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "MALFORMED"}
    return {
        "status": "PRESENT",
        "commercial_use": payload.get("commercial_use", "requires_review"),
        "tools": [item.get("tool") for item in payload.get("created_with", []) if item.get("tool")],
    }


def build_catalog(directory: Path, *, max_files: int = 10000) -> dict[str, Any]:
    """Inspect local files without writing an index or changing source assets."""
    root = _root(directory)
    if not 1 <= max_files <= 100000:
        raise AssetCatalogError("max_files must be between 1 and 100000")
    assets: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if any(part.casefold() in _IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        if not path.is_file() or path.name.endswith(".provenance.json"):
            continue
        if len(assets) >= max_files:
            raise AssetCatalogError(f"Catalog stopped at {max_files} files; narrow the directory or raise --max-files")
        relative = path.relative_to(root).as_posix()
        assets.append({
            "path": relative,
            "format": path.suffix.casefold().lstrip(".") or "none",
            "bytes": path.stat().st_size,
            "tags": sorted(set(_tokens(path.stem))),
            "provenance": _provenance(path),
        })
    assets.sort(key=lambda item: item["path"].casefold())
    return {
        "format": "toolbox-local-asset-catalog/v1",
        "root": str(root),
        "asset_count": len(assets),
        "assets": assets,
        "execution": "local_only",
        "mutations_performed": [],
    }


def search_catalog(
    directory: Path,
    query: str = "",
    *,
    format_name: str | None = None,
    tag: str | None = None,
    commercial: bool = False,
    max_files: int = 10000,
) -> dict[str, Any]:
    """Filter local catalog records by filename tags, format, and recorded license state."""
    catalog = build_catalog(directory, max_files=max_files)
    query_tokens = set(_tokens(query))
    tag = tag.casefold() if tag else None
    format_name = format_name.casefold().lstrip(".") if format_name else None
    results = []
    for asset in catalog["assets"]:
        tags = set(asset["tags"])
        if format_name and asset["format"] != format_name:
            continue
        if tag and tag not in tags:
            continue
        if query_tokens and not query_tokens.issubset(tags | set(_tokens(asset["path"]))):
            continue
        provenance = asset["provenance"] or {}
        if commercial and provenance.get("commercial_use") not in {"allowed", "allowed_with_attribution"}:
            continue
        results.append(asset)
    return {
        "format": "toolbox-local-asset-catalog-search/v1",
        "root": catalog["root"],
        "query": query,
        "filters": {"format": format_name, "tag": tag, "commercial": commercial},
        "results": results,
        "execution": "local_only",
        "next_action": "Review source-license records before external distribution." if results else "No local assets matched the filters.",
    }


def write_catalog(catalog: dict[str, Any], output: Path, *, overwrite: bool = False) -> Path:
    """Persist an explicitly requested catalog report without touching indexed assets."""
    output = output.resolve()
    if output.exists() and not overwrite:
        raise FileExistsError(f"Catalog output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return output
