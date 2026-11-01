"""Conservative local memory matching and contradiction hints.

This module never merges, deletes, or rewrites a memory. It only reports likely
duplicates, related facts, and possible polarity changes for owner review.
"""
import re
from collections.abc import Iterable

from app.services.semantic_memory import cosine_similarity, embed_text

_TOKEN_RE = re.compile(r"[\wآ-ی]{2,}", re.UNICODE)
_NEGATION_RE = re.compile(
    r"(?:^|\s)(?:نه|نیست\w*|ندار\w*|نمی\s*\w+|هرگز|هیچ\s*وقت)(?:$|\s)"
)
_STOP_WORDS = {
    "من", "تو", "او", "ما", "شما", "آنها", "این", "آن", "را", "به", "از",
    "در", "با", "برای", "که", "و", "یا", "اما", "اگر", "هم", "همه",
    "یک", "یه", "است", "هست", "بود", "باشد", "می", "می‌", "روی", "تا",
}


def normalize_persian(text: str) -> str:
    value = (text or "").casefold().replace("ي", "ی").replace("ك", "ک")
    value = value.replace("\u200c", " ").replace("\u200f", " ")
    value = re.sub(r"[\u064b-\u065f\u0670]", "", value)
    value = re.sub(r"[^\wآ-ی\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _has_negation(text: str) -> bool:
    return bool(_NEGATION_RE.search(normalize_persian(text)))


def _canonical_tokens(text: str) -> set[str]:
    value = normalize_persian(text)
    value = re.sub(r"نمی\s*([آ-ی]+)", r"\1", value)
    for negative, positive in (
        ("ندارم", "دارم"),
        ("نداری", "داری"),
        ("ندارد", "دارد"),
        ("ندارند", "دارند"),
        ("نیستم", "هستم"),
        ("نیستی", "هستی"),
        ("نیست", "است"),
    ):
        value = value.replace(negative, positive)
    return {
        token for token in _TOKEN_RE.findall(value)
        if token not in _STOP_WORDS and len(token) > 1
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union)


def layer_for_category(category: str) -> str:
    if category == "preference":
        return "preference"
    if category in {"important_event", "shared_story"}:
        return "episodic"
    return "semantic"


def find_memory_matches(
    content: str,
    memories: Iterable,
    *,
    limit: int = 5,
) -> list[dict]:
    """Return review hints without mutating any stored memory."""
    candidate = normalize_persian(content)
    if not candidate:
        return []

    candidate_tokens = _canonical_tokens(content)
    candidate_negative = _has_negation(content)
    candidate_embedding = embed_text(content)
    matches: list[dict] = []

    for memory in memories:
        existing_content = memory.content or ""
        existing = normalize_persian(existing_content)
        if not existing:
            continue

        lexical_similarity = _jaccard(candidate_tokens, _canonical_tokens(existing_content))
        semantic_similarity = 0.0
        existing_embedding = getattr(memory, "embedding", None)
        if candidate_embedding is not None and existing_embedding:
            semantic_similarity = cosine_similarity(candidate_embedding, existing_embedding)
        similarity = max(lexical_similarity, semantic_similarity)

        opposite_polarity = (
            lexical_similarity >= 0.45
            and candidate_negative != _has_negation(existing_content)
        )
        if opposite_polarity:
            kind = "potential_conflict"
            reason = "موضوع این خاطره شبیه خاطره قبلی است، اما جهت جمله متفاوت است؛ ممکن است اطلاعات تغییر کرده باشد."
        elif similarity >= 0.88:
            kind = "duplicate"
            reason = "این خاطره بسیار شبیه یک خاطره ذخیره‌شده است."
        elif similarity >= 0.48:
            kind = "related"
            reason = "این خاطره با یکی از اطلاعات قبلی ارتباط زیادی دارد."
        else:
            continue

        matches.append({
            "memory_id": memory.id,
            "category": memory.category,
            "content": existing_content,
            "kind": kind,
            "similarity": round(max(0.0, min(1.0, similarity)), 3),
            "reason": reason,
        })

    priority = {"potential_conflict": 0, "duplicate": 1, "related": 2}
    matches.sort(key=lambda item: (priority[item["kind"]], -item["similarity"]))
    return matches[:max(1, min(limit, 10))]
