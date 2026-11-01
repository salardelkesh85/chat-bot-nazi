"""Optional local semantic memory using a locally stored SentenceTransformer model.

No embedding API or remote inference is used. If the optional package or model
folder is missing, callers transparently retain the lexical retrieval fallback.
"""
from functools import lru_cache
from pathlib import Path
from typing import Sequence
import math

from app.core.config import BACKEND_DIR

MODEL_DIR = BACKEND_DIR / "models" / "paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def _model():
    if not MODEL_DIR.is_dir():
        return None
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    try:
        return SentenceTransformer(str(MODEL_DIR), local_files_only=True)
    except Exception:
        return None


def semantic_available() -> bool:
    return _model() is not None


def embed_text(text: str) -> list[float] | None:
    model = _model()
    if model is None or not text.strip():
        return None
    vector = model.encode(text, normalize_embeddings=True)
    return [float(value) for value in vector.tolist()]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
