"""Ordered local evidence verification for software and UI tutorial workflows."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .asset_review import _evidence_items
from .timeline_review import _terms, load_timeline


class TutorialReviewError(ValueError):
    """Raised when a tutorial-step document is malformed or unsafe."""


STEPS_FORMAT = "toolbox-ui-tutorial-steps/v1"


def load_steps(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Tutorial steps file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise TutorialReviewError(f"Tutorial steps file is not valid JSON: {path}") from error
    if payload.get("format") != STEPS_FORMAT:
        raise TutorialReviewError(f"Tutorial steps must use {STEPS_FORMAT}")
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise TutorialReviewError("Tutorial steps must contain a non-empty steps list")
    ids: set[str] = set()
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("id"), str) or not step["id"]:
            raise TutorialReviewError("Each tutorial step needs a non-empty id")
        if step["id"] in ids:
            raise TutorialReviewError(f"Tutorial steps contains duplicate id: {step['id']}")
        ids.add(step["id"])
        for field in ("required_terms", "any_of_terms"):
            terms = step.get(field, [])
            if not isinstance(terms, list) or not all(isinstance(term, str) and term.strip() for term in terms):
                raise TutorialReviewError(f"Tutorial step {step['id']} has invalid {field}")
        if not step.get("required_terms") and not step.get("any_of_terms"):
            raise TutorialReviewError(f"Tutorial step {step['id']} needs evidence terms")
    return steps


def verify_tutorial(timeline_path: Path, steps_path: Path) -> dict[str, Any]:
    """Verify an ordered tutorial only from local transcript/OCR evidence."""
    source = timeline_path.resolve()
    steps_source = steps_path.resolve()
    timeline = load_timeline(source)
    steps = load_steps(steps_source)
    evidence = sorted(_evidence_items(timeline), key=lambda item: item["timestamp_seconds"])
    findings: list[dict[str, Any]] = []
    last_timestamp = float("-inf")
    for step in steps:
        required = _terms(" ".join(step.get("required_terms", [])))
        any_of = _terms(" ".join(step.get("any_of_terms", [])))
        matches = [
            item for item in evidence
            if (not required or required <= item["terms"])
            and (not any_of or any_of & item["terms"])
        ]
        in_order = [item for item in matches if item["timestamp_seconds"] >= last_timestamp]
        if in_order:
            item = in_order[0]
            status = "PASS"
            reason = "Local evidence matches this tutorial step in sequence."
            last_timestamp = item["timestamp_seconds"]
            citations = [{key: item[key] for key in ("kind", "timestamp_seconds", "text")}]
        elif matches:
            status = "OUT_OF_ORDER"
            reason = "Matching evidence exists, but only before the preceding verified step."
            citations = [{key: item[key] for key in ("kind", "timestamp_seconds", "text")} for item in matches]
        else:
            status = "NEEDS_HUMAN_REVIEW"
            reason = "The saved transcript/OCR evidence cannot verify this step."
            citations = []
        findings.append({
            "id": step["id"],
            "description": step.get("description", step["id"]),
            "status": status,
            "reason": reason,
            "citations": citations,
        })
    statuses = {finding["status"] for finding in findings}
    overall = "OUT_OF_ORDER" if "OUT_OF_ORDER" in statuses else "PASS" if statuses == {"PASS"} else "NEEDS_HUMAN_REVIEW"
    return {
        "format": "toolbox-ui-tutorial-review/v1",
        "created_at": datetime.now(UTC).isoformat(),
        "timeline": str(source),
        "steps": str(steps_source),
        "overall_status": overall,
        "findings": findings,
        "limitations": "This verifies only saved transcript or OCR evidence. It cannot infer an unseen click, control state, or visual change.",
        "provenance": {
            "tool": "toolbox-local-ui-tutorial-review",
            "execution": "local_only",
            "source_timeline_format": timeline["format"],
        },
    }


def write_tutorial_review(review: dict[str, Any], source: Path, output: Path, *, overwrite: bool = False) -> Path:
    output = output.resolve()
    if output.suffix.casefold() != ".json":
        raise TutorialReviewError("Tutorial review output must use a .json extension")
    if output == source.resolve():
        raise TutorialReviewError("Tutorial review output must differ from the source timeline")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    return output
