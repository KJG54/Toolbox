"""Explicit sidecar creation for generated or transformed assets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


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
    extra: dict[str, Any] | None = None,
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
    if extra:
        payload["extra"] = extra
    sidecar.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return sidecar


def record_external_generation(
    asset: Path,
    *,
    provider: str,
    plan: str,
    terms_url: str,
    output_status: str,
    prompt_reference: str,
    source_assets: list[str],
    force: bool = False,
) -> Path:
    """Record an already-downloaded external output without contacting its provider."""
    allowed_statuses = {"DRAFT_ONLY", "PERSONAL_ONLY", "ATTRIBUTION_REQUIRED", "RECHECK_TERMS", "RELEASE_APPROVED"}
    if not provider.strip() or not plan.strip():
        raise ValueError("provider and plan must not be empty")
    if not terms_url.startswith(("https://", "http://")):
        raise ValueError("terms_url must be an http(s) URL")
    if output_status not in allowed_statuses:
        raise ValueError(f"output_status must be one of: {', '.join(sorted(allowed_statuses))}")
    return create_sidecar(
        asset,
        tools=[f"external-provider:{provider.strip()}", "toolbox-external-generation-intake"],
        source_assets=source_assets,
        human_modifications="Recorded existing externally generated output; Toolbox made no network request.",
        commercial_use="allowed_with_attribution" if output_status == "ATTRIBUTION_REQUIRED" else "requires_review",
        force=force,
        extra={
            "external_generation": {
                "provider": provider.strip(),
                "plan": plan.strip(),
                "terms_url": terms_url,
                "output_status": output_status,
                "prompt_reference": prompt_reference.strip() or "not_recorded",
                "network_action": "none; metadata recorded locally after download",
            }
        },
    )
