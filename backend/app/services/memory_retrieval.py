import re
import math
from collections import Counter
from datetime import datetime, timezone

from app.models import CompanionMemory
from app.services.semantic_memory import cosine_similarity, embed_text

_TOKEN_RE = re.compile(r"[\wآ-ی]{2,}", re.UNICODE)


def _tokens(text: str) -> Counter[str]:
    return Counter(token.casefold() for token in _TOKEN_RE.findall(text or ""))


def _memory_boost(memory: CompanionMemory) -> float:
    importance = max(1, min(5, getattr(memory, "importance", 3))) * 0.008
    confidence = max(0.0, min(1.0, getattr(memory, "confidence", 0.85))) * 0.025
    access_count = min(20, max(0, getattr(memory, "access_count", 0))) * 0.001
    created_at = getattr(memory, "created_at", None)
    recency = 0.0
    if created_at:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (datetime.now(timezone.utc) - created_at).total_seconds() / 86400)
        recency = 0.025 * math.exp(-age_days / 180)
    layer = getattr(memory, "layer", "semantic")
    layer_boost = {"preference": 0.012, "episodic": 0.008}.get(layer, 0.0)
    return importance + confidence + access_count + recency + layer_boost


def rank_memories(memories: list[CompanionMemory], query: str, limit: int = 8) -> list[CompanionMemory]:
    """Rank relevant facts using local vectors when available and lexical fallback otherwise."""
    query_vector = embed_text(query)
    scored: list[tuple[float, CompanionMemory]] = []

    if query_vector is not None:
        query_tokens = _tokens(query)
        for memory in memories:
            if memory.embedding:
                score = cosine_similarity(query_vector, memory.embedding)
            else:
                memory_tokens = _tokens(memory.content)
                overlap = sum(min(count, memory_tokens[token]) for token, count in query_tokens.items())
                coverage = overlap / max(1, sum(query_tokens.values()))
                score = min(0.35, coverage * 0.35)
            score += _memory_boost(memory)
            scored.append((score, memory))

        if scored:
            scored.sort(key=lambda item: (item[0], item[1].importance, item[1].created_at), reverse=True)
            relevant = [memory for score, memory in scored if score >= 0.18]
            return relevant[:limit]

    query_tokens = _tokens(query)
    for memory in memories:
        memory_tokens = _tokens(memory.content)
        overlap = sum(min(count, memory_tokens[token]) for token, count in query_tokens.items())
        coverage = overlap / max(1, sum(query_tokens.values()))
        score = (coverage * 5.0) + _memory_boost(memory) * 5
        if overlap:
            score += 0.5
        scored.append((score, memory))

    scored.sort(key=lambda item: (item[0], item[1].importance, item[1].created_at), reverse=True)
    relevant = [memory for score, memory in scored if score >= 0.25]
    return relevant[:limit]
