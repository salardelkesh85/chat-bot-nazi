import re
from collections import Counter

from app.models import CompanionMemory
from app.services.semantic_memory import cosine_similarity, embed_text

_TOKEN_RE = re.compile(r"[\\wآ-ی]{2,}", re.UNICODE)

def _tokens(text: str) -> Counter[str]:
    return Counter(token.casefold() for token in _TOKEN_RE.findall(text or ""))

def rank_memories(memories: list[CompanionMemory], query: str, limit: int = 8) -> list[CompanionMemory]:
    """Prefer local multilingual vector similarity; fall back to lexical ranking."""
    query_vector = embed_text(query)
    scored: list[tuple[float, CompanionMemory]] = []
    if query_vector is not None:
        for memory in memories:
            vector = memory.embedding
            if vector:
                score = cosine_similarity(query_vector, vector)
                score += max(1, min(5, memory.importance)) * 0.008
                scored.append((score, memory))
        if scored:
            scored.sort(key=lambda item: (item[0], item[1].importance, item[1].created_at), reverse=True)
            return [memory for score, memory in scored if score >= 0.18][:limit]

    query_tokens = _tokens(query)
    for memory in memories:
        memory_tokens = _tokens(memory.content)
        overlap = sum(min(count, memory_tokens[token]) for token, count in query_tokens.items())
        coverage = overlap / max(1, sum(query_tokens.values()))
        score = (coverage * 5.0) + (max(1, min(5, memory.importance)) * 0.12)
        if overlap:
            score += 0.5
        scored.append((score, memory))
    scored.sort(key=lambda item: (item[0], item[1].importance, item[1].created_at), reverse=True)
    relevant = [memory for score, memory in scored if score >= 0.25]
    if not relevant:
        relevant = [memory for _, memory in scored]
    return relevant[:limit]
