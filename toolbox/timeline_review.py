"""Question-directed, local evidence retrieval over saved Watch timelines."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class TimelineReviewError(ValueError):
    """Raised when a timeline is not a usable Toolbox Watch-review artifact."""


_STOPWORDS = {
    "a", "an", "and", "are", "at", "do", "does", "for", "how", "in", "is", "it",
    "of", "on", "the", "to", "was", "what", "when", "where", "which", "with",
}
_WORD = re.compile(r"[\w'-]+", re.UNICODE)


def _script_tokens(text: str) -> set[str]:
    """Keep individual CJK, Kana, and Hangul characters searchable locally."""
    return {
        character
        for character in text
        if (
            "\u3040" <= character <= "\u30ff"
            or "\u3400" <= character <= "\u9fff"
            or "\uac00" <= character <= "\ud7af"
        )
    }


def _terms(text: str) -> set[str]:
    words = {
        word.casefold()
        for word in _WORD.findall(text)
        if len(word) > 2 and word.casefold() not in _STOPWORDS
    }
    return words | _script_tokens(text)


def _timestamp(item: dict[str, Any]) -> float:
    value = item.get("timestamp_seconds", item.get("start_seconds", 0.0))
    return float(value)


def _format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def load_timeline(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Timeline does not exist: {path}")
    try:
        timeline = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise TimelineReviewError(f"Timeline is not valid JSON: {path}") from error
    if timeline.get("format") != "toolbox-watch-review/v1":
        raise TimelineReviewError("Timeline must use toolbox-watch-review/v1")
    if not isinstance(timeline.get("evidence_timeline"), list):
        raise TimelineReviewError("Timeline is missing its evidence_timeline list")
    return timeline


def answer_timeline(path: Path, question: str, *, max_evidence: int = 5) -> dict[str, Any]:
    """Return extractive, timestamped evidence without a model or remote call."""
    if not question.strip():
        raise TimelineReviewError("Question must not be empty")
    if max_evidence < 1:
        raise TimelineReviewError("max_evidence must be at least 1")
    source = path.resolve()
    timeline = load_timeline(source)
    query_terms = _terms(question)
    if not query_terms:
        raise TimelineReviewError("Question needs at least one meaningful search term")

    matches: list[dict[str, Any]] = []
    for item in timeline["evidence_timeline"]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("ocr_text") or "").strip()
        if not text:
            continue
        evidence_terms = _terms(text)
        overlap = query_terms & evidence_terms
        if not overlap:
            continue
        score = round(len(overlap) / len(query_terms), 3)
        timestamp = _timestamp(item)
        citation = {
            "kind": item.get("kind", "evidence"),
            "timestamp_seconds": timestamp,
            "timestamp": _format_timestamp(timestamp),
            "text": text,
            "matched_terms": sorted(overlap),
            "relevance": score,
        }
        if item.get("path"):
            citation["path"] = item["path"]
        matches.append(citation)
    matches.sort(key=lambda item: (-item["relevance"], item["timestamp_seconds"]))
    citations = matches[:max_evidence]

    if citations:
        best = citations[0]
        answer = f"Top matching evidence at {best['timestamp']}: {best['text']}"
        status = "EVIDENCE_FOUND"
    else:
        answer = "No matching transcript or OCR evidence was found in this saved timeline."
        status = "NO_MATCHING_EVIDENCE"
    return {
        "format": "toolbox-timeline-answer/v1",
        "created_at": datetime.now(UTC).isoformat(),
        "timeline": str(source),
        "question": question,
        "status": status,
        "answer": answer,
        "citations": citations,
        "limitations": "Extractive local retrieval only; it does not infer content absent from transcript or OCR evidence.",
        "provenance": {
            "tool": "toolbox-local-timeline-review",
            "execution": "local_only",
            "source_timeline_format": timeline["format"],
        },
    }


def write_answer(
    answer: dict[str, Any], path: Path, output: Path, *, overwrite: bool = False
) -> Path:
    """Persist a query result without modifying the source evidence timeline."""
    output = output.resolve()
    if output.suffix.casefold() != ".json":
        raise TimelineReviewError("Answer output must use a .json extension")
    if output == path.resolve():
        raise TimelineReviewError("Answer output must differ from the source timeline")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(answer, indent=2) + "\n", encoding="utf-8")
    return output
