import re
from collections import Counter

from app.models import CompanionMemory


_TOKEN_RE = re.compile(r"[\wآ-ی]{2,}", re.UNICODE)


def _tokens(text: str) -> Counter[str]:
    return Counter(token.casefold() for token in _TOKEN_RE.findall(text or ""))


def rank_memories(memories: list[CompanionMemory], query: str, limit: int = 8) -> list[CompanionMemory]:
    """Rank saved memories by lexical relevance, then importance and recency.

    This is a lightweight local retrieval baseline, not vector/embedding search.
    """
    query_tokens = _tokens(query)
    scored: list[tuple[float, CompanionMemory]] = []

    for memory in memories:
        memory_tokens = _tokens(memory.content)
        overlap = sum(min(count, memory_tokens[token]) for token, count in query_tokens.items())
        coverage = overlap / max(1, sum(query_tokens.values()))
        # Importance keeps durable facts available when the current query is vague.
        score = (coverage * 5.0) + (max(1, min(5, memory.importance)) * 0.12)
        if overlap:
            score += 0.5
        scored.append((score, memory))

    scored.sort(key=lambda item: (item[0], item[1].importance, item[1].created_at), reverse=True)
    relevant = [memory for score, memory in scored if score >= 0.25]
    if not relevant:
        relevant = [memory for _, memory in scored]
    return relevant[:limit]
