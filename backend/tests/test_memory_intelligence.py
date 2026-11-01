import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.memory_intelligence import find_memory_matches, layer_for_category


def saved_memory(content: str, *, category: str = "personal_context"):
    return SimpleNamespace(
        id="memory-1",
        category=category,
        content=content,
        embedding=None,
    )


class MemoryIntelligenceTests(unittest.TestCase):
    @patch("app.services.memory_intelligence.embed_text", return_value=None)
    def test_detects_possible_polarity_change_without_overwriting(self, _embed):
        existing = saved_memory("کاربر موسیقی سنتی را دوست دارد")
        matches = find_memory_matches("کاربر موسیقی سنتی را دوست ندارد", [existing])
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["kind"], "potential_conflict")
        self.assertEqual(existing.content, "کاربر موسیقی سنتی را دوست دارد")

    @patch("app.services.memory_intelligence.embed_text", return_value=None)
    def test_detects_duplicate_memory(self, _embed):
        existing = saved_memory("من موسیقی سنتی را دوست دارم")
        matches = find_memory_matches("من موسیقی سنتی را دوست دارم", [existing])
        self.assertEqual(matches[0]["kind"], "duplicate")

    @patch("app.services.memory_intelligence.embed_text", return_value=None)
    def test_does_not_flag_unrelated_facts(self, _embed):
        existing = saved_memory("کاربر رنگ آبی را دوست دارد")
        matches = find_memory_matches("کاربر موسیقی سنتی را دوست دارد", [existing])
        self.assertEqual(matches, [])

    @patch("app.services.memory_intelligence.embed_text", return_value=None)
    def test_related_memory_is_reviewed_without_being_called_a_conflict(self, _embed):
        existing = saved_memory("کاربر موسیقی سنتی را دوست دارد")
        matches = find_memory_matches("کاربر موسیقی سنتی را خیلی دوست دارد", [existing])
        self.assertEqual(matches[0]["kind"], "related")

    def test_memory_layer_is_derived_from_category(self):
        self.assertEqual(layer_for_category("preference"), "preference")
        self.assertEqual(layer_for_category("important_event"), "episodic")
        self.assertEqual(layer_for_category("shared_story"), "episodic")
        self.assertEqual(layer_for_category("personal_context"), "semantic")


if __name__ == "__main__":
    unittest.main()
