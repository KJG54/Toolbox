"""Component-interpreter bridge for local semantic evidence-library search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from toolbox.asset_review import _evidence_items
from toolbox.timeline_review import TimelineReviewError, load_timeline
from watch_skill.index import embeddings as emb


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--max-results", type=int, required=True)
    args = parser.parse_args()
    candidates = []
    scanned = 0
    for path in args.directory.rglob("*.json"):
        try:
            timeline = load_timeline(path)
        except (FileNotFoundError, TimelineReviewError):
            continue
        scanned += 1
        for item in _evidence_items(timeline):
            candidates.append({
                "timeline": str(path.resolve()), "kind": item["kind"],
                "timestamp_seconds": item["timestamp_seconds"], "text": item["text"],
            })
    vectors = emb.embed_texts([args.question, *[item["text"] for item in candidates]])
    if not vectors:
        raise SystemExit("The local semantic embedding model is not cached")
    query, vectors = vectors[0], vectors[1:]
    for item, vector in zip(candidates, vectors, strict=False):
        item["relevance"] = round(emb.cosine_similarity(query, vector), 3)
    candidates.sort(key=lambda item: (-item["relevance"], item["timeline"], item["timestamp_seconds"]))
    print(json.dumps({
        "format": "toolbox-evidence-library-search/v1", "library": str(args.directory.resolve()),
        "question": args.question, "timelines_scanned": scanned,
        "matches": candidates[:args.max_results],
        "status": "EVIDENCE_FOUND" if candidates else "NO_MATCHING_EVIDENCE",
        "limitations": "Local semantic embeddings only; no original media was processed.",
        "provenance": {"tool": "toolbox-local-evidence-library", "execution": "local_only", "semantic": True},
    }))


if __name__ == "__main__":
    main()
