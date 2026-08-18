"""Search the locally curated, license-aware asset-source catalog."""

from __future__ import annotations

from typing import Any

from .registry import load_registry


def search_asset_sources(query: str, *, kind: str | None = None, commercial: bool = False) -> dict[str, Any]:
    """Return source recommendations without contacting or downloading from a provider."""
    query = query.strip()
    if not query:
        raise ValueError("Asset search query must not be empty")
    tokens = {token for token in query.casefold().replace("-", " ").split() if token}
    licenses = {record["id"]: record for record in load_registry().records("licenses")}
    results = []
    for source in load_registry().records("asset_sources"):
        if kind and kind not in source.get("kinds", []):
            continue
        license_record = licenses[source["license_id"]]
        commercial_status = license_record["commercial_use"]
        if commercial and commercial_status not in {"allowed", "allowed_with_attribution"}:
            continue
        searchable = " ".join([source["name"], *source.get("kinds", []), *source.get("tags", [])]).casefold()
        score = sum(token in searchable for token in tokens) + (2 if kind in source.get("kinds", []) else 0)
        if score:
            results.append({
                "id": source["id"],
                "name": source["name"],
                "homepage": source["homepage"],
                "kinds": source["kinds"],
                "license_status": commercial_status,
                "per_asset_review_required": source.get("per_asset_review_required", False),
                "score": score,
            })
    results.sort(key=lambda item: (-item["score"], item["id"]))
    return {
        "format": "toolbox-asset-source-search/v1",
        "query": query,
        "kind": kind,
        "commercial": commercial,
        "results": results,
        "external_actions_performed": [],
        "next_action": (
            "Review the selected source and individual asset license before downloading."
            if results else
            "No locally cataloged source matched. Create a capability-gap brief before researching new providers."
        ),
    }
