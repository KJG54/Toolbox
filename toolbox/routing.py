"""Deterministic, local-only Toolbox recommendation logic."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from .doctor import detect_hardware, detect_tools
from .registry import Registry, load_registry


class HardwareOutcome(StrEnum):
    LOCAL_OK = "LOCAL_OK"
    LOCAL_SLOW = "LOCAL_SLOW"
    HARDWARE_UPGRADE_REQUIRED = "HARDWARE_UPGRADE_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


def _vram_gb(hardware: dict[str, Any]) -> float:
    return max((gpu["vram_mb"] / 1024 for gpu in hardware.get("gpus", [])), default=0.0)


def hardware_outcome(tool: dict[str, Any], hardware: dict[str, Any]) -> HardwareOutcome:
    requirements = tool.get("hardware", {})
    minimum = requirements.get("min_vram_gb")
    recommended = requirements.get("recommended_vram_gb")
    available = _vram_gb(hardware)
    if requirements.get("gpu_required") and available == 0:
        return HardwareOutcome.HARDWARE_UPGRADE_REQUIRED
    if minimum is not None and available < minimum:
        return HardwareOutcome.HARDWARE_UPGRADE_REQUIRED
    if recommended is not None and available < recommended:
        return HardwareOutcome.LOCAL_SLOW
    return HardwareOutcome.LOCAL_OK


def recommend(
    capability: str,
    *,
    commercial: bool = False,
    free_only: bool = False,
    allow_external: bool = False,
    input_format: str | None = None,
    registry: Registry | None = None,
    hardware: dict[str, Any] | None = None,
    installed: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    hardware = hardware or detect_hardware()
    installed = installed or detect_tools()
    licenses = {record["id"]: record for record in registry.records("licenses")}
    candidates = []
    rejected = []
    for tool in registry.records("tools"):
        if capability not in tool.get("capabilities", []):
            continue
        license_record = licenses[tool["license_id"]]
        reasons = []
        if commercial and license_record["commercial_use"] not in {"allowed", "allowed_with_attribution"}:
            reasons.append("commercial-use status is not approved")
        if free_only and tool.get("cost", {}).get("tier") != "free":
            reasons.append("not free")
        if tool.get("external_opt_in") and not allow_external:
            reasons.append("external service requires explicit approval")
        if input_format and input_format not in tool.get("formats", {}).get("input", []):
            reasons.append(f"does not accept {input_format}")
        outcome = hardware_outcome(tool, hardware)
        if outcome == HardwareOutcome.HARDWARE_UPGRADE_REQUIRED:
            reasons.append("local hardware is insufficient")
        if reasons:
            rejected.append({"id": tool["id"], "reasons": reasons, "hardware": outcome})
            continue
        ready = installed.get(tool["id"], {}).get("status", "").startswith("READY")
        score = tool.get("routing_priority", 0) + 15 + (20 if ready else 0)
        if tool.get("cost", {}).get("tier") == "free":
            score += 15
        if outcome == HardwareOutcome.LOCAL_OK:
            score += 10
        candidates.append({"id": tool["id"], "score": score, "hardware": outcome, "installed": ready})
    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["id"]))
    return {
        "capability": capability,
        "recommendations": candidates,
        "rejected": rejected,
        "capability_gap": not candidates,
        "next_action": (
            "Research candidates from official product and license sources; present a proposed record for review."
            if not candidates
            else "Use the highest-ranked local tool or inspect its status before execution."
        ),
    }
