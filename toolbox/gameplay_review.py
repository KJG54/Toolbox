"""Ordered local evidence verification for gameplay recordings."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .asset_review import _evidence_items
from .timeline_review import _terms, load_timeline


class GameplayReviewError(ValueError):
    """Raised when a gameplay event plan is malformed or unsafe."""


EVENTS_FORMAT = "toolbox-gameplay-events/v1"


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Gameplay events file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise GameplayReviewError(f"Gameplay events file is not valid JSON: {path}") from error
    if payload.get("format") != EVENTS_FORMAT:
        raise GameplayReviewError(f"Gameplay events must use {EVENTS_FORMAT}")
    events = payload.get("events")
    if not isinstance(events, list) or not events:
        raise GameplayReviewError("Gameplay events must contain a non-empty events list")
    seen: set[str] = set()
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("id"), str) or not event["id"]:
            raise GameplayReviewError("Each gameplay event needs a non-empty id")
        if event["id"] in seen:
            raise GameplayReviewError(f"Gameplay events contains duplicate id: {event['id']}")
        seen.add(event["id"])
        for field in ("required_terms", "any_of_terms", "forbidden_terms"):
            values = event.get(field, [])
            if not isinstance(values, list) or not all(isinstance(value, str) and value.strip() for value in values):
                raise GameplayReviewError(f"Gameplay event {event['id']} has invalid {field}")
        if not any(event.get(field) for field in ("required_terms", "any_of_terms", "forbidden_terms")):
            raise GameplayReviewError(f"Gameplay event {event['id']} needs evidence terms")
    return events


def review_gameplay(timeline_path: Path, events_path: Path) -> dict[str, Any]:
    """Report observed, forbidden, missing, and out-of-order local evidence."""
    source = timeline_path.resolve()
    events_source = events_path.resolve()
    timeline = load_timeline(source)
    events = load_events(events_source)
    evidence = sorted(_evidence_items(timeline), key=lambda item: item["timestamp_seconds"])
    last_timestamp = float("-inf")
    findings = []
    for event in events:
        required = _terms(" ".join(event.get("required_terms", [])))
        any_of = _terms(" ".join(event.get("any_of_terms", [])))
        forbidden = _terms(" ".join(event.get("forbidden_terms", [])))
        forbidden_hits = [item for item in evidence if forbidden & item["terms"]]
        matches = [
            item for item in evidence
            if (not required or required <= item["terms"])
            and (not any_of or any_of & item["terms"])
        ]
        in_order = [item for item in matches if item["timestamp_seconds"] >= last_timestamp]
        if forbidden_hits:
            status, reason, selected = "FAIL", "Forbidden gameplay evidence was found.", forbidden_hits
        elif forbidden and not required and not any_of:
            status, reason, selected = "OBSERVED", "No forbidden gameplay evidence was found.", []
        elif in_order:
            status, reason, selected = "OBSERVED", "Local evidence matches this gameplay event in sequence.", [in_order[0]]
            last_timestamp = in_order[0]["timestamp_seconds"]
        elif matches:
            status, reason, selected = "OUT_OF_ORDER", "Matching evidence exists only before a previous event.", matches
        else:
            status, reason, selected = "NEEDS_HUMAN_REVIEW", "The saved transcript/OCR evidence cannot verify this gameplay event.", []
        findings.append({
            "id": event["id"],
            "description": event.get("description", event["id"]),
            "status": status,
            "reason": reason,
            "citations": [
                {key: item[key] for key in ("kind", "timestamp_seconds", "text")}
                for item in selected
            ],
        })
    statuses = {finding["status"] for finding in findings}
    overall = "FAIL" if "FAIL" in statuses else "OUT_OF_ORDER" if "OUT_OF_ORDER" in statuses else "PASS" if statuses == {"OBSERVED"} else "NEEDS_HUMAN_REVIEW"
    return {
        "format": "toolbox-gameplay-review/v1",
        "created_at": datetime.now(UTC).isoformat(),
        "timeline": str(source),
        "events": str(events_source),
        "overall_status": overall,
        "findings": findings,
        "limitations": "This uses only local transcript/OCR evidence. Visual-only gameplay events need human review or separately approved local vision evidence.",
        "provenance": {"tool": "toolbox-local-gameplay-review", "execution": "local_only"},
    }


def write_gameplay_review(review: dict[str, Any], source: Path, output: Path, *, overwrite: bool = False) -> Path:
    output = output.resolve()
    if output.suffix.casefold() != ".json":
        raise GameplayReviewError("Gameplay review output must use a .json extension")
    if output == source.resolve():
        raise GameplayReviewError("Gameplay review output must differ from the source timeline")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return output
