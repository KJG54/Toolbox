"""Review-only capability-gap briefs for agents using Toolbox."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .routing import recommend


class CapabilityResearchError(ValueError):
    """Raised when a requested research brief cannot be written safely."""


def research_capability(
    capability: str,
    *,
    commercial: bool = False,
    free_only: bool = False,
    input_format: str | None = None,
) -> dict[str, Any]:
    """Return installed routing advice or a review-only capability-gap brief."""
    routing = recommend(
        capability,
        commercial=commercial,
        free_only=free_only,
        input_format=input_format,
    )
    if not routing["capability_gap"]:
        return {
            "format": "toolbox-capability-research/v1",
            "status": "AVAILABLE",
            "request": {
                "capability": capability,
                "commercial": commercial,
                "free_only": free_only,
                "input_format": input_format,
            },
            "routing": routing,
            "next_action": "Use the highest-ranked local candidate or inspect its status.",
        }
    return {
        "format": "toolbox-capability-research/v1",
        "status": "CAPABILITY_GAP",
        "request": {
            "capability": capability,
            "commercial": commercial,
            "free_only": free_only,
            "input_format": input_format,
        },
        "routing": routing,
        "research_requirements": [
            "Use the candidate's official project documentation.",
            "Verify the license from the primary license or model-card source.",
            "Record local hardware and installation requirements.",
            "Present candidates for human review before adding, installing, or invoking them.",
        ],
        "mutations_performed": [],
        "external_actions_performed": [],
    }


def write_research_brief(brief: dict[str, Any], output: Path, *, overwrite: bool = False) -> Path:
    output = output.resolve()
    if output.suffix.casefold() != ".json":
        raise CapabilityResearchError("Capability research output must use a .json extension")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
    return output
