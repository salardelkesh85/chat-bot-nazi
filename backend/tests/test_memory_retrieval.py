import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.services.memory_retrieval import rank_conversation_messages, rank_memories
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



class ConversationRecallTests(unittest.TestCase):
    @patch("app.services.memory_retrieval.embed_text", return_value=None)
    def test_lexical_recall_searches_messages_from_older_sessions(self, _embed):
        now = datetime.now(timezone.utc)
        messages = [
            SimpleNamespace(
                content="امروز درباره موسیقی سنتی صحبت کردیم",
                embedding=None,
                created_at=now,
                session_id="older-session",
                role="user",
            ),
            SimpleNamespace(
                content="رنگ آبی برای طراحی مناسب است",
                embedding=None,
                created_at=now,
                session_id="other-session",
                role="assistant",
            ),
        ]
        results = rank_conversation_messages(messages, "موسیقی سنتی", limit=3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].session_id, "older-session")

    @patch("app.services.memory_retrieval.embed_text", return_value=[1.0, 0.0])
    def test_semantic_recall_prefers_matching_message_embedding(self, _embed):
        now = datetime.now(timezone.utc)
        messages = [
            SimpleNamespace(content="مورد نامرتبط", embedding=[0.0, 1.0], created_at=now),
            SimpleNamespace(content="مورد مرتبط", embedding=[1.0, 0.0], created_at=now),
        ]
        results = rank_conversation_messages(messages, "پرسش", limit=2)
        self.assertEqual(results[0].content, "مورد مرتبط")



class PersonalityConfigTests(unittest.TestCase):
    def test_default_personality_settings(self):
        from app.schemas import PersonalityConfig
        config = PersonalityConfig()
        self.assertEqual(config.preset, "custom")
        self.assertEqual(config.warmth, 70)

    def test_personality_slider_bounds_are_validated(self):
        from pydantic import ValidationError
        from app.schemas import PersonalityConfig
        with self.assertRaises(ValidationError):
            PersonalityConfig(humor=101)

    def test_personality_presets_are_restricted(self):
        from pydantic import ValidationError
        from app.schemas import PersonalityConfig
        with self.assertRaises(ValidationError):
            PersonalityConfig(preset="unknown")


if __name__ == "__main__":
    unittest.main()
