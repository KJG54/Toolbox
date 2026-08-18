"""Read-only cross-video search over local Watch evidence timelines."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .asset_review import _evidence_items
from .paths import ROOT
from .timeline_review import TimelineReviewError, _terms, load_timeline
from .watch_review import component_python


class EvidenceLibraryError(ValueError):
    """Raised when a requested local timeline library cannot be searched safely."""


def search_library(root: Path, question: str, *, max_results: int = 12, semantic: bool = False) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise EvidenceLibraryError(f"Timeline library directory does not exist: {root}")
    if max_results < 1:
        raise EvidenceLibraryError("max_results must be at least 1")
    query_terms = _terms(question)
    if not question.strip() or not query_terms:
        raise EvidenceLibraryError("Question needs at least one meaningful search term")
    if semantic:
        return _semantic_search(root, question, max_results)
    matches: list[dict[str, Any]] = []
    scanned = 0
    for path in root.rglob("*.json"):
        try:
            timeline = load_timeline(path)
        except (FileNotFoundError, TimelineReviewError):
            continue
        scanned += 1
        for item in _evidence_items(timeline):
            overlap = query_terms & item["terms"]
            if not overlap:
                continue
            matches.append({
                "timeline": str(path.resolve()),
                "kind": item["kind"],
                "timestamp_seconds": item["timestamp_seconds"],
                "text": item["text"],
                "matched_terms": sorted(overlap),
                "relevance": round(len(overlap) / len(query_terms), 3),
            })
    matches.sort(key=lambda item: (-item["relevance"], item["timeline"], item["timestamp_seconds"]))
    return {
        "format": "toolbox-evidence-library-search/v1",
        "library": str(root),
        "question": question,
        "timelines_scanned": scanned,
        "matches": matches[:max_results],
        "status": "EVIDENCE_FOUND" if matches else "NO_MATCHING_EVIDENCE",
        "limitations": "Local keyword/OCR/transcript search only. Use --semantic for the approved cached local embedding model.",
        "provenance": {"tool": "toolbox-local-evidence-library", "execution": "local_only"},
    }


def _semantic_search(root: Path, question: str, max_results: int) -> dict[str, Any]:
    command = [
        str(component_python()), str(ROOT / "toolbox" / "evidence_library_runner.py"),
        "--directory", str(root), "--question", question, "--max-results", str(max_results),
    ]
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, text=True, capture_output=True, check=False, env=environment)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()[-1000:]
        raise EvidenceLibraryError(f"Local semantic search failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise EvidenceLibraryError("Local semantic search returned malformed output") from error
