"""Lesson injection: the top-k relevant guidance lines, under a hard budget.

Relevance = embedding similarity on the question (+ a content-type match
bonus). The injected section may never exceed ``lessons_injection_token_cap``
tokens — lessons exist to raise accuracy, not to erode the token economy.
"""
from __future__ import annotations

import re
from typing import Any

from watch_skill.answer.types import est_text_tokens
from watch_skill.config import get_settings
from watch_skill.index import embeddings as emb
from watch_skill.lessons import store
from watch_skill.lessons.classify import classify_content_type

_TOP_K = 5
_MIN_SIMILARITY = 0.25
_CONTENT_TYPE_BONUS = 0.15
_STOPWORDS = {"about", "and", "are", "at", "do", "does", "for", "how", "is", "of", "on", "the", "to", "what", "when", "where", "which"}

# lessons excluded from injection right now — the eval report uses this to
# ask "does this answer still pass WITHOUT the lesson?" (prunable check)
_EXCLUDED_LESSON_IDS: set[int] = set()


class excluding:
    """Context manager: suppress specific lessons during injection."""

    def __init__(self, lesson_ids: list[int]) -> None:
        self.lesson_ids = set(lesson_ids)

    def __enter__(self) -> None:
        _EXCLUDED_LESSON_IDS.update(self.lesson_ids)

    def __exit__(self, *exc_info: object) -> None:
        _EXCLUDED_LESSON_IDS.difference_update(self.lesson_ids)


def _terms(text: str) -> set[str]:
    return {
        term for term in re.findall(r"[\w'-]+", text.casefold())
        if len(term) > 2 and term not in _STOPWORDS
    }


def relevant_guidance(question: str, video: dict[str, Any]) -> list[str]:
    """Guidance lines for this question/video, budget-capped, LRU-touched."""
    settings = get_settings()
    conn = store.connect()
    try:
        rows = conn.execute(
            "SELECT id, content_type, question, guidance, embedding, dim FROM lessons"
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return []

    content_type = classify_content_type(video)
    scored: list[tuple[float, int, str]] = []
    vecs = emb.embed_texts([question])
    if vecs:
        query = vecs[0]
        for row in rows:
            if row["embedding"] is None or row["id"] in _EXCLUDED_LESSON_IDS:
                continue
            sim = emb.cosine_similarity(query, emb.unpack_vector(row["embedding"], row["dim"]))
            if row["content_type"] == content_type:
                sim += _CONTENT_TYPE_BONUS
            if sim >= _MIN_SIMILARITY:
                scored.append((sim, row["id"], row["guidance"]))
    else:
        query_terms = _terms(question)
        for row in rows:
            if row["id"] in _EXCLUDED_LESSON_IDS:
                continue
            overlap = query_terms & _terms(f"{row['question']} {row['guidance']}")
            if len(overlap) >= min(2, len(query_terms)):
                score = len(overlap) / max(1, len(query_terms))
                if row["content_type"] == content_type:
                    score += _CONTENT_TYPE_BONUS
                scored.append((score, row["id"], row["guidance"]))
    scored.sort(reverse=True)

    lines: list[str] = []
    used_ids: list[int] = []
    budget = settings.lessons_injection_token_cap
    spent = 0
    for _sim, lesson_id, guidance in scored[:_TOP_K]:
        cost = est_text_tokens(guidance)
        if spent + cost > budget:
            break
        spent += cost
        lines.append(guidance)
        used_ids.append(lesson_id)
    store.mark_used(used_ids)
    return lines
