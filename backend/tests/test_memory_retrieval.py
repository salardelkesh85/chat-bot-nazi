import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.services.memory_retrieval import rank_memories
from app.services.semantic_memory import cosine_similarity


class SemanticMemoryTests(unittest.TestCase):
    def test_cosine_similarity_normalized_vectors(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)

    @patch("app.services.memory_retrieval.embed_text", return_value=None)
    def test_lexical_fallback_finds_persian_memory(self, _embed):
        now = datetime.now(timezone.utc)
        memories = [
            SimpleNamespace(content="کاربر عاشق موسیقی سنتی است", importance=4, created_at=now, embedding=None),
            SimpleNamespace(content="کاربر رنگ آبی را دوست دارد", importance=3, created_at=now, embedding=None),
        ]
        results = rank_memories(memories, "موسیقی سنتی", limit=2)
        self.assertEqual(results[0].content, "کاربر عاشق موسیقی سنتی است")

    @patch("app.services.memory_retrieval.embed_text", return_value=[1.0, 0.0])
    def test_semantic_ranking_uses_stored_vectors(self, _embed):
        now = datetime.now(timezone.utc)
        memories = [
            SimpleNamespace(content="مورد اول", importance=3, created_at=now, embedding=[0.0, 1.0]),
            SimpleNamespace(content="مورد دوم", importance=3, created_at=now, embedding=[1.0, 0.0]),
        ]
        results = rank_memories(memories, "پرسش", limit=2)
        self.assertEqual(results[0].content, "مورد دوم")


if __name__ == "__main__":
    unittest.main()
