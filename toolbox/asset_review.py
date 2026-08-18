"""Evidence-bounded acceptance-criteria assessments for local Watch timelines."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .timeline_review import TimelineReviewError, _terms, _timestamp, load_timeline


class AssetReviewError(ValueError):
    """Raised when an asset-review criteria document is malformed or unsafe."""


CRITERIA_FORMAT = "toolbox-asset-review-criteria/v1"


def load_criteria(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Criteria file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AssetReviewError(f"Criteria file is not valid JSON: {path}") from error
    if payload.get("format") != CRITERIA_FORMAT:
        raise AssetReviewError(f"Criteria must use {CRITERIA_FORMAT}")
    criteria = payload.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise AssetReviewError("Criteria must contain a non-empty criteria list")
    ids: set[str] = set()
    for item in criteria:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise AssetReviewError("Each criterion needs a non-empty id")
        if item["id"] in ids:
            raise AssetReviewError(f"Criteria contains duplicate id: {item['id']}")
        ids.add(item["id"])
        for field in ("required_terms", "any_of_terms", "forbidden_terms"):
            terms = item.get(field, [])
            if not isinstance(terms, list) or not all(isinstance(term, str) and term.strip() for term in terms):
                raise AssetReviewError(f"Criterion {item['id']} has invalid {field}")
        if not any(item.get(field) for field in ("required_terms", "any_of_terms", "forbidden_terms")):
            raise AssetReviewError(f"Criterion {item['id']} needs evidence terms")
    return criteria


def _evidence_items(timeline: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = []
    for item in timeline["evidence_timeline"]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("ocr_text") or "").strip()
        if not text:
            continue
        evidence.append({
            "kind": item.get("kind", "evidence"),
            "timestamp_seconds": _timestamp(item),
            "text": text,
            "terms": _terms(text),
        })
    return evidence


def _citations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: item[key] for key in ("kind", "timestamp_seconds", "text")}
        for item in sorted(items, key=lambda item: item["timestamp_seconds"])
    ]


def assess_timeline(timeline_path: Path, criteria_path: Path) -> dict[str, Any]:
    """Assess explicit criteria only when local text/OCR evidence supports it."""
    source = timeline_path.resolve()
    criteria_source = criteria_path.resolve()
    timeline = load_timeline(source)
    criteria = load_criteria(criteria_source)
    evidence = _evidence_items(timeline)
    findings = []
    for criterion in criteria:
        required = _terms(" ".join(criterion.get("required_terms", [])))
        any_of = _terms(" ".join(criterion.get("any_of_terms", [])))
        forbidden = _terms(" ".join(criterion.get("forbidden_terms", [])))
        forbidden_hits = [item for item in evidence if forbidden & item["terms"]]
        required_hits = [item for item in evidence if required <= item["terms"]] if required else evidence
        any_hits = [item for item in evidence if any_of & item["terms"]] if any_of else evidence
        if forbidden_hits:
            status = "FAIL"
            citations = _citations(forbidden_hits)
            reason = "Forbidden evidence was found."
        elif required_hits and any_hits:
            status = "PASS"
            citations = _citations([*required_hits, *any_hits])
            reason = "Required local evidence was found."
        else:
            status = "NEEDS_HUMAN_REVIEW"
            citations = []
            reason = "The saved transcript/OCR evidence cannot verify this criterion."
        findings.append({
            "id": criterion["id"],
            "description": criterion.get("description", criterion["id"]),
            "status": status,
            "reason": reason,
            "citations": citations,
        })
    statuses = {finding["status"] for finding in findings}
    overall = "FAIL" if "FAIL" in statuses else "PASS" if statuses == {"PASS"} else "NEEDS_HUMAN_REVIEW"
    return {
        "format": "toolbox-asset-review/v1",
        "created_at": datetime.now(UTC).isoformat(),
        "timeline": str(source),
        "criteria": str(criteria_source),
        "overall_status": overall,
        "findings": findings,
        "limitations": "This is a local evidence assessment. Criteria without transcript or OCR support require human visual review; no model inference was used.",
        "provenance": {
            "tool": "toolbox-local-asset-review",
            "execution": "local_only",
            "source_timeline_format": timeline["format"],
        },
    }


def write_assessment(assessment: dict[str, Any], source: Path, output: Path, *, overwrite: bool = False) -> Path:
    output = output.resolve()
    if output.suffix.casefold() != ".json":
        raise AssetReviewError("Assessment output must use a .json extension")
    if output == source.resolve():
        raise AssetReviewError("Assessment output must differ from the source timeline")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    return output
